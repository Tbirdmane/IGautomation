# Assets

Drop brand assets here and reference them from your content JSON.

- **`logo.png`** — your Fortune University logo. Reference it as the avatar:
  ```json
  "brand": { "avatar": "assets/logo.png" }
  ```
  If no avatar is set, slides fall back to a clean "FU" monogram circle.

- **`backgrounds/`** — dramatic images for `mythos` covers (AI art, etc.).
  Reference one with `"background": "assets/backgrounds/robot.png"`.
  Use `"background": "auto"` (or omit it) to get a generated ember backdrop.

Images are center-cropped to fill the 1080×1350 canvas, so favor high-res,
roughly portrait sources.
