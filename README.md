# ClipForge Site

This repository contains the static website for ClipForge, an application that helps create and publish short-form informational videos. 
This site serves as the official public website required for TikTok Developer App verification and other OAuth platform reviews.

## GitHub Pages Deployment

This site is built with plain HTML and CSS and requires no build system or frameworks.

**To deploy to GitHub Pages:**

1. Push this code to a public GitHub repository named `clipforge-site` (or similar).
2. Go to your repository **Settings**.
3. Navigate to **Pages** in the left sidebar.
4. Under **Build and deployment**, select **Deploy from a branch**.
5. Under **Branch**, select `main` (or `master`) and the `/ (root)` folder.
6. Click **Save**.

Your site will be available at `https://<your-username>.github.io/clipforge-site/`.

## Pages

| Page | Purpose |
| --- | --- |
| `index.html` | What ClipForge does, how video creation and publishing work, supported platforms |
| `tiktok.html` | TikTok Login Kit / Content Posting API: OAuth flow, scopes, posting controls, disconnecting |
| `privacy.html` | Privacy Policy |
| `terms.html` | Terms of Service |
| `contact.html` | Support contact |
| `404.html` | Not-found page (uses `<base href="/clipforge-site/">` so it works at any path) |

All other references are relative, so the site works under the `/clipforge-site/` base path.

## Branding

`branding/clipforge-app-icon.webp` is an exact copy of the canonical ClipForge app icon from the
main ClipForge repository (`branding/clipforge-app-icon.webp`, branch `cloud/unified-app-branding`,
commit `4dfb882`) - the icon submitted in the TikTok Developer Portal. Do not redraw or restyle it.

`scripts/generate_icons.py` checks the master's SHA-256 and derives every icon by plain resizing:

| File | Size | Used for |
| --- | --- | --- |
| `favicon.ico` | 16, 32, 48 | browser tab, bookmarks |
| `assets/icons/favicon-16x16.png`, `-32x32`, `-48x48` | 16, 32, 48 | browser tab (PNG) |
| `assets/icons/apple-touch-icon.png` | 180 | iOS/iPadOS home screen |
| `assets/icons/icon-192.png` | 192 | web app manifest, header logo |
| `assets/icons/icon-512.png` | 512 | web app manifest, home page |
| `assets/og-image.png` | 1200x630 | Open Graph / social previews (icon on black) |

Every page links these in `<head>` with a `?v=` cache-busting suffix (the master's hash prefix);
`site.webmanifest` lists the 192/512 icons. The icons are byte-identical to the main ClipForge web
app's own `favicon.ico`, `apple-icon.png`, `icon.png` and manifest icons.

```bash
python3 scripts/generate_icons.py          # regenerate after replacing the master (needs Pillow)
python3 scripts/generate_icons.py --check  # fail if a committed icon is stale
python3 scripts/verify_site.py             # links, icon tags and sizes, OG URLs, base paths, secrets
```

If the icon or a page's icon links change, bump the `?v=` value on every page.

## TikTok URL-Prefix Verification

If TikTok or another platform requires you to place a verification file at the root of your domain (e.g., `tiktok-verify-xyz.txt`), you can simply upload that `.txt` file into the root of this repository. It will automatically be served by GitHub Pages at `https://<your-username>.github.io/clipforge-site/tiktok-verify-xyz.txt`.

## Security

**Do NOT commit to this repository:**
- OAuth Client Secrets
- API Keys
- Personal Access Tokens
- Backend code for ClipForge

This repository should remain strictly for static, public-facing website assets.
