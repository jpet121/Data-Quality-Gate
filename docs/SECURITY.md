# Data safety, control limitations and extension policy

- The demo has no permission to operate on live enterprise accounts and no outbound network connector. Never route its synthetic cases to corporate systems.
- Raw strings are hashed and never echoed into rejection messages. Event trace contains token **names** and version IDs, not rejected values. Transform records are hash-only. Validated accepted records can contain identifiers; therefore stdout and database are still sensitive destinations when wired to real data. Protect them accordingly.
- A configuration snapshot is immutable for a processing batch. The allowed class registry and exact-match grammar are code-defined; external JSON cannot run a regex, eval or plugin.
- Application-level key idempotency is not a substitute for source authentication, signature checking, identity authorization or transport replay protection.
- SQLite uses a serialized immediate transaction and foreign keys. Demonstration path uses local filesystem and no multi-process adversarial deployment review.
- Audit metadata is not cryptographically signed; SHA-256 digests make accidental differences observable but do not establish provenance authenticity.
- Operator must define real schema and policies externally, approve them, assess privacy controls and verify production integration before enabling any actual effects.
