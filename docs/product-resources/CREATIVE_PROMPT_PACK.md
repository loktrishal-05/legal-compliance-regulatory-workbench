# Creative Prompt Pack — copy & paste

Brand palette (from `DESIGN.md`) used in every prompt: brand navy `#020e21`, night surfaces `#010a18` / `#041329` / `#081d38`, instrument cyan `#35d7e8`, agent blue `#3d8bff`, flow green `#2fe0a4`, review amber `#f2a93b`, knowledge violet `#8b6cff`, signal white `#eef6fb`.
Mood: dark, calm, precise, cinematic, trustworthy — "evidence under light", not sci-fi hacker.

---

## A. NotebookLM — Video guide (how to use the app)

**Add these sources:** `docs/product-resources/LEGAL_PLATFORM_USER_GUIDE.md` (main), `docs/product-resources/LEGAL_PLATFORM_TERMS_AND_CONDITIONS_v2.0_DRAFT.md`, `README.md`, and the "VIDEO BRIEFING – read first" note from the explainer notebook. Rename a `.md` copy to `.txt` if the upload is rejected. You can add them to the same notebook as the explainer.

**Customize prompt (Video Overview):**
```
Create a step-by-step video GUIDE (not a sales pitch) that teaches a new user how to use the Legal & Regulatory Assurance Platform. Base it on the User Guide source. Structure:
1) The golden rule: the Platform proposes, a person decides; every statement cites its exact source.
2) Roles: counsel, compliance officer, business owner, auditor and administrator — what each can and cannot do.
3) Sign in, accept the terms, choose a workspace and matter, read the honest dashboard.
4) Upload a contract: safety checks, quarantine, the original fingerprint, background job progress.
5) Source viewer: spans, page locations, proposing and reviewing an OCR correction.
6) Contract analysis: clauses, parties, dates, playbook deviations, missing clauses, redline, submit for review.
7) Summaries and the assistant: profiles, clickable citations, uncertainty, refusal, approved-only export.
8) Regulatory: register a source, import a version, view the diff, decide applicability, watchlist freshness, impact campaign.
9) Compliance: requirement -> control -> evidence map; explain each of the six states with a one-line example; stale assessments after evidence expiry.
10) Obligations, tasks, reminders, remediation closure with retest, exceptions with expiry.
11) The review queue: approve, reject, request changes, escalate; no self-approval.
12) Audit timeline, as-of snapshots, evidence packs.
13) What the "unavailable / degraded / needs review" messages mean and what to do.
Use one running example throughout: a fictional SaaS contract with a 60-day renewal notice, plus a fictional data-retention regulation whose evidence certificate expires. Show screen-like diagrams of each step. Keep the language simple, and repeat that outputs are not legal advice. Do not invent features, numbers or customers; mention MVP limitations briefly at the end.
```

---

## B. Cinematic background videos (8 seconds each)

**Rules for every clip:** 8 s, seamless loop (the last frame matches the first), slow continuous camera move, **no text, no logos, no letters, no readable words, no human faces**, dark navy base, low contrast where the form or headline sits, 24 fps, and no flashing (photosensitivity-safe). Generate a 16:9 desktop clip (1920×1080) and a 9:16 mobile clip (1080×1920) of each. Each clip has a fallback poster (the first frame).

**Negative prompt (paste wherever the tool supports one):**
```
text, letters, words, numbers, watermark, logo, signature, faces, people, hands, gavel, scales of justice cliché, courtroom, cartoon, neon cyberpunk city, glitch, flashing strobe, rapid cuts, camera shake, lens dirt, oversaturated colors, red alarm lighting, low resolution, jpeg artifacts
```

