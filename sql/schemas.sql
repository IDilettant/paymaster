--SELECT 'CREATE DATABASE treasury;'
--WHERE NOT EXISTS (SELECT * FROM pg_database WHERE datname = 'treasury';)\gexec  --CREATE DATABASE IF NOT EXISTS treasury; ?


DROP TABLE IF EXISTS accounts, transactions, currencies;


CREATE TABLE accounts (
    id              SERIAL          PRIMARY KEY,
    user_id         INTEGER         NOT NULL UNIQUE,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP(2)
);


CREATE TABLE transactions (
    id              SERIAL          PRIMARY KEY,
    account_id      INTEGER         NOT NULL,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP(2),
    deal_with       INTEGER         NOT NULL,
    description     VARCHAR(255)    NOT NULL,
    qty_change      BIGINT          NOT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts (id)
);


CREATE TABLE currencies (
    cur_name        VARCHAR(3)      PRIMARY KEY,
    rate_to_base    DECIMAL         NOT NULL,
    updated_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP(2)
);
