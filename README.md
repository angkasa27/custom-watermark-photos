# 📸 Photos Watermark with Custom Data

This script adds watermarks to JPEG images based on folder-specific metadata, and also updates the EXIF metadata (including timestamp and GPS).

## 🗂 Folder Structure

```
custom-watermark/
├── bulk_watermark.py           # Main script
├── folder_metadata.csv         # Folder-specific metadata
├── input_images/               # Source folders with images
│   ├── CGK05-070/
│   └── CGK05-071/
├── output_images/              # Output (auto-created)
```

## 📝 `folder_metadata.csv` Format

```csv
folder,start,end,lat,lon,address
CGK05-070,2025:04:22 14:00:00,2025:04:22 15:00:00,-6.291590,106.956761,"Jl. Jatiasih, RT.001/RW.012"
CGK05-071,2025:04:23 08:00:00,2025:04:23 10:00:00,-6.292000,106.957000,"Jl. Mangga Raya, Jakarta"
```

- `start`, `end`: Used to generate a random datetime for watermark and EXIF
- `lat`, `lon`: Used for watermark and EXIF GPS metadata
- `address`: Displayed in watermark

## ⚙️ How to Run

### 1. Install Requirements

```bash
pip install pillow piexif
```

### 2. Place Your Files

- Put all your images in folders under `input_images/`
- Ensure each folder has a matching row in `folder_metadata.csv`

### 3. Run the Script

```bash
python bulk_watermark.py
```

### ✅ Features

- Random timestamp per image (based on date range)
- Slight GPS variations (1–2 meters) on some images
- Watermark includes:
  - Randomized timestamp
  - GPS coordinates
  - Address
  - Folder name and incremented version
- GPS and DateTime also updated in EXIF metadata

---
