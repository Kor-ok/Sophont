from __future__ import annotations

import itertools as it
import logging
from time import sleep

from colorama import Fore, Style
from colorama import init as colorama_init

from utils.terminal import divider, header

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

colorama_init(
    autoreset=True, convert=True
)  # Initialize colorama for colored output in the terminal
REFRESH_RATE = 0.05  # Time in seconds between updates


def _print_nth_element_in_colour(
    iterable: list,
    colour: str = Fore.WHITE,
    length_to_colour: int = 1,
    prefix: str = "",
    suffix: str = "",
) -> None:
    """Print the nth element of an iterable in a specified colour."""

    for n, e in enumerate(iterable):
        to_print = []
        # length_to_colour determines how many elements to colour starting from the nth element
        for i, e in enumerate(iterable):
            if n <= i < n + length_to_colour:
                to_print.append(f"{colour}{Style.BRIGHT}{e}{Style.RESET_ALL}")
            else:
                to_print.append(f"{Style.DIM}{e}{Style.RESET_ALL}")
        print(f"{prefix}{' '.join(to_print)}{suffix}", end="\r", flush=True)

        sleep(REFRESH_RATE)


def demo_print_nth_element_in_colour() -> None:
    header("Demo: Print nth element in colour")
    array_evens = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
    array_odds = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]

    print(f"{Style.DIM}Even: {Style.RESET_ALL}{Style.NORMAL}{array_evens}{Style.RESET_ALL}")
    print(f"{Style.DIM}Odd:  {Style.RESET_ALL}{Style.NORMAL}{array_odds}{Style.RESET_ALL}")
    print()

    _print_nth_element_in_colour(array_evens, Fore.GREEN, length_to_colour=3, prefix="   Even:  ")
    print()
    _print_nth_element_in_colour(array_odds, Fore.RED, length_to_colour=2, prefix="   Odd:   ")
    print()


def demo_count() -> None:
    array_evens = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
    array_odds = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
    print(f"{Style.DIM}Even: {Style.RESET_ALL}{Style.NORMAL}{array_evens}{Style.RESET_ALL}")
    print(f"{Style.DIM}Odd:  {Style.RESET_ALL}{Style.NORMAL}{array_odds}{Style.RESET_ALL}")
    print()

    # ── itertools.count ──────────────────────────────────────────────────
    # count(start, step) produces an *infinite* counter.
    # Useful for labelling, indexing, or generating sequences on-the-fly.
    divider()
    header("itertools.count")
    print(f"{Style.DIM}count(start=0, step=1) → infinite iterator: 0, 1, 2, …{Style.RESET_ALL}")
    print()

    # Pair each even number with a running index starting at 1
    indexed = list(zip(it.count(1), array_evens))
    for idx, val in indexed:
        print(f"  {Style.DIM}#{idx:<3}{Style.RESET_ALL}{Fore.GREEN}{val}{Style.RESET_ALL}")

    print()

    # count with a custom step — generate a sequence of multiples of 5
    multiples_of_5 = list(it.islice(it.count(start=5, step=5), 8))
    print(f"  First 8 multiples of 5: {Fore.CYAN}{multiples_of_5}{Style.RESET_ALL}")


def demo_islice() -> None:
    array_evens = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
    array_odds = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
    print(f"{Style.DIM}Even: {Style.RESET_ALL}{Style.NORMAL}{array_evens}{Style.RESET_ALL}")
    print(f"{Style.DIM}Odd:  {Style.RESET_ALL}{Style.NORMAL}{array_odds}{Style.RESET_ALL}")
    print()

    # ── itertools.islice ─────────────────────────────────────────────────
    # islice(iterable, [start,] stop [, step]) lets you take a slice of
    # *any* iterable — including infinite ones — without building a list.
    divider()
    header("itertools.islice")
    print(f"{Style.DIM}islice(iterable, [start,] stop [, step]) → lazy slice{Style.RESET_ALL}")
    print()

    # Take elements 2‥5 (zero-based) from the odds array
    middle_odds = list(it.islice(array_odds, 2, 6))
    print(f"  Odds[2:6]       → {Fore.RED}{middle_odds}{Style.RESET_ALL}")

    # Every other element from evens
    every_other_even = list(it.islice(array_evens, 0, None, 2))
    print(f"  Evens[::2]      → {Fore.GREEN}{every_other_even}{Style.RESET_ALL}")

    # Safely peek at the first 3 items of an infinite counter
    first_three = list(it.islice(it.count(100, 7), 3))
    print(f"  count(100,7)[:3] → {Fore.CYAN}{first_three}{Style.RESET_ALL}")