### B1. Landing page hero — "Evidence becomes light"
**Desktop 16:9:**
```
Cinematic 8-second seamless loop, 16:9. Deep navy darkness (#020e21). Translucent sheets of paper float in slow motion in a vast dark space, like contract pages suspended in still water. Thin luminous cyan lines (#35d7e8) trace across the pages, lifting individual sentences out as glowing filaments that drift together and weave into an elegant, slowly rotating constellation-like network of connected nodes in cyan, soft blue (#3d8bff) and a few calm green points (#2fe0a4). Volumetric light, shallow depth of field, soft bokeh, fine dust particles catching the light. The camera makes a slow, steady push-in and slight orbit. The left third stays darker and calm for a headline overlay. Premium, precise, trustworthy, quiet. The ending frame matches the starting frame for a perfect loop. No text, no logos, no people.
```
**Mobile 9:16:** use the same prompt with "vertical 9:16", and "the upper half stays darker and calm for a headline; the network forms in the lower half".

### B2. Sign in — "The vault of sources" (form is centered)
```
Cinematic 8-second seamless loop, 16:9. A quiet, endless archive in deep navy (#010a18): tall, softly lit shelves of glass document panels recede into fog. A gentle cyan scan line (#35d7e8) glides horizontally across the panels; each panel it passes briefly shows a faint fingerprint-like hash pattern, then settles. Very slow forward dolly down the center aisle. Low-key lighting; the CENTER of the frame stays darkest and softly blurred so a sign-in form can sit on top; the detail lives at the left and right edges. Calm, secure, private, like a bank vault for knowledge. Subtle volumetric haze, fine particles. The last frame matches the first. No text, no logos, no people.
```
**Mobile 9:16:** same, vertical, with "the center column stays darkest; the archive detail is at the top and bottom".

### B3. Sign up — "Joining the network" (headline/form in the upper area)
```
Cinematic 8-second seamless loop, 16:9. Deep navy space (#041329). In the lower half, a calm network of luminous nodes and thin connecting lines breathes slowly. A new node appears softly from below in warm amber (#f2a93b), drifts upward and connects to the network with a gentle cyan pulse (#35d7e8) that travels along the lines, and the whole network brightens subtly and then settles. A slow upward tilt of the camera. The UPPER portion of the frame stays dark and clean for a form and headline. Welcoming, collaborative, orderly. Soft bokeh, volumetric light. Seamless loop with matching first and last frames. No text, no logos, no people.
```
**Mobile 9:16:** same, vertical, with the network in the bottom 40% only.

### B4. Forgot / reset password — "Restoring the thread" (optional 4th clip)
```
Cinematic 8-second seamless loop, 16:9. Deep navy (#020e21). A single delicate thread of cyan light (#35d7e8), broken in the middle, floats in darkness. The two ends drift slowly toward each other and reconnect with a soft, warm white glow (#eef6fb), then the light flows smoothly along the restored thread toward a calm, distant network of nodes. A very slow lateral camera drift. The center stays dark for a form. Reassuring, steady, safe. Fine particles, shallow depth of field. Seamless loop. No text, no logos, no people.
```

**After generating:** compress each to H.264 MP4 under ~6 MB (desktop) and ~3 MB (mobile), muted, with `+faststart`, and export frame 0 as a WebP poster. The existing slots are `frontend/public/assets/auth/auth-bg-01.mp4` (login), `-02` (recovery), `-03` (signup), each with `-mobile.mp4` and `-poster.webp` variants. Add the landing clip as `frontend/public/assets/landing/hero-loop.mp4` (a code change is needed later to use it). Respect `prefers-reduced-motion`: show the poster instead.

---

## C. Logo and agent icon images

**Rules for every image:** a flat vector-style mark, geometric and minimal, readable at 32 px, a transparent or solid `#020e21` background, centered, no gradients beyond one subtle glow, **no text inside the mark**, and no gavel or scales-of-justice cliché. Generate 1024×1024 PNGs. Ask for "on transparent background" and also a version on the navy background.

