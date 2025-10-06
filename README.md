# Region of Interest (ROI) Selector

A Python script that allows users to define regions of interest on images using mouse interactions. Users can draw polygon regions to select areas of interest and save the coordinates or export cropped regions.

## Features

- **Interactive ROI Selection**: Draw polygon regions of interest using mouse
- **Multiple ROI Support**: Select multiple regions on the same image
- **Coordinate Export**: Save ROI coordinates to JSON file
- **Region Cropping**: Automatically crop and save selected regions
- **Visual Feedback**: Real-time display of selected regions with numbering
- **Easy Controls**: Simple keyboard and mouse controls

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python roi_selector.py <image_path>
```

### Examples

```bash
# Select ROIs on a JPEG image
python roi_selector.py photo.jpg

# Select ROIs on a PNG image
python roi_selector.py /path/to/image.png
```

### Extract RGB values inside ROIs across time-lapse images

```bash
python extract_roi_rgb.py --images <dir_of_images> --roi-json <roi_json_path> --output output.csv
```

The script supports both polygon ROIs and legacy rectangles stored by earlier versions.

### Detect camera movement across a time-lapse

```bash
python detect_camera_movement.py --images <dir_of_images> --output movement.csv --crop-top-frac 0.333 --clahe --tx-th 3 --rot-th 1.0 --scale-th 0.02
```

Output CSV columns:
- image_filename, index, ref_keypoints, keypoints, good_matches, translation_px, rotation_deg, scale, status

Notes:
- Frames with large translation/rotation/scale changes are flagged as "moved".
- Each frame is compared against the most recent stable frame (closest good photo).
- Use `--clahe` for illumination normalization and `--crop-top-frac 0.333` to focus on top third.

### Extract image metadata

```bash
python extract_metadata.py --images <dir_of_images> --output metadata.csv
```

Extracts EXIF data including:
- Date/time taken, image dimensions, file size
- Camera make/model, software
- Exposure settings (shutter speed, aperture, ISO)
- Focal length, flash settings, white balance
- GPS coordinates (if available)

## Controls

### Mouse Controls
- **Left click**: Add a vertex to the current polygon
- **Right click**: Undo last vertex; if none, delete last polygon

### Keyboard Controls
- **'n'**: Finish the current polygon (requires at least 3 vertices)
- **'r'**: Reset all polygons
- **'s'**: Save ROI coordinates to JSON file (appends for same image)
- **'c'**: Crop and save selected regions as separate images
- **'h'**: Show help information in console
- **'q' or ESC**: Quit the application

## Output Files

### ROI Coordinates (JSON)
When you press 's', the script saves ROI coordinates to a JSON file. If the file already exists for the same image, new ROIs are appended and IDs continue from the last saved ROI. Polygons are saved as arrays of points. Structure example:

```json
{
  "image_path": "path/to/image.jpg",
  "image_dimensions": {
    "width": 1920,
    "height": 1080
  },
  "rois": [
    {
      "id": 1,
      "type": "polygon",
      "points": [[x1, y1], [x2, y2], [x3, y3]]
    }
  ]
}
```

### Cropped Regions
When you press 'c', the script creates a directory with cropped images:
- `image_name_cropped_regions/roi_01.jpg`
- `image_name_cropped_regions/roi_02.jpg`
- etc.

## Requirements

- Python 3.7+
- OpenCV (cv2) >= 4.8.0
- NumPy >= 1.24.0

## File Structure

```
snapshotwi/
├── roi_selector.py      # Main script
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## How It Works

1. **Image Loading**: The script loads the specified image using OpenCV
2. **Interactive Selection**: Users draw rectangles by clicking and dragging
3. **Visual Feedback**: Selected regions are displayed with green rectangles and numbers
4. **Data Storage**: ROI coordinates are stored in memory and can be exported
5. **Region Extraction**: Selected regions can be cropped and saved as separate images

## Tips

- Draw rectangles from top-left to bottom-right for best results
- Use the 'r' key to start over if you make mistakes
- Save coordinates frequently with 's' to avoid losing your work
- The script automatically creates output directories as needed
- ROI numbers are displayed on the image for easy identification

## Troubleshooting

### Common Issues

1. **Image not loading**: Ensure the image path is correct and the file exists
2. **No display window**: Make sure you have a display available (for headless systems, use X11 forwarding)
3. **Permission errors**: Ensure you have write permissions in the output directory

### Error Messages

- `Could not load image`: Check that the image file exists and is a supported format
- `No ROIs to crop!`: You need to draw at least one rectangle before cropping

## License

This project is open source and available under the MIT License.
