# Passkey accounts and cloud notebooks

Guest research remains available. The header opens account controls. Signup remains unavailable until the server has a database, secret and fixed origin configured. Creating an account does not upload the guest notebook. The user explicitly saves a separate copy.

## Connect infrastructure

1. Choose the permanent HTTPS domain first. Passkeys belong to its hostname. A later hostname change can require enrolling new passkeys.
2. Provision managed PostgreSQL with a pooled connection URL and automated backups. Set `REEF_DATABASE_URL` privately in the server environment. Follow the database provider's TLS instructions.
3. Generate a random server secret of at least 32 characters. Set `BETTER_AUTH_SECRET` and set `BETTER_AUTH_URL` to the exact HTTPS origin, without a hash route. Never use a `VITE_` prefix for these secrets.
4. In an environment containing that database URL, run `node web/accounts/migrate.mjs`. The migration applies the reviewed, checked-in SQL in one transaction. `generate-schema.mjs` regenerates the auth schema from the pinned library version; review schema changes before applying them to an existing database.
5. Optionally set `RESEND_API_KEY` and `REEF_EMAIL_FROM` for a verified sending domain. Without them, email recovery is unavailable. Users should add a second passkey. Recovery links are available only for a verified recovery address.
6. Redeploy Vercel. Its account endpoints run on Node; the Cloudflare research Worker does not implement accounts.

## Storage and access

Better Auth and its passkey plugin verify WebAuthn responses. Reef requires device user verification. Session cookies authenticate notebook requests; every notebook query includes the authenticated owner. Signup context expires after ten minutes, is bound to an HttpOnly browser cookie, and can be consumed once. State-changing requests require the configured Origin. Auth and signup limits persist in PostgreSQL.

Named notebooks store up to 200 turns and 2 MB. Saves use a version check: a conflicting write is rejected and the local draft can be saved as another notebook. Browser drafts are scoped to the account and notebook. Signing out clears those drafts after sync; unsynced changes block sign-out. Trash is recoverable, with no automatic purge implemented. JSON export remains available. Cloud storage is not a promise of permanent retention; maintain provider backups and test restoration.

## Activation checks

After migration, run `node web/accounts/check-database.mjs` with the database URL supplied privately in the environment. It tests real save/reopen, owner isolation, stale writes, trash and restore inside one rolled-back transaction. It does not validate passkey enrollment or backup restoration. Never share the connection URL in chat or put it in browser code.

Run `node --test web/accounts/*.test.mjs` and `npm run build --prefix web`. The automated checks cover configuration gating, mutation origins, owner-scoped queries, conflicting saves and notebook validation. They do not replace a real database and browser enrollment test.

Before enabling accounts for users, verify signup and cancelled enrollment, sign-in, a second passkey, verified email recovery if configured, save and reopen across devices, trash and restore, sign-out isolation, and concurrent saves. Verify that a second account cannot read, overwrite or restore the first account's notebook. Test a backup restoration. Enrollment requires a person's device confirmation.
