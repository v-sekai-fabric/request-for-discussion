# Recurring failure modes

Each entry names a way this system goes wrong, what it costs, and the guard that catches it.
Every one holds for real code in these repos rather than in general. Most recur at three or
more sites, which is why they live here rather than in memory.

Written in the present per RFD 2025: a mode that stops applying is a line to delete rather
than a line to date. Ordered by cost.

---

## 1. Bugs live at interfaces, never inside components

Every defect in this system sits at a boundary between two things:

| boundary                                        | cost                                                |
| ----------------------------------------------- | --------------------------------------------------- |
| ANNY gender `0=male` against GNM `FEMALE=0`     | flips sex on 800k images                            |
| ANNY Z-up/metres against SOMA +Y-up/centimetres | 100x scale, or a body on its side                   |
| "local Z" against the bone's roll axis          | measures a bend and calls it a twist                |
| `rest_bone_heads` against `vertices`            | 55 mm on an adult, **500 mm on a child**            |
| `lowerarm01` / `lowerarm02` weight boundary     | the forearm twist defect                            |
| twist bones against LabRCSF's joint list        | 12 ANNY bones carry no canonical name               |
| forearm / hand mask boundary                    | mesh mean understates finger error 4x               |
| train / val split                               | contamination                                       |
| BVH bind orientation against ANNY's             | 29.6 deg per-limb offset; blocks the poses relation |

Components get tested because they are easy to name. Interfaces belong to nobody.

**Guard:** `interface_audit.py` names 17 interfaces. Each resolves to
`OK`, `HAZARD`, or `UNCHECKED` — never absent.

---

## 2. A check that passes on known-broken input certifies the defect

The forearm-twist gate reaches honesty on its third form. The first two pass on a rig that
does not transmit twist:

1. a dominance-share proxy — passes outright
2. a distal-band reading driven from the twist bone — 66.9 deg of an ideal 78.8, passes, and
   measures an interface nothing crosses: capture supplies the wrist, never a twist bone
3. a distal-band reading driven from the wrist — still lenient, because a dispersed stock rig
   reads 67 deg near the wrist while its mid-forearm stays flat

Scoring the profile's **linearity** separates all three: stock 52.8, dispersed 24.0,
shipping 3.6.

**Guard:** every gate carries a negative control asserting that broken input fails.
`test_preflight.py` red-tests 10 corruptions. `check_readme_claims.py` answers its own red
test — falsifying two claims trips exactly those two.

**Naming convention for spread-and-threshold gates:** ship the companion mode as a CLI
switch `--negative-control` on the same script that computes the number. Two shapes seen
in `anny-keypoint-anchors`:

1. **Re-run with the known-bad selector.** `face_anchors.py --negative-control` calls the
   same builder with the pre-rework region selector (a per-target 1.5 mm floor over the
   union, no excluded-vertex filter) and asserts the spread gate rejects the result. The
   pre-rework worst comes in at 22.4 mm (about a nickel) against a 13 mm cap. A gate the
   pre-rework selector's output does not fail is a gate that does not measure what the
   rework changed.
2. **Re-run the placement check against the previous artifact.** `check_keypoint_anchors.py
--self-test` reads `face68_v2_snapshot.pth` (v2 weights preserved as evidence per rule 10) and asserts the same placement priors that pass on `face68.pth` fail on the
   snapshot. v2 fails six priors (jawline monotone-X, chin at min-Z, eyes lateral, mouth
   corners flanking the nose tip); v3 passes all. A gate whose new build passes it and
   whose known-broken build passes it too is not a placement gate — it is decoration.

Both shapes name the same rule: the gate must reject the known-broken input. Both survive
review the same way: a green gate is not evidence until the negative control turns red.

---

## 3. A silent skip reads exactly like a pass

Three checks in this system produce no output and look clean while doing nothing:

- split-contamination nested under `if "scenes" in tables`, so it sits out identity
  generation — the phase that creates contamination
- dimorphism, when both sex subgroups come out empty
- child stature, when the sample holds no children