def demo_groupby() -> None:
    array_evens = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
    array_odds = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
    print(f"{Style.DIM}Even: {Style.RESET_ALL}{Style.NORMAL}{array_evens}{Style.RESET_ALL}")
    print(f"{Style.DIM}Odd:  {Style.RESET_ALL}{Style.NORMAL}{array_odds}{Style.RESET_ALL}")
    print()

    # ── itertools.groupby ────────────────────────────────────────────────
    # groupby(iterable, key=None) clusters *consecutive* elements that
    # share the same key.  The iterable must already be sorted by that key
    # if you want global grouping; otherwise you only get runs.
    divider()
    header("itertools.groupby")
    print(f"{Style.DIM}groupby(iterable, key) → (key_value, group_iterator) pairs{Style.RESET_ALL}")
    print()

    # Merge both arrays, sort, then group by "small (≤10)" vs "large (>10)"
    combined = sorted(array_evens + array_odds)

    def size_label(x: int) -> str:
        return "small (≤10)" if x <= 10 else "large (>10)"

    for key, group in it.groupby(combined, key=size_label):
        members = list(group)
        colour = Fore.YELLOW if "small" in key else Fore.MAGENTA
        print(f"  {colour}{key:>12}{Style.RESET_ALL} → {members}")

    print()

    # Group by tens digit to show finer-grained bucketing
    def tens_digit(x: int) -> int:
        """e.g. 14 → 10"""
        return x // 10 * 10

    print(f"  {Style.DIM}Grouped by tens digit:{Style.RESET_ALL}")
    for key, group in it.groupby(combined, key=tens_digit):
        members = list(group)
        print(f"    {Fore.CYAN}{key:>3}s{Style.RESET_ALL}: {members}")


def demo_starmap() -> None:
    array_evens = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
    array_odds = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
    print(f"{Style.DIM}Even: {Style.RESET_ALL}{Style.NORMAL}{array_evens}{Style.RESET_ALL}")
    print(f"{Style.DIM}Odd:  {Style.RESET_ALL}{Style.NORMAL}{array_odds}{Style.RESET_ALL}")
    print()

    # ── itertools.starmap ────────────────────────────────────────────────
    # starmap(function, iterable_of_tuples) unpacks each tuple as *args*.
    # Think of it as map() but for functions that take multiple arguments.
    divider()
    header("itertools.starmap")
    print(f"{Style.DIM}starmap(func, iterable_of_tuples) → map with unpacked args{Style.RESET_ALL}")
    print()

    # Multiply paired elements from evens and odds
    pairs = list(zip(array_evens, array_odds))
    products = list(it.starmap(lambda a, b: a * b, pairs))

    print(f"  {'Even':>4}  {'Odd':>3}  {'Product':>7}")
    print(f"  {'────':>4}  {'───':>3}  {'───────':>7}")
    for (e, o), p in zip(pairs, products):
        print(
            f"  {Fore.GREEN}{e:>4}{Style.RESET_ALL}  {Fore.RED}{o:>3}{Style.RESET_ALL}  {Fore.CYAN}= {p:>5}{Style.RESET_ALL}"
        )

    print()

    # starmap with pow(): compute e**o for small values
    small_pairs = list(zip(array_evens[:4], array_odds[:4]))
    powers = list(it.starmap(pow, small_pairs))
    print("  pow(even, odd) for first 4 pairs:")
    for (e, o), p in zip(small_pairs, powers):
        print(
            f"    {Fore.GREEN}{e}{Style.RESET_ALL}^{Fore.RED}{o}{Style.RESET_ALL} = {Fore.YELLOW}{p}{Style.RESET_ALL}"
        )


