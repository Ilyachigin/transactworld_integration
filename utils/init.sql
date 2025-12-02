PRAGMA auto_vacuum = FULL;

CREATE TABLE IF NOT EXISTS merchant_tokens (
    gateway_token TEXT PRIMARY KEY,
    bearer_token TEXT NOT NULL,
    auth_token TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS auth_tokens (
    login TEXT NOT NULL,
    token TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    PRIMARY KEY (login)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_auth_tokens_login_key
    ON auth_tokens(login);