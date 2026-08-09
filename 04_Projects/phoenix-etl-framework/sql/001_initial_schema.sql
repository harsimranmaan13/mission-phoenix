CREATE SCHEMA IF NOT EXISTS phoenix;

CREATE TABLE IF NOT EXISTS phoenix.transactions (
    transaction_id VARCHAR(100) PRIMARY KEY,
    customer_id VARCHAR(100) NOT NULL,
    amount NUMERIC(18, 2) NOT NULL CHECK (amount >= 0),
    currency CHAR(3) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    source_updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_transactions_customer_id
    ON phoenix.transactions(customer_id);

CREATE TABLE IF NOT EXISTS phoenix.rejected_records (
    id BIGSERIAL PRIMARY KEY,
    pipeline_run_id VARCHAR(100) NOT NULL,
    source_file TEXT NOT NULL,
    rejected_at TIMESTAMPTZ NOT NULL,
    transaction_id VARCHAR(100),
    rejection_reason TEXT NOT NULL,
    original_record JSONB NOT NULL
);