### C1. Main application logo (mark)
```
Minimal geometric logo mark for "Legal & Regulatory Assurance Platform", an evidence-first legal and compliance software product. Concept: a document page whose folded corner becomes a precise checkmark, inside a subtle shield-like outline formed by two clean strokes, with one small cyan node where the check meets the page, symbolizing a verified source. Colors: instrument cyan #35d7e8 and signal white #eef6fb on deep navy #020e21. Flat vector style, balanced negative space, crisp edges, readable at 32 pixels, professional and trustworthy like a bank or audit firm brand, modern SaaS quality. No text, no gavel, no scales, no 3D, no photorealism. Centered, 1024x1024.
```
**Wordmark lockup:** generate the mark only, then set the name in the existing **Archivo** font (`frontend/public/fonts/archivo-latin-var.woff2`). Image generators misspell text.

**App icon variant:**
```
The same logo mark placed inside a rounded-square app icon with a deep navy #020e21 background and a soft inner cyan glow at the bottom edge. Flat, minimal, 1024x1024, no text.
```

### C2. Agent icons — one consistent family

Shared style line (paste first, then add an agent line):
```
Icon from a consistent family of AI agent icons for a legal compliance platform. Style: minimal geometric line icon, 2-pixel-equivalent rounded strokes, inside a circular badge with a thin ring, deep navy #020e21 background, one accent color per agent, a tiny glowing node as a shared family motif, flat vector, readable at 24 pixels, no text, no faces, no robots, no gavel, no scales. Centered, 1024x1024.
```

| Agent (in the app) | Accent | Add this line |
|---|---|---|
| Contract Analyst | agent blue `#3d8bff` | `Symbol: a contract page with three horizontal clause lines, one highlighted and bracketed.` |
| Summary Writer | instrument cyan `#35d7e8` | `Symbol: several long lines condensing into one short line, with a small citation link mark.` |
| Regulatory Watch | knowledge violet `#8b6cff` | `Symbol: a document with a small radar arc and a version fork (two branching lines).` |
| Compliance Assessor | flow green `#2fe0a4` | `Symbol: three connected nodes (requirement, control, evidence) in a short chain, the last one checked.` |
| Obligation & Deadline Keeper | review amber `#f2a93b` | `Symbol: a calendar page with a clock hand and a small bell.` |
| Evidence & Audit Keeper | signal white `#eef6fb` with a cyan node | `Symbol: a stack of layered sheets with a fingerprint-like hash ring and a chain link.` |
| Research Assistant (Q&A) | instrument cyan `#35d7e8` | `Symbol: a speech bubble containing a small quotation mark and a source pin.` |
| Human Review Gate (person, not AI — keep it distinct) | review amber `#f2a93b` | `Symbol: an open hand-shaped checkmark inside a doorway outline, signifying human approval.` |

**Consistency tips:** generate all icons in one session, reuse the same seed if the tool allows it, and if one comes out off-style, paste the best icon back as a style reference. Save them to `frontend/public/assets/branding/agents/<agent-name>.png`.

---

## D. Where the finished files go

| Output | Path |
|---|---|
| Terms DOCX/PDF (after counsel approval) | `frontend/public/resources/legal-platform-terms-legal-2.0.docx` |
| User guide PDF | `frontend/public/resources/legal-platform-user-guide-v1.0.pdf` |
| Guide video (NotebookLM export) | `frontend/public/resources/legal-guidance-video.mp4` + `-poster.webp` |
| Auth backgrounds | `frontend/public/assets/auth/auth-bg-0{1,2,3}{,-mobile}.mp4` + `-poster.webp` |
| Landing hero | `frontend/public/assets/landing/hero-loop{,-mobile}.mp4` + poster |
| Logo / app icons | `frontend/public/assets/branding/legal-logo*.png`; regenerate the favicons/icons in `frontend/public/` |
| Agent icons | `frontend/public/assets/branding/agents/*.png` |

The wiring (Help page, terms gate v2, landing video slot, icons) is one later integration task. Give the paths above to the frontend agent.