def demo_zip_longest() -> None:
    array_evens = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
    array_odds = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
    print(f"{Style.DIM}Even: {Style.RESET_ALL}{Style.NORMAL}{array_evens}{Style.RESET_ALL}")
    print(f"{Style.DIM}Odd:  {Style.RESET_ALL}{Style.NORMAL}{array_odds}{Style.RESET_ALL}")
    print()

    # ── itertools.zip_longest ────────────────────────────────────────────
    # zip_longest(*iterables, fillvalue=None) zips iterables together but
    # continues until the *longest* one is exhausted, filling missing
    # values with fillvalue.  (Regular zip() stops at the shortest.)
    divider()
    header("itertools.zip_longest")
    print(
        f"{Style.DIM}zip_longest(*iterables, fillvalue=None) → zip to the longest{Style.RESET_ALL}"
    )
    print()

    # Uneven lists to show the fill behaviour
    short = array_evens[:4]  # [2, 4, 6, 8]
    long = array_odds[:7]  # [1, 3, 5, 7, 9, 11, 13]

    print(f"  short (4 items): {Fore.GREEN}{short}{Style.RESET_ALL}")
    print(f"  long  (7 items): {Fore.RED}{long}{Style.RESET_ALL}")
    print()

    for a, b in it.zip_longest(short, long, fillvalue="·"):
        a_str = (
            f"{Fore.GREEN}{a:>4}{Style.RESET_ALL}"
            if a != "·"
            else f"{Style.DIM}{'·':>4}{Style.RESET_ALL}"
        )
        b_str = (
            f"{Fore.RED}{b:>4}{Style.RESET_ALL}"
            if b != "·"
            else f"{Style.DIM}{'·':>4}{Style.RESET_ALL}"
        )
        print(f"    {a_str}  ↔  {b_str}")

    print()

    # Practical use: interleave two sequences with zip_longest + chain
    interleaved = [
        val
        for pair in it.zip_longest(array_evens, array_odds, fillvalue=None)
        for val in pair
        if val is not None
    ]
    print(f"  Interleaved: {Fore.CYAN}{interleaved}{Style.RESET_ALL}")


