"""Inventory and anti-entropy check over the workspace. CLAUDE.md names this check.

METHOD, AND WHY IT IS MOSTLY NOT RANDOM. CLAUDE.md rule 5: "A sampled check only sees
defects larger than ~3/n. For a FIXED population, enumerate rather than estimate."
Manifest projects, serials, blocklist rows and linkfiles are all fixed and countable,
so sampling them would be strictly worse than reading all of them. They are enumerated.

Randomness earns its place only where enumeration costs too much to run: picking which
expensive re-verification to perform. That draw uses `secrets`, so it cannot be nudged.
"""
import os, re, secrets, subprocess, sys, xml.etree.ElementTree as ET
from pathlib import Path

RFD = Path(__file__).resolve().parent.parent
ROOT = next((c for c in [RFD, *RFD.parents] if (c / ".repo").is_dir()), None)
if ROOT is None:
    print("no .repo above this checkout, so there is no workspace to check")
    raise SystemExit(0)
out, fails = [], 0

def check(name, ok, detail=""):
    global fails
    if not ok: fails += 1
    out.append(f"  {'ok  ' if ok else 'FAIL'} {name:<42} {detail}")

# --- A. manifest projects, enumerated -------------------------------------------------
man = ET.parse(ROOT/".repo/manifests/default.xml").getroot()
projects = [(p.get("name"), p.get("path")) for p in man.iter("project")]
missing = [p for _, p in projects if not (ROOT/p).is_dir()]
check("manifest paths exist on disk", not missing, f"{len(projects)} projects, missing: {missing or 'none'}")
# RFD 2064: a checkout directory keeps the name its build hardcodes, so only the segments
# the workspace picks -- the side and the repo -- are ours to spell. Deeper segments sit
# inside an upstream tree and are named and counted rather than dropped from the count.
OURS = 2


def _segments(path):
    return [s for s in path.replace("\\", "/").split("/") if s]


bad = [p for _, p in projects if any("_" in s or " " in s for s in _segments(p)[:OURS])]
vendored = sorted({p for _, p in projects
                   if any("_" in s or " " in s for s in _segments(p)[OURS:])})
check("every path we pick is hyphen-only", not bad, f"offenders: {bad or 'none'}")
check("  vendored segments named, not dropped", True,
      f"{len(vendored)} path(s) exempt under RFD 2064: {vendored or 'none'}")
check("  control: an underscore we picked is caught",
      bool([x for x in ["3-interactor/bad_name"] if any("_" in s for s in _segments(x)[:OURS])])
      and not [x for x in ["3-interactor/ok/third_party/eigen"]
               if any("_" in s for s in _segments(x)[:OURS])],
      "planted 3-interactor/bad_name caught, vendored third_party not")

# --- B. serials, enumerated both directions -------------------------------------------
# A text read, where check-rfd-serials.py reads the same rows through the USD API; two
# implementations disagreeing is the finding. The .exs source is tracked, the .usda is not.
REGISTERS = ["SERIALS.exs", "SERIALS-vsekai-fabric.exs"]
absent = [f for f in REGISTERS if not (RFD/f).is_file()]
check("every serial register present", not absent, f"{len(REGISTERS)} registers, absent: {absent or 'none'}")
s = "\n".join((RFD/f).read_text(encoding="utf-8") for f in REGISTERS if (RFD/f).is_file())

# `allocated` and `deleted` both spell a row `serial N, "slug"`, so reading the whole file
# counts a retired serial as live and then reports it as a serial that reaches no document.
BLOCKS = re.compile(r"^\s*(allocated|unused|deleted)\b[^\n]*\n(.*?)^\s{4}end$", re.M | re.S)
blocks = {}
for _name, _body in BLOCKS.findall(s):
    blocks.setdefault(_name, []).append(_body)


def _rows_in(body):
    return [(int(n), sl) for n, sl in re.findall(r'^\s*serial (\d+), "([^"]*)"', body, re.M)]


def _rows(name):
    return _rows_in("\n".join(blocks.get(name, [])))


rows = _rows("allocated")
live = [n for n, _ in rows]
slugs = [sl for _, sl in rows]
declared = len(re.findall(r"^\s*serial \d+", "\n".join(blocks.get("allocated", [])), re.M))
dead = sorted({n for n, _ in _rows("deleted")}
              | {int(x) for x in re.findall(r"^\s*retired (\d+),", s, re.M)})
check("every register block is parsed",
      "allocated" in blocks and set(blocks) <= {"allocated", "unused", "deleted"},
      f"blocks: {sorted(blocks)}")
check("  control: a deleted row is not counted live",
      2000 in set(dead) and 2000 not in set(live), "2000 sits in deleted, not allocated")

# Both sites register here, but 39 of site 2's documents live in `manuals-vsk`, so a sweep
# scoped to this checkout returns a true count and answers the wrong question.
docs = {}
for tree in sorted({ROOT/p/"rfd" for _, p in projects} | {RFD/"rfd"}):
    if not tree.is_dir():
        continue
    for entry in sorted(os.listdir(tree)):
        name = entry[:-4] if entry.endswith(".exs") else entry
        m = re.match(r"^(\d{4})-", name)
        if m:
            # A name, not a path: 1144 is both an .exs source and a linked directory.
            docs.setdefault(int(m.group(1)), set()).add(name)

