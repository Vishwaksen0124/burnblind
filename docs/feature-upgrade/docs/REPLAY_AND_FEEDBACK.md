# Blind Spot Replay + Human Feedback

## Replay

Purpose: show judges and operators how an event evolved.

Controls:
- date
- time
- play/pause
- previous/next
- speed

Example:

```text
15:42 observation
15:54 independent sensor
16:00 candidate
16:02 scoring
16:03 priority
16:04 investigation
16:05 recommendation
```

Replay must use real historical timestamps and be labelled `HISTORICAL REPLAY`.

## Human outcome

After investigation:

```text
CONFIRMED
FALSE_POSITIVE
NEEDS_VERIFICATION
INSUFFICIENT_EVIDENCE
```

Persist:

- event ID
- outcome
- timestamp
- notes
- scoring version
- investigation version

Do not automatically retrain during the hackathon. Use outcomes for evaluation and future threshold/model improvement.
