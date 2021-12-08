CREATE TYPE status AS ENUM ('active', 'deleted');


CREATE TABLE accounts (
    id              SERIAL          PRIMARY KEY,
    user_id         INTEGER         NOT NULL,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP(2),
    current_status  status          DEFAULT 'active'
);


CREATE UNIQUE INDEX active_account_index ON accounts (user_id)
    WHERE current_status = 'active';


CREATE TABLE transactions (
    id              SERIAL          PRIMARY KEY,
    account_id      INTEGER         NOT NULL REFERENCES accounts,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP(2),
    deal_with       INTEGER         NOT NULL REFERENCES accounts,
    description     VARCHAR(255)    NOT NULL,
    qty_change      BIGINT          NOT NULL
);


CREATE TABLE currencies (
    cur_name        VARCHAR(3)      PRIMARY KEY,
    rate_to_base    DECIMAL         NOT NULL,
    updated_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP(2)
);
