CREATE TABLE bmc_helix_transactions (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    service_code VARCHAR(100),
    event_id VARCHAR(100),
    status VARCHAR(100),
    incident_id VARCHAR(100),
    request JSON,
    response JSON
);

CREATE INDEX idx_service_code ON bmc_helix_transactions (service_code);