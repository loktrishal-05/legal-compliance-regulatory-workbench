# Generation prompts — light cinematic media (Phase B)

Palette to repeat in every prompt: vellum #F3EFE6, paper #FBF8F2, iron-gall ink #1C2330, sealing-wax red #8E2C36, ledger green #2E6A4E, aged brass #8A5300.
Global spec suffix (append to every video prompt): **"16:9, 1920×1080, 24 fps, 8 seconds, no audio, slow steady camera, smooth easing, bright premium daylight grade, soft diffused window light, shallow depth of field, no text, no letters, no numbers, no logos, no watermark, no faces, no people, no neon, no dark background, no lens flare."**

| Use | Clips | Save as |
|---|---|---|
| Landing hero | 3 × 8 s (scatter → stitch → bind) | `frontend/public/media/landing-1..3.mp4` |
| Sign-in background | 2 × 8 s, seamless loop | `frontend/public/media/signin-1..2.mp4` |
| Sign-up background | 2 × 8 s, seamless loop | `frontend/public/media/signup-1..2.mp4` |
| Logo (full + mark) | 2 images | `frontend/public/brand/logo.png`, `logo-mark.png` |
| Feature icon set | 8 images | `frontend/public/brand/icon-*.png` |
| Assistant avatar | 1 image | `frontend/public/brand/assistant.png` |

## Landing hero

**landing-1 — scatter (problem).** "Dozens of blank cream paper pages (#FBF8F2) drift and tumble slowly through a bright, airy vellum-coloured space (#F3EFE6), soft daylight from a tall window on the left, gentle shadows tinted ink-blue (#1C2330), pages slightly curled, unordered, floating at different depths, camera slowly dolly forward, calm but unsettled mood." + suffix.

**landing-2 — stitch (transformation).** "In the same bright vellum space, a single fine sealing-wax red thread (#8E2C36) glides through the floating cream pages, passing through one small precise point on each page; as the thread passes, each page gently straightens and turns to face the same direction, pages begin to align into a loose column, soft daylight, camera slowly orbits right, satisfying and precise." + suffix.

**landing-3 — bind (resolved, seamless loop).** "The aligned cream pages settle into a neat bound stack on a pale oak desk in soft daylight, the red thread (#8E2C36) ties around the stack and finishes in a small matte wax seal of the same red, a thin ledger-green ribbon (#2E6A4E) marker, dust motes drifting in the light, very slow camera push-in and return so the first frame equals the last frame, calm, resolved, trustworthy." + suffix + "seamless loop, first frame identical to last frame."

## Auth backgrounds

**signin-1/2 — trustworthy and quiet.** "A quiet sunlit records room: pale wooden shelves of cream archive boxes softly out of focus, the centre of the frame kept brighter and empty as soft white light, faint slow movement of dust motes and a gently swaying sheer curtain, palette #F3EFE6 #FBF8F2 with ink-blue shadows #1C2330." + suffix + "seamless loop."

**signup-1/2 — welcoming, joining the team.** "Bright morning light across a pale oak table, cream pages and a red thread (#8E2C36) loosely arranged on the right half of the frame, the left half kept bright, empty and calm, a few pages slowly sliding into a neat pile, warm welcoming daylight, palette #F3EFE6 #FBF8F2." + suffix + "seamless loop."

## Brand

Icon style line (prefix every icon prompt): **"Single-weight 1.75 px ink line icon (#1C2330) on transparent background, 24-unit grid, 2 px corner radius, one small sealing-wax red (#8E2C36) accent element, flat, no gradient, no shadow, no text."**

- logo.png: "A refined emblem: an open folio with a single red thread (#8E2C36) stitched through it ending in a small round seal, ink lines #1C2330 on transparent background, flat, minimal, no text." (the app renders the name in Fraunces)
- logo-mark.png: same emblem, square, 1024×1024, transparent.
- icons: documents (stack of pages), contracts (folio with clause marks), review (checkmark seal), compliance (shield with ledger lines), regulatory (columned building), obligations (calendar with thread), audit (magnifier over ledger), assistant (speech mark with thread).
- assistant.png: "A calm abstract avatar: a cream paper disc with a single red thread loop and ink outline, flat, transparent background, no face, no text."
