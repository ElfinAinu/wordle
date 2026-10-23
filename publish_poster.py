#!/usr/bin/env python3
"""Publish the poster to the served branch in one guarded step.

Source of truth:  ``infographic-v4.html`` on the default branch (``main``).
Served artefact:  ``index.html`` on the served branch (``gh-pages``).
The duplicate ``infographic-v4.html`` is removed from the served branch so a
stale copy can never be served again.

The served ref only moves when every guard passes:

1. no retracted claim survives in the source poster;
2. no guess word appears inside a hit-count band in sections I or II;
3. the copied ``index.html`` matches the source poster byte-for-byte, and the
   duplicate poster is gone.

The step is idempotent: a second run with nothing changed writes nothing.
It never pushes; it only updates the local served branch and prints the
suggested push command.

Run: ``python3 publish_poster.py`` (optionally ``--check`` to run the guards
without writing).
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# Claims the poster has retracted; none may reach the served page.
RETRACTED_CLAIMS = (
    "median human",
    "doubles (14.7",
    "solved on the second guess",
    "Five hits means",
)

# Guess words the poster used to print inside hit-count bands. The real guard
# is the vocabulary match below; these are kept as a belt-and-braces fallback.
HISTORICAL_BAND_WORDS = ("dumpy", "debug", "reedy", "gawky", "match", "resin")

SOURCE_PATH = "infographic-v4.html"
SERVED_PATH = "index.html"
DUPLICATE_PATH = SOURCE_PATH
VOCAB_PATHS = ("data/allowed.txt", "data/answers.txt")

WORD_LENGTH = 5
WORD_RE = re.compile(rf"\b[A-Z]{{{WORD_LENGTH}}}\b")


class PublishError(Exception):
    """A guard failed or the publish could not complete."""


def run_git(
    repo: Path,
    *args: str,
    input: bytes | None = None,
    env: dict | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        input=input,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    if check and result.returncode != 0:
        detail = (
            result.stderr.decode(errors="replace").strip()
            or result.stdout.decode(errors="replace").strip()
        )
        raise PublishError(f"git {' '.join(args)} failed: {detail}")
    return result


def git(
    repo: Path, *args: str, input: bytes | None = None, env: dict | None = None
) -> bytes:
    return run_git(repo, *args, input=input, env=env).stdout


def git_text(repo: Path, *args: str, env: dict | None = None) -> str:
    return git(repo, *args, env=env).decode(errors="replace").strip()


def git_text_or_default(repo: Path, *args: str, default: str = "") -> str:
    result = run_git(repo, *args, check=False)
    if result.returncode != 0:
        return default
    return result.stdout.decode(errors="replace").strip()


def ref_exists(repo: Path, ref: str) -> bool:
    result = run_git(
        repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}", check=False
    )
    return result.returncode == 0


def repo_root(start: Path) -> Path:
    return Path(git_text(start, "rev-parse", "--show-toplevel"))


def read_blob(repo: Path, ref: str, path: str) -> bytes:
    return git(repo, "show", f"{ref}:{path}")


def has_blob(repo: Path, ref: str, path: str) -> bool:
    result = run_git(repo, "cat-file", "-e", f"{ref}:{path}", check=False)
    return result.returncode == 0


def clean_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def get_section(html: str, anchor_id: str) -> str:
    at = html.index(f'id="{anchor_id}"')
    start = html.rindex("<section", 0, at)
    return html[start : html.index("</section>", start)]


def band_strategies(html: str) -> list[tuple[str, str]]:
    """The strategy text of every band-level hit-count row in sections I and II.

    Only sections I and II are band-level: each row is a hit count whose
    Strategy cell must state a mix, so a guess word there is a bug. Sections
    III and IV name a word per pattern by design — that word is the answer to
    the row — so they are not parsed as bands.
    """
    bands: list[tuple[str, str]] = []
    method = get_section(html, "method")
    for match in re.finditer(r'<div class="flow-strat">(.*?)</div>', method, re.DOTALL):
        bands.append(("I", clean_html(match.group(1))))
    tree = get_section(html, "tree")
    for match in re.finditer(r'<td class="strat">(.*?)</td>', tree, re.DOTALL):
        bands.append(("II", clean_html(match.group(1))))
    if not bands:
        raise PublishError("could not parse any hit-count band from sections I/II")
    return bands


def load_vocabulary(repo: Path, source_ref: str) -> set[str]:
    words: set[str] = set()
    for path in VOCAB_PATHS:
        if has_blob(repo, source_ref, path):
            words.update(read_blob(repo, source_ref, path).decode().split())
    if not words:
        raise PublishError(
            f"no guess vocabulary found on {source_ref}: expected {' or '.join(VOCAB_PATHS)}"
        )
    return {
        word.lower() for word in words if word.isalpha() and len(word) == WORD_LENGTH
    }


def guard_source(repo: Path, source_ref: str, poster: bytes) -> None:
    text = poster.decode(errors="replace")
    lower = text.lower()
    failures: list[str] = []

    for claim in RETRACTED_CLAIMS:
        if claim.lower() in lower:
            failures.append(f"retracted claim is back: {claim!r}")

    if "<section" not in text or 'id="reference"' not in text:
        failures.append("source does not look like the poster (missing section markup)")

    vocabulary = load_vocabulary(repo, source_ref)
    for section, strategy in band_strategies(text):
        tokens = {t.lower() for t in WORD_RE.findall(strategy)}
        for word in sorted(tokens & vocabulary):
            failures.append(
                f"section {section} band names the guess word {word.upper()}: {strategy!r}"
            )
        for word in HISTORICAL_BAND_WORDS:
            if re.search(rf"\b{word}\b", strategy, re.IGNORECASE):
                failures.append(
                    f"section {section} band names the guess word {word.upper()}: {strategy!r}"
                )

    failures = list(dict.fromkeys(failures))

    if failures:
        raise PublishError("source guards failed:\n  - " + "\n  - ".join(failures))


def build_tree(repo: Path, served_ref: str, poster: bytes) -> tuple[str, str]:
    """Return (new_tree, old_tree) with index.html = poster and no duplicate."""
    old_tree = git_text(repo, "rev-parse", f"{served_ref}^{{tree}}")
    with tempfile.TemporaryDirectory(prefix="publish-poster-index-") as tmp:
        index = os.path.join(tmp, "index")
        env = {**os.environ, "GIT_INDEX_FILE": index}
        git(repo, "read-tree", served_ref, env=env)
        blob = git(repo, "hash-object", "-w", "--stdin", input=poster).decode().strip()
        git(
            repo,
            "update-index",
            "--add",
            "--cacheinfo",
            f"100644,{blob},{SERVED_PATH}",
            env=env,
        )
        if has_blob(repo, served_ref, DUPLICATE_PATH):
            git(repo, "update-index", "--force-remove", DUPLICATE_PATH, env=env)
        new_tree = git_text(repo, "write-tree", env=env)
    return new_tree, old_tree


def verify_served(repo: Path, ref: str, poster: bytes) -> None:
    served = read_blob(repo, ref, SERVED_PATH)
    if served != poster:
        raise PublishError(
            f"{ref}:{SERVED_PATH} does not match {SOURCE_PATH} after the copy "
            f"({len(served)} vs {len(poster)} bytes)"
        )
    if has_blob(repo, ref, DUPLICATE_PATH):
        raise PublishError(f"{ref} still carries the duplicate {DUPLICATE_PATH}")


def commit(repo: Path, tree: str, parent: str, message: str) -> str:
    env = dict(os.environ)
    env.setdefault(
        "GIT_AUTHOR_NAME",
        git_text_or_default(
            repo, "config", "--get", "user.name", default="poster-publish"
        ),
    )
    env.setdefault(
        "GIT_AUTHOR_EMAIL",
        git_text_or_default(
            repo, "config", "--get", "user.email", default="poster-publish@localhost"
        ),
    )
    env.setdefault("GIT_COMMITTER_NAME", env["GIT_AUTHOR_NAME"])
    env.setdefault("GIT_COMMITTER_EMAIL", env["GIT_AUTHOR_EMAIL"])
    return (
        git(repo, "commit-tree", tree, "-p", parent, input=message.encode(), env=env)
        .decode()
        .strip()
    )


def validate_source_and_served(repo: Path, source_ref: str, served_ref: str) -> None:
    if not has_blob(repo, source_ref, SOURCE_PATH):
        raise PublishError(f"{source_ref} has no {SOURCE_PATH}")
    if not ref_exists(repo, served_ref):
        raise PublishError(f"served branch {served_ref!r} does not exist")


def clean_source(repo: Path, source_ref: str) -> bytes:
    poster = read_blob(repo, source_ref, SOURCE_PATH)
    guard_source(repo, source_ref, poster)
    bands = band_strategies(poster.decode(errors="replace"))
    print(
        f"guards: source {source_ref}:{SOURCE_PATH} is clean ({len(bands)} bands checked)"
    )
    return poster


def move_served_ref(
    repo: Path, served_ref: str, new_tree: str, parent: str, message: str, poster: bytes
) -> str:
    """Commit the new tree, move the served ref, and roll back if it fails to verify."""
    verify_served(repo, new_tree, poster)
    commit_sha = commit(repo, new_tree, parent, message)
    git(repo, "update-ref", f"refs/heads/{served_ref}", commit_sha, parent)
    try:
        verify_served(repo, served_ref, poster)
    except PublishError:
        git(repo, "update-ref", f"refs/heads/{served_ref}", parent, commit_sha)
        raise
    return commit_sha


def publish(args: argparse.Namespace) -> int:
    repo = repo_root(Path(args.repo))
    source_ref = args.source
    served_ref = args.served_branch

    validate_source_and_served(repo, source_ref, served_ref)
    poster = clean_source(repo, source_ref)
    if args.check:
        print("check-only: guards passed, nothing written")
        return 0

    new_tree, old_tree = build_tree(repo, served_ref, poster)
    if new_tree == old_tree:
        print(
            f"no-op: {served_ref} already serves {source_ref}:{SOURCE_PATH} with no duplicate"
        )
        return 0

    parent = git_text(repo, "rev-parse", served_ref)
    message = args.message or f"chore(pages): publish poster from {source_ref}"
    commit_sha = move_served_ref(repo, served_ref, new_tree, parent, message, poster)

    print(f"published: {served_ref} now {commit_sha[:12]} (was {parent[:12]})")
    print(f"  {SERVED_PATH} <- {source_ref}:{SOURCE_PATH}")
    print(f"  removed {DUPLICATE_PATH} from {served_ref}")
    print(f"not pushed; review, then: git push origin {served_ref}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=".", help="any path inside the repository")
    parser.add_argument(
        "--source",
        default=os.environ.get("PUBLISH_SOURCE_REF", "main"),
        help="default branch holding the poster (default: main)",
    )
    parser.add_argument(
        "--served-branch",
        default=os.environ.get("PUBLISH_SERVED_BRANCH", "gh-pages"),
        help="branch that serves the page (default: gh-pages)",
    )
    parser.add_argument("--message", default=None, help="commit subject")
    parser.add_argument(
        "--check", action="store_true", help="run guards only, write nothing"
    )
    args = parser.parse_args(argv)
    try:
        return publish(args)
    except PublishError as exc:
        print(f"ABORT: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
