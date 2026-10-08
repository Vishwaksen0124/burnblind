# BURNBLIND — VISUAL DESIGN SYSTEM

The frontend must follow this visual system consistently across every page.

Do not improvise a generic dashboard theme.

The design should communicate:

**EARTH + HEAT + SATELLITE + INTELLIGENCE + OPERATIONAL CLARITY**

The visual identity should feel like a combination of:

- satellite imagery
- thermal imaging
- wildfire monitoring
- geospatial intelligence
- environmental science
- modern mission-control software

It should feel premium, technical and serious.

---

# 1. COLOR SYSTEM

Use a very dark neutral base rather than pure black.

### Primary background

```text
#0B0D0E
```

Use this for the overall application background.

Avoid pure `#000000`.

The slight charcoal tone makes the interface feel less harsh.

---

### Secondary background

```text
#111416
```

Use for:

- navigation
- cards
- side panels
- event panels
- sections

---

### Elevated surface

```text
#171A1C
```

Use sparingly for:

- selected cards
- dropdowns
- expanded sections
- event details

Do not turn the entire interface into floating cards.

---

### Borders

Primary:

```text
#292D2F
```

Secondary:

```text
#202426
```

Borders should be subtle.

Never use thick bright borders around every card.

---

# 2. TEXT COLORS

Primary text:

```text
#F1F0EB
```

Secondary text:

```text
#A5A8A8
```

Muted metadata:

```text
#707577
```

The hierarchy should be obvious:

```text
Primary
↓
Secondary
↓
Metadata
```

Do not use bright white for every piece of text.

---

# 3. FIRE / HEAT COLOR PALETTE

Orange is the primary BurnBlind accent.

### Thermal orange

```text
#FF6A1A
```

Use for:

- primary CTA
- thermal highlights
- important map markers
- active states
- key visual accents

### Amber

```text
#FFB020
```

Use for:

- medium priority
- warnings
- elevated uncertainty
- historical activity

### Red

```text
#E5483F
```

Use only for:

- high priority
- severe alerts
- critical investigation states

Do NOT use red everywhere.

Red should mean:

> "Pay attention."

---

### Soft orange highlight

```text
#FF8A3D
```

Use for subtle hover states and secondary highlights.

---

# 4. COLOR USAGE RULE

The interface should NOT look orange everywhere.

Use approximately:

```text
85–90% neutral dark colors
8–12% warm accent colors
1–3% red/high-severity colors
```

Orange should feel valuable because it is used selectively.

The page should remain mostly dark.

---

# 5. GRADIENTS

Use gradients extremely carefully.

Allowed:

Very subtle thermal gradients inside:

- map heat layers
- satellite imagery
- hero visual
- data visualization

Example conceptual gradient:

```text
deep charcoal
→ dark brown
→ burnt orange
→ thermal orange
→ red
```

Do NOT use:

```text
purple → blue
pink → purple
blue → cyan
```

Do not use giant gradient backgrounds behind text.

---

# 6. HERO IMAGERY

The landing page should contain a strong visual.

Do NOT use generic stock photos of:

- people looking at laptops
- forests with people
- firefighters posing
- AI robots
- servers
- generic technology

Instead use imagery that feels directly related to BurnBlind.

Preferred visual:

### Satellite / thermal Earth imagery

A top-down or orbital view showing:

- Indian subcontinent
- northern India
- Punjab/Haryana region
- agricultural fields
- subtle thermal/fire signatures

The image should feel like **real remote-sensing data**, not a fantasy illustration.

---

# 7. HERO IMAGE TREATMENT

The hero image should blend naturally into the dark interface.

Do not place a rectangular stock-photo card in the hero.

Instead:

```text
Dark background
       ↓
Satellite / thermal image
       ↓
Image gradually fades into background
       ↓
Text overlays / sits beside it
```

Use a dark gradient overlay so text remains readable.

The image can have:

- subtle orange thermal regions
- faint geographic boundaries
- very subtle coordinate/grid markings

Avoid excessive labels.

The image should support the story rather than become the entire design.

---

# 8. OPTIONAL HERO VISUAL CONCEPT

A strong composition could be:

```text
LEFT

BURNBLIND

Seeing the Fires
Others Might Miss.

Short product explanation

[Explore Monitoring]


RIGHT

Large satellite/thermal map of
Punjab + Haryana

Small glowing thermal points
and subtle geographic lines
```

The right-side imagery should visually connect with the monitoring dashboard.

This creates continuity between:

```text
Landing page
      ↓
Monitoring dashboard
```

---

# 9. PHOTOGRAPHY STYLE

