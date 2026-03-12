from __future__ import annotations

from random import randint

# from rich import print
from rich import print
from rich.pretty import pprint
from sortedcontainers import SortedKeyList

from components.applied import Sensation
from components.primitives import VisionCode


def _roll(num_dice: int) -> int:
    rolls = [randint(1, 6) for _ in range(num_dice)]
    return sum(rolls)


def _get_matching_sensation_components(
    sensor: Sensation, emitter: Sensation
) -> tuple[list[Sensation], list[Sensation], list[Sensation]]:
    matching_senses_sensor_components = []
    matching_senses_emitter_components = []
    difference_sensor_emitter_components = []

    if sensor.sense is None or emitter.sense is None:
        return (
            matching_senses_sensor_components,
            matching_senses_emitter_components,
            difference_sensor_emitter_components,
        )
    for sense in sensor.sense:
        if sense in emitter.sense:
            sensor_component = Sensation(
                sense=tuple([sense]),
                constant=(sensor.constant[sensor.sense.index(sense)],),
            )
            matching_senses_sensor_components.append(sensor_component)
    for sense in emitter.sense:
        if sense in sensor.sense:
            emitter_component = Sensation(
                sense=tuple([sense]),
                constant=(emitter.constant[emitter.sense.index(sense)],),
            )
            matching_senses_emitter_components.append(emitter_component)

    for constant in zip(
        matching_senses_emitter_components, matching_senses_sensor_components
    ):
        difference = constant[0].constant[0] - constant[1].constant[0]
        difference_component = Sensation(
            sense=constant[0].sense,
            constant=(difference,),
        )
        difference_sensor_emitter_components.append(difference_component)

    return (
        matching_senses_sensor_components,
        matching_senses_emitter_components,
        difference_sensor_emitter_components,
    )


def roll_for_sensory_acquisition(
    sensor: Sensation,
    emitter: Sensation,
    distance: int,
    size: int,
) -> Sensation | None:
    benchmark = size - distance
    if benchmark < 0:
        print("Impossible to perceive")
        return

    matching_senses_sensor, matching_senses_emitter, difference_senses = (
        _get_matching_sensation_components(sensor, emitter)
    )
    # print("Matching Senses Sensor:")
    # pprint(matching_senses_sensor)
    # print()
    # print("Matching Senses Emitter:")
    # pprint(matching_senses_emitter)
    # print()
    # print("Difference Sensor Emitter:")
    # pprint(difference_senses)
    # print()

    roll_result = _roll(distance)
    # print(f"Roll Result: {roll_result}")
    # print()

    roll_targets = []
    for sense in matching_senses_sensor:
        roll_targets.append(benchmark + sense.constant[0])
    # print(f"Roll Targets: {roll_targets}")
    # print()

    result_sensation = Sensation(
        sense=tuple(s.sense[0] for s in matching_senses_sensor),
        constant=tuple(
            target - roll_result + difference_senses[i].constant[0]
            for i, target in enumerate(roll_targets)
        ),
    )

    return result_sensation


def emitter_factory(emitter_template: Sensation) -> Sensation:
    sorted_key_values: SortedKeyList = SortedKeyList(key=lambda x: x[0])
    # for each sense the key is the VisionCode key and the value is the tuple element from the constant tuple in the Sensation
    for i, sense in enumerate(emitter_template.sense or []):
        sorted_key_values.add((sense.key, emitter_template.constant[i]))

    new_senses = []
    new_constants = []
    for key in range(sorted_key_values[0][0], sorted_key_values[-1][0] + 1):
        # Generate a new Sensation where new VisionCodes are created for each key in the range and the constant is interpolated based on the sorted key values
        new_senses.append(VisionCode(key))
        new_constants.append(
            tuple(
                int(
                    sorted_key_values[i][1]
                    + (key - sorted_key_values[i][0])
                    * (sorted_key_values[i + 1][1] - sorted_key_values[i][1])
                    / (sorted_key_values[i + 1][0] - sorted_key_values[i][0])
                )
                for i in range(len(sorted_key_values) - 1)
                if sorted_key_values[i][0]
                <= key
                <= sorted_key_values[i + 1][0]
            )
        )

    new_emitter = Sensation(
        sense=tuple(reversed(new_senses)),
        constant=tuple(c[0] for c in reversed(new_constants)),
    )
    return new_emitter


if __name__ == "__main__":
    vision_senses = [
        red := VisionCode(8),
        green := VisionCode(7),
        blue := VisionCode(6),
    ]

    human_vision_sensor = Sensation(
        sense=tuple(vision_senses), constant=(16, 16, 16)
    )

    # print("Human Vision Sensor:")
    # pprint(human_vision_sensor)

    emitter_senses = [
        ir := VisionCode(12),
        red := VisionCode(8),
        green := VisionCode(7),
        blue := VisionCode(6),
    ]

    thing_emission = Sensation(
        sense=tuple(emitter_senses), constant=(32, 18, 16, 11)
    )

    # print("Thing Emitter:")
    # pprint(thing_emission)
    print()

    thing_from_factory = emitter_factory(thing_emission)
    print("Thing from Factory:")
    pprint(thing_from_factory)

    thing_range = 5  # id=5 means Vlong 1000m
    thing_size = 6  # id=6 means Vehicle Sized

    perception_result = roll_for_sensory_acquisition(
        sensor=human_vision_sensor,
        emitter=thing_from_factory,
        distance=thing_range,
        size=thing_size,
    )

    print("Result Sensation:")
    pprint(perception_result)
