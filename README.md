# IGautomation — Fortune University slide generator

Turn the day's real news into two finished Instagram carousels — one **Twitter-style**
value post and one **flashy "mythos"** hook post — from a single JSON file each.

- **`mythos`** — flashy dark style: big ALL-CAPS lines, white text with key
  phrases in red, a cinematic AI-energy backdrop (or your own hero art), a
  "swipe left" hook, and a follow-CTA outro.
- **`twitter`** — tweet-thread style: a dark branded cover, then clean white
  "tweet card" slides with the verified badge, heading + body.

Everything renders to **1080×1350 PNGs** (Instagram's reach-friendly 4:5 portrait).

---

## The daily loop

```
research the web ──► pick 2 ideas ──► write copy (JSON) ──► [hero art] ──► render ──► post
   ideas.py / chat         you          generate.py        imagegen.py    igslides
```

1. **Get ideas** — researched from live news (see below). Pick one for `twitter`,
   one for `mythos`.
2. **Write the copy** into `content/<slug>.json` — by hand (copy an example),
   in a chat with Claude, or with `generate.py`.
3. **Flashy cover art** (mythos only) — generate the hero image from the cover's
   `image_prompt`, or let the built-in cinematic backdrop stand in. (details below)
4. **Render**: `python -m igslides content/your_post.json`
5. Post the `output/<slug>/` folder as a carousel.

---

## Quickstart

```bash
pip install -r requirements.txt          # just Pillow

# render today's two example posts
python -m igslides content/daily_twitter.json content/daily_mythos.json

# or everything in the folder
python -m igslides content/
```

Output lands in `output/<slug>/slide-01.png`, `slide-02.png`, …

---

## 1. Daily ideas (live research)

Two ways to get fresh, on-brand ideas grounded in real news (AI, crypto, money,
apps, tech):

- **Just ask Claude in chat** — "give me today's two post ideas" — and Claude
  researches the web and proposes a `mythos` hook + a `twitter` post.
- **Run the script** for hands-off automation:
  ```bash
  pip install anthropic && export ANTHROPIC_API_KEY=sk-...
  python ideas.py --count 8 --json ideas.json
  ```
  It web-searches and prints ranked ideas, each tagged `mythos`/`twitter` with a
  source link, ready to hand to `generate.py`.

> Ground every hook in something true. The audience that converts to buyers is
> the one that trusts you.

---

## 2. Generate the copy

```bash
pip install anthropic && export ANTHROPIC_API_KEY=sk-...
python generate.py "A solo founder hit $10k/mo in 47 days with no code" --style twitter --render
python generate.py "ChatGPT just hit 1 billion users" --style mythos --render
```

Writes `content/<slug>.json` (and renders with `--render`). For `mythos` posts it
also fills in an `image_prompt` and `mood` for the cover. Tweak the voice by
editing `SYSTEM_PROMPT` in `generate.py`. No API key? Hand-write the JSON — copy
`content/daily_twitter.json` or `content/daily_mythos.json` and edit.

---

## 3. Flashy cover art (mythos)

Each `mythos` cover carries an **`image_prompt`** (art-direction for a dramatic AI
hero image) and a **`mood`**. Three ways to turn that into the cover image:

1. **Auto-generate with Nano Banana (default).** Uses Google's Gemini image model
   over its REST API — no SDK needed, and its host is reachable from the Claude
   web sandbox, so this runs in a web session *or* locally:
   ```bash
   export GEMINI_API_KEY=...        # from Google AI Studio
   python -m igslides.imagegen content/daily_mythos.json   # generate + wire in
   python -m igslides content/daily_mythos.json            # re-render
   ```
   Higher-res "Nano Banana Pro": `export GEMINI_IMAGE_MODEL=gemini-3-pro-image`.
   Generated images carry Google's SynthID watermark. OpenAI Images also works —
   `export OPENAI_API_KEY=... IMAGE_PROVIDER=openai` (runs locally; OpenAI's host
   is firewalled in the sandbox).
2. **Paste workflow.** Copy the cover's `image_prompt` into any image tool
   (Midjourney, ChatGPT/DALL·E, Leonardo…), save to
   `assets/backgrounds/<slug>.png`, and set the cover's
   `"background": "assets/backgrounds/<slug>.png"`.
3. **Zero effort.** Leave `"background": "auto"` and pick a `mood`
   (`ember`, `crimson`, `electric`, `gold`, `violet`) for the built-in cinematic
   "AI energy core" backdrop.

---

## 4. Your logo

Drop your real Fortune University seal at **`assets/logo.png`** — it's used
automatically as the avatar on Twitter-style slides (circular-cropped). Until
then, slides fall back to a navy/gold "FU" monogram. See `assets/README.md`.

---

## Content schema (reference)

```jsonc
{
  "style": "mythos" | "twitter",
  "slug": "kebab-case-name",          // output folder name
  "brand": { "name": "...", "handle": "@...", "verified": true, "avatar": "assets/logo.png" },
  "slides": [ ... ]
}
```

A **line** is a string, `{"text", "color"}`, or `{"spans": [...]}` for inline
multi-colour. Colours: `white`, `red`, `muted`, `blue`, or hex (`"#E8372B"`).

- **mythos** `variant`: `cover` (`background`, `mood`, `image_prompt`, `lines`, `hint`)
  · `content` (`lines`, optional `subtext`) · `outro` (`lines`).
- **twitter** `variant`: `cover` (`lines`, optional `accent_right`/`accent_left` emoji)
  · `tweet` (`heading`, `body` array) · `outro` (`lines`).

Full working examples: `content/daily_*.json` and `content/example_*.json`.