If photographs are used elsewhere, use:

- aerial photography
- satellite imagery
- agricultural landscapes from above
- wildfire/smoke viewed from a distance
- environmental monitoring imagery

Prefer imagery with:

- dark tonal range
- warm highlights
- strong geometry
- aerial perspective
- natural textures

Avoid:

- smiling people
- corporate stock photography
- posed firefighters
- generic forest photographs
- excessive dramatic flames

BurnBlind is about **observation and intelligence**, not disaster spectacle.

---

# 10. MAP VISUAL STYLE

The map must not look like a default Google Maps screen.

Use a dark basemap.

The map should visually integrate with the application:

```text
Dark charcoal terrain
+
muted geographic boundaries
+
subtle roads/cities
+
orange/amber thermal events
```

Keep map labels muted.

The map should never compete with event markers.

---

# 11. MAP HEAT LAYER

If a heatmap exists, use a restrained thermal scale:

```text
transparent
→ amber
→ orange
→ red
```

The heat layer should represent actual data.

Do not add decorative heat merely because it looks cool.

---

# 12. MAP MARKERS

Markers should be simple.

Candidate:

```text
small orange dot
```

Medium:

```text
orange/amber circle
```

High priority:

```text
red/orange core
+
subtle outer ring
```

Investigating:

```text
orange marker
+
thin animated ring
```

Do not use huge glowing circles.

---

# 13. SHAPES

The product should use mostly:

- rectangles
- slightly rounded corners
- subtle geometric lines
- map boundaries
- thin dividers

Recommended card radius:

```text
8px–12px
```

Do NOT use huge:

```text
24px
32px
40px
```

rounded cards everywhere.

BurnBlind should feel technical rather than playful.

---

# 14. CARD DESIGN

Cards should be quiet.

Example:

```text
┌──────────────────────────────┐
│ HIGH PRIORITY                │
│                              │
│ Patiala, Punjab              │
│ Potential fire event         │
│                              │
│ Fire likelihood     HIGH     │
│ Blindness           HIGH     │
│ Exposure            12.4K    │
└──────────────────────────────┘
```

Use:

- dark surface
- thin border
- small radius
- strong typography
- minimal decoration

Avoid:

- giant shadows
- glowing edges
- gradient cards
- icons everywhere

---

# 15. KPI CARDS

KPI cards should be compact.

Do not make them giant dashboard tiles.

Example:

```text
HIGH PRIORITY

8

events requiring investigation
```

Use a small colored status indicator.

The number should be visually prominent.

The description should be secondary.

---

# 16. TYPOGRAPHY

Use a modern technical sans-serif.

Recommended:

```text
Inter
```

or an equivalent clean sans-serif.

Use heavier weight for:

- hero title
- page title
- event location
- important numbers

Use regular/light weight for:

- descriptions
- methodology
- secondary information

---

# 17. MONOSPACE TYPOGRAPHY

Use monospace sparingly.

Good uses:

```text
16:04 UTC
30 NOV 2025
31.6208° N
75.1234° E
BL-1042
```

Do not use monospace for normal paragraphs.

This creates the feeling of an operational system without becoming a developer console.

---

# 18. HERO TYPOGRAPHY

The landing page headline should be large.

Example:

```text
Seeing the Fires
Others Might Miss.
```

Use approximately:

```text
64–80px desktop
```

with tight line height.

Do not make every heading huge.

Only the hero should have dramatic typography.

---

# 19. BUTTONS

Primary button:

```text
orange background
dark text
```

Example:

```text
[ Explore Monitoring → ]
```

Secondary:

```text
transparent
thin grey border
light text
```

Example:

```text
[ How It Works ]
```

Buttons should have subtle hover transitions.

Avoid pill-shaped buttons everywhere.

Use slightly rounded rectangular buttons.

---

# 20. NAVIGATION

The navigation should be minimal.

Dark transparent/near-dark background.

Example:

```text
BURNBLIND

Monitoring
Investigations
How It Works
Methodology
Docs

HISTORICAL REPLAY · 2025
```

The BurnBlind logo should be simple.

Do not create a complicated AI logo.

A subtle geometric mark inspired by:

- satellite signal
- eye
- thermal contour
- geographic coordinate

would work.

---

# 21. SECTION DIVIDERS

Use thin horizontal lines:

```text
────────────────────────────
```

in muted grey.

Occasionally use small metadata labels above headings:

```text
01 / MONITORING
```

or:

```text
ENVIRONMENTAL INTELLIGENCE
```

This gives the interface a technical editorial feel.

Do not overuse these labels.

---

