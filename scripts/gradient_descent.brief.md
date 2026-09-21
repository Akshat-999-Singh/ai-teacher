# Gradient descent: visual brief

topic: gradient_descent | title: Gradient descent | category: math | source: generated (Step B)

## Input
Loss f(x, y) = x^2 + 4y^2, start (4, 1), and three learning rates from that one
start: 0.1 for five steps, 0.2 for four, 0.3 for three. The bowl is four times
steeper in y than in x, so it is a valley, and the valley is what makes the
learning rate matter. Every position is an exact decimal, the start has loss 20,
and the gradient there is (8, 8). At 0.1 the y error dies in two steps and the
run crawls along the valley floor, steps shrinking 1.13, 0.66, 0.51, 0.41, 0.33.
At 0.2 each step flips the sign of y (factor -0.6), a clean zigzag, yet the loss
is 0.34 after four steps against 1.72 after five. At 0.3 the y factor is -1.4,
so the dot leaps the valley and lands further out every time, and the loss reads
10.4, 15.8, 30.2. The first of those, 10.4, equals the careful run's first loss
exactly, so the loss readout alone cannot tell the two steps apart. The map can.

Rejected:
- Round bowl x^2 + y^2: the gradient points straight at the minimum, so no path
  ever zigzags, and rate 0.5 lands on the minimum in one step, after which the
  process has nothing left to repeat. No learning-rate story at all.
  ```
--- round bowl: f = x^2 + 1y^2, start (4, 1), learning rate 1/2
  step 0: p=(4.0000, 1.0000)  loss=17.0000  grad=(8.000, 2.000)  next step length=4.123
  step 1: p=(0.0000, 0.0000)  loss=0.0000  grad=(0.000, 0.000)  next step length=0.000
  step 2: p=(0.0000, 0.0000)  loss=0.0000  grad=(0.000, 0.000)  next step length=0.000
--- round bowl: f = x^2 + 1y^2, start (4, 1), learning rate 1/5
  step 0: p=(4.0000, 1.0000)  loss=17.0000  grad=(8.000, 2.000)  next step length=1.649
  step 1: p=(2.4000, 0.6000)  loss=6.1200  grad=(4.800, 1.200)  next step length=0.990
  step 2: p=(1.4400, 0.3600)  loss=2.2032  grad=(2.880, 0.720)  next step length=0.594
  step 3: p=(0.8640, 0.2160)  loss=0.7932  grad=(1.728, 0.432)  next step length=0.356
  ```
- Start (4, 2) with rate 0.3: the second step is already outside the map window
  (|y| 3.92 against a 3.05 budget), so the diverging run would show one leap.
  ```
--- start (4,2), large: f = x^2 + 4y^2, start (4, 2), learning rate 3/10
  step 0: p=(4.0000, 2.0000)  loss=32.0000  grad=(8.000, 16.000)  next step length=5.367
  step 1: p=(1.6000, -2.8000)  loss=33.9200  grad=(3.200, -22.400)  next step length=6.788 loss UP
  step 2: p=(0.6400, 3.9200)  loss=61.8752  grad=(1.280, 31.360)  next step length=9.416 loss UP OUTSIDE MAP
  step 3: p=(0.2560, -5.4880)  loss=120.5381  grad=(0.512, -43.904)  next step length=13.172 loss UP OUTSIDE MAP
  ```
- Rate 0.25 as the large rate: y bounces between 1 and -1 forever while the loss
  still falls toward 4. The run neither converges nor visibly fails, so the loss
  chart would show a descending line for a broken run.
  ```
--- rate 0.25: f = x^2 + 4y^2, start (4, 1), learning rate 1/4
  step 0: p=(4.0000, 1.0000)  loss=20.0000  grad=(8.000, 8.000)  next step length=2.828
  step 1: p=(2.0000, -1.0000)  loss=8.0000  grad=(4.000, -8.000)  next step length=2.236
  step 2: p=(1.0000, 1.0000)  loss=5.0000  grad=(2.000, 8.000)  next step length=2.062
  step 3: p=(0.5000, -1.0000)  loss=4.2500  grad=(1.000, -8.000)  next step length=2.016
  step 4: p=(0.2500, 1.0000)  loss=4.0625  grad=(0.500, 8.000)  next step length=2.004
  step 5: p=(0.1250, -1.0000)  loss=4.0156  grad=(0.250, -8.000)  next step length=2.001
  ```

