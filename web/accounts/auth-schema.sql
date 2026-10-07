-- Generated from Better Auth and @better-auth/passkey 1.7.7. Review before applying.

CREATE TABLE IF NOT EXISTS "user" (
 "id" text PRIMARY KEY,
 "name" text NOT NULL,
 "email" text NOT NULL UNIQUE,
 "emailVerified" boolean NOT NULL,
 "image" text,
 "createdAt" timestamptz NOT NULL,
 "updatedAt" timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS "session" (
 "id" text PRIMARY KEY,
 "expiresAt" timestamptz NOT NULL,
 "token" text NOT NULL UNIQUE,
 "createdAt" timestamptz NOT NULL,
 "updatedAt" timestamptz NOT NULL,
 "ipAddress" text,
 "userAgent" text,
 "userId" text NOT NULL REFERENCES "user"("id") ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS "session_userId_idx" ON "session"("userId");

CREATE TABLE IF NOT EXISTS "account" (
 "id" text PRIMARY KEY,
 "accountId" text NOT NULL,
 "providerId" text NOT NULL,
 "userId" text NOT NULL REFERENCES "user"("id") ON DELETE CASCADE,
 "accessToken" text,
 "refreshToken" text,
 "idToken" text,
 "accessTokenExpiresAt" timestamptz,
 "refreshTokenExpiresAt" timestamptz,
 "scope" text,
 "password" text,
 "createdAt" timestamptz NOT NULL,
 "updatedAt" timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS "account_userId_idx" ON "account"("userId");

CREATE TABLE IF NOT EXISTS "verification" (
 "id" text PRIMARY KEY,
 "identifier" text NOT NULL,
 "value" text NOT NULL,
 "expiresAt" timestamptz NOT NULL,
 "createdAt" timestamptz NOT NULL,
 "updatedAt" timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS "verification_identifier_idx" ON "verification"("identifier");

CREATE TABLE IF NOT EXISTS "passkey" (
 "id" text PRIMARY KEY,
 "name" text,
 "publicKey" text NOT NULL,
 "userId" text NOT NULL REFERENCES "user"("id") ON DELETE CASCADE,
 "credentialID" text NOT NULL,
 "counter" double precision NOT NULL,
 "deviceType" text NOT NULL,
 "backedUp" boolean NOT NULL,
 "transports" text,
 "createdAt" timestamptz,
 "aaguid" text
);

CREATE INDEX IF NOT EXISTS "passkey_userId_idx" ON "passkey"("userId");

CREATE INDEX IF NOT EXISTS "passkey_credentialID_idx" ON "passkey"("credentialID");

CREATE TABLE IF NOT EXISTS "rateLimit" (
 "id" text PRIMARY KEY,
 "key" text NOT NULL UNIQUE,
 "count" double precision NOT NULL,
 "lastRequest" bigint NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS "passkey_credential_unique" ON "passkey"("credentialID");
