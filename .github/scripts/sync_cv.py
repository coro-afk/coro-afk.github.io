"""Copy the compiled CV from its private source and propose a reviewed update.

Runs on a fresh GitHub Actions runner using Python's standard library, git, and gh.
Only the public PDF is copied; the source repository is never checked out.
"""

import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


SOURCE = "coro-afk/academic-cv"
DESTINATION = "coro-afk/coro-afk.github.io"
PDF = "haotianyin_cv.pdf"
BRANCH = "automation/update-cv"


def run(*args, env=None):
    return subprocess.check_output(args, env=env, text=True).strip()


def report(message):
    print(message)
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(summary, "a", encoding="utf-8") as stream:
            stream.write(message + "\n")


def main():
    if os.environ.get("GITHUB_REPOSITORY") != DESTINATION:
        raise RuntimeError("Run this workflow in the homepage repository.")
    if os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise RuntimeError("Run the workflow from main; all edits go to the sync branch.")
    if not os.environ.get("GH_TOKEN"):
        raise RuntimeError("The homepage GITHUB_TOKEN is required.")
    source_token = os.environ.pop("CV_REPO_READ_TOKEN", "")
    if not source_token:
        raise RuntimeError("Add the CV_REPO_READ_TOKEN Actions secret; see README.md.")
    if run("git", "status", "--porcelain"):
        raise RuntimeError("Stop: the working tree contains uncommitted changes.")

    # This credential is passed only to read requests for the private CV repository.
    source_env = dict(os.environ, GH_TOKEN=source_token)
    revision = json.loads(run("gh", "api", f"repos/{SOURCE}/commits/main", env=source_env))["sha"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise RuntimeError("Unexpected CV source revision.")
    entry = json.loads(run(
        "gh", "api", f"repos/{SOURCE}/contents/{PDF}?ref={revision}", env=source_env
    ))
    if entry.get("encoding") != "base64" or entry.get("type") != "file":
        raise RuntimeError("The source must be a regular PDF file supported by the Contents API.")
    data = base64.b64decode("".join(entry["content"].split()), validate=True)
    blob = b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    if hashlib.sha1(blob).hexdigest() != entry["sha"]:
        raise RuntimeError("The downloaded CV does not match the source Git blob.")
    if not data.startswith(b"%PDF-") or b"%%EOF" not in data[-1024:]:
        raise RuntimeError("The source file does not have a complete PDF signature.")

    # The built-in token is scoped to this homepage repository.
    run("gh", "auth", "setup-git", "--hostname", "github.com")
    run("git", "fetch", "origin")
    if run("git", "remote", "get-url", "origin") != f"https://github.com/{DESTINATION}":
        # GitHub checkouts may include the optional .git suffix.
        if run("git", "remote", "get-url", "origin") != f"https://github.com/{DESTINATION}.git":
            raise RuntimeError("Unexpected destination remote.")
    published_blob = run("git", "rev-parse", f"origin/main:{PDF}")
    if published_blob == entry["sha"]:
        report("The public CV already matches the latest compiled source. No update needed.")
        return

    pull_requests = json.loads(run(
        "gh", "pr", "list", "--repo", DESTINATION, "--head", BRANCH,
        "--base", "main", "--state", "all", "--limit", "1",
        "--json", "url,state,mergedAt"
    ))
    previous_pr = pull_requests[0] if pull_requests else None
    if previous_pr and previous_pr["state"] == "CLOSED" and not previous_pr["mergedAt"]:
        raise RuntimeError("The previous sync PR was closed without merging. Reopen it to resume.")

    run("git", "config", "user.name", "github-actions[bot]")
    run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    remote_branch = run("git", "branch", "--remotes", "--list", f"origin/{BRANCH}")
    if remote_branch:
        changes = run("git", "diff", "--name-only", f"origin/main...origin/{BRANCH}").splitlines()
        if any(path != PDF for path in changes):
            raise RuntimeError("The sync branch contains unrelated changes; review it manually.")
        run("git", "switch", "--create", BRANCH, f"origin/{BRANCH}")
        # Preserve existing commits. A conflict fails the job instead of discarding changes.
        run("git", "merge", "--no-edit", "origin/main")
    else:
        run("git", "switch", "--create", BRANCH, "origin/main")

    Path(PDF).write_bytes(data)
    run("git", "add", "--", PDF)
    changes = run("git", "diff", "--cached", "--name-only").splitlines()
    if changes:
        if changes != [PDF]:
            raise RuntimeError("Only the CV PDF may be committed by this workflow.")
        run("git", "diff", "--cached", "--check")
        print(run("git", "diff", "--cached", "--stat"))
        run("git", "commit", "-m", f"Update public CV from academic-cv {revision[:12]}")

    if run("git", "diff", "--name-only", "origin/main", "HEAD").splitlines() != [PDF]:
        raise RuntimeError("The proposed update must change only the CV PDF.")
    run("git", "push", "origin", f"HEAD:refs/heads/{BRANCH}")

    if previous_pr and previous_pr["state"] == "OPEN":
        pr_url = previous_pr["url"]
    else:
        # Keep the description stable when subsequent source revisions update this PR.
        body = (
            "Update the public CV PDF from the latest compiled version in academic-cv.\n\n"
            "The PDF is copied unchanged and its Git blob hash is verified. The sync "
            "commit message identifies the source revision. Homepage text is unchanged.\n\n"
            "Review the PDF before merging. Merging updates the existing CV download "
            "link after GitHub Pages publishes the change.\n"
        )
        with tempfile.TemporaryDirectory(prefix="cv-pr-") as directory:
            body_file = Path(directory) / "body.md"
            body_file.write_text(body, encoding="utf-8")
            pr_url = run(
                "gh", "pr", "create", "--repo", DESTINATION, "--base", "main",
                "--head", BRANCH, "--draft", "--title", "Update public CV",
                "--body-file", str(body_file)
            )
    report(f"CV update ready for review: {pr_url}")


if __name__ == "__main__":
    main()
