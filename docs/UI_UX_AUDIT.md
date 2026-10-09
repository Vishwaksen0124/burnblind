# BurnBlind UI/UX Audit

**Audited:** 2026-10-09  
**Implementation inspected:** React 18 + Vite, React Leaflet/Leaflet, `lucide-react`, shared CSS in `frontend/src/styles.css` and `features.css`. No component library is installed.  
**Rendered review:** Local Vite app using the deployed read-only API. Chrome headless captures reviewed at 1440×1100, 768×1024, and 390×844. Desktop captures were made for landing, monitoring, replay, investigations, how-it-works, and methodology. Event detail/report was inspected in source; a selected-event browser state was not captured in this pass.  
**Specification references:** `docs/frontend_implementation.md`, `docs/BurnBlind_FRONTEND_IMPLEMENTATION_SPEC.md`, `docs/API_SPEC.md`, and `docs/feature-upgrade/docs/FRONTEND_IMPLEMENTATION_V2.md`.

This is an audit of the current implementation and observed renders, not a claim that every asynchronous state was browser-rendered. Existing API-backed loading, empty, error, and partial-availability branches were inspected in the corresponding components.

## Existing capability inventory

| Screen | Actual implementation and data | Audit note |
| --- | --- | --- |
| Product landing | Attributed NASA Earth Observatory image, API-backed replay preview, source limitations, links to product sections | Image and warm dark visual identity are useful; headline wraps its final word alone at desktop. Several section labels and body copy are too small. |
| Monitoring | Summary, action-center candidate queue, Leaflet map, sourced map-layer selectors, search/filter, date/source context summaries | Works with real replay data. Marker overlap, undersized text, generic event titles, dense metadata and header compression weaken its primary operational view. |
| Event detail | Inline event panel, event and investigation tabs, evidence IDs, comparison/exposure availability, investigation request/retry, evidence report, reviewer outcome form | This is a real workflow, not a chatbot. The screen needs a rendered interaction check and stronger separation of report summary, sourced evidence, uncertainty, and human action. |
| Investigations | API-backed paginated list; completed, failed, queued/running states; cited evidence summary, recommendations, timestamps and model metadata | The current card header leads with raw event IDs, and summary/metadata typography is small. Page has no list-level search/filter. |
| Replay | Timestamp-sorted API events, play/pause, previous/next, speed, scrubber, map and selectable event detail | Functional and honestly labeled historical. Full replay draws a dense set of individual markers; the counter and map can become visually noisy. |
| How it works | Seven documented application stages with input/output/readiness plus scientific boundary | The two-column grid renders an empty eighth cell; small labels, state text and body copy make the detailed flow harder to read. |
| Data & methodology | Source cards and limitations, investigation input/output, operating flow, expandable terminology | Contains the needed operational and agent detail, but cards and technical copy use very small text and multiple bordered panels compete equally. |

## Findings and planned fixes

