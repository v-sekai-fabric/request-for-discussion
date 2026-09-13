"""Gate: the rulesets the working agreements describe are the rulesets the repository has.

Reads the claimed ids out of CLAUDE.md and PITFALLS.md rather than restating them.

Usage:
    python check_rulesets.py [--repo owner/name]
    python check_rulesets.py --self-test
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ("CLAUDE.md", "PITFALLS.md")

CLAIM = re.compile(r"ruleset\s*\(?\s*(?:id\s*)?(\d{5,})", re.I)
RETRACTED = re.compile(r"\bretract(?:ed|s|ion)?\b", re.I)
REPO = re.compile(r"`([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+|dot-claude|manifest-weftspun"
                  r"|request-for-discussion)`")


def paragraphs(text):
    return re.split(r"\n\s*\n", text)


def claimed_ids(texts, default_repo=None):
    """Live ids keyed by (repo, id); a retracting paragraph is not a claim."""
    found = {}
    for name, text in texts.items():
        for para in paragraphs(text):
            if RETRACTED.search(para):
                continue
            ids = [int(m.group(1)) for m in CLAIM.finditer(para)]
            if not ids:
                continue
            m = REPO.search(para)
            repo = m.group(1) if m else default_repo
            if repo and "/" not in repo:
                repo = f"V-Sekai-fire/{repo}"
            for rid in ids:
                found.setdefault((repo, rid), []).append(name)
    return found


def live_rulesets(repo):
    """Ids the repository carries, or None when the API cannot be read."""
    r = subprocess.run(
        ["gh", "api", f"repos/{repo}/rulesets", "--paginate"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        return None, r.stderr.strip().splitlines()[-1:] or ["gh api failed"]
    try:
        return {int(x["id"]): x.get("name", "") for x in json.loads(r.stdout)}, []
    except (ValueError, KeyError, TypeError) as exc:
        return None, [f"unparseable ruleset payload: {exc}"]


def report(claims, live_by_repo):
    rows = []
    for (repo, rid), docs in sorted(claims.items(), key=lambda kv: (kv[0][0] or "", kv[0][1])):
        where = ", ".join(sorted(set(docs)))
        live = live_by_repo.get(repo) or {}
        if rid in live:
            rows.append((True, repo, rid, f"named by {where}, present as {live[rid]!r}"))
        else:
            rows.append((False, repo, rid, f"named by {where}, absent from {repo}"))
    return rows


def self_test():
    controls = []
    R = "V-Sekai-fire/request-for-discussion"

    texts = {"CLAUDE.md": "the merge queue on this repo (ruleset 21131040, `MERGE` method)"}
    controls.append(("an id in prose is read",
                     claimed_ids(texts, R) == {(R, 21131040): ["CLAUDE.md"]}))

    texts = {"PITFALLS.md": "main ruleset (id 21131040) enables `merge_queue`"}
    controls.append(("the parenthesised form is read",
                     (R, 21131040) in claimed_ids(texts, R)))

    controls.append(("prose naming no ruleset yields no claim",
                     claimed_ids({"CLAUDE.md": "the queue batches ALLGREEN PRs"}, R) == {}))

    retraction = {"CLAUDE.md": "Earlier text described ruleset 21131040 with ALLGREEN "
                               "grouping. Retracted 2026-09-12; the id returns 404."}
    controls.append(("  control: a retracted id is not a claim",
                     claimed_ids(retraction, R) == {}))

    gap = chr(10) + chr(10)
    mixed = {"CLAUDE.md": "The queue runs under ruleset 30000001." + gap +
                          "Ruleset 21131040 is retracted 2026-09-12."}
    controls.append(("  control: a live id beside a retracted one survives",
                     claimed_ids(mixed, R) == {(R, 30000001): ["CLAUDE.md"]}))

    controls.append(("  control: deleting the retraction makes it live again",
                     claimed_ids({"CLAUDE.md": "The queue runs under ruleset 21131040."}, R)
                     == {(R, 21131040): ["CLAUDE.md"]}))

    other = {"CLAUDE.md": "`dot-claude` runs its queue under ruleset 23145798."}
    controls.append(("a claim names the repository it is about",
                     claimed_ids(other, R) == {("V-Sekai-fire/dot-claude", 23145798):
                                               ["CLAUDE.md"]}))
    controls.append(("  control: without a repository it falls to the default",
                     list(claimed_ids({"CLAUDE.md": "ruleset 30000002 is live."}, R))
                     == [(R, 30000002)]))

    claims = {(R, 21131040): ["CLAUDE.md"]}
    controls.append(("a present ruleset passes",
                     report(claims, {R: {21131040: "main"}})[0][0] is True))
    controls.append(("  control: an absent ruleset fails",
                     report(claims, {R: {}})[0][0] is False))
    controls.append(("  control: a different id does not satisfy the claim",
                     report(claims, {R: {99999999: "main"}})[0][0] is False))
    controls.append(("  control: the right id on the wrong repo does not satisfy it",
                     report(claims, {"V-Sekai-fire/other": {21131040: "main"}})[0][0] is False))

    ok = all(passed for _, passed in controls)
    for label, passed in controls:
        print(f"  {'ok  ' if passed else 'FAIL'} {label}")
    print("")
    print(f"{'ok   ' if ok else 'FAIL '}{len(controls)} controls, both directions")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="V-Sekai-fire/request-for-discussion")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    texts = {}
    for name in DOCS:
        p = ROOT / name
        if not p.is_file():
            print(f"FAIL {name} is absent; the claims cannot be read")
            return 1
        texts[name] = p.read_text(encoding="utf-8")

    claims = claimed_ids(texts, default_repo=args.repo)
    live_by_repo, errs = {}, []
    for repo in sorted({r for r, _ in claims} - {None}):
        live, e = live_rulesets(repo)
        if live is None:
            # Rule 3: an unmet precondition is a FAIL, named, never a silent skip.
            errs.append(f"cannot read {repo} rulesets")
            errs += e
        else:
            live_by_repo[repo] = live

    if errs:
        print(f"FAIL {len(errs)} repository read(s) failed, so claims go unchecked")
        for e in errs:
            print(f"     {e}")
        return 1

    rows = report(claims, live_by_repo)
    for ok, repo, rid, detail in rows:
        print(f"  {'ok  ' if ok else 'FAIL'} {repo} ruleset {rid}  {detail}")
    for repo, live in sorted(live_by_repo.items()):
        for rid, name in sorted(live.items()):
            if (repo, rid) not in claims:
                print(f"  ok   {repo} ruleset {rid}  live as {name!r}, named by no document")
    bad = [r for r in rows if not r[0]]
    total_live = sum(len(v) for v in live_by_repo.values())
    print("")
    print(f"{len(rows)} claimed across {len(live_by_repo)} repo(s), "
          f"{total_live} live, {len(bad)} unhonoured")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
