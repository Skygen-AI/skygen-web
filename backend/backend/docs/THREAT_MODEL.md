## Threat Model

Assets:

- User accounts and credentials
- Device tokens (JWT with JTI)
- Artifacts in object storage (presigned S3)
- Audit logs in ClickHouse

Adversaries:

- Network attacker (MitM)
- Compromised endpoint (malware)
- Malicious insider (admin/user)

Controls:

- TLS everywhere, HSTS at edge
- Short-lived access JWT; opaque refresh rotated on use
- Device token revocation via Redis; `kid`-based key rotation
- Policy engine (server + local) to gate dangerous actions
- Immutable audit sink; alerts on anomalous behavior

Out of scope (today):

- Supply chain compromise; mitigate with SBOM and signature verification
- Rooted devices; mitigate with posture checks (future)
