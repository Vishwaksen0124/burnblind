# BurnBlind — Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| Historical source schema changes | High | Pin source version/checksum and manifest |
| Sensor disagreement misinterpreted | Critical | Spatial/temporal matching + scientific caveat |
| Future-data leakage | Critical | Timestamp cutoff + temporal holdout |
| Weather unavailable | Medium | Degrade exposure confidence |
| Population estimate stale | Medium | Show source/year |
| Agent hallucination | Critical | Deterministic tools + evaluation |
| Agent unavailable | Medium | Keep deterministic event path |
| SQS duplicate | Medium | Idempotency keys |
| Model cost spike | High | Trigger gating + quotas |
| Large satellite data | High | Small samples first + S3 |
| Lambda package too large | Medium | Separate heavy processing from API |
| Public API abuse | High | Validation + controlled public surface |
| Generic frontend | Medium | Thermal/operations design system |
| Live dependency fails | High | Deterministic replay mode |
| Eligibility uncertainty | Critical | Verify Builder Center before submission |
