# Backend Build Prompt

Read all V2 docs before coding.

Extend the existing pipeline:
data → features → scoring → impact → priority → investigation.

Implement in this order:
1. provenance
2. sensor comparison
3. blind spot score
4. exposure corridor
5. action-center API
6. investigation trigger policy
7. real Strands + real model provider
8. structured investigation persistence
9. telemetry
10. replay
11. human review

Do not move deterministic scoring into the LLM. Do not fabricate missing data. Keep provider selection configurable.
