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

## Placeholder Configuration

Before making the site fully public, please ensure you have replaced all instances of `[CONTACT EMAIL]` in the following files with a real email address (e.g., `support@yourdomain.com` or your personal developer email):
- `privacy.html`
- `terms.html`
- `contact.html`

## TikTok URL-Prefix Verification

If TikTok or another platform requires you to place a verification file at the root of your domain (e.g., `tiktok-verify-xyz.txt`), you can simply upload that `.txt` file into the root of this repository. It will automatically be served by GitHub Pages at `https://<your-username>.github.io/clipforge-site/tiktok-verify-xyz.txt`.

## Security

**Do NOT commit to this repository:**
- OAuth Client Secrets
- API Keys
- Personal Access Tokens
- Backend code for ClipForge

This repository should remain strictly for static, public-facing website assets.
