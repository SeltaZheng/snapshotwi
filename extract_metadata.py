#!/usr/bin/env python3
"""
Extract EXIF metadata from images and save to CSV.

Extracts common camera settings and image properties:
- Date/time taken
- Image dimensions
- Camera make/model
- Exposure settings (shutter speed, aperture, ISO)
- Focal length
- Flash settings
- GPS coordinates (if available)

Usage:
    python extract_metadata.py --images <dir> --output metadata.csv
"""

import argparse
import csv
import glob
import os
from datetime import datetime
from typing import Dict, List, Optional

import exifread


def get_exif_data(image_path: str) -> Dict:
    """Extract EXIF data from image file using exifread."""
    try:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f, details=True)
            return tags
    except Exception as e:
        print(f"Warning: Could not read EXIF from {image_path}: {e}")
        return {}


def get_gps_data(exif_data: Dict) -> Dict:
    """Extract GPS data from EXIF."""
    gps_data = {}
    for key, value in exif_data.items():
        if key.startswith('GPS '):
            gps_data[key] = value
    return gps_data


def convert_to_degrees(value):
    """Convert GPS coordinates to decimal degrees."""
    if hasattr(value, 'values') and len(value.values) == 3:
        d, m, s = [float(v) for v in value.values]
        return d + (m / 60.0) + (s / 3600.0)
    return value


def format_gps_coordinates(gps_data: Dict) -> tuple:
    """Format GPS coordinates as decimal degrees."""
    lat = None
    lon = None
    
    if 'GPS GPSLatitude' in gps_data and 'GPS GPSLongitude' in gps_data:
        lat = convert_to_degrees(gps_data['GPS GPSLatitude'])
        lon = convert_to_degrees(gps_data['GPS GPSLongitude'])
        
        # Apply hemisphere corrections
        if 'GPS GPSLatitudeRef' in gps_data and str(gps_data['GPS GPSLatitudeRef']) == 'S':
            lat = -lat
        if 'GPS GPSLongitudeRef' in gps_data and str(gps_data['GPS GPSLongitudeRef']) == 'W':
            lon = -lon
    
    return lat, lon


def get_image_dimensions(image_path: str) -> tuple:
    """Get image dimensions using exifread."""
    try:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f, details=True)
            width = tags.get('EXIF ExifImageWidth')
            height = tags.get('EXIF ExifImageHeight')
            
            if width and height:
                return int(str(width)), int(str(height))
            
            # Fallback to EXIF ImageWidth/ImageLength
            width = tags.get('Image ImageWidth')
            height = tags.get('Image ImageLength')
            
            if width and height:
                return int(str(width)), int(str(height))
                
    except Exception:
        pass
    
    return None, None


def extract_metadata_from_image(image_path: str) -> Dict:
    """Extract all metadata from a single image."""
    exif_data = get_exif_data(image_path)
    gps_data = get_gps_data(exif_data)
    
    # Get image dimensions
    width, height = get_image_dimensions(image_path)
    
    # Extract common metadata fields
    metadata = {
        'filename': os.path.basename(image_path),
        'filepath': image_path,
        'width': width,
        'height': height,
        'file_size_bytes': os.path.getsize(image_path) if os.path.exists(image_path) else None,
    }
    
    # Date/Time
    date_fields = ['Image DateTime', 'EXIF DateTimeOriginal', 'EXIF DateTimeDigitized']
    for field in date_fields:
        if field in exif_data:
            try:
                date_str = str(exif_data[field])
                dt = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                metadata['date_taken'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                metadata['date_taken_iso'] = dt.isoformat()
                break
            except (ValueError, TypeError):
                continue
    
    # Camera info
    metadata['camera_make'] = str(exif_data.get('Image Make', ''))
    metadata['camera_model'] = str(exif_data.get('Image Model', ''))
    metadata['software'] = str(exif_data.get('Image Software', ''))
    
    # Exposure settings
    metadata['exposure_time'] = str(exif_data.get('EXIF ExposureTime', ''))
    metadata['f_number'] = str(exif_data.get('EXIF FNumber', ''))
    metadata['iso'] = str(exif_data.get('EXIF ISOSpeedRatings', exif_data.get('EXIF ISO', '')))
    metadata['exposure_mode'] = str(exif_data.get('EXIF ExposureMode', ''))
    metadata['exposure_program'] = str(exif_data.get('EXIF ExposureProgram', ''))
    metadata['metering_mode'] = str(exif_data.get('EXIF MeteringMode', ''))
    
    # Lens info
    metadata['focal_length'] = str(exif_data.get('EXIF FocalLength', ''))
    metadata['focal_length_35mm'] = str(exif_data.get('EXIF FocalLengthIn35mmFilm', ''))
    
    # Flash
    metadata['flash'] = str(exif_data.get('EXIF Flash', ''))
    
    # White balance
    metadata['white_balance'] = str(exif_data.get('EXIF WhiteBalance', ''))
    
    # GPS coordinates
    lat, lon = format_gps_coordinates(gps_data)
    metadata['gps_latitude'] = lat
    metadata['gps_longitude'] = lon
    metadata['gps_altitude'] = str(gps_data.get('GPS GPSAltitude', ''))
    
    # Orientation
    metadata['orientation'] = str(exif_data.get('Image Orientation', ''))
    
    # Color space
    metadata['color_space'] = str(exif_data.get('EXIF ColorSpace', ''))
    
    return metadata


def extract_metadata_from_directory(images_dir: str, output_csv: str) -> None:
    """Extract metadata from all images in directory and save to CSV."""
    # Find all image files
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.tiff', '*.tif', '*.bmp', '*.gif']
    image_paths = set()  # Use set to avoid duplicates
    
    for ext in image_extensions:
        image_paths.update(glob.glob(os.path.join(images_dir, ext)))
        image_paths.update(glob.glob(os.path.join(images_dir, ext.upper())))
    
    image_paths = sorted(list(image_paths))  # Convert back to sorted list
    
    if not image_paths:
        raise FileNotFoundError(f"No images found in directory: {images_dir}")
    
    print(f"Found {len(image_paths)} images to process...")
    
    # Extract metadata from all images
    all_metadata = []
    for i, img_path in enumerate(image_paths):
        print(f"Processing {i+1}/{len(image_paths)}: {os.path.basename(img_path)}")
        metadata = extract_metadata_from_image(img_path)
        all_metadata.append(metadata)
    
    # Write to CSV
    if all_metadata:
        fieldnames = all_metadata[0].keys()
        os.makedirs(os.path.dirname(output_csv) or ".", exist_ok=True)
        
        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_metadata)
        
        print(f"Metadata saved to: {output_csv}")
        print(f"Processed {len(all_metadata)} images")
    else:
        print("No metadata extracted")


def main():
    parser = argparse.ArgumentParser(
        description="Extract EXIF metadata from images and save to CSV"
    )
    parser.add_argument(
        "--images", 
        required=True, 
        help="Directory containing images"
    )
    parser.add_argument(
        "--output", 
        required=True, 
        help="Output CSV file path"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.images):
        print(f"Error: Directory '{args.images}' not found!")
        return 1
    
    try:
        extract_metadata_from_directory(args.images, args.output)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
