# Help & Resources

In-app page: `/app/help` (sidebar **Trust → Help & Resources**, account menu, command palette).
Everything is served from `frontend/public/resources/`; no external player or viewer is used.

| File | Source | Notes |
|---|---|---|
| `guidance-video.mp4` | Supplied 90 s, 1280×720 H.264 recording (26.9 MB) | Re-encoded H.264 High / CRF 23 / AAC 128k with `+faststart` → 14.3 MB. Frame-aligned SSIM vs source 0.993 (Y 0.992). Original kept outside git in `data/resources-source/guidance-video-original.mp4`. |
| `guidance-video-poster.webp` | Frame at 6 s of the encoded video | Poster only; the video never autoplays. |
| `application-user-guide.pdf` | Supplied ReportLab PDF, 8 pages | Served unmodified (see stale wording below). |
| `sovereign-workbench-terms-v1.0.docx` | Supplied terms, v1.0 | Authoritative download. The in-app text is generated from it into `frontend/src/features/resources/termsV1.js`; `termsModel.test.js` pins the DOCX SHA-256, so a changed document fails the tests until the module is regenerated. |

Encoding command (reproducible):

```sh
ffmpeg -i guidance-video-original.mp4 -c:v libx264 -preset slow -crf 23 -profile:v high -level 4.0 \
  -pix_fmt yuv420p -c:a aac -b:a 128k -ac 2 -movflags +faststart guidance-video.mp4
```

## Stale wording in the user guide (regenerate later)

Page 7, *Limitations*: "Advanced features (verified registry fast path, shift-handover intelligence,
compliance agent, voice/multilingual interface, BI dashboards) …" describes them as rolling out
progressively. No editable source was supplied and the PDF is not patched in place. The Help page
shows the correction: *Feature availability depends on role, deployment mode, configured data and
enabled local services.* Replace that sentence when the guide is next generated from its source.

## Serving

Serve `.docx` as `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
(the Vite dev server sends no type; the `download` attribute still saves it correctly) and
`.mp4` with HTTP range support so the player can seek.

## First-login terms

`TermsGate` (between authentication and the Workbench shell) follows `docs/terms_acceptance.md`:
`GET /auth/terms/current`, `POST /auth/terms/accept` with the server-listed acknowledgements,
409 `terms_version_changed` → refetch and re-confirm, and any 403 `terms_acceptance_required`
from a protected API re-opens the gate. A backend without the terms routes (404) is not gated:
it cannot record consent, and the frontend never stores acceptance itself.