# 22. VISUAL MOTIF

Use a recurring visual language based on:

### Thermal contours

Subtle contour lines can appear in:

- hero imagery
- map backgrounds
- section transitions

### Satellite coordinates

Small coordinate labels can appear occasionally.

### Grid lines

Very subtle grid lines can appear behind hero imagery.

### Scan lines

If used, they must be extremely subtle.

These should create the feeling of remote sensing without becoming sci-fi decoration.

---

# 23. LANDING PAGE COMPOSITION

The landing page should have strong visual rhythm:

```text
HERO
   ↓
PROBLEM
   ↓
HOW BURNBLIND SEES
   ↓
PRODUCT PREVIEW
   ↓
WHY IT MATTERS
   ↓
DATA SOURCES
   ↓
INVESTIGATION AGENT
   ↓
LIMITATIONS / TRUST
   ↓
FINAL CTA
```

Use generous spacing between major sections.

But avoid empty screens.

The landing page should feel editorial and intentional.

---

# 24. PRODUCT PREVIEW SECTION

Show an actual miniature representation of the monitoring interface.

It should include:

```text
dark map
orange event points
right-side event queue
small KPI row
```

This should visually tease the actual product.

Do not use a random dashboard screenshot unrelated to the application.

---

# 25. INVESTIGATION PAGE VISUAL STYLE

The Investigation page should become slightly more document-oriented.

Use:

```text
dark background
+
structured evidence panels
+
thin dividers
+
orange highlights
```

The most important information should be:

```text
INVESTIGATION RESULT

REVIEW REQUIRED

Why:
...

Evidence:
...

Uncertainty:
...

Recommendation:
...
```

The recommendation should visually stand out.

---

# 26. EVIDENCE VISUAL LANGUAGE

Use small indicators:

```text
✓ Observed
◆ Derived
○ Historical
≈ Estimated
⚠ Uncertain
```

These labels should be textual as well as visual.

Never depend solely on color.

---

# 27. ANIMATION

Animation should feel like a monitoring system, not a marketing website.

Allowed:

- subtle event pulse
- map marker transitions
- section fade-in
- hover movement
- investigation progress state

Avoid:

- constant floating objects
- particle backgrounds
- rotating 3D objects
- excessive parallax
- flashy transitions

Animation duration:

```text
150–300ms
```

for normal UI interactions.

---

# 28. LANDING PAGE SCROLL EXPERIENCE

The page should progressively tell a story.

For example:

```text
Hero
     ↓
"The problem isn't that satellites can't see fires."
     ↓
"The problem is that no single observation is complete."
     ↓
BurnBlind methodology
     ↓
Real monitoring interface
     ↓
Investigation Agent
     ↓
Data sources and limitations
```

The user should understand the product before reaching the dashboard.

---

# 29. IMAGE RULE

Every image must have a purpose.

Before adding an image ask:

> Does this image help communicate environmental monitoring, satellite observation, geography, fire detection, or impact?

If not, do not use it.

Prefer a few excellent images over many decorative images.

---

# 30. NO GENERIC AI DESIGN

This is extremely important.

Do NOT use visual patterns associated with generic AI websites:

- purple gradients
- glowing neural networks
- robot faces
- AI brains
- floating glass cards
- "AI-powered" repeated everywhere
- chat bubbles
- sparkles
- generic generated illustrations

BurnBlind is an **environmental intelligence system**.

The AI is one component of the system.

The visual identity should be about:

**Earth + observation + evidence + heat + geography.**

---

# 31. FINAL VISUAL TEST

Before considering the frontend complete, ask:

### Does it look like a satellite/environmental intelligence product?

YES.

### Does it look like a generic AI SaaS template?

NO.

### Is the map visually important?

YES.

### Are orange/red colors used intentionally?

YES.

### Is the interface mostly dark neutral?

YES.

### Are images relevant to satellite/environmental monitoring?

YES.

### Are cards restrained and technical?

YES.

### Can a judge understand the product in 10 seconds?

YES.

### Is every visible metric backed by actual or clearly labeled replay/demo data?

YES.

### Does the landing page look like a polished real product?

YES.

---

# DESIGN NORTH STAR

The final aesthetic should feel like:

> **A NASA/earth-observation operations interface redesigned as a modern premium product.**

Not a gaming interface.

Not a generic SaaS dashboard.

Not an AI chatbot.

Not a developer console.

**BurnBlind should visually communicate:**

```text
EARTH
+
SATELLITE
+
HEAT
+
EVIDENCE
+
INTELLIGENCE
```

Every visual decision should reinforce that identity.
