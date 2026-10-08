# Canonical contracts

The canonical typed contracts currently live in `backend/common/models.py` so
validation logic has one source of truth. Contract fixtures in tests are
synthetic and explicitly labeled; they are not environmental observations.

JSON Schema exports can be added alongside these models if an external data
exchange requires them. Avoid maintaining a second schema definition by hand.
