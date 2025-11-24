#!/usr/bin/env python3
"""Diagnostic tool to help identify battle screen coordinates.

This tool helps analyze screenshots to find the correct pixel coordinates
for battle detection after UI updates.

Usage:
    python tools/battle_screen_diagnostic.py <screenshot_path>
"""

import sys
from pathlib import Path

import cv2


def analyze_screenshot(image_path: str):
    """Analyze a screenshot to help identify battle screen coordinates.

    Args:
        image_path: Path to the screenshot file
    """
    print(f"\n{'='*60}")
    print(f"Analyzing screenshot: {image_path}")
    print(f"{'='*60}\n")

    # Load image
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        print(f"Error: Could not load image from {image_path}")
        return

    # Convert BGR to RGB (same as bot does)
    img = img_bgr[..., ::-1]

    height, width = img.shape[:2]
    print(f"Image dimensions: {width}x{height}")
    print()

    # Helper functions matching the bot's detection logic
    def get_pixel(y: int, x: int) -> list[int] | None:
        if y >= height or x >= width or y < 0 or x < 0:
            return None
        return img[y][x].tolist()

    def is_bright(pixel: list[int] | None, threshold: int = 180) -> bool:
        return pixel is not None and all(channel >= threshold for channel in pixel)

    def is_scoreboard_purple(pixel: list[int] | None) -> bool:
        if pixel is None:
            return False
        r, g, b = pixel
        return r >= 200 and b >= 200 and g <= 140

    def pixel_to_str(pixel: list[int] | None) -> str:
        if pixel is None:
            return "None"
        return f"RGB({pixel[0]:3d}, {pixel[1]:3d}, {pixel[2]:3d})"

    # Check old coordinates
    print("Checking OLD COORDINATES:")
    print("-" * 60)

    coords_1v1 = [(515, 49), (518, 77), (530, 52), (530, 77), (618, 115)]
    coords_2v2 = [(515, 53), (518, 80), (531, 52), (514, 76), (615, 114)]

    print("\n1v1 Coordinates:")
    for i, (y, x) in enumerate(coords_1v1):
        pixel = get_pixel(y, x)
        bright = is_bright(pixel)
        purple = is_scoreboard_purple(pixel)
        print(f"  [{i}] ({y:3d}, {x:3d}): {pixel_to_str(pixel):20s} | Bright: {bright:5} | Purple: {purple}")

    print("\n2v2 Coordinates:")
    for i, (y, x) in enumerate(coords_2v2):
        pixel = get_pixel(y, x)
        bright = is_bright(pixel)
        purple = is_scoreboard_purple(pixel)
        print(f"  [{i}] ({y:3d}, {x:3d}): {pixel_to_str(pixel):20s} | Bright: {bright:5} | Purple: {purple}")

    # Analyze top area where battle UI typically appears
    print("\n\nSCANNING TOP AREA FOR BATTLE UI ELEMENTS:")
    print("-" * 60)

    # Scan the top area (y: 40-120, x: 500-650) for bright pixels
    print("\nBright pixels in top area (potential timer/score indicators):")
    bright_coords = []
    for y in range(40, 120, 2):  # Sample every 2 pixels
        for x in range(500, 650, 2):
            pixel = get_pixel(y, x)
            if is_bright(pixel):
                bright_coords.append((y, x, pixel))

    if bright_coords:
        print(f"Found {len(bright_coords)} bright pixels")
        # Show some representative samples
        print("Sample bright pixels:")
        for y, x, pixel in bright_coords[::max(1, len(bright_coords)//10)][:10]:
            print(f"  ({y:3d}, {x:3d}): {pixel_to_str(pixel)}")
    else:
        print("No bright pixels found in expected area")

    # Scan for purple pixels (scoreboard)
    print("\nPurple pixels in top area (potential scoreboard):")
    purple_coords = []
    for y in range(40, 120, 2):
        for x in range(500, 650, 2):
            pixel = get_pixel(y, x)
            if is_scoreboard_purple(pixel):
                purple_coords.append((y, x, pixel))

    if purple_coords:
        print(f"Found {len(purple_coords)} purple pixels")
        print("Sample purple pixels:")
        for y, x, pixel in purple_coords[::max(1, len(purple_coords)//10)][:10]:
            print(f"  ({y:3d}, {x:3d}): {pixel_to_str(pixel)}")
    else:
        print("No purple pixels found in expected area")

    # Suggest coordinate scan areas
    print("\n\nSUGGESTED ANALYSIS:")
    print("-" * 60)
    print("1. The battle timer typically appears in the top-middle area")
    print("2. The scoreboard (purple) usually appears near the timer")
    print("3. For hero updates, UI elements may have shifted down or to the sides")
    print("\nTo find new coordinates:")
    print("  - Look for clusters of bright (white) pixels in the timer area")
    print("  - Find purple pixels indicating the scoreboard")
    print("  - Select 4-5 stable pixels that are consistently present during battle")
    print("  - Last coordinate should be purple (scoreboard), others should be bright")

    # Create a visual overlay for analysis
    input_path = Path(image_path)
    output_path = str(input_path.with_stem(input_path.stem + '_analyzed'))
    img_vis = img_bgr.copy()

    # Mark old coordinates in red
    for y, x in coords_1v1 + coords_2v2:
        if 0 <= y < height and 0 <= x < width:
            cv2.circle(img_vis, (x, y), 3, (0, 0, 255), -1)

    # Mark bright pixels in green
    for y, x, _ in bright_coords[::5]:  # Sample to avoid clutter
        cv2.circle(img_vis, (x, y), 1, (0, 255, 0), -1)

    # Mark purple pixels in blue
    for y, x, _ in purple_coords[::5]:
        cv2.circle(img_vis, (x, y), 1, (255, 0, 0), -1)

    cv2.imwrite(output_path, img_vis)
    print(f"\nVisualization saved to: {output_path}")
    print("  - Red circles: OLD coordinate positions")
    print("  - Green dots: Bright pixels found")
    print("  - Blue dots: Purple pixels found")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nError: No screenshot path provided")
        sys.exit(1)

    screenshot_path = sys.argv[1]
    if not Path(screenshot_path).exists():
        print(f"Error: File not found: {screenshot_path}")
        sys.exit(1)

    analyze_screenshot(screenshot_path)
