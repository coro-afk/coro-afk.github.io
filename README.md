# Haotian Yin's academic homepage

A single-page academic homepage, written in plain HTML and CSS. There are no
JavaScript files, build tools, dependencies, or external fonts.

## Files

- `index.html` — biography, research interests, publications, talks, and contact.
- `style.css` — responsive layout and typography.
- `haotianyin_cv.pdf` — public copy of the compiled CV, kept byte-for-byte unchanged.
- `.nojekyll` — tells GitHub Pages to serve the files without Jekyll processing.
- `.github/workflows/sync-cv.yml` and `.github/scripts/sync_cv.py` — propose CV
  updates through draft PRs; they are not part of the website runtime.

## Preview and GitHub Pages

Open `index.html` directly in a browser, or serve the repository root locally:

```sh
python -m http.server 8000
```

In the repository's **Settings → Pages**, use **Deploy from a branch**, select
`main`, and choose **/ (root)**. The homepage will be served at
<https://coro-afk.github.io/> after the changes have been reviewed and merged.
No build step or site generator is required.

## CV link and automatic updates

The editable CV is maintained in the private
[`coro-afk/academic-cv`](https://github.com/coro-afk/academic-cv) repository.
This website publishes only a copy of `haotianyin_cv.pdf`; a direct link to the
private repository would be inaccessible to visitors.

The homepage uses the relative link `haotianyin_cv.pdf`. Its public address remains
<https://coro-afk.github.io/haotianyin_cv.pdf> when the file is updated.

The **Sync CV** workflow checks the compiled PDF on the CV repository's `main`
branch daily at 03:17 UTC (11:17 China Standard Time), or when run manually.
GitHub may delay scheduled runs. It copies only the PDF, verifies its Git blob
hash, and creates a **draft PR** from `automation/update-cv` to `main`. Further
updates reuse the same open PR and preserve its existing description and review
state. It never merges a PR, pushes to `main`, force-pushes, or deletes a branch.

### One-time setup

After this homepage PR is reviewed and merged:

1. Create a **fine-grained personal access token** in your GitHub account settings.
   Select only `coro-afk/academic-cv` under repository access, grant **Contents:
   Read-only** (with the automatically required metadata access), and choose an
   expiration date.
2. In **this homepage repository**, open **Settings → Secrets and variables →
   Actions → New repository secret**. Name the secret `CV_REPO_READ_TOKEN` and
   paste the token as its value. Do not put the token in a file or commit.
3. Under **Settings → Actions → General → Workflow permissions**, enable
   **Allow GitHub Actions to create and approve pull requests**. The workflow
   requests `contents: write` and `pull-requests: write` for this repository only;
   it does not approve PRs. Account or organization policy must permit this option.
4. Open **Actions → Sync CV → Run workflow**, select `main`, and run it once.
   If both PDFs already match, it succeeds without creating a PR.

The built-in `GITHUB_TOKEN` handles writes to this homepage repository. The
separate read-only token is used only to retrieve the CV from its private source.
The workflow does not execute or copy the CV's LaTeX sources or build scripts.

### When you update the CV

1. Update and compile `haotianyin_cv.pdf` in `academic-cv`, then review and merge
   its update to that repository's `main` branch.
2. Wait for the daily check or run **Sync CV** manually.
3. Review the proposed PDF in the draft PR, mark the PR ready, and merge it.
   GitHub Pages then serves the updated PDF at the same address.

Updating only the LaTeX source does not update the compiled PDF. The biography,
publication statuses, and talks in `index.html` also need separate edits; the
workflow only synchronizes the PDF.

Missing or expired credentials, merge conflicts, or unrelated changes on the
automation branch fail the workflow for manual review. Closing its PR without
merging pauses further proposals until that PR is reopened. You can disable the
workflow from the Actions tab; GitHub may also disable scheduled workflows in
public repositories after 60 days without repository activity.

### Manual fallback

1. Update and compile the CV in `academic-cv`, then review and merge its update.
2. Fetch the latest `origin/main` in this homepage repository. Start a task branch
   from it with a clean working tree.
3. Copy the latest compiled `haotianyin_cv.pdf` into this repository's root,
   replacing the previous public copy without editing the PDF.
4. Review the diff, commit, push the task branch, and open a draft PR against `main`.
5. After review and merge, GitHub Pages serves the new PDF at the same address.

## Content source and scope

The initial content and PDF match the CV in `academic-cv` at commit
`f1ed3b42fdecadcc69e871c1068246837fd085e7` (15 September 2026).
The introduction also draws on the thesis overview in that repository.
Publication titles, author order, venues, statuses, and supplied links follow
the CV. Accepted work and manuscripts under review are listed separately.

The concise homepage omits the full education history, research appointments,
older funded-project descriptions, honors and scholarships, language scores,
and examiner-facing thesis material. No public research-software URL or personal
GitHub profile link is supplied in the CV, so no software section or guessed
profile link is included. Google Scholar and ORCID are included as supplied.
No photo is present in the source repositories.
