# Phoenix ETL - Transaction Data Contract

## 1. Purpose

This data contract defines the structure, constraints, and processing rules for transaction data processed by the Phoenix ETL Framework.

## 2. Source Schema

| Field | Data Type | Required | Business Rule |
|---|---|---:|---|
| transaction_id | string | Yes | Unique transaction identifier |
| customer_id | string | Yes | Must identify a valid customer |
| amount | decimal | Yes | Must be greater than or equal to 0 |
| currency | string | Yes | Valid currency code |
| timestamp | datetime | Yes | Transaction timestamp |
| source_updated_at | datetime | Yes | Timestamp of latest source version |

## 3. Validation Rules

### transaction_id

- Must not be null.
- Must not be empty.
- Must uniquely identify a transaction.

### customer_id

- Must not be null.
- Must not be empty.
- Must reference a valid customer.

### amount

- Must not be null.
- Must be greater than or equal to 0.
- Negative values are rejected.
- The pipeline must not silently convert negative values.

### currency

- Must not be null.
- Must contain a valid currency code.

### timestamp

- Must not be null.
- Must contain a valid datetime value.

### source_updated_at

- Must not be null.
- Used to determine whether an incoming record is newer than the existing database record.

## 4. Processing Rules

### New Transaction

If `transaction_id` does not exist:

    INSERT

### Existing Transaction

If `transaction_id` already exists:

- If incoming `source_updated_at` is newer -> UPDATE.
- If incoming `source_updated_at` is equal to or older -> IGNORE.

### Invalid Records

Invalid records must not enter the target transaction table.

They must be written to the rejected-records store together with:

- Original record
- Rejection reason
- Source file
- Pipeline run ID
- Rejection timestamp

## 5. Failure Handling

If PostgreSQL is temporarily unavailable:

1. Retry the database operation.
2. Use controlled retry intervals.
3. Log the failure.
4. Do not silently discard the input data.
5. Fail the pipeline if the database remains unavailable.

## 6. Idempotency

Processing the same source file multiple times must not create duplicate transactions.

`transaction_id` identifies the business transaction.

`source_updated_at` identifies the version of the transaction received from the source.

The combination of these fields is used to determine whether an incoming record should be inserted, updated, or ignored.
