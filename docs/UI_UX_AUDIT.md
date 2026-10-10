# BurnBlind UI/UX Audit

Updated: 2026-10-10

## Scope inspected

Inspected the React/Vite frontend routes, shared header, monitoring candidate queue, investigation list, event review page, the two global stylesheets, and Amplify hosting configuration. Current primary views are `/`, `/monitoring`, `/replay`, `/investigations`, `/investigations/{event_id}`, `/how-it-works`, and `/methodology`.

## Findings and changes

| Severity | Area | Finding | Change |
|---|---|---|---|
| High | Investigation queue | Reports were rendered as large bordered cards with a multi-line summary and a visually prominent full action button. Reviewers had to scan repeated containers to compare state. | Replaced each card with a compact aligned row: candidate and observation time, truncated report summary, review state/outcome, and a small dedicated-page action. Filters now read as compact tabs with counts. |
| High | Investigation queue data | The list API omitted event details, leaving each row with the same generic “Candidate event” label and request time instead of location and observation time. | Added one batched event lookup to the investigation-list response and show coordinates and observation time. The UI does not issue one request per row. |
| High | Page routing | The application encoded product pages and event review routes in the URL fragment, which made direct paths unavailable and obscured the route from links. Amplify had no SPA fallback rule. | Migrated product pages to clean paths, added history/popstate navigation, and configured the Amplify SPA rewrite. Landing-page section jumps remain fragments by design. |
| Medium | Monitoring queue | Candidate rows were at least 82px high with generous padding; event status metadata made the queue unnecessarily tall. | Reduced candidate row height and tightened metadata spacing while keeping location/source and deterministic triage visible. |
| Medium | Review status | Duplicate `.human-review` rules across both global stylesheets produced inconsistent type and control sizing. | Removed the obsolete duplicate rules; the reviewer queue, decision form, and saved outcome styles now live together in `reviewer.css`. |
| Medium | Typography and hierarchy | Reviewer list headings, labels, descriptions, and actions had competing sizes and weights; repeated card boundaries reduced hierarchy. | Set the queue to a restrained 11–14px scan hierarchy and use separators instead of nested card chrome. |

## Files changed for this refinement

- `frontend/src/App.jsx` — clean pathname routes, History API handling, and not-found state.
- `frontend/src/components/shared.jsx` — brand and global page links now use paths.
- `frontend/src/components/ProductPage.jsx` — product navigation calls use paths; section anchors remain local.
- `frontend/src/components/SupportingPages.jsx` — investigation queue uses compact rows and opens `/investigations/{event_id}`.
- `frontend/src/reviewer.css` — compact queue and candidate styles, including narrow-screen layout.
- `frontend/src/main.jsx` — loads reviewer styles after shared feature styles.
- `backend/api/handler.py`, `backend/api/repository.py`, `backend/api/dynamodb_repository.py` — attach candidate metadata through a single batch lookup.
- `tests/unit/test_api.py`, `tests/unit/test_dynamodb_repository.py` — verify event summaries and one-call batch lookup.

## Validation

- `npm run build` (frontend) — passed; Vite transformed 1,968 modules and produced the production bundle.
- Current unit suite — 102 passed.
- Browser visual inspection at 1440px and 390px — completed for the investigation queue; the compact rows remain readable at both sizes.
- Additional investigation queue inspection at 1280px and 768px found and fixed a tablet-width candidate/summary collision; the 768px queue was recaptured and checked after the fix.
- Browser visual inspection at 1440px and 390px — completed for a real event review, including source evidence, saved-review state, and mobile stacking.
- Browser visual inspection at 1440px — completed for populated monitoring data; candidate queue rows are compact and map markers remain visible.
- Production API read checks — `/investigations?limit=50` and `/events?limit=1` returned HTTP 200 with real records.
- The path-routing batch (commit `7bbc717`) passed GitHub Actions and Amplify deployment; production returned HTTP 200 for `/`, `/monitoring`, `/investigations`, `/investigations/{event_id}`, `/how-it-works`, and `/methodology`. The subsequent batch adding batched event summaries is awaiting deployment verification.
- No separate frontend lint or test script is defined in `frontend/package.json`; the production build is the available frontend check.

## Remaining review items

- Browser screenshots were inspected locally at 1440px, 1280px, 768px, and 390px. Production direct-route responses were checked, but a production browser session with Cognito reviewer authentication was not exercised.
- Verify event coordinates and observation time in the live investigation list after the backend batch deploys.
- Accessibility/color-contrast review remains to be completed after screenshot inspection.
