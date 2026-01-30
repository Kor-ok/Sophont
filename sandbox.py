"""
Exploratory sandbox for custom space coordinates

"""

from __future__ import annotations

import json
import math

import httpx
import numpy as np

PARSEC_SCALE_X: np.float32 = np.float32(math.cos(math.pi / 6))  # sqrt(3)/2 ≈ 0.8660254037844386
PARSEC_SCALE_Y: np.float32 = np.float32(1.0)

def is_even(n: int) -> bool:
  return (n % 2) == 0

def worldXY_to_mapXY(world_x: np.float32, world_y: np.float32) -> tuple[np.float32, np.float32]:
  
  ix = world_x - np.float32(0.5)
  iy = (world_y - np.float32(0.5)) if is_even(int(world_x)) else world_y
  x = ix * PARSEC_SCALE_X
  y = iy * -PARSEC_SCALE_Y
  return x, y

def mapXY_to_worldXY(map_x: np.float32, map_y: np.float32, *, tolerance: np.float32 = np.finfo(np.float32).eps) -> tuple[np.float32, np.float32]:
  
  world_x_float = map_x / PARSEC_SCALE_X + np.float32(0.5)

  # Candidate integers to test (centered around nearest int)
  base = int(round(world_x_float))
  candidates = [base - 1, base, base + 1]

  best_candidate: int | None = None
  best_error = np.float32(np.inf)
  best_world_y = np.float32(0.0)

  for cand in candidates:
    if is_even(cand):
      world_y = -map_y + np.float32(0.5)
    else:
      world_y = -map_y
    # Reconstruct forward to measure error
    rx, ry = worldXY_to_mapXY(np.float32(cand), world_y)
    err = abs(rx - map_x) + abs(ry - map_y)
    if err < best_error:
      best_error = err
      best_candidate = cand
      best_world_y = world_y
      if err <= tolerance:
        break  # Good enough

  if best_candidate is None:
    raise ValueError("Failed to invert map coordinates (no candidate chosen).")

  return np.float32(best_candidate), best_world_y

def sector_hex_to_world_xy(sector_x: int, sector_y: int, hex_x: int, hex_y: int) -> tuple[np.float32, np.float32]:
    """Convert sector and hex coordinates to world-space X,Y coordinates."""
    SECTOR_WIDTH = 32
    SECTOR_HEIGHT = 40

    REFERENCE_SECTOR_X = 0
    REFERENCE_SECTOR_Y = 0

    REFERENCE_HEX_X = 1
    REFERENCE_HEX_Y = 40

    x = (sector_x - REFERENCE_SECTOR_X) * SECTOR_WIDTH + (hex_x - REFERENCE_HEX_X)
    y = (sector_y - REFERENCE_SECTOR_Y) * SECTOR_HEIGHT + (hex_y - REFERENCE_HEX_Y)
    return np.float32(x), np.float32(y)

def get_world_data(world_x: np.float32, world_y: np.float32, milieu: str | None = None) -> dict[str, object]:
    
    url = "https://travellermap.com/api/credits"
    params = {
    "x": str(world_x),
    "y": str(world_y),
    }
    if milieu:
        params["milieu"] = milieu

    response = httpx.get(url, params=params)
    response.raise_for_status()  # Raise error for bad responses

    try:
        data = response.json()
    except json.JSONDecodeError as e:
        raise ValueError("Failed to parse JSON response") from e

    return data


