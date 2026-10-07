# Neon database activation, 6 October 2026

- Provisioned `reef-notebooks` on Neon's `free_v3` plan in `iad1` and connected it only to Reef's Vercel production environment. Neon Auth is disabled; Reef uses its existing Better Auth passkey implementation.
- Stored the pooled connection as the sensitive server variable `REEF_DATABASE_URL`. The account origin is `https://getreef.xyz`.
- Applied both checked-in SQL schemas in one transaction.
- The real PostgreSQL check passed save/reopen, owner isolation, stale-write rejection, trash and restore. All test writes were rolled back.
- Production discovery returned `enabled: true`; unauthenticated notebook access returned 401 and foreign-origin signup returned 403.
- Initial live passkey endpoint checks revealed missing nested Vercel routing. Added an explicit rewrite and auth handler. The corrected production endpoint returned HTTP 200, a WebAuthn challenge and relying-party ID `getreef.xyz`. The signup and sign-in controls are visible in the live notebook UI. Deployment: `dpl_3qM6jEZ5hA4ZPaaYWmiUXroAcUhR`.
- The seven account and notebook automated tests passed.

Still requires a human device test: passkey registration, sign-in, secondary passkey, authenticated browser save/reopen and sign-out. Cross-device behavior and provider backup restoration are not yet verified. Email recovery is not configured. Database storage does not guarantee permanent retention; keep exports.
