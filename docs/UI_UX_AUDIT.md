# BurnBlind UI/UX Audit

Updated: 2026-10-10

## Scope inspected

Inspected the React/Vite frontend routes, shared header, monitoring candidate queue, investigation list, event review page, the two global stylesheets, and Amplify hosting configuration. Current primary views are `/`, `/monitoring`, `/replay`, `/investigations`, `/investigations/{event_id}`, `/how-it-works`, and `/methodology`.

## Findings and changes

| Severity | Area | Finding | Change |
|---|---|---|---|
| High | Investigation queue | Reports were rendered as large bordered cards with a multi-line summary and a visually prominent full action button. Reviewers had to scan repeated containers to compare state. | Replaced each card with a compact aligned row: candidate and observation time, truncated report summary, review state/outcome, and a small dedicated-page action. Filters now read as compact tabs with counts. |
| High | Page routing | The application encoded product pages and event review routes in the URL fragment, which made direct paths unavailable and obscured the route from links. Amplify had no SPA fallback rule. | Migrated product pages to clean paths, added history/popstate navigation, and configured the Amplify SPA rewrite. Landing-page section jumps remain fragments by design. |
| Medium | Monitoring queue | Candidate rows were at least 82px high with generous padding; event status metadata made the queue unnecessarily tall. | Reduced candidate row height and tightened metadata spacing while keeping location/source and deterministic triage visible. |
| Medium | Review status | Old `.human-review` declarations in `features.css` overrode newer declarations in `styles.css`, producing inconsistent type and control sizing. | Confirmed the cascade issue; consolidated review-page visual overrides into a dedicated stylesheet loaded last so the review flow has one explicit precedence layer. Existing legacy rules remain and should be consolidated during a focused stylesheet cleanup. |
| Medium | Typography and hierarchy | Reviewer list headings, labels, descriptions, and actions had competing sizes and weights; repeated card boundaries reduced hierarchy. | Set the queue to a restrained 11–14px scan hierarchy and use separators instead of nested card chrome. |

## Files changed for this refinement

- `frontend/src/App.jsx` — clean pathname routes, History API handling, and not-found state.
- `frontend/src/components/shared.jsx` — brand and global page links now use paths.
- `frontend/src/components/ProductPage.jsx` — product navigation calls use paths; section anchors remain local.
- `frontend/src/components/SupportingPages.jsx` — investigation queue uses compact rows and opens `/investigations/{event_id}`.
- `frontend/src/reviewer.css` — compact queue and candidate styles, including narrow-screen layout.
- `frontend/src/main.jsx` — loads reviewer styles after shared feature styles.

## Validation

Validation commands and actual outcomes will be recorded after the production build, local route checks, viewport inspection, and Amplify deployment complete.

## Remaining review items

- Verify each route on desktop and mobile in a browser, including refreshing a deep event-review path.
- Verify API-backed data, report status, failed investigation state, and review outcomes in the live environment.
- Review and remove obsolete duplicate stylesheet declarations after the visual behavior is stable.
- Accessibility/color-contrast review remains to be completed after screenshot inspection.
