# animated-github-profile

Make your GitHub profile look like a terminal: a self-typing **ASCII portrait** of you, a **neofetch-style info card**, and a **live contribution heatmap** that refreshes itself every day.

No tokens. No servers. No third-party stats services. Just three SVG files, two Python scripts, and one GitHub Actions cron.

Live example: [github.com/navi3582](https://github.com/navi3582)

## How it works

GitHub strips `<script>` from profile READMEs, but it renders SVG images and plays the animations inside them. So all the motion lives inside self-contained SVG files, and your README just places them.

The contribution data comes from GitHub's public HTML endpoint `github.com/users/<you>/contributions`. No API key needed.

## Setup

**1. Create your profile repo.** GitHub gives every account one magic repo: name it exactly your username. Its README shows on your profile.

```bash
gh repo create YOUR_USERNAME --public --clone
```

**2. Copy the `scripts/` folder from this template into it, then install:**

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r scripts/requirements.txt            # heatmap only
pip install -r scripts/requirements-portrait.txt   # portrait (local, one-time)
```

**3. Make your ASCII portrait** (once, or whenever you change your photo):

```bash
python scripts/prep_photo.py your-photo.jpg   # background removal + contrast
python scripts/make_ascii_svg.py              # writes ascii-portrait.svg
```

A clean, well-lit photo works best. The background is removed automatically.

**4. Edit `scripts/make_info_card.py`** — fill in the `ROWS` list with your name, role, projects and contact, then:

```bash
python scripts/make_info_card.py              # writes info-card.svg
```

**5. Render your heatmap:**

```bash
GITHUB_USERNAME=YOUR_USERNAME python scripts/fetch_contributions.py
python scripts/render_heatmap_svg.py          # writes contrib-heatmap.svg
```

**6. Compose your README.md:**

```html
<div align="center">
<h3><code>you@github ~ $ ./contributions.sh</code></h3>
<img src="./contrib-heatmap.svg" width="860" />
<br><br>
<h3><code>you@github ~ $ whoami</code></h3>
<table>
<tr>
<td valign="top"><img src="./ascii-portrait.svg" width="370" /></td>
<td valign="top"><img src="./info-card.svg" width="490" /></td>
</tr>
</table>
</div>
```

**7. Auto-refresh daily.** Create `.github/workflows/update-profile-art.yml` in your repo:

```yaml
name: Update profile art
"on":
  schedule:
    - cron: "17 6 * * *"
  workflow_dispatch: {}
  push:
    branches: [main]
permissions:
  contents: write
jobs:
  heatmap:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r scripts/requirements.txt
      - run: python scripts/fetch_contributions.py
        env:
          GITHUB_USERNAME: YOUR_USERNAME
      - run: python scripts/render_heatmap_svg.py
      - uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore: refresh contribution graph [skip ci]"
          file_pattern: "data/contributions.json contrib-heatmap.svg"
```

Push, trigger it once from the Actions tab, and your profile wakes up before you do.

## Tips

- **Monochrome portraits look clean. Rainbow ASCII looks like noise.** One light color on a dark background.
- Keep the widths aligned: the heatmap's 860 equals the two columns below it (370 + 490).
- If your public heatmap shows fewer contributions than you expect, enable Profile → Contribution settings → Private contributions. Only anonymous counts are shown, never repo names.

## Credits

Approach inspired by [Avi Vashishta's write-up](https://www.avivashishta.com/blog/build-animated-github-profile-readme.html). This template was extracted from [navi3582's profile](https://github.com/navi3582/navi3582).

MIT licensed. Fork away.
