# rghosh08.github.io
my personal website

## Updating the resume

The served resume lives at `public/resume_rajat-ghosh.pdf` — the **only** copy in
the repo. Vite copies `public/` into `dist/`, which the GitHub Pages workflow
deploys, so the site always serves this file at the stable URL
`/resume_rajat-ghosh.pdf`. Never rename it; shared links depend on it.

The LaTeX source of truth is maintained on Overleaf. To publish a new version:

1. Compile and download the PDF from Overleaf.
2. Run `scripts/update-resume.sh [path-to-pdf]` (defaults to `~/Downloads/resume.pdf`) —
   it validates the file, replaces `public/resume_rajat-ghosh.pdf`, and stages it.
3. Commit with a message describing the content change, e.g.
   `Resume: add SNIA talk, July 2026`, and push. The Pages workflow deploys it.

View the version history with `git log --oneline -- public/resume_rajat-ghosh.pdf`;
recover any past version with `git show <commit>:public/resume_rajat-ghosh.pdf > old.pdf`.
