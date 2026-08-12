CREATE TABLE IF NOT EXISTS phoenix.pipeline_runs (
    pipeline_run_id VARCHAR(100) PRIMARY KEY,
    source_file TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    total_records INTEGER NOT NULL DEFAULT 0,
    valid_records INTEGER NOT NULL DEFAULT 0,
    rejected_records INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,

    CONSTRAINT pipeline_runs_status_check
        CHECK (status IN ('STARTED', 'COMPLETED', 'FAILED')),

    CONSTRAINT pipeline_runs_total_check
        CHECK (total_records >= 0),

    CONSTRAINT pipeline_runs_valid_check
        CHECK (valid_records >= 0),

    CONSTRAINT pipeline_runs_rejected_check
        CHECK (rejected_records >= 0),

    CONSTRAINT pipeline_runs_counts_check
        CHECK (valid_records + rejected_records <= total_records)
);
