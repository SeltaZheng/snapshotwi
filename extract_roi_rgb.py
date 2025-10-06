#!/usr/bin/env python3
"""
Extract RGB values of pixels inside ROIs from time-lapse photos and store them in a single CSV.

Supports polygon ROIs (preferred) and legacy rectangle ROIs.

Usage:
    python extract_roi_rgb.py --images <dir> --roi-json <path> --output <csv>

Columns:
    image_filename, roi_id, pixel_index, x, y, r, g, b

Notes:
    - pixel_index is the 0-based index of the pixel within the ROI mask ordering
    - For polygons, the mask determines which (x,y) are included
    - Images are processed in sorted filename order
"""

import argparse
import csv
import glob
import json
import os
from typing import Dict, List, Tuple

import cv2
import numpy as np


def load_roi_definitions(roi_json_path: str) -> Dict:
    with open(roi_json_path, 'r') as f:
        data = json.load(f)
    return data


def build_mask_for_roi(image_shape: Tuple[int, int, int], roi: Dict) -> np.ndarray:
    h, w = image_shape[0], image_shape[1]
    mask = np.zeros((h, w), dtype=np.uint8)

    roi_type = roi.get("type")

    if roi_type == "polygon" and "points" in roi:
        pts = np.array(roi["points"], dtype=np.int32)
        if pts.ndim != 2 or pts.shape[1] != 2:
            return mask
        cv2.fillPoly(mask, [pts], 255)
        return mask

    # Legacy rectangle support: fields x,y,width,height
    if all(k in roi for k in ("x", "y", "width", "height")):
        x = int(roi["x"])
        y = int(roi["y"])
        w_rect = int(roi["width"])
        h_rect = int(roi["height"])
        x2 = min(x + w_rect, w)
        y2 = min(y + h_rect, h)
        mask[y:y2, x:x2] = 255
        return mask

    return mask


def iterate_mask_pixels(mask: np.ndarray) -> List[Tuple[int, int]]:
    ys, xs = np.where(mask > 0)
    # Order by y, then x for deterministic ordering
    coords = list(zip(xs.tolist(), ys.tolist()))
    coords.sort(key=lambda p: (p[1], p[0]))
    return coords


def extract_rgb_from_images(images_dir: str, roi_json_path: str, output_csv: str) -> None:
    roi_data = load_roi_definitions(roi_json_path)
    rois = roi_data.get("rois", [])

    image_paths = sorted(
        glob.glob(os.path.join(images_dir, "*.jpg"))
        + glob.glob(os.path.join(images_dir, "*.jpeg"))
        + glob.glob(os.path.join(images_dir, "*.png"))
        + glob.glob(os.path.join(images_dir, "*.bmp"))
        + glob.glob(os.path.join(images_dir, "*.tif"))
        + glob.glob(os.path.join(images_dir, "*.tiff"))
    )

    if not image_paths:
        raise FileNotFoundError(f"No images found in directory: {images_dir}")

    # Prepare CSV
    os.makedirs(os.path.dirname(output_csv) or ".", exist_ok=True)
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["image_filename", "roi_id", "pixel_index", "x", "y", "r", "g", "b"])

        for img_path in image_paths:
            img = cv2.imread(img_path)
            if img is None:
                print(f"Warning: could not read image: {img_path}")
                continue

            # Convert to RGB from BGR
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            for roi in rois:
                roi_id = int(roi.get("id", 0))
                mask = build_mask_for_roi(img_rgb.shape, roi)
                if mask.sum() == 0:
                    continue

                coords = iterate_mask_pixels(mask)
                for idx, (x, y) in enumerate(coords):
                    r, g, b = img_rgb[y, x].tolist()
                    writer.writerow([os.path.basename(img_path), roi_id, idx, x, y, r, g, b])

    print(f"Wrote CSV: {output_csv}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract RGB values inside ROIs from time-lapse images into a single CSV"
    )
    parser.add_argument("--images", required=True, help="Directory containing time-lapse images")
    parser.add_argument("--roi-json", required=True, help="Path to ROI JSON file")
    parser.add_argument("--output", required=True, help="Output CSV path")

    args = parser.parse_args()

    extract_rgb_from_images(args.images, args.roi_json, args.output)


if __name__ == "__main__":
    main()



