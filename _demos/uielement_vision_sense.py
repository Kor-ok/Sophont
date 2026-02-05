from __future__ import annotations

import base64
import io
from pathlib import Path

import numpy as np
from nicegui import ui
from PIL import Image

from _gui import styles

ChannelValueRange = tuple[np.float32, np.float32]
PerChannelLatitudes = tuple[ChannelValueRange, ChannelValueRange, ChannelValueRange]


class VisionSenseCodec:
    BIT_DEPTH: int = 32  # bits per channel
    INTENSITY_INCREMENT = 1.0 / BIT_DEPTH

    SPECTRUM_SEGMENTS: int = 16  # number of discrete segments in the vision spectrum
    SPECTRUM_SEGMENT_WIDTH = 1.0 / SPECTRUM_SEGMENTS

    @staticmethod
    def compute_per_channel_latitudes(bands: tuple[int, int, int]) -> PerChannelLatitudes:
        """Compute the value range for each RGB channel based on band sensitivities."""

        def _band_to_range(band: int) -> ChannelValueRange:
            segment = band * VisionSenseCodec.SPECTRUM_SEGMENT_WIDTH
            min_value = np.float32(segment)
            max_value = np.float32(segment + VisionSenseCodec.SPECTRUM_SEGMENT_WIDTH) 
            return (min_value, max_value)

        return (_band_to_range(bands[0]), _band_to_range(bands[1]), _band_to_range(bands[2]))


def _convert_linear_tif_to_filtered_data_uri(
    tif_path: Path,
    per_channel_latitudes: PerChannelLatitudes,
    *,
    gamma: float = 2.2,
    apply_gamma: bool = True,
    apply_ui_overlay: bool = True,
) -> str:
    """Convert a 32-bit linear TIFF to a base64 PNG data URI for direct use in NiceGUI.

    Returns a data URI string (data:image/png;base64,...) that can be passed directly
    to ui.image() without writing to disk.
    """

    tif_path = Path(tif_path)

    with Image.open(tif_path) as img:
        img.load()
        arr = np.asarray(img)

    # Work with the raw grayscale data.
    gray_f = arr.astype(np.float32)
    finite = np.isfinite(gray_f)

    # Normalize grayscale to [0, 1].
    if not finite.any():
        gray_n = np.zeros_like(gray_f, dtype=np.float32)
    else:
        g_min = float(np.min(gray_f[finite]))
        g_max = float(np.max(gray_f[finite]))

        # If it already looks normalized, keep it.
        if 0.0 <= g_min and g_max <= 1.0:
            gray_n = np.clip(gray_f, 0.0, 1.0)
        else:
            denom = g_max - g_min
            if denom <= 0:
                gray_n = np.zeros_like(gray_f, dtype=np.float32)
            else:
                gray_n = (gray_f - g_min) / denom
                gray_n = np.clip(gray_n, 0.0, 1.0)

    # Build RGB output by extracting each channel's latitude band from the normalized grayscale.
    # Pixels whose normalized value falls within [c_min, c_max) are rescaled to [0, 1] for that channel;
    # pixels outside the range are set to 0.
    h, w = gray_n.shape[:2]
    rgb_n = np.zeros((h, w, 3), dtype=np.float32)

    for c in range(3):
        c_min, c_max = per_channel_latitudes[c]
        c_range = float(c_max - c_min)
        if c_range <= 0.0:
            continue  # leave channel black
        # Mask: pixels in this latitude band
        in_band = (gray_n >= c_min) & (gray_n < c_max)
        # Rescale in-band values to [0, 1]
        rgb_n[..., c] = np.where(in_band, (gray_n - c_min) / c_range, 0.0)

    # Apply gamma correction.
    if apply_gamma:
        rgb_n = np.power(rgb_n, 1.0 / float(gamma), dtype=np.float32)

    rgb_u8 = (rgb_n * 255.0 + 0.5).astype(np.uint8)

    # Apply UI overlay tif_path = append "_UI" and ".png" for the overlay whose alpha channel will be blended
    if apply_ui_overlay:
        overlay_path = tif_path.parent / (tif_path.stem + "_UI.png")
        if overlay_path.exists():
            with Image.open(overlay_path) as overlay_img:
                overlay_img = overlay_img.convert("RGBA")
                overlay_arr = np.asarray(overlay_img).astype(np.float32) / 255.0
            overlay_rgb = overlay_arr[..., :3]
            overlay_alpha = overlay_arr[..., 3:4]

            rgb_f = rgb_u8.astype(np.float32) / 255.0
            rgb_f = rgb_f * (1.0 - overlay_alpha) + overlay_rgb * overlay_alpha
            rgb_u8 = (np.clip(rgb_f, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)

    # Encode to PNG in memory and return as base64 data URI.
    out = Image.fromarray(rgb_u8)
    buffer = io.BytesIO()
    out.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


# Convert tif to data URI for NiceGUI display (no disk write, always fresh on reload)
REPO_ROOT = Path(__file__).resolve().parents[1]
tif_image_path = REPO_ROOT / "game" / "primitives" / "vision_chart.tif"

sense_values = (8, 7, 6)
per_channel_latitudes = VisionSenseCodec.compute_per_channel_latitudes(sense_values)

image_data_uri = _convert_linear_tif_to_filtered_data_uri(tif_image_path, per_channel_latitudes)

with ui.header().classes("items-center justify-center bg-deep-orange-10 q-ma-none"):
    ui.label("NOTE: Isolated Vision Sense UI Element Development").classes(
        "text-sm font-thin q-ma-none"
    )

with ui.row().classes(styles.TAB_ROW):

    # LEFT COLUMN ===================== PACKAGE BUILDER
    with ui.column().classes(styles.TAB_COLUMN_LEFT) as sense_builder_container:
        ui.label("Vision Sense Builder Area")
        ui.label(f"{per_channel_latitudes}")

    # RIGHT COLUMN ==================== PACKAGE COLLECTION
    with ui.column().classes(styles.TAB_COLUMN_RIGHT) as sense_debug_area:
        ui.label("Vision Sense Debug Area")
        ui.image(image_data_uri)

ui.run(dark=True)
