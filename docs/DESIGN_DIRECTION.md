# Design direction — Legal & Regulatory Assurance Platform (cinematic light frontend)

Status: **proposal for owner approval (Phase A)**. Nothing is built from this until approved. Replaces the retained dark navy/cyan public look described in `DESIGN.md` for the landing and auth surfaces; the workbench keeps its light calm base and adopts these tokens.

## 0. Brief (derived from the repo; correct anything wrong)

- **App:** Legal & Regulatory Assurance Platform (LRA).
- **One sentence:** turns contracts, regulations and evidence into cited, independently reviewed obligations, assessments and audit trails.
- **Users:** legal counsel, compliance reviewers, business owners, auditors, at a desk (laptop/desktop first; phone for review and notifications).
- **Audience for the landing:** hackathon judges / investors first, pilot clients second.
- **Domain world:** paper and archives — case files, vellum, ink, ribbons and seals, ledgers, the quiet of a records room.
- **Stack:** React 19 + Vite + react-router 8, GSAP already installed. Add **Lenis** only (≈4 KB gz). No Three.js (the hero does not need it).
- **Languages:** English now; all copy goes through one i18n module.
- **Do not repeat:** P2E Bridge (navy #14213D + violet #5B3FD1, Manrope/Inter, scroll-scrubbed frame hero) and this repo's current navy #020E21 + cyan #35D7E8 / Archivo + Inter dark landing.

## 1. Domain metaphor

**"Loose pages become one bound, cited record."** Scattered pages drift in daylight; a single ink-red thread passes through them, stitching each claim to the exact line it came from; the pages settle into an ordered, sealed file. Every hero beat and transition serves it: *scatter → stitch → bind*. In the product the same thread is the citation link from a statement to its source span.

## 2. Three adjectives

**Precise, calm, trustworthy** (with a little editorial warmth).

## 3. Palette (real materials: vellum, iron-gall ink, sealing wax, ledger green, aged brass)

| Token | Hex | Material |
|---|---|---|
| `--ground` | `#F3EFE6` | vellum page |
| `--surface` | `#FBF8F2` | fresh paper |
| `--line` | `rgba(28,35,48,.12)` | pencil rule |
| `--ink` | `#1C2330` | iron-gall ink |
| `--ink-muted` | `#596273` | faded ink |
| `--accent` | `#8E2C36` | sealing wax / red thread |
| `--success` | `#2E6A4E` | ledger green |
| `--warning` | `#8A5300` | aged brass |
| `--shadow` | `0 18px 40px -18px rgba(28,35,48,.28)` | ink-tinted, never grey |

WCAG contrast (computed): ink on ground **13.73:1**, on surface **14.87:1**; muted 5.35 / 5.79; accent 7.14 / 7.73; success 5.57 / 6.03; warning 5.52 / 5.97; surface text on accent **7.73:1**. All AA (most AAA). Status is never colour-only (badge text + icon shape).

## 4. Type pairing

- **Display: Fraunces** (variable, optical size + "SOFT" axis) — an editorial serif with the gravity of a law report but warm, not stiff. Tight: `-0.03em`, line-height 0.95 at display sizes, opsz 144.
- **Text/UI: Instrument Sans** — crisp, slightly condensed grotesque that stays readable in dense tables.
- Neither appears in the do-not-repeat list. Self-hosted woff2 subsets (no runtime font CDN).

## 5. Hero archetype

**Primary: (a) scroll-scrubbed image sequence on a sticky canvas**, built from three light clips telling *scatter → stitch → bind*. Reason: the metaphor is a transformation over time that the reader controls; scrubbing lets judges "pull the thread" themselves. Frames ≈ 220 webp at 1600 px, < 12 MB, batched loading with nearest-frame fallback.

**Secondary moments (3):**
1. **Statement reveal** — "Every conclusion cites its source. Every decision has a reviewer." words scrub from 0.12 → 1.
2. **3D product reveal** — the real review queue + citation panel in HTML rises from `rotateX(58deg) scale(.72)` to flat; rows stagger in.
3. **Flow path** — one SVG red thread draws itself (`pathLength`) through five steps: intake → extract → propose → independent review → obligation & audit.
Closing CTA uses the resolved "bound record" loop.

## 6. Motion signature

- Easing: `expo.out` for reveals (crisp), `power2.inOut` for scrubbed transforms; base 0.9 s, stagger 0.06, scrub 0.6, Lenis `lerp 0.09`.
- **Signature interaction: "pull the thread".** Hovering or focusing any citation anywhere (landing demo and app) draws a thin ink-red thread from the statement to its source line — the same visual as the hero.
- Reduced motion: static key frames, no scrub/parallax/autoplay, all text in DOM order.

## 7. Reference board (to capture in Chrome during build)

godly.website and awwwards editorial/legal-tech sites (serif display + generous whitespace), gsap.com/showcase (scrubbed sequences), Aceternity "tracing beam" (re-skinned as the red thread), Magic UI "animated beam" (flow step connections), Dribbble paper/document motion shots (paper drift and settle). Techniques only, never copied visuals.

## 8. Media status — **decision needed**

The three supplied clips (`Generated Video October 09, 2026 - 8_47PM.mp4`, `…(1).mp4`, `gemini_generated_video_fed08d06.mp4`) are **dark** (navy/black ground, neon cyan particles and lens flares), which contradicts this brief's light rule, and the 40 s Gemini clip carries a **visible watermark** (bottom-right ✦). Its story (scattered papers → knowledge graph → archive → connecting threads) fits the metaphor well. Options are in the owner question; recommended: regenerate three light clips with `docs/GENERATION_PROMPTS.md`, and use the current clips only as a temporary placeholder (watermark cropped) if the demo deadline forces it.
