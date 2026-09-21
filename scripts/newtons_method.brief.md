# Newton's method: visual brief

topic: newtons_method | title: Newton's method | category: math | source: generated (Step B)

## Input
f(x) = x^2 - 2, starting guess x0 = 2, four Newton steps. The root is the square
root of 2, which every viewer knows but nobody can compute in their head, so the
method has a real job. The iterates are the clean fractions 3/2, 17/12, 577/408,
665857/470832, and their correct significant digits go 0, 1, 3, 6, 12: an exact
doubling, which is the whole point of Newton's method, visible in a digit strip
without any hedging.

Rejected:
- x^2 - 2 from x0 = 0: the slope there is 0, the tangent is flat and never meets
  the axis, so there is no step at all. Kept only as a two-beat warning at the end.
  ```
  x0 =            0  = 0.000000000000  f=-2  slope=0  err=1.41 (~10^0)  correct sig digits=0
  slope is 0: tangent is horizontal and never meets the axis -> STOP
  ```
- x^2 - 2 from x0 = 3: correct digits go 1, 2, 4, 7, 13, so the doubling only
  shows late, and 11/6, 193/132 and 72097/50952 are unsayable.
  ```
  x1 =         11/6  = 1.833333333333  err=0.419 (~10^0)  correct sig digits=1
  x2 =      193/132  = 1.462121212121  err=0.0479 (~10^-1)  correct sig digits=2
  x3 =  72097/50952  = 1.414998429894  err=0.000785 (~10^-3)  correct sig digits=4
  x4 = ...           = 1.414213780047  err=2.18e-07 (~10^-7)  correct sig digits=7
  x5 = ...           = 1.414213562373  err=1.68e-14 (~10^-14)  correct sig digits=13
  ```
- x^3 - 2 from x0 = 2 (tried to move away from the parabola the derivative topic
  uses): correct digits go 1, 2, 2, 7, 12. x3 = 1.2609 against the root 1.2599
  straddles a rounding boundary, so the digit strip would show no progress on
  the step where the error actually shrank 36-fold. The doubling is hidden.
  ```
  x1 =          3/2  = 1.500000000000  err=0.24 (~10^-1)  correct sig digits=1
  x2 =        35/27  = 1.296296296296  err=0.0364 (~10^-1)  correct sig digits=2
  x3 = 125116/99225  = 1.260932224741  err=0.00101 (~10^-3)  correct sig digits=2
  x4 = ...           = 1.259921860565  err=8.11e-07 (~10^-6)  correct sig digits=7
  x5 = ...           = 1.259921049895  err=5.22e-13 (~10^-12)  correct sig digits=12
  ```

## Trace
```
root sqrt2 = 1.414213562373  cbrt2 = 1.259921049894
--- CHOSEN f=x^2-2, x0 = 2
  x0 =            2  = 2.000000000000  f=2  slope=4  err=0.586 (~10^0)  correct sig digits=0
  x1 =          3/2  = 1.500000000000  f=0.25  slope=3  err=0.0858 (~10^-1)  correct sig digits=1
  x2 =        17/12  = 1.416666666666  f=0.00694444  slope=2.83333  err=0.00245 (~10^-3)  correct sig digits=3
  x3 =      577/408  = 1.414215686274  f=6.0073e-06  slope=2.82843  err=2.12e-06 (~10^-6)  correct sig digits=6
  x4 = 665857/470832  = 1.414213562374  f=4.51095e-12  slope=2.82843  err=1.59e-12 (~10^-12)  correct sig digits=12
```
Digits are truncated, not rounded, to 12 decimals, so a rounding carry can never
fake a correct digit.

Hop sizes on screen decided the zooms. Main plot (2.0 units per x, 0.7 per y):
step 1 runs 1.0 and rises 1.4, step 2 only 0.17 and 0.18, so step 2 needs a zoom.
Inset 1 (x10, window 0.25 wide, y -0.1..0.45 so its box on the main plot clears
the x1 label): step 2 runs 1.67 and rises 1.64, but x2 lands
0.05 units from the root and step 3 would be 0.05 wide, so it needs a second
zoom. Inset 2 (x250, window 0.01 wide): step 3 runs 1.22 and rises 1.39.
Step 4 is 2e-6 wide, invisible at any zoom that fits, which is exactly when the
video switches from pictures to digits.

## Visual vocabulary
- Drawn: left, the main axes (x -0.5..2.5, y -2.5..3.5, centred at (-3.3, 0.55))
  with the parabola, a green root ring at the square root of 2 labelled above the
  axis, yellow guess ticks x0, x1 labelled below the axis, a dashed riser from
  each guess up to the curve, and each orange tangent clipped to the plot. A teal
  zoom box around the root. Right, (3.9, 0.55), a teal-framed inset plot showing
  the zoom window with its own ticks, ring, riser and tangent, with a magnification
  tag in its corner; a second, smaller box inside it opens the second inset in the
  same slot. Later the right panel holds the update rule at y 2.2 and a digit
  table: guess name, value to 12 decimals, error exponent. Caption at y -2.35.
- Motion: discrete hops, no tracker. A yellow dot rises along the dashed riser to
  the curve, then rides down the tangent (MoveAlongPath) to the axis, where the
  next tick appears. Each inset grows out of its zoom box (TransformFromCopy). In
  the table, the correct leading digits of each value turn green in place, one
  row per beat. The warning slides a red dot along a flat tangent that never
  reaches the axis.
- Colour: blue the curve, yellow guesses and the hopping dot, orange tangents,
  green the true root and every correct digit, teal zoom boxes and inset frames,
  red the failing flat tangent.

## Distinct from
- `derivative`: one fixed point on x^2, a secant rotating continuously (ValueTracker)
  into the tangent, h/rise/slope table. The tangent is the destination.
- `derivatives`: the point of tangency slides along x^3/3 - x while a second axes
  traces the slope graph.
- Here the tangent is a tool used once and left behind: the picture is a
  staircase of risers and tangents marching toward a root, nested zoom insets,
  and a digit strip, none of which appears in either derivative topic. Motion is
  hop-and-slide along straight paths plus zooms, not a continuously driven
  rotation or sweep. The curve is a parabola like `derivative`'s, kept because
  it is the only candidate traced that makes the digit doubling exact (see Input).

## Key teaching moment
`d_x4`: the table already shows 1.5 with 1 green digit, 17/12 with 3 and 577/408
with 6. A fifth row fades in, 1.414213562374, with 12 green digits, and the
sentence says "One more step gives twelve correct digits, doubling once again."
x^2 - 2 from 2 is what makes it exact: 1, 3, 6, 12.

## Beat outline
- Intro (4): curve, root we want, it is the square root of 2, guess x0 = 2
- Step 1 on the main plot (3): rise, tangent, slide to 1.5
- Zoom 1 and step 2 (5): zoom box, inset opens, rise, tangent, slide to 17/12
- Zoom 2 and step 3 (5): zoom box, inset opens, rise, tangent, slide to 1.414216
- Update rule (2): x minus f over slope, the average of x and 2/x
- Digits (6): table, 1 digit, 3 digits, 6 digits, 12 digits, error squares
- Warning (2): flat tangent at 0, never reaches the axis
- End (2): digits double, guess-tangent-repeat
- Total: 29
