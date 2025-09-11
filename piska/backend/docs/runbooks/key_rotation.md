## Device JWT Key Rotation

Steps:

1. Generate a new random 256-bit secret
2. Add to `DEVICE_JWT_KEYS.keys` as `vN`
3. Set `active_kid` to `vN` and deploy
4. Optionally revoke old device JTIs to force reconnection
5. Monitor audit logs for revoked connections

Rollback: set `active_kid` to the previous key id.
