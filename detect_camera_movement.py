#!/usr/bin/env python3
"""
Detect camera movement in a time-lapse image sequence by estimating homographies
between a reference image and each subsequent image.

Method:
  - Detect ORB features and match with BFMatcher
  - Estimate homography with RANSAC
  - Decompose to translation (px), rotation (deg), scale
  - Flag frames exceeding user thresholds
  - Compare each image to the closest recent stable image (adaptive reference)

Usage:
  python detect_camera_movement.py --images <dir> --output movement.csv \
      --ref first --tx-th 3 --rot-th 1.0 --scale-th 0.02 --ratio 0.75 --crop-top-frac 0.333

Notes:
  - If homography cannot be estimated reliably, the frame is flagged
  - Images are processed in sorted filename order
"""

import argparse
import csv
import glob
import math
import os
from typing import Dict, List, Tuple

import cv2
import numpy as np


def compute_metrics_from_homography(H: np.ndarray) -> Tuple[float, float, float]:
    # Normalize homography
    H = H / H[2, 2]
    # Extract rotation+scale from top-left 2x2
    a, b, c, d = H[0, 0], H[0, 1], H[1, 0], H[1, 1]
    tx, ty = H[0, 2], H[1, 2]

    # Scale estimate from sqrt of determinant magnitudes
    scale = math.sqrt(max(1e-12, abs(a * d - b * c)))

    # Rotation angle from atan2 of elements (assuming limited projective skew)
    angle_rad = math.atan2(b, a)
    angle_deg = math.degrees(angle_rad)

    # Translation magnitude in pixels
    translation = math.sqrt(tx * tx + ty * ty)

    return translation, angle_deg, scale


def detect_movement(
    images_dir: str,
    output_csv: str,
    orb_features: int = 2000,
    match_ratio: float = 0.75,
    ransac_thresh: float = 3.0,
    tx_threshold: float = 3.0,
    rot_threshold: float = 1.0,
    scale_threshold: float = 0.02,
    crop_top_frac: float = 1.0,
    use_clahe: bool = True,
):
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

    # Will set first stable image as reference automatically

    def preprocess(img: np.ndarray) -> np.ndarray:
        out = img
        if crop_top_frac > 0.0 and crop_top_frac < 1.0:
            h = out.shape[0]
            cut = max(1, int(h * crop_top_frac))
            out = out[:cut, :]
        if use_clahe:
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            out = clahe.apply(out)
        return out

    orb = cv2.ORB_create(nfeatures=orb_features)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

    rows = []
    current_ref_img = None
    current_kp_ref, current_des_ref = None, None
    current_ref_name = ""

    for idx, img_path in enumerate(image_paths):
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            rows.append([os.path.basename(img_path), idx, 0, 0, 0, 0, 0, 0, "read_error"])
            continue

        img = preprocess(img)

        kp, des = orb.detectAndCompute(img, None)
        if des is None:
            rows.append([os.path.basename(img_path), idx, 0, 0, 0, 0, 0, 0, "no_descriptors"])
            continue

        # If this is the first image or no reference yet, make it the reference
        if current_ref_img is None:
            current_ref_img = img
            current_kp_ref, current_des_ref = kp, des
            current_ref_name = os.path.basename(img_path)
            translation, angle_deg, scale = 0.0, 0.0, 1.0
            status = "initial_reference"
        else:
            # Match against current reference
            matches = bf.knnMatch(current_des_ref, des, k=2)
            good = []
            for m, n in matches:
                if m.distance < match_ratio * n.distance:
                    good.append(m)

            if len(good) < 8:
                translation, angle_deg, scale = 0.0, 0.0, 1.0
                moved = True  # Default to moved if can't match
                status = "insufficient_matches"
            else:
                src_pts = np.float32([current_kp_ref[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
                dst_pts = np.float32([kp[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

                H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, ransac_thresh)
                if H is None:
                    translation, angle_deg, scale = 0.0, 0.0, 1.0
                    moved = True
                    status = "homography_failed"
                else:
                    translation, angle_deg, scale = compute_metrics_from_homography(H)
                    moved = (
                        (translation > tx_threshold)
                        or (abs(angle_deg) > rot_threshold)
                        or (abs(scale - 1.0) > scale_threshold)
                    )
                    status = "moved" if moved else "stable"

        rows.append([
            os.path.basename(img_path),
            idx,
            len(current_kp_ref) if current_kp_ref is not None else 0,
            len(kp),
            len(good) if 'good' in locals() else 0,
            translation,
            angle_deg,
            scale,
            status,
        ])

        # If stable or initial frame, update reference to this frame (closest good photo)
        if status in ["stable", "initial_reference"]:
            current_ref_img = img
            current_kp_ref, current_des_ref = kp, des
            current_ref_name = os.path.basename(img_path)

    # Write CSV
    os.makedirs(os.path.dirname(output_csv) or ".", exist_ok=True)
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "image_filename",
            "index",
            "ref_keypoints",
            "keypoints",
            "good_matches",
            "translation_px",
            "rotation_deg",
            "scale",
            "status",
        ])
        writer.writerows(rows)

    print(f"Wrote movement CSV: {output_csv}")


def main():
    parser = argparse.ArgumentParser(description="Detect camera movement in a time-lapse sequence")
    parser.add_argument("--images", required=True, help="Directory with images")
    parser.add_argument("--output", required=True, help="Output CSV path")
    # Reference is now automatically set to closest good photo
    parser.add_argument("--features", type=int, default=2000, help="Number of ORB features")
    parser.add_argument("--ratio", type=float, default=0.75, help="Lowe's ratio for KNN matching")
    parser.add_argument("--ransac", type=float, default=3.0, help="RANSAC reprojection threshold")
    parser.add_argument("--tx-th", type=float, default=3.0, help="Translation threshold (pixels)")
    parser.add_argument("--rot-th", type=float, default=1.0, help="Rotation threshold (degrees)")
    parser.add_argument("--scale-th", type=float, default=0.02, help="Scale delta threshold (abs(scale-1))")
    parser.add_argument("--crop-top-frac", type=float, default=1.0, help="Crop to top fraction of image before matching (e.g., 0.333)")
    parser.add_argument("--clahe", action="store_true", help="Apply CLAHE to normalize illumination before feature detection")

    args = parser.parse_args()

    detect_movement(
        images_dir=args.images,
        output_csv=args.output,
        # reference parameter removed
        orb_features=args.features,
        match_ratio=args.ratio,
        ransac_thresh=args.ransac,
        tx_threshold=args.tx_th,
        rot_threshold=args.rot_th,
        scale_threshold=args.scale_th,
        crop_top_frac=args.crop_top_frac,
        use_clahe=args.clahe,
    )


if __name__ == "__main__":
    main()


