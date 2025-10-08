#!/usr/bin/env python3
"""
Region of Interest (ROI) Selector

A Python script that allows users to define regions of interest on images
using mouse interactions. Users can draw polygons to select areas of interest.

Features:
- Load and display images
- Draw polygonal regions of interest
- Save ROI coordinates
- Export cropped regions
- Multiple ROI selection support

Usage:
    python roi_selector.py <image_path>
    
Controls:
    - Left click: Add vertex
    - Right click: Undo last vertex / delete last polygon
    - 'n': Finish current polygon
    - 'r': Reset all polygons
    - 's': Save ROI coordinates to file
    - 'c': Crop and save selected regions
    - 'q' or ESC: Quit
"""

import cv2
import numpy as np
import argparse
import json
import os
from typing import List, Tuple, Optional


class ROISelector:
    def __init__(self, image_path: str):
        """Initialize the ROI selector with an image."""
        self.image_path = image_path
        self.original_image = cv2.imread(image_path)
        
        if self.original_image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Create a copy for drawing
        self.display_image = self.original_image.copy()
        
        # ROI storage (polygons). Each ROI is a list of (x, y) tuples
        self.rois: List[List[Tuple[int, int]]] = []
        self.current_polygon: List[Tuple[int, int]] = []
        
        # Mouse hover point for drawing helper line
        self.hover_point: Optional[Tuple[int, int]] = None
        
        # Window settings
        self.window_name = "ROI Selector - Press 'h' for help"
        
    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse events for drawing polygons."""
        if event == cv2.EVENT_LBUTTONDOWN:
            # Add a vertex
            self.current_polygon.append((x, y))
            self.update_display()
        elif event == cv2.EVENT_RBUTTONDOWN:
            # Undo last vertex; if none, delete last polygon
            if self.current_polygon:
                self.current_polygon.pop()
            else:
                self.delete_last_roi()
            self.update_display()
        elif event == cv2.EVENT_MOUSEMOVE:
            # Update hover point for helper line
            self.hover_point = (x, y)
            self.update_display()
    
    def update_display(self):
        """Update the display image with current ROIs and drawing state."""
        self.display_image = self.original_image.copy()
        
        # Draw completed polygon ROIs
        for i, pts in enumerate(self.rois):
            if len(pts) >= 2:
                poly_np = np.array(pts, dtype=np.int32)
                cv2.polylines(self.display_image, [poly_np], isClosed=True, color=(0, 255, 0), thickness=2)
            if pts:
                x0, y0 = pts[0]
                cv2.putText(self.display_image, f"ROI {i+1}", (x0, y0-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            # Draw vertices
            for (vx, vy) in pts:
                cv2.circle(self.display_image, (vx, vy), 3, (0, 255, 0), -1)
        
        # Draw current polygon in progress
        if self.current_polygon:
            pts = self.current_polygon
            # Lines between current vertices
            for i in range(1, len(pts)):
                cv2.line(self.display_image, pts[i-1], pts[i], (0, 0, 255), 2)
            # Helper line to hover point
            if self.hover_point and pts:
                cv2.line(self.display_image, pts[-1], self.hover_point, (0, 0, 255), 1)
            # Vertices
            for (vx, vy) in pts:
                cv2.circle(self.display_image, (vx, vy), 3, (0, 0, 255), -1)
        
        # Add instructions
        instructions = [
            "Left click: Add vertex",
            "Right click: Undo vertex / delete last polygon",
            "N: Finish current polygon",
            "R: Reset all polygons",
            "S: Save ROI coordinates",
            "C: Crop and save regions",
            "Q/ESC: Quit"
        ]
        
        for i, instruction in enumerate(instructions):
            cv2.putText(self.display_image, instruction, (10, 30 + i*25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(self.display_image, instruction, (10, 30 + i*25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        cv2.imshow(self.window_name, self.display_image)
    
    def delete_last_roi(self):
        """Delete the last drawn polygon ROI."""
        if self.rois:
            self.rois.pop()
            self.update_display()
    
    def reset_rois(self):
        """Reset all polygon ROIs and current polygon."""
        self.rois.clear()
        self.current_polygon = []
        self.update_display()
    
    def save_roi_coordinates(self, output_file: str = None):
        """Save ROI coordinates (polygons) to a JSON file, appending if it already exists for this image."""
        if not output_file:
            base_name = os.path.splitext(os.path.basename(self.image_path))[0]
            output_file = f"{base_name}_roi_coordinates.json"
        
        # Load existing data if present to support multiple saves for the same image
        existing_data = None
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r') as f:
                    existing_data = json.load(f)
            except Exception:
                existing_data = None
        
        # Consolidate polygons to save: include completed polygons and optionally a finished current polygon
        rois_to_add = [
            {
                "type": "polygon",
                "points": [[int(px), int(py)] for (px, py) in pts]
            }
            for pts in self.rois
        ]
        # Do not auto-save in-progress polygon; user should press 'n' to finish
        
        if existing_data and isinstance(existing_data, dict) and existing_data.get("image_path") == self.image_path:
            # Continue numbering from last id
            existing_rois = existing_data.get("rois", [])
            next_id = (existing_rois[-1]["id"] + 1) if existing_rois else 1
            for idx, roi in enumerate(rois_to_add):
                roi["id"] = next_id + idx
                existing_rois.append(roi)
            existing_data["rois"] = existing_rois
            roi_data = existing_data
        else:
            # Create new file or overwrite if for different image
            roi_data = {
                "image_path": self.image_path,
                "image_dimensions": {
                    "width": self.original_image.shape[1],
                    "height": self.original_image.shape[0]
                },
                "rois": [
                    {
                        "id": i + 1,
                        **roi
                    }
                    for i, roi in enumerate(rois_to_add)
                ]
            }
        
        with open(output_file, 'w') as f:
            json.dump(roi_data, f, indent=2)
        
        print(f"ROI coordinates saved to: {output_file}")
        return output_file
    
    def crop_and_save_regions(self, output_dir: str = None):
        """Crop and save the selected polygon regions using a mask."""
        if not self.rois:
            print("No ROIs to crop!")
            return
        
        if not output_dir:
            base_name = os.path.splitext(os.path.basename(self.image_path))[0]
            output_dir = f"{base_name}_cropped_regions"
        
        os.makedirs(output_dir, exist_ok=True)
        
        for i, pts in enumerate(self.rois):
            if len(pts) < 3:
                continue
            mask = np.zeros(self.original_image.shape[:2], dtype=np.uint8)
            poly_np = np.array(pts, dtype=np.int32)
            cv2.fillPoly(mask, [poly_np], 255)
            masked = cv2.bitwise_and(self.original_image, self.original_image, mask=mask)
            # Tight crop to polygon bounding rect
            x, y, w, h = cv2.boundingRect(poly_np)
            cropped = masked[y:y+h, x:x+w]
            output_path = os.path.join(output_dir, f"roi_{i+1:02d}.png")
            cv2.imwrite(output_path, cropped)
            print(f"Cropped region {i+1} saved to: {output_path}")
        
        print(f"All cropped regions saved to: {output_dir}")
        return output_dir
    
    def run(self):
        """Main loop for the ROI selector."""
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        
        # Initial display
        self.update_display()
        
        print("ROI Selector started!")
        print("Controls:")
        print("  - Left click: Add vertex")
        print("  - Right click: Undo vertex / delete last polygon")
        print("  - 'n': Finish current polygon")
        print("  - 'r': Reset all polygons")
        print("  - 's': Save ROI coordinates to file")
        print("  - 'c': Crop and save selected regions")
        print("  - 'q' or ESC: Quit")
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q') or key == 27:  # 'q' or ESC
                break
            elif key == ord('r'):
                self.reset_rois()
            elif key == ord('n'):
                # Finish current polygon
                if len(self.current_polygon) >= 3:
                    self.rois.append(self.current_polygon.copy())
                    self.current_polygon = []
                    self.update_display()
                else:
                    print("Need at least 3 vertices to finish a polygon.")
            elif key == ord('s'):
                self.save_roi_coordinates()
            elif key == ord('c'):
                self.crop_and_save_regions()
            elif key == ord('h'):
                print("\nHelp - Controls:")
                print("  - Left click: Add vertex")
                print("  - Right click: Undo vertex / delete last polygon")
                print("  - 'n': Finish current polygon")
                print("  - 'r': Reset all polygons")
                print("  - 's': Save ROI coordinates to file")
                print("  - 'c': Crop and save selected regions")
                print("  - 'q' or ESC: Quit")
        
        cv2.destroyAllWindows()
        
        # Final summary
        if self.rois:
            print(f"\nSession completed with {len(self.rois)} ROI(s) defined:")
            for i, pts in enumerate(self.rois):
                print(f"  ROI {i+1}: {len(pts)} vertices")
        else:
            print("\nSession completed with no ROIs defined.")


def main():
    """Main function to run the ROI selector."""
    parser = argparse.ArgumentParser(
        description="Select regions of interest on an image",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python roi_selector.py image.jpg
  python roi_selector.py /path/to/image.png
        """
    )
    
    parser.add_argument(
        "image_path",
        help="Path to the image file"
    )
    
    args = parser.parse_args()
    
    # Check if image file exists
    if not os.path.exists(args.image_path):
        print(f"Error: Image file '{args.image_path}' not found!")
        return 1
    
    try:
        # Create and run ROI selector
        selector = ROISelector(args.image_path)
        selector.run()
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
