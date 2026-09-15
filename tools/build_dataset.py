"""Build a balanced, mutually-exclusive problem-classification dataset.

Source: public LeetCode scrape (topicTags are the free labels).
Physics/geometry rows are hand-written, since LeetCode has no such category.
"""
import json, re, html, csv, random, collections

random.seed(17)

# --- category mapping -------------------------------------------------
# Order matters: the FIRST rule that matches wins, so specific structural
# tags beat the generic "Array" tag that sits on half the corpus.
PRIORITY = [
    ("linked_list",        {"Linked List"}),
    ("stack",              {"Stack", "Monotonic Stack"}),
    ("searching",          {"Binary Search"}),
    ("graphs",             {"Graph", "Breadth-First Search", "Depth-First Search",
                            "Union Find", "Topological Sort", "Shortest Path"}),
    ("dynamic_programming",{"Dynamic Programming"}),
    ("arrays",             {"Two Pointers", "Sliding Window", "Prefix Sum"}),
    ("sorting",            {"Sorting"}),
    ("math",               {"Math", "Number Theory", "Combinatorics"}),
    ("arrays",             {"Array"}),
]

PER_CLASS = 45
MIN_WORDS, MAX_WORDS = 12, 90


def clean(raw: str) -> str:
    """HTML problem body -> one plain-text statement."""
    if not raw:
        return ""
    t = raw
    t = re.sub(r"<pre>.*?</pre>", " ", t, flags=re.S | re.I)   # drop worked examples
    t = re.sub(r"<img[^>]*>", " ", t, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)                              # strip remaining tags
    t = html.unescape(t)
    t = t.replace("\u00a0", " ")
    # cut everything from the first Example/Constraints marker onward
    t = re.split(r"\b(Example\s*\d|Constraints:|Follow[- ]up)", t)[0]
    t = re.sub(r"\s+", " ", t).strip()
    return t


def categorise(tags):
    names = {t["name"] if isinstance(t, dict) else t for t in tags}
    for cat, trigger in PRIORITY:
        if names & trigger:
            return cat
    return None


