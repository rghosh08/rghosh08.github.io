# rghosh08.github.io
my personal website

## Updating the resume

The served resume lives at `public/resume_rajat-ghosh.pdf` — the **only** copy in
the repo. Vite copies `public/` into `dist/`, which the GitHub Pages workflow
deploys, so the site always serves this file at the stable URL
`/resume_rajat-ghosh.pdf`. Never rename it; shared links depend on it.

The LaTeX source of truth is `resume/resume.tex`, version-controlled in this repo.
To publish a new version:

1. Edit `resume/resume.tex`.
2. Run `scripts/update-resume.sh` — it compiles with [tectonic](https://tectonic-typesetting.github.io)
   (`brew install tectonic`), replaces `public/resume_rajat-ghosh.pdf`, and stages both files.
   (Alternatively compile anywhere — e.g. Overleaf — and pass the PDF: `scripts/update-resume.sh <pdf>`.)
3. Commit with a message describing the content change, e.g.
   `Resume: add SNIA talk, July 2026`, and push. The Pages workflow deploys it.

View the version history with `git log --oneline -- public/resume_rajat-ghosh.pdf`;
recover any past version with `git show <commit>:public/resume_rajat-ghosh.pdf > old.pdf`.