def demo_transform() -> None:
    """Demonstrate array transformation using groupby + islice + chain.from_iterable."""
    # ── itertools combo: groupby · islice · chain.from_iterable ──────────
    # Given a nested input array and a [depth, id, count] pattern series,
    # flatten-and-reassemble the data into a new flat array.
    #
    # Rules per pattern entry [depth, id, count]:
    #   • depth  – nesting level to read from (0 = top-level scalars, etc.)
    #   • id     – value prepended when depth *increases* vs. previous step
    #   • count  – how many atoms to consume from that depth's stream
    divider()
    header("itertools combo: groupby + islice + chain.from_iterable")
    print(f"{Style.DIM}Transform a nested array via a [depth, id, count] pattern.{Style.RESET_ALL}")
    print()

    array_input = [42, [1, 0, 1], 7, 3, [6, -99, [12, 1, -99]], 99]
    array_transform_pattern = [
        [0, 4, 1],
        [1, 0, 3],
        [0, 4, 2],
        [1, 2, 2],
        [2, 1, 3],
        [0, 4, 1],
    ]
    array_expected_output = [4, 42, 0, 1, 0, 1, 7, 3, 2, 6, -99, 1, 12, 1, -99, 99]

    print(f"  Input:    {array_input}")
    print(f"  Pattern:  {array_transform_pattern}")
    print(f"  Expected: {array_expected_output}")
    print()

    # ── 1. Recursive generator — tag every atom with its nesting depth ───
    def atoms_with_depth(arr: list, depth: int = 0):
        """Yield (depth, value) for each non-list element."""
        for item in arr:
            if isinstance(item, list):
                yield from atoms_with_depth(item, depth + 1)
            else:
                yield (depth, item)

    tagged = list(atoms_with_depth(array_input))

    DEPTH_COLOURS = {0: Fore.GREEN, 1: Fore.YELLOW, 2: Fore.CYAN}
    print(f"  {Style.DIM}1) Tag atoms with depth:{Style.RESET_ALL}")
    for d, v in tagged:
        c = DEPTH_COLOURS.get(d, Fore.WHITE)
        print(f"     ({c}{d}{Style.RESET_ALL}, {v})")
    print()

    # ── 2. groupby(depth) → per-depth iterators ─────────────────────────
    # sorted() is stable, so within-depth order matches the original walk.
    sorted_tagged = sorted(tagged, key=lambda t: t[0])
    depth_streams: dict[int, iter] = {}

    print(f"  {Style.DIM}2) groupby(depth) → bucket per level:{Style.RESET_ALL}")
    for d, grp in it.groupby(sorted_tagged, key=lambda t: t[0]):
        values = [v for _, v in grp]
        depth_streams[d] = iter(values)
        c = DEPTH_COLOURS.get(d, Fore.WHITE)
        print(f"     depth-{c}{d}{Style.RESET_ALL}: {values}")
    print()

    # ── 3. Walk the pattern — islice consumes exactly `count` atoms ──────
    # The id is prepended only when depth *increases* relative to the
    # previous step (i.e. we are descending into a deeper nesting level).
    def transform_segments(pattern, streams):
        """Yield tuple-segments: optional (id,) then islice(stream, count)."""
        prev_depth = -1
        for depth, id_val, count in pattern:
            if depth > prev_depth:
                yield (id_val,)
            yield tuple(it.islice(streams[depth], count))
            prev_depth = depth

    # Materialise segments for step-by-step display
    # (rebuild streams — iterators are single-pass)
    sorted_tagged2 = sorted(tagged, key=lambda t: t[0])
    display_streams: dict[int, iter] = {}
    for d, grp in it.groupby(sorted_tagged2, key=lambda t: t[0]):
        display_streams[d] = iter([v for _, v in grp])

    print(f"  {Style.DIM}3) Walk pattern — islice(stream[depth], count):{Style.RESET_ALL}")
    segments: list[list[int]] = []
    prev_depth = -1
    for depth, id_val, count in array_transform_pattern:
        descending = depth > prev_depth
        seg: list[int] = []
        if descending:
            seg.append(id_val)
        seg.extend(it.islice(display_streams[depth], count))
        segments.append(seg)

        dc = DEPTH_COLOURS.get(depth, Fore.WHITE)
        arrow = (
            f"{Fore.CYAN}\u2193{Style.RESET_ALL}"
            if descending
            else f"{Fore.RED}\u2191{Style.RESET_ALL}"
        )
        id_note = (
            f"  id={Fore.MAGENTA}{id_val}{Style.RESET_ALL}"
            if descending
            else f"  {Style.DIM}(no id){Style.RESET_ALL}"
        )
        print(
            f"     [{depth},{id_val:>2},{count}] {arrow} d{dc}{depth}{Style.RESET_ALL}"
            f"{id_note}  \u2192  {seg}"
        )
        prev_depth = depth
    print()

    # ── 4. chain.from_iterable flattens all segments into the result ─────
    result = list(it.chain.from_iterable(segments))

    print(f"  {Style.DIM}4) chain.from_iterable(segments):{Style.RESET_ALL}")
    print(f"     {Style.DIM}segments = {segments}{Style.RESET_ALL}")
    print()
    print(f"  Result:   {Fore.CYAN}{result}{Style.RESET_ALL}")
    print(f"  Expected: {Fore.CYAN}{array_expected_output}{Style.RESET_ALL}")

    match = result == array_expected_output
    c = Fore.GREEN if match else Fore.RED
    symbol = "\u2713" if match else "\u2717"
    print(f"  {c}{symbol} {'MATCH' if match else 'MISMATCH'}{Style.RESET_ALL}")


if __name__ == "__main__":
    header("SANDBOX", char="\u2500")
    print(
        f"{Fore.BLACK}{Style.DIM}This is for testing and experimentation. Not intended for production use.{Style.RESET_ALL}"
    )
    divider()
    print()

    demo_transform()

    print()
    divider()