**Guard:** an unmet precondition fails rather than skipping. `interface_audit.py` counts
`UNCHECKED` and names each. `check_readme_claims.py` reports an unregistered claim as
`UNVERIFIED` and counts it against the total.

---

## 4. The convenient proxy lies

Five pairs, where the left column is the one that is easy to read:

| proxy                                          | measurement that settles it             |
| ---------------------------------------------- | --------------------------------------- |
| joints.csv **name coverage**                   | silhouette survival                     |
| Godot's **API surface**                        | the source                              |
| phenotype **parameter percentiles**            | decoded stature in metres               |
| **centroid** limb direction (thigh "+9.7 deg") | recovered **joint angle** (2.2 deg)     |
| joint-**position** residual (BVH "153 mm")     | limb **direction**, which is scale-free |

---

## 5. A number without a baseline is not a measurement

A 153 mm BVH retarget residual reads as damning until a control scores **two rest skeletons
at 139.7 mm**: the posed figure sits 13 mm above an unmeasured floor. The verdict drawn from
it does not hold.

The thigh figure has the same shape — 19.7 deg raw, of which 10.0 deg is static body-shape
difference, so the raw number overstates by 2x.

**Guard:** the floor appears first, in the same table. `bvh_retarget_probe.py` prints the
rest-vs-rest control above its results.

---

## 6. A sampled check claims more than it sees unless it states its floor

A sample of `n` catches defects larger than roughly `3/n`. At `--sample 300` that floor sits
at **10,000 ppm**: nothing below 1 identity in 100 is certified, a defect touching 23
identities (800 of 800k images) escapes 95% of the time, and the audit prints all-PASS.

A full decode of 23,000 identities costs **95 seconds**.

For a _fixed_ population, enumeration replaces estimation. Estimation belongs to unbounded
streams.

**Guard:** `preflight_audit.py` prints its detection floor and fails when asked to certify
below what its sample resolves.

---

## 7. A denominator that does not track reality flatters the result

Whole-mesh mean error reads 9.2 mm during a forearm pronation, because 1,356 torso vertices
sit at exactly 0.00 mm and dilute it, while the fingers sit a golf ball out. The average
understates the part that matters **4x**.

The shape matches a dashboard counting 500s against a fixed denominator: the quiet
datacentre looks healthy because traffic sleeps, not because the failure rate moves.

**Guard:** `corpus_defect_rate.py` reports an exceedance **rate against a stated tolerance**,
over the region that moves, against a baseline. A rate without a threshold is not a
measurement; an absolute rate without a reference does not interpret.

---

## 8. Conventions are data — parse them

- BVH channel order is per-joint and declared. 100STYLE writes `Yrotation Xrotation
Zrotation`; a positional read transposes every rotation.
- ANNY's `local-ref` rotation axes are world-aligned. The local-to-world map is the identity,
  so "local Z" is _world_ Z, 55 deg off the forearm.
- An identity `pose_parameters` is not the rest pose.
- `rest_bone_heads` pairs with `rest_vertices`, never with `vertices`.
- Up axis and units differ per model and per rig.

**Guard:** rotation axes come from probing — rotate 10 deg about each local axis, read the
world axis the skin turns about, invert. The probe reads **descendant** vertices, because a
bone's own vertices blend under LBS and fitting them displaces the recovered rotation centre
by 33 mm.

---

## 9. Documentation rots silently, and rotted documentation misleads worse than none

Two live examples in this system:

- a README headline asserting Godot's twist disperser as the solution, while the shipping
  answer is zero twist bones — a reader following the headline builds the wrong thing
- a docstring asserting Delta Mush is "available here", where `grep` finds zero occurrences

**Guard:** README numbers are tagged claims that `check_readme_claims.py` re-derives from
live code, so drift fails a command. Superseded findings occupy a **SUPERSEDED** section
rather than vanishing under an edit, so dead ends stay visible.

---

## 10. Retractions belong beside what they retract

Claims in this system that do not hold: the twist ratio sweep and its "no ratio works"
conclusion; the soma/game_engine "frame hazard"; the 9.7 deg thigh error; the "neither BVH
formulation transfers the pose" verdict; the claim that Delta Mush is implemented in
`anny_rig`.

