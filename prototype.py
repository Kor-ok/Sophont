from __future__ import annotations

import itertools as it
import logging

from colorama import Fore, Style
from colorama import init as colorama_init

from utils.terminal import divider, header

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

colorama_init(autoreset=True, convert=True)

def signature_transformer(semantic_signature: list, semantic_mapping: list) -> list:
    # ── 1. Recursive generator — tag every atom with its nesting depth ───
    def atoms_with_depth(arr: list, depth: int = 0):
        """Yield (depth, value) for each non-list element."""
        for item in arr:
            if isinstance(item, list):
                yield from atoms_with_depth(item, depth + 1)
            else:
                yield (depth, item)

    tagged = list(atoms_with_depth(semantic_signature))

    # ── 2. groupby(depth) → per-depth iterators ─────────────────────────
    # sorted() is stable, so within-depth order matches the original walk.
    sorted_tagged = sorted(tagged, key=lambda t: t[0])
    depth_streams: dict[int, iter] = {}

    for d, grp in it.groupby(sorted_tagged, key=lambda t: t[0]):
        values = [v for _, v in grp]
        depth_streams[d] = iter(values)

    # Materialise segments for step-by-step display
    # (rebuild streams — iterators are single-pass)
    sorted_tagged2 = sorted(tagged, key=lambda t: t[0])
    display_streams: dict[int, iter] = {}
    for d, grp in it.groupby(sorted_tagged2, key=lambda t: t[0]):
        display_streams[d] = iter([v for _, v in grp])

    segments: list[list[int]] = []
    prev_depth = -1
    for depth, id_val, count in semantic_mapping:
        descending = depth > prev_depth
        seg: list[int] = []
        if descending:
            seg.append(id_val)
        seg.extend(it.islice(display_streams[depth], count))
        segments.append(seg)

        prev_depth = depth
    
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

    # ── 4. chain.from_iterable flattens all segments into the result ─────
    result = list(it.chain.from_iterable(segments))

    return result


if __name__ == "__main__":
    header("PROTOTYPE", char="\u2500")
    print(
        f"{Fore.BLACK}{Style.DIM}Generate Component Signature from Semantic Signature and Semantic Mapping{Style.RESET_ALL}"
    )
    divider()
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


    result = signature_transformer(array_input, array_transform_pattern)
    print(f"  Result:   {result}")
    print(f"  Expected: {array_expected_output}")
    print(f"  Match:    {result == array_expected_output}")


    print()
    divider()