if __name__ == "__main__":
    print("\033c", end="")  # Clear terminal
    XRANGE: np.float32 = PARSEC_SCALE_X / 2
    YRANGE: np.float32 = PARSEC_SCALE_Y / 2
    REQUIRED_SUBDIVISIONS = 32 * 16 # 512 subdivisions
    
    epsilon_float32 = np.finfo(np.float32).eps
    bits = 13  # ~1/8192 resolution
    binary_friendly_step_size: np.float32 = np.float32(1 / (2 ** bits))
    
    x_steps_in_range = XRANGE / binary_friendly_step_size
    y_steps_in_range = YRANGE / binary_friendly_step_size
    print(f"Binary friendly step size: {binary_friendly_step_size} (epsilon: {epsilon_float32})")
    print(f"Steps in Y range ({YRANGE}): {y_steps_in_range}")
    print(f"Steps in X range ({XRANGE}): {x_steps_in_range}")

    # Examples of integer based data to encode into the x float coordinate space within the fractional part
    ORBIT_NUMBER: int = 3 # 0-20
    ORBIT_DECIMAL: int = 1 # 0-9

    SATELLITE_NUMBER: int = 1 # 0-26

    encoded_coordinate_offset = np.float32(ORBIT_NUMBER)
    encoded_coordinate_offset += np.float32(ORBIT_DECIMAL / 10.0)
    encoded_coordinate_offset += np.float32(SATELLITE_NUMBER / 100.0)
    encoded_x_coordinate_offset: np.float32 = np.float32(encoded_coordinate_offset * binary_friendly_step_size)
    print(f"Encoded coordinate offset: {encoded_x_coordinate_offset}")

    # Examples of integer based data to encode into the y float coordinate space within the fractional part
    WORLD_TRI: int = 11 # 0 - 19
    WORLD_HEX: int = 30 # 0 - 219
    TERRAIN_HEX: int = 37 # 0 - 74
    LOCAL_HEX: int = 37 # 0 - 74

    encoded_y_coordinate_offset = np.float32(WORLD_TRI)
    encoded_y_coordinate_offset += np.float32(WORLD_HEX / 100.0)
    encoded_y_coordinate_offset += np.float32(TERRAIN_HEX / 10000.0)
    encoded_y_coordinate_offset += np.float32(LOCAL_HEX / 1000000.0)
    encoded_y_coordinate_offset: np.float32 = np.float32(encoded_y_coordinate_offset * binary_friendly_step_size)
    print(f"Encoded Y coordinate offset: {encoded_y_coordinate_offset}")

    map_space_coordinates: tuple[np.float32, np.float32] = (np.float32(14.289), np.float32(-107.0))
    world_space_coordinates = mapXY_to_worldXY(*map_space_coordinates)
    encoded_coordinates = (world_space_coordinates[0] + encoded_x_coordinate_offset, world_space_coordinates[1] + encoded_y_coordinate_offset)
    print(f"World-Space Coordinates: {world_space_coordinates}")
    print(f"Encoded World-Space Coordinates: {encoded_coordinates}")
    data = get_world_data(*encoded_coordinates)
    data_to_print = {"World Name: ": data.get("WorldName")}
    print("\nRetrieved World Data:")
    print(data_to_print)
    print("\n")

    # Decode back to ORBIT_NUMBER, ORBIT_DECIMAL, SATELLITE_NUMBER
    decoded_world_x = encoded_coordinates[0] - (int(encoded_coordinates[0]))
    decoded_orbit_number = int(decoded_world_x / binary_friendly_step_size)
    decoded_orbit_decimal = int((decoded_world_x - (decoded_orbit_number * binary_friendly_step_size)) / (binary_friendly_step_size / 10.0))
    decoded_satellite_number = int((decoded_world_x - (decoded_orbit_number * binary_friendly_step_size) - (decoded_orbit_decimal * (binary_friendly_step_size / 10.0))) / (binary_friendly_step_size / 100.0))
    print(f"Decoded Orbit Number: {decoded_orbit_number}, Orbit Decimal: {decoded_orbit_decimal}, Satellite Number: {decoded_satellite_number}")
    # Decode back to WORLD_TRI, WORLD_HEX, TERRAIN_HEX, LOCAL_HEX
    decoded_world_y = encoded_coordinates[1] - (int(encoded_coordinates[1]))
    decoded_world_tri = int(decoded_world_y / binary_friendly_step_size)
    decoded_world_hex = int((decoded_world_y - (decoded_world_tri * binary_friendly_step_size)) / (binary_friendly_step_size / 100.0))
    decoded_terrain_hex = int((decoded_world_y - (decoded_world_tri * binary_friendly_step_size) - (decoded_world_hex * (binary_friendly_step_size / 100.0))) / (binary_friendly_step_size / 10000.0))
    decoded_local_hex = int((decoded_world_y - (decoded_world_tri * binary_friendly_step_size) - (decoded_world_hex * (binary_friendly_step_size / 100.0)) - (decoded_terrain_hex * (binary_friendly_step_size / 10000.0))) / (binary_friendly_step_size / 1000000.0))
    print(f"Decoded World Tri: {decoded_world_tri}, World Hex: {decoded_world_hex}, Terrain Hex: {decoded_terrain_hex}, Local Hex: {decoded_local_hex}")