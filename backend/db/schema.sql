CREATE TABLE libraries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    code VARCHAR(50) UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE zones (
    id SERIAL PRIMARY KEY,
    library_id INTEGER NOT NULL REFERENCES libraries(id) ON DELETE CASCADE,
    zone_name VARCHAR(120) NOT NULL,
    floor_label VARCHAR(20) NOT NULL,
    zone_type VARCHAR(50) NOT NULL,      -- quiet / discussion / open / etc.
    capacity INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE occupancy_snapshots (
    id BIGSERIAL PRIMARY KEY,
    zone_id INTEGER NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
    observed_at TIMESTAMP NOT NULL,
    occupied_count INTEGER NOT NULL,
    available_count INTEGER,
    occupancy_rate NUMERIC(5,4),
    source_type VARCHAR(30) NOT NULL,    -- sensor / gate / manual / fused
    confidence_score NUMERIC(5,4),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE forecast_runs (
    id BIGSERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    trained_at TIMESTAMP,
    generated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    horizon_minutes INTEGER NOT NULL,
    notes TEXT
);

CREATE TABLE occupancy_forecasts (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES forecast_runs(id) ON DELETE CASCADE,
    zone_id INTEGER NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
    forecast_for TIMESTAMP NOT NULL,
    predicted_occupied_count NUMERIC(8,2),
    predicted_occupancy_rate NUMERIC(5,4),
    lower_bound NUMERIC(8,2),
    upper_bound NUMERIC(8,2),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE user_preferences (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(120),
    study_preference VARCHAR(50) NOT NULL,
    preferred_floor VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);