def main():
    problems = json.load(open("probs.json"))["problems"]
    buckets = collections.defaultdict(list)
    seen = set()

    for p in problems:
        tags = p.get("topicTags") or []
        cat = categorise(tags)
        if not cat:
            continue
        text = clean(p.get("content", ""))
        wc = len(text.split())
        if not (MIN_WORDS <= wc <= MAX_WORDS):
            continue
        key = text[:120].lower()
        if key in seen:
            continue
        seen.add(key)
        buckets[cat].append(text)

    rows = []
    for cat, texts in buckets.items():
        random.shuffle(texts)
        for t in texts[:PER_CLASS]:
            rows.append((t, cat))

    # physics: hand-written, no LeetCode equivalent
    rows += [(t, "physics") for t in PHYSICS]

    random.shuffle(rows)

    with open("problems.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["text", "category"])
        w.writerows(rows)

    counts = collections.Counter(c for _, c in rows)
    print(f"total rows: {len(rows)}")
    for c, n in sorted(counts.items()):
        print(f"  {n:3d}  {c}")


PHYSICS = [
    "A ball is thrown horizontally from the top of a cliff with an initial speed of twenty metres per second. Find how far from the base of the cliff it lands.",
    "A projectile is launched at thirty degrees above the horizontal with a speed of forty metres per second. Determine its maximum height and total time of flight.",
    "Two cars start from the same point and travel in perpendicular directions. Find the rate at which the distance between them increases.",
    "A boat crosses a river flowing at three metres per second while the boat travels at four metres per second relative to the water. Find the resultant velocity.",
    "A block slides down a frictionless inclined plane of angle thirty degrees. Calculate its acceleration along the incline.",
    "A stone is dropped from rest and falls for three seconds. How far does it travel and what is its final speed?",
    "Find the resultant of two forces of magnitude five newtons and twelve newtons acting at right angles to each other.",
    "A car accelerates uniformly from rest to twenty five metres per second in ten seconds. Find the acceleration and the distance covered.",
    "A pendulum of length two metres swings with small amplitude. Determine its period of oscillation.",
    "A cyclist moving at fifteen metres per second brakes and comes to rest in five seconds. Find the deceleration.",
    "An object is launched vertically upward. Show that the time to rise equals the time to fall back to the launch height.",
    "Decompose a velocity vector of magnitude fifty metres per second at sixty degrees into horizontal and vertical components.",
    "A plane flies north at two hundred kilometres per hour while wind blows east at fifty kilometres per hour. Find the ground velocity.",
    "Two blocks connected by a string over a pulley have masses three and five kilograms. Find the acceleration of the system.",
    "A ball bounces to sixty percent of its previous height each time. Find the total distance travelled before it comes to rest.",
    "A force of ten newtons acts on a two kilogram mass for four seconds. Find the change in momentum and final velocity.",
    "Calculate the kinetic energy of a car of mass one thousand kilograms travelling at twenty metres per second.",
    "A spring with stiffness constant two hundred newtons per metre is compressed by ten centimetres. Find the stored elastic energy.",
    "A satellite orbits at a fixed radius around the Earth. Derive the relationship between orbital speed and orbital radius.",
    "A swimmer aims directly across a river but is carried downstream by the current. Find the angle at which they must aim to land directly opposite.",
    "Show that for a projectile launched over level ground the range is maximised at forty five degrees.",
    "A wheel rotating at ten radians per second decelerates uniformly and stops in four seconds. Find the angular deceleration.",
    "Two trains approach each other on the same track. Determine whether they collide given their speeds and braking distances.",
    "A mass hangs in equilibrium from two ropes at different angles. Find the tension in each rope.",
    "An object moves with constant acceleration. Derive the equation relating final velocity, initial velocity, acceleration and displacement.",
    "A ball rolls off a table one metre high with a horizontal speed of three metres per second. Find where it lands.",
    "Find the centripetal acceleration of an object moving in a circle of radius five metres at eight metres per second.",
    "A rocket expels gas downward. Explain how conservation of momentum produces upward thrust.",
    "A skier descends a slope of twenty degrees with a coefficient of friction of zero point one. Find the acceleration.",
    "Determine the work done by a constant force of twenty newtons moving an object five metres at an angle of sixty degrees to the displacement.",
    "Two vectors of equal magnitude are added. Show how the angle between them determines the magnitude of the resultant.",
    "A car rounds an unbanked curve of radius fifty metres. Find the maximum speed before it skids given the friction coefficient.",
    "A body is in equilibrium under three concurrent forces. State the condition their vector sum must satisfy.",
    "A lift accelerates upward at two metres per second squared. Find the apparent weight of a passenger inside.",
    "Calculate the momentum of a bullet of mass ten grams moving at four hundred metres per second.",
    "A ball is thrown upward with initial speed thirty metres per second. Sketch how velocity and acceleration change over time.",
    "Given displacement as a function of time, find the instantaneous velocity and acceleration by differentiation.",
    "Two objects collide elastically head on. Determine their velocities after the collision.",
    "A uniform beam rests on two supports. Find the reaction force at each support using moments.",
    "An electron enters a uniform magnetic field perpendicular to its velocity. Describe the resulting path and find its radius.",
    "A wave travels along a string at twenty metres per second with a frequency of five hertz. Find its wavelength.",
    "Find the terminal velocity of a sphere falling through a viscous fluid.",
    "A particle undergoes simple harmonic motion with amplitude four centimetres. Find its maximum speed and acceleration.",
    "Two forces act on a body at an angle of one hundred and twenty degrees. Find the magnitude of the resultant using the cosine rule.",
    "A projectile is fired up an inclined plane. Determine the range measured along the incline.",
]


if __name__ == "__main__":
    main()
