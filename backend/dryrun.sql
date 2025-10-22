CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 38bfc3b56da1

CREATE TABLE ota_channels (
    id INTEGER NOT NULL, 
    code VARCHAR(50) NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (code)
);

CREATE TABLE ota_commissions (
    id INTEGER NOT NULL, 
    channel_id INTEGER NOT NULL, 
    rate FLOAT NOT NULL, 
    effective_date DATE NOT NULL, 
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(channel_id) REFERENCES ota_channels (id) ON DELETE CASCADE
);

CREATE INDEX ix_ota_commissions_channel_date ON ota_commissions (channel_id, effective_date);

INSERT INTO alembic_version (version_num) VALUES ('38bfc3b56da1') RETURNING version_num;

-- Running upgrade 38bfc3b56da1 -> 2bf033a72e6e

UPDATE alembic_version SET version_num='2bf033a72e6e' WHERE alembic_version.version_num = '38bfc3b56da1';

-- Running upgrade 2bf033a72e6e -> e86edf299644

CREATE TABLE ota_commissions (
    id INTEGER NOT NULL, 
    channel_id INTEGER NOT NULL, 
    valid_from DATE NOT NULL, 
    valid_to DATE NOT NULL, 
    rate FLOAT NOT NULL, 
    note TEXT, 
    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(channel_id) REFERENCES ota_channels (id) ON DELETE CASCADE
);

CREATE INDEX ix_ota_commissions_channel_id ON ota_commissions (channel_id);

CREATE INDEX ix_ota_commissions_id ON ota_commissions (id);

CREATE INDEX ix_ota_commissions_channel_id ON ota_commissions (channel_id);

CREATE INDEX ix_ota_commissions_valid_from ON ota_commissions (valid_from);

CREATE INDEX ix_ota_commissions_valid_to ON ota_commissions (valid_to);

CREATE INDEX ix_ota_commissions_channel_period ON ota_commissions (channel_id, valid_from, valid_to);

UPDATE alembic_version SET version_num='e86edf299644' WHERE alembic_version.version_num = '2bf033a72e6e';

-- Running upgrade e86edf299644 -> 2322535ac344

CREATE TABLE IF NOT EXISTS sales_front (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      business_date TEXT NOT NULL,
      tag TEXT NOT NULL,
      amount INTEGER NOT NULL
    );

CREATE INDEX IF NOT EXISTS idx_sales_front_date ON sales_front(business_date);

CREATE INDEX IF NOT EXISTS idx_sales_front_tag_date ON sales_front(tag, business_date);

CREATE TABLE IF NOT EXISTS audit_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ts DATETIME NOT NULL,
      actor TEXT NOT NULL,
      action TEXT NOT NULL,
      target TEXT NOT NULL,
      meta_json TEXT
    );

UPDATE alembic_version SET version_num='2322535ac344' WHERE alembic_version.version_num = 'e86edf299644';

-- Running upgrade e86edf299644 -> 20251001_add_commission_period_rate

