from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "gmail_accounts" (
    "id" UUID NOT NULL PRIMARY KEY,
    "email_address" VARCHAR(255) NOT NULL,
    "meta" JSONB NOT NULL,
    "token_expiry" TIMESTAMPTZ NOT NULL,
    "status" VARCHAR(20) NOT NULL DEFAULT 'active',
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_gmail_accou_user_id_a01825" UNIQUE ("user_id", "email_address")
);
CREATE INDEX IF NOT EXISTS "idx_gmail_accou_email_a_2b7994" ON "gmail_accounts" ("email_address");
CREATE INDEX IF NOT EXISTS "idx_gmail_accou_token_e_7ed335" ON "gmail_accounts" ("token_expiry");
CREATE INDEX IF NOT EXISTS "idx_gmail_accou_user_id_a01825" ON "gmail_accounts" ("user_id", "email_address");
CREATE INDEX IF NOT EXISTS "idx_gmail_accou_token_e_ad6525" ON "gmail_accounts" ("token_expiry", "status");
COMMENT ON COLUMN "gmail_accounts"."status" IS 'ACTIVE: active\nEXPIRED: expired\nERROR: error\nDISCONNECTED: disconnected';
COMMENT ON TABLE "gmail_accounts" IS 'Stores the Gmail account information for the user';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "gmail_accounts";"""