## Trace
```
--- small: f = x^2 + 4y^2, start (4, 1), learning rate 1/10
  step 0: p=(4.0000, 1.0000)  loss=20.0000  grad=(8.000, 8.000)  next step length=1.131
  step 1: p=(3.2000, 0.2000)  loss=10.4000  grad=(6.400, 1.600)  next step length=0.660
  step 2: p=(2.5600, 0.0400)  loss=6.5600  grad=(5.120, 0.320)  next step length=0.513
  step 3: p=(2.0480, 0.0080)  loss=4.1946  grad=(4.096, 0.064)  next step length=0.410
  step 4: p=(1.6384, 0.0016)  loss=2.6844  grad=(3.277, 0.013)  next step length=0.328
  step 5: p=(1.3107, 0.0003)  loss=1.7180  grad=(2.621, 0.003)  next step length=0.262
--- medium: f = x^2 + 4y^2, start (4, 1), learning rate 1/5
  step 0: p=(4.0000, 1.0000)  loss=20.0000  grad=(8.000, 8.000)  next step length=2.263
  step 1: p=(2.4000, -0.6000)  loss=7.2000  grad=(4.800, -4.800)  next step length=1.358
  step 2: p=(1.4400, 0.3600)  loss=2.5920  grad=(2.880, 2.880)  next step length=0.815
  step 3: p=(0.8640, -0.2160)  loss=0.9331  grad=(1.728, -1.728)  next step length=0.489
  step 4: p=(0.5184, 0.1296)  loss=0.3359  grad=(1.037, 1.037)  next step length=0.293
--- large: f = x^2 + 4y^2, start (4, 1), learning rate 3/10
  step 0: p=(4.0000, 1.0000)  loss=20.0000  grad=(8.000, 8.000)  next step length=3.394
  step 1: p=(1.6000, -1.4000)  loss=10.4000  grad=(3.200, -11.200)  next step length=3.494
  step 2: p=(0.6400, 1.9600)  loss=15.7760  grad=(1.280, 15.680)  next step length=4.720 loss UP
  step 3: p=(0.2560, -2.7440)  loss=30.1837  grad=(0.512, -21.952)  next step length=6.587 loss UP
  step 4: p=(0.1024, 3.8416)  loss=59.0420  grad=(0.205, 30.733)  next step length=9.220 loss UP OUTSIDE MAP
```
The large run stops at step 3. Step 4 is at y = 3.84, outside the map.

## Visual vocabulary
- Drawn: left, a framed top-down contour map, equal aspect, world window
  x -2.5..6, y -3.05..3.05 at 0.72 screen units per unit, centred near (-3.64, 0.5).
  Rings are the level sets 1, 4, 9, 16, 25, 36 (ellipses clipped to the frame),
  labelled with their loss on the upper left, away from every path. A green dot
  marks the minimum. A dot for the current point, a red uphill gradient arrow, a
  dashed arc of the ring through the start with a right-angle mark, a downhill
  step arrow, and a polyline trail per run. Right panel: the loss formula
  (y 2.45), the update rule (y 1.95), learning rate and loss readouts (y 1.45),
  and a loss-against-step chart (centre y -0.2) with one line per run. Caption
  at y -2.35.
- Motion: the gradient arrow grows from the dot, rotates half a turn about the
  dot to point downhill, then shrinks toward the dot by the learning rate. The
  dot slides along the arrow while its trail segment draws and the loss chart
  gains one point. Later steps do arrow then slide in one play. A new run drops
  a fresh dot on the start and dims the old trail. No ValueTracker: steps are
  discrete.
- Colour: blue-grey rings, green the minimum, red the uphill gradient and the
  diverging run, yellow the 0.1 run, teal the 0.2 run, white the step arrow.

## Distinct from
- `newtons_method`: a curve on axes, a dot that climbs a dashed riser and rides
  an orange tangent down to the x-axis, nested zoom insets, a digit table.
- `derivative` / `derivatives`: a curve on axes with a secant or tangent driven
  continuously by a ValueTracker.
- Here nothing is a graph of a function and no tangent line is drawn. The
  picture is a map seen from above: rings, arrows that cross them at right
  angles, and three polyline paths. Motion is an arrow that grows, turns around
  and shrinks, and a dot that walks in 2D, plus a chart that grows a point per
  step. The teaching moment is the step size, which Newton's method does not
  have.

## Key teaching moment
`c_s2`: the 0.3 run has just leapt across the valley and the readout says 10.4,
the same number the careful run showed after its first step. The dot leaps back
across, lands further out still at (0.64, 1.96), and the red chart line turns
upward to 15.8. The sentence says the loss goes up, not down. The valley's
4-to-1 steepness is what makes the y factor -1.4 while x still shrinks, so the
path visibly widens while staying on the map for three steps.

## Beat outline
- Intro (5): map, rings and levels, minimum, loss formula, start at loss 20
- First step in detail (5): gradient uphill, right angle to the ring, turn
  around, shrink by 0.1, step and loss falls to 10.4
- Rate 0.1 continues (4): steps 2 to 5, steps shorten by themselves
- Rule (1): subtract learning rate times gradient, repeat
- Rate 0.2 (5): reset, cross the valley, zigzag, below one, beats the careful run
- Rate 0.3 (5): reset, leap lands further out, loss up, leaps grow, diverging
- End (4): only the rate changed, too small, too large, closing line
- Total: 29