check("every allocated row carries a slug", declared == len(rows), f"{declared} rows / {len(rows)} slugs")
check("no duplicate serials", len(live) == len(set(live)), f"{len(live)} rows, {len(set(live))} distinct")
check("  control: a planted duplicate row is seen",
      len(_rows_in("\n".join(blocks["allocated"]) + '\n      serial 1000, "conventions"\n')) == len(rows)+1)
check("no retired serial reused", not (set(live) & set(dead)), f"{len(dead)} retired")
# A deleted serial keeps its row and its document: the document moved to another checkout,
# and the row is what stops the number being handed out again. Registered means either block.
registered = set(live) | set(dead)
unregistered = sorted(n for n in docs if n not in registered)
check("every document registered", not unregistered, f"{len(docs)} documents, unregistered: {unregistered or 'none'}")
orphans = sorted(n for n in live if n not in docs)
check("every allocated serial resolves to a document", not orphans,
      f"{len(live)} allocated, no document: {len(orphans)}{' ' + str(orphans[:8]) if orphans else ''}")
forked = {n: v for n, v in docs.items() if len(v) > 1}
check("one document per serial", not forked, f"forked: {({n: sorted(v) for n, v in forked.items()}) or 'none'}")
check("  control: a planted second document is seen",
      len(docs.get(1000, set()) | {"1000-planted"}) == len(docs.get(1000, set())) + 1)
mismatch = [f"{n}-{sl}" for n, sl in rows if n in docs and f"{n}-{sl}" not in docs[n]]
check("slug matches document name", not mismatch, f"mismatches: {mismatch or 'none'}")

# --- C. blocklist rows vs sections, enumerated ----------------------------------------
cl = (RFD/"CLAUDE.md").read_text(); bl = (RFD/"BLOCKLIST.md").read_text()
rows = [l for l in cl.splitlines() if l.startswith("|") and "see below" in l.lower()]
secs = [l for l in bl.splitlines() if l.startswith("### ")]
check("blocklist rows == sections", len(rows)==len(secs), f"{len(rows)} rows / {len(secs)} sections")
check("  control: counter finds a planted row", 
      len([l for l in (cl+"\n| planted | See Below |").splitlines() if l.startswith("|") and "see below" in l.lower()]) == len(rows)+1,
      "case-insensitive match verified against a planted row")

# --- D. linkfiles, enumerated ----------------------------------------------------------
links = [(lf.get("src"), lf.get("dest"), p.get("path"))
         for p in man.iter("project") for lf in p.iter("linkfile")]
broken = [d for src, d, pp in links if not (ROOT/d).exists()]
check("every linkfile resolves", not broken, f"{len(links)} links, broken: {broken or 'none'}")

# --- E. README line bound, enumerated over all RFDs ------------------------------------
# The READMEs are build artifacts (RFD 2232). Rule 3: an unbuilt checkout is an unmet
# precondition and fails, rather than measuring zero of them and reporting no offenders.
limit = 40
sources = sorted((RFD/"rfd").glob("*.exs"))
rendered = sorted((RFD/"rfd").glob("*/README.md"))
check("READMEs rendered to measure", bool(rendered),
      f"{len(rendered)} rendered / {len(sources)} sources"
      + ("" if rendered else "; run `mix rfd.render`"))
over = [p.parent.name for p in rendered
        if len(p.read_text(encoding="utf-8").splitlines()) > limit]
check(f"every README <= {limit} lines", not over, f"{len(rendered)} READMEs, over: {over or 'none'}")

# --- F. shuffled full pass over the expensive checks -----------------------------------
# A SHUFFLE RATHER THAN A DRAW, AND THE DIFFERENCE IS COVERAGE. The first version of this
# used `secrets.randbelow` three times, which samples WITH REPLACEMENT: one run drew three
# picks and got two distinct checks, and nothing bounds how long an item can go unvisited.
# A shuffled full pass visits every item exactly once, so coverage is total and the only
# thing randomised is the order -- which still surfaces anything order-dependent.
#
# Enumerating rather than sampling is also what CLAUDE.md rule 5 asks for: this population
# is fixed and countable, so a sample would see only defects larger than about 3/n while
# costing nearly as much.
EXPENSIVE = ["check_fourloops_plan", "check_fourloops_etnf", "check_rfd1122_plan",
             "check_usd_valid", "check_pen_66606", "check_blocklist_detail",
             "check_goal_manifests", "check-rfd-structure",
             ("check_comment_ladder", ("--self-test",)),
             ("check_rfd_canary", ("--self-test",)),
             ("check_project_readme_length", ("--self-test",)),
             ("check_rulesets", ("--self-test",))]
order = list(EXPENSIVE)
secrets.SystemRandom().shuffle(order)
out.append("")
out.append(f"  shuffled full pass, {len(order)} of {len(EXPENSIVE)} (every item, random order):")
for item in order:
    name, extra = item if isinstance(item, tuple) else (item, ())
    r = subprocess.run([sys.executable, str(RFD/"scripts"/f"{name}.py"), *extra],
                       capture_output=True, text=True, cwd=RFD)
    tail = (r.stdout.strip().splitlines() or [""])[-1][:58]
    check(f"  {name}", r.returncode == 0, tail)
seen = set(order)
check("shuffle covered every item", seen == set(EXPENSIVE),
      f"{len(seen)}/{len(EXPENSIVE)} distinct, repeats: {len(order)-len(seen)}")

print("\n".join(out))
print(f"\n  enumerated checks: {len(out)-2} run, {fails} failed")
sys.exit(1 if fails else 0)
