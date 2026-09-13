# The spring-bone parameter mapping, measured, and three constants overturned

`apparatus/springbone_mujoco.py` maps a social-VR spring-bone chain onto a MuJoCo
ball-jointed body so a chain budget can be met by measured silhouette error rather than a
guessed geometry knob. The five constants doing that mapping were guessed. Three of them
were wrong, and the measurement says so.

## The rig

17 chains of 8 bones, driven from one root by a 0.15 m step (about two credit cards laid
end to end) in the editor, one knob varied at a time. A GPU sweep then solved for the
`(stiffness, damping)` pair reproducing each chain's peak deflection and 5% settling time.
`apparatus/springbone_calibrate.py` records the step response; `apparatus/mjx_map.py`
solves for the pair.

## What each knob does

| knob | measured | was mapped as | verdict |
| --- | --- | --- | --- |
| `pull` | settling 5.00 s to 0.10 s over 0.05..0.8, peak barely moving | stiffness alone | sets the DECAY RATE: stiffness against near-constant damping |
| `spring` | lowers damping | damping | the one mapping already right |
| `stiffness` | peak 58.721 to 58.722 deg, settling flat at 1.18 s across 0..1 | a stiffness term | NO measurable effect; all four fitted the identical pair |
| `immobile` | response size scales, settling time unchanged | damping | a GAIN on the root motion the chain sees |

Three of five overturned. The `stiffness` term is deleted rather than re-fitted: a constant
with no measurable effect is not a constant that needs a better value.

Values interpolate in log-log between measured points rather than fitting an invented
functional form. `k(pull)` is superlinear with a log-log slope climbing 1.06, 1.33, 2.39,
so no single power law describes it.

**Not converged.** `pull=0.05` and `spring=1.0` both pinned at the search floor of
`k=0.05`, so anything below `pull=0.1` is extrapolation and is unmeasured.

## The mass conflation, in both directions

Half-thickness sets MASS and inertia and is not the collision radius. A skirt panel is
checked against a 5 cm capsule and is still cloth.

Taking mass from the collision radius gave 244 g a link for a dress panel and 729 g for the
tail; 244 g is about a cup of water hanging off one link. The default 0.02 m, a little under
a nickel's width, is the thickness the calibration rig actually ran at, and puts a link at
29.9 g, about the weight of a AA battery.

The effect is modest rather than catastrophic: 1.6x on bend across a 163x mass change,
because `k` scales by inertia (~m r squared) while gravity torque goes as m, so the radius
term largely cancels.

It is recorded because the same conflation ran the other way earlier, 0.31 g against
29.9 g, and there it did not cancel. The calibration rig holds `k` fixed, so nothing
absorbed the error.

## What this does not settle

Whether the three reduction tiers rank anything useful. They are scored with a corrected
metric on a driven rig now, but tier 1 is the only one that needs no simulation and is
therefore the only one exact by construction. Tier 2 and tier 3 are validated in the engine
before shipping, not here.

[[logbook-springbone-mujoco-two-wrong-metrics]] carries the metric and the rig that produced
no force at all, which is the defect underneath this one.
