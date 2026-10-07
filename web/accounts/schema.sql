-- Better Auth's tables are generated separately with the pinned Better Auth CLI.
-- Apply this after the authentication migration. Deleting an account removes its notebooks.
CREATE TABLE IF NOT EXISTS reef_notebook (
 id uuid PRIMARY KEY,
 user_id text NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
 title varchar(100) NOT NULL,
 data jsonb NOT NULL,
 version integer NOT NULL DEFAULT 1,
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 deleted_at timestamptz
);
CREATE INDEX IF NOT EXISTS reef_notebook_owner ON reef_notebook(user_id,updated_at DESC);
CREATE TABLE IF NOT EXISTS reef_signup (
 id uuid PRIMARY KEY,
 name varchar(80) NOT NULL,
 binding_hash text NOT NULL,
 expires_at timestamptz NOT NULL,
 consumed_at timestamptz
);
CREATE TABLE IF NOT EXISTS reef_signup_limit (
 id text PRIMARY KEY,
 count integer NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS reef_signup_limit_age ON reef_signup_limit(created_at);