| Severity | Location | Observed problem | Recommended fix |
| --- | --- | --- | --- |
| High | Global text: `.eyebrow`, `.detail-label`, `.event-meta`, `.queue-note`, `.method-detail`, `.source-card`, `.context-foot` in `frontend/src/styles.css` / `features.css` | Many labels render at 7–9px and body/secondary copy at 9–11px. At 1440px the app is still difficult to scan; at 390px those sizes become especially hard to read. | Establish shared type tokens; move body copy toward 14–16px, metadata toward 12–13px, labels to at least 11–12px, and reserve compact mono type for truly technical values. |
| High | Monitoring queue, `Dashboard.jsx` and `eventView.js` | Most queue rows read “Potential thermal detection”; the event label hides place. A technical status, repeated source/time, coordinates and tiny reason compete in the same row. | Lead with a human-readable location when available, preserve candidate/uncertainty wording, and make status/reason a secondary scan line. Keep the event ID in details. |
| High | Monitoring/replay map, `CandidateMap.jsx` | Up to 100 monitoring markers and all replay markers render independently. The desktop and replay screenshots show overlapping orange circles, particularly over Punjab/Haryana. | Reduce marker collision at low zoom with data-derived spatial grouping or an existing Leaflet mechanism; retain selection and expose a cluster count/zoom affordance. Never remove or synthesize event records. |
| High | Shared header, `shared.jsx` and responsive CSS | At 768px, nav, replay badge, reviewer sign-in and CTA compete in one line and the reviewer control is clipped. At 390px the horizontal nav clips “Documentation” with no explicit menu affordance. | Rework tablet/mobile navigation into a deliberate compact menu/second row with visible focus and touch-sized targets; keep current route and all existing destinations. |
| High | Product hero, `ProductPage.jsx` and hero rules | At 1440px the intended headline wraps “miss.” onto a third line by itself; the large hero measure and image/heading alignment feel unfinished. | Tune the display measure/font size at desktop breakpoints so the intended phrase wraps deliberately; preserve the image, attribution, and landing-page identity. |
| Medium | `HowItWorksPage`, `.pipeline` | Seven stages in a two-column grid leave a conspicuous empty eighth cell in the actual desktop render. Stage detail text is too small. | Use a seven-item grid that gives the final stage an intentional full-width or editorial placement and apply the shared type scale. |
| Medium | Investigation cards, `SupportingPages.jsx` | Raw event ID is the eyebrow on every report and appears before classification; recommendations, evidence count, status and dates use tiny text. | Lead with classification/status and concise summary, keep IDs in secondary detail, and give citations, uncertainty, missing evidence, and next human step clear hierarchy. |
| Medium | Event detail report, `EventDetail.jsx` | Findings are separated in markup but visual hierarchy should distinguish observed records, derived/estimated context, contradictions, unavailable evidence, and human recommendation. Technical IDs can dominate the report. | Refine the report into scannable evidence sections with provenance and uncertainty visible; keep app-owned status/metadata separate from generated report content. |
| Medium | Monitoring summary and filters | The 250 total candidates, 100 loaded candidates, and visible map candidates appear in several similarly styled count treatments. Filter chips and compact controls are small. | Label total vs loaded vs currently visible counts explicitly, use consistent control sizing, and avoid showing a number without its scope. |
| Medium | Iconography, `Dashboard.jsx`, `ReplayPage.jsx`, `EventDetail.jsx` | Several controls and metrics use Unicode glyphs (`⌖`, `◉`, `△`, `⌕`, arrows, `×`) while Lucide is already installed and used for the brand. | Replace production UI glyphs with aligned Lucide icons where the icon clarifies an action; retain text labels and accessible names. |
| Medium | Shared CSS architecture | Styles are concentrated in two long, compressed stylesheets with repeated late overrides and one-off pixel sizes. `.landing-topbar` styles the application-wide header, and the generic `.topbar` block is stale. | Introduce tokens and readable component sections, remove only demonstrably dead/overridden rules, and make route/header ownership explicit without adding a UI framework. |
| Medium | How-it-works color and card treatment | Alternating unrelated cool-toned backgrounds appear in the workflow grid; repeated bordered panels flatten hierarchy. | Use the established charcoal/earth palette, reserve accent colors for meaning, and use dividers/spacing for related workflow rather than treating every section as a card. |
| Low | Landing and secondary-page captions/metadata | High letter spacing and mono uppercase labels are applied widely; some technical metadata is more prominent than nearby plain-language explanation. | Keep mono labels only for provenance, timestamps, and compact system state; use regular readable copy for section context. |
| Low | 390px baseline | `body` enforces a 360px minimum. The requested 390px viewport renders, but narrower devices can overflow. | Remove the unnecessary minimum width and confirm content/control wrapping down to the supported viewport. |

## Responsive and accessibility observations

- The 390px monitoring page stacks its map and queue, and the Leaflet map remains usable, but labels and row copy are too small. The header navigation requires horizontal scrolling and has no clear “more navigation” affordance.
- At 768px the map and queue remain side by side, leaving a narrow map and queue while the top navigation is clipped. The layout should switch to a single column earlier or rebalance its columns and header.
- Keyboard focus rules and reduced-motion CSS exist. The review found button targets as small as 28–35px and filter controls below the 44px touch target guidance. Keep focus indicators and arrow-key tabs while enlarging controls.
- The map has text attribution and a marker legend. Statuses also include text, so color is not the only state signal.
- Browser screenshots showed Chrome background push-messaging registration errors unrelated to the BurnBlind application. Application console errors and keyboard traversal still require a focused browser check after implementation.

## Implementation order

1. Shared typography, spacing, surfaces, buttons, input and badge tokens.
2. Header responsiveness, dashboard hierarchy, queue semantics and marker density.
3. Investigation report and list hierarchy; seven-stage workflow layout.
4. Accessible controls, route/state regression review, and desktop/tablet/mobile screenshots.

## Validation record

Initial visual inspection commands used the existing `npm run dev` command with the production read-only API configuration and Chrome headless screenshots. Captures were written to `/tmp` for inspection and are not product assets. `npm run build` and route/interaction/state checks will be recorded after the refinement. No frontend edits have been made before this audit.
