CREATE TABLE IF NOT EXISTS environmental_readings (
    id BIGSERIAL PRIMARY KEY,
    zone_id INTEGER NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    temperature_c DOUBLE PRECISION,
    noise_db DOUBLE PRECISION,
    updated_at TIMESTAMPTZ NOT NULL
);


CREATE TABLE IF NOT EXISTS occupancy_readings (
    hour_str VARCHAR(13) PRIMARY KEY,
    occupant_count INTEGER NOT NULL CHECK (occupant_count >= 0),
    updated_at TIMESTAMPTZ NOT NULL
);

