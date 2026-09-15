# Derivative as a function: visual brief

topic: derivatives | title: Derivative as a function | category: math | source: generated (Step B)

## Input
f(x) = x^3/3 - x, so f'(x) = x^2 - 1. The point of tangency slides along the curve
from x = -2 to x = 2, stopping at x = -2, -1, 0, 1, 2. The slopes at the stops are
3, 0, -1, 0, 3: every number the narration says is a small integer. The curve has a
hill (x = -1) and a valley (x = 1), so the slope graph has two zeros, one negative
stretch between them and two positive stretches, and every sign branch fires. Both flat
tangents sit at height +-2/3, well off the x-axis, and the top graph can be drawn at
equal aspect (the curve stays within +-2/3 on [-2, 2]), so the tangent's on-screen tilt is
its true slope.

Rejected:
- f(x) = x^2 (f' = 2x). Trace: slopes -4, -2, 0, 2, 4 at x = -2..2. The only flat point is
  (0, 0), so the horizontal tangent is drawn along the x-axis (two things the viewer must
  tell apart coincide). It has a single turning point, and it is the exact function the
  existing `derivative` topic uses.
- f(x) = x^3 (f' = 3x^2). Trace: slopes 12, 3, 0, 3, 12. The slope is never negative, so
  the "falling curve means negative slope" branch never fires. Its flat tangent at (0, 0)
  also lies on the x-axis.
- f(x) = x^3 - 3x (f' = 3x^2 - 3). Trace: slopes 9, 0, -3, 0, 9; f spans -2..2. The
  shape teaches, but the values fall outside the layout budget: the slope spans 12 units,
  so the equal-aspect top graph would be 5.2 units tall and the slope graph 6.24 units
  tall, against about 3 units available per graph.
- f(x) = sin x (f' = cos x). Trace: slopes -1, 0, 0.7071, 1, 0.7071, 0 at
  x = -pi, -pi/2, -pi/4, 0, pi/4, pi/2. The turning points sit at +-pi/2, not at a readable
  tick, and the in-between slopes (0.7071) are numbers the narration cannot say cleanly.

## Trace
```
REJECTED CANDIDATES
--- f(x) = x^2  (f' = 2x)
  x=-2.00  f=+4.0000  slope=-4.0000  falling (-)
  x=-1.00  f=+1.0000  slope=-2.0000  falling (-)
  x=+0.00  f=+0.0000  slope=+0.0000  flat (zero)
  x=+1.00  f=+1.0000  slope=+2.0000  rising (+)
  x=+2.00  f=+4.0000  slope=+4.0000  rising (+)
  flat point x=0 has f(0)=0: the horizontal tangent lies ON the x-axis; one turning point only; same function as topic `derivative`.
--- f(x) = x^3  (f' = 3x^2)
  x=-2.00  f=-8.0000  slope=+12.0000  rising (+)
  x=-1.00  f=-1.0000  slope=+3.0000  rising (+)
  x=+0.00  f=+0.0000  slope=+0.0000  flat (zero)
  x=+1.00  f=+1.0000  slope=+3.0000  rising (+)
  x=+2.00  f=+8.0000  slope=+12.0000  rising (+)
  slope never negative (falling branch never fires); flat tangent at (0,0) lies on the x-axis.
--- f(x) = x^3 - 3x  (f' = 3x^2 - 3)
  x=-2.00  f=-2.0000  slope=+9.0000  rising (+)
  x=-1.00  f=+2.0000  slope=+0.0000  flat (zero)
  x=+0.00  f=+0.0000  slope=-3.0000  falling (-)
  x=+1.00  f=-2.0000  slope=+0.0000  flat (zero)
  x=+2.00  f=+2.0000  slope=+9.0000  rising (+)
  slope spans -3..9 on [-2, 2] (span 12); f spans -2..2. Equal-aspect top graph at 1.3 u/unit would be 5.2 u tall, slope graph at 0.52 u/unit 6.24 u: both exceed the ~3 u per graph budget.
--- f(x) = sin x  (f' = cos x)
  x=-3.14  f=-0.0000  slope=-1.0000  falling (-)
  x=-1.57  f=-1.0000  slope=+0.0000  flat (zero)
  x=-0.79  f=-0.7071  slope=+0.7071  rising (+)
  x=+0.00  f=+0.0000  slope=+1.0000  rising (+)
  x=+0.79  f=+0.7071  slope=+0.7071  rising (+)
  x=+1.57  f=+1.0000  slope=+0.0000  flat (zero)
  turning points at x = +-pi/2 (not readable tick positions); slopes like 0.7071 are unsayable.

CHOSEN: f(x) = x^3/3 - x,  f'(x) = x^2 - 1,  tangent point slides x = -2 -> -1 -> 0 -> 1 -> 2
--- stops
  x=-2.00  f=-0.6667  slope=+3.0000  rising (+)
  x=-1.00  f=+0.6667  slope=+0.0000  flat (zero)
  x=+0.00  f=+0.0000  slope=-1.0000  falling (-)
  x=+1.00  f=-0.6667  slope=+0.0000  flat (zero)
  x=+2.00  f=+0.6667  slope=+3.0000  rising (+)

SWEEP LEGS (slope along each slide)
  -2 -> -1: f'(-2.00)=+3.0000, f'(-1.75)=+2.0625, f'(-1.50)=+1.2500, f'(-1.25)=+0.5625, f'(-1.00)=+0.0000   f rises -0.6667 -> +0.6667
  -1 -> +0: f'(-1.00)=+0.0000, f'(-0.75)=-0.4375, f'(-0.50)=-0.7500, f'(-0.25)=-0.9375, f'(+0.00)=-1.0000   f falls +0.6667 -> +0.0000
  +0 -> +1: f'(+0.00)=-1.0000, f'(+0.25)=-0.9375, f'(+0.50)=-0.7500, f'(+0.75)=-0.4375, f'(+1.00)=+0.0000   f falls +0.0000 -> -0.6667
  +1 -> +2: f'(+1.00)=+0.0000, f'(+1.25)=+0.5625, f'(+1.50)=+1.2500, f'(+1.75)=+2.0625, f'(+2.00)=+3.0000   f rises -0.6667 -> +0.6667

DISTINCTNESS / DEGENERACY CHECKS
  flat tangent at x=-1: y = f(-1) = +0.6667  (not on the x-axis: True)
  flat tangent at x=+1: y = f(+1) = -0.6667  (not on the x-axis: True)
  hill f(-1)=+0.6667 vs valley f(1)=-0.6667; zeros of f' at x=-1, x=+1, scene x -3.80, -1.20
  slope readout values the narration says: [3, 0, -1, 0, 3]

LAYOUT BUDGET
  top graph incl. tangent: y +0.014 .. +2.886   (title bottom ~3.2)
  slope graph: dot y at slope 3 -> -0.610, slope 0 -> -2.170, slope -1 -> -2.690; axes span -0.35 .. -2.95
  gap tangent-low-end to slope-graph top: +0.364
  gap slope-graph bottom to caption top: +0.320
  top < title: True; tangent clear of slope graph: True; slope graph clear of caption: True

BEATS: intro 5 + setup 3 + sweep 12 (4 legs) + analysis 6 + end 2 = 28
```

## Visual vocabulary
- Drawn:
  - Title at the top, scaled down to 0.75 so its bottom clears the tangent at x = 2 (about y = 3.2).
  - Two axes stacked on the left, sharing one x mapping (x from -2.5 to 2.5, 1.3 units per x, centred at scene x = -2.5).
    The top axes hold the curve f at equal aspect (y from +0.01 to +2.89, tangent included). The lower axes are the
    slope graph (slope from -1.5 to 3.5, spanning y -0.35 to -2.95).
  - "hill" and "valley" labels at the two turning points.
  - A point of tangency (Dot) on the curve, with a fixed-length (1.2) tangent segment through it.
  - A vertical dashed guide from that point straight down to a slope dot on the lower axes.
  - The slope dot's trail: the derivative graph drawn from x = -2 up to the current x.
  - A live readout "slope = 3.00" in the right panel, under the curve's formula label.
  - Frozen gold links at the two zeros: a dashed line plus a ring on the turning point above and a ring on the zero below.
  - A clean f' curve that replaces the trail, with green and red area shading between it and the axis.
  - The formula f'(x) = x^2 - 1 in the right panel (x >= 2.2).
  - Caption at STATUS_AT = DOWN * 3.45.
- Motion: one ValueTracker holds x. Sliding it moves the point along the curve. The tangent translates *and* rotates
  with it, the guide shifts sideways, the slope dot rides up and down, and the trail grows rightward, so the lower
  curve is drawn by the sweep. The readout counts continuously. At a turning point the tracker stops. The link is
  drawn with Create, then the rings are Circumscribed and Flashed. In the analysis, area shading fades in over sign
  regions, the same stretches of f are recoloured by overlay, and the formula is FadeTransformed in the panel.
- Colour: BLUE is the curve f. YELLOW is the tangent line and point. PURPLE_B is the slope dot, its trail and the
  f' curve. GREEN means positive slope (f climbing), as the readout colour, the shading and the overlay on f. RED
  means negative slope (f falling). GOLD marks a zero slope: the rings, the frozen links, and the readout at zero.
  PURPLE_A is the guide line. The brief first specified GREY_B, but frame review showed that at x = 0 a grey
  guide vanishes into both grey y-axes, so it was changed after the first render.

## Distinct from
- `derivative` (nearest). One Axes with x^2. A fixed point P, and a second point Q approaching it as h shrinks, with
  a secant pivoting about P, rise and run legs, and a table of h, rise and slope. It teaches the derivative *at one
  point* as a limit. In this brief, what is drawn is two stacked axes linked by a vertical guide, a tangent (never a
  secant), and a second curve built out of slope values. How it moves differs too: the point of tangency travels
  the whole curve, so the tangent slides and rotates, and a dot traces a new graph underneath. Nothing converges
  and there is no h. It teaches the derivative *as a function*: the sign of f' against rising and falling, and the
  zeros of f' against turning points.
- `projectile_motion`. A ball on a parabola with two "shadow" dots, each isolating one coordinate. It shares the idea
  of one moving thing driving a second readout. But its shadows copy a *position*, whereas here the lower dot plots a
  *slope*, on a separate graph with its own axis.

## Key teaching moment
Beat `s1_link`. The tangent has just gone flat at the hilltop (x = -1, height 2/3), and the slope dot sits exactly on
the lower x-axis. A gold dashed link is drawn from the hilltop straight down to that zero, with rings on both ends.
The sentence: "The top of the hill lines up exactly with a zero below." The input makes this visible for three
reasons. The hill sits at a readable x = -1. The flat tangent is drawn 0.87 units above the top x-axis, not along it.
And the slope dot is on the axis at exactly 0, not 0.06. Beat `s3_link` repeats it at the valley (x = 1), so the
pattern is seen twice.

## Beat outline
1. Intro, 5 beats: curve; hill and valley; point at x = -2; tangent; slope readout 3.
2. Setup, 3 beats: lower axes; dashed guide; first slope dot at height 3.
3. Sweep, 12 beats:
   - leg -2 -> -1 (slide, flat, zero, link);
   - leg -1 -> 0 (slide, negative, slope -1);
   - leg 0 -> 1 (slide, flat, link);
   - leg 1 -> 2 (slide, positive at 3).
4. Analysis, 6 beats: trail becomes the slope graph; formula x^2 - 1; check at x = 1; climbing is above the axis;
   falling is below it; turning points are zeros.
5. End, 2 beats: a derivative is a whole function; fade out.

Total: 28 beats.