Each sits next to the thing it corrects. A reader who knows the dead ends is better off than
one who knows only the current answer, which is the reason this file exists.

---

## 11. Rebase-and-force-push in a tight loop deadlocks under a merge storm

The failure pattern seen against `weftspun/request-for-discussion` on 2026-09-03:

- Ruleset requires branches up to date before merging, and requires all status checks
  green.
- Many small PRs land in a short window; main advances every few minutes.
- A green PR shows `mergeStateStatus: BEHIND`; a rebase-and-force-push is the mechanical
  answer, but it resets prek from scratch, and by the time prek finishes, main has moved
  again. The PR never catches up.
- `--force-with-lease` starts rejecting because the remote has shifted between the local
  rebase and the push.

**Cost:** unbounded rebase loop that keeps a green PR open indefinitely; wasted CI
minutes; a human eventually admin-merges to break the loop.

**Recovery:** `gh pr merge <N> --repo <r> --admin --merge` bypasses the up-to-date
requirement for one stuck PR.

**Guard:** GitHub's merge queue, which serialises PRs into a merge_group event, runs
checks on a temporary branch that already has main's tip merged in, and merges in order.
`.github/workflows/checks.yml` declares `merge_group:` as a trigger, so the workflow side
is ready. `gh pr merge --auto --merge` adds to a queue rather than firing immediately.

**The queue is ruleset 23145233**, created 2026-09-13 on the default branch: `MERGE`
method, `ALLGREEN` grouping, a 60-minute check timeout, batches of up to five, and a pull
request required with zero approvals.

**Require only checks that run on `merge_group`.** Seven of the nine jobs in
`checks.yml` do; `rfd-canary` and `rulesets` guard on `pull_request` alone. A required
check that never runs holds the queue for the whole 60 minutes and then fails it, so the
required set is read off each job's `if:` condition rather than assumed from the list of
jobs.

`scripts/check_rulesets.py` reads the ids named in `CLAUDE.md` and this file and fails
when the repository does not carry them, so a claim cannot go stale in silence.

**When not to enable, and why that changed.** A repo with a single committer and
rarely-concurrent PRs gains serialisation with no contention to serialise, which still
argues against a queue here. The second condition no longer holds: every pull request on
2026-09-11 and 2026-09-12 sat `queued` on starved runners, several beyond half an hour,
so a queue would have converted a slow check into a blocked merge. On 2026-09-13 checks
completed in seconds, which is what made the queue affordable.

## 12. A timeout is not a state

The hosted door's cluster credentials took four runs to land on 2026-09-07, and every
failed run ended in a timeout standing in for a state nobody had read:

1. `op read` from a background process reported `authorization timeout`. The state was
   "a human has not approved the prompt", and no retry from that process could change it.
2. bao's listener answered `tls: certificate required`. The state was "no client
   certificate presented": the script carried three of the credential helper's four
   variables.
3. flyctl on Windows exits 1 after a clean `ssh console -C`. Under `pipefail` the
   script stopped after the leaf was minted, and its cleanup trap deleted the
   material, silently.
4. `fly secrets set` triggered a deploy whose health checks never passed. The state
   was a crash loop on a priv path resolved at compile time, which the log states
   plainly as `max restart count of 10`.

A fifth, while measuring: a log poll matched `BENCH-DONE` in the line that echoed the
command it was waiting for, and reported done before the download had finished.

**Guard:** a multi-step operation is a state machine over observed states. Each step
names the state it needs and the state it leaves behind, checks the artifact rather than
the tool's exit status (a leaf that verifies against its chain, a cluster string with an
`@`, the four secret names in the list, a health body that says `primary`), and a failure
names the state. Minted material is placed before anything optional runs and is never
deleted by a later step's failure. A human approval is a state the human's own process
reaches (`! <command>` in the session), not something to wait out. A packaging defect
faults the release (operator, 2026-09-07: "it must fault"); only an unreachable cluster
degrades. `scripts/issue_cluster_credentials.sh` in `transport-taskweft-acp` is the
shape, and rule 3 above (a silent skip reads like a pass) is the same guard for a
script's silent stop.
