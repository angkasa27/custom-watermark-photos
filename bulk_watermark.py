import os
from PIL import Image, ImageDraw, ImageFont
import piexif
from datetime import datetime
from datetime import datetime, timedelta
import random
import csv

def load_folder_metadata(csv_path="folder_metadata.csv"):
    metadata = {}
    try:
        with open(csv_path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                folder = row["folder"]
                start = datetime.strptime(row["start"], "%Y:%m:%d %H:%M:%S")
                end = datetime.strptime(row["end"], "%Y:%m:%d %H:%M:%S")
                lat = float(row["lat"])
                lon = float(row["lon"])
                address = row["address"]
                metadata[folder] = {
                    "start": start,
                    "end": end,
                    "lat": lat,
                    "lon": lon,
                    "address": address
                }
    except Exception as e:
        print("⚠️ Error loading folder metadata:", e)
    return metadata

folder_metadata = load_folder_metadata()
input_root = "input_images"
output_root = "output_images"

def format_datetime(raw):
    try:
        dt = datetime.strptime(raw, "%Y:%m:%d %H:%M:%S")
        return dt.strftime("%d %b %Y %H:%M:%S")
    except:
        return "Unknown Date"

def draw_text_with_shadow(draw, position, text, font, shadow_offset=(2, 2)):
    x, y = position
    draw.text((x + shadow_offset[0], y + shadow_offset[1]), text, font=font, fill="black")
    draw.text((x, y), text, font=font, fill="white")

def add_watermark(image_path, output_path):
    try:
        img = Image.open(image_path)
        exif_bytes = img.info.get("exif")
        exif_data = piexif.load(exif_bytes) if exif_bytes else {"0th": {}, "Exif": {}, "GPS": {}}

        folder_name = os.path.basename(os.path.dirname(image_path))

        # Generate a random date in the folder's range
        if folder_name in folder_metadata:
            start = folder_metadata[folder_name]["start"]
            end = folder_metadata[folder_name]["end"]
            delta = end - start
            random_seconds = random.randint(0, int(delta.total_seconds()))
            random_dt = start + timedelta(seconds=random_seconds)
            exif_datetime_str = random_dt.strftime("%Y:%m:%d %H:%M:%S")
            display_datetime_str = random_dt.strftime("%d %b %Y %H:%M:%S")

            encoded_date = exif_datetime_str.encode()
            exif_data["0th"][piexif.ImageIFD.DateTime] = encoded_date
            exif_data["Exif"][piexif.ExifIFD.DateTimeOriginal] = encoded_date
            exif_data["Exif"][piexif.ExifIFD.DateTimeDigitized] = encoded_date
        else:
            display_datetime_str = "Unknown Date"

        if folder_name in folder_metadata:
            lat = folder_metadata[folder_name]["lat"]
            lon = folder_metadata[folder_name]["lon"]
            # Randomly apply small GPS offset to about half the images
            if random.random() < 0.5:
                lat += random.uniform(-0.00001, 0.00001)
                lon += random.uniform(-0.00001, 0.00001)
            location = folder_metadata[folder_name]["address"]
            coords_text = f"{lon:.6f}E {lat:.6f}S"

            def to_deg(value, ref_positive, ref_negative):
                ref = ref_positive if value >= 0 else ref_negative
                abs_value = abs(value)
                d = int(abs_value)
                m = int((abs_value - d) * 60)
                s = int((abs_value - d - m / 60) * 3600 * 100)
                return ((d, 1), (m, 1), (s, 100)), ref

            lat_data, lat_ref = to_deg(lat, b'N', b'S')
            lon_data, lon_ref = to_deg(lon, b'E', b'W')

            exif_data["GPS"] = {
                piexif.GPSIFD.GPSLatitudeRef: lat_ref,
                piexif.GPSIFD.GPSLatitude: lat_data,
                piexif.GPSIFD.GPSLongitudeRef: lon_ref,
                piexif.GPSIFD.GPSLongitude: lon_data,
            }
        else:
            coords_text = "Unknown GPS"
            location = "Address"

        custom1 = folder_name
        try:
            prefix, number = folder_name.split("-")
            custom2 = f"{prefix}-{int(number) + 1:03}"
        except:
            custom2 = "Custom text2"

        lines = [
            display_datetime_str,
            coords_text,
            location,
            custom1,
            custom2
        ]

        draw = ImageDraw.Draw(img)
        font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
        font = ImageFont.truetype(font_path, 64)

        margin = 20
        line_height = font.getbbox("Hg")[3] + 10
        total_height = line_height * len(lines)

        x_base = img.width - margin
        y = img.height - total_height - margin - 64 #add a little space for the bottom

        for line in lines:
            line_width = draw.textbbox((0, 0), line, font=font)[2]
            draw_text_with_shadow(draw, (x_base - line_width, y), line, font)
            y += line_height

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, exif=piexif.dump(exif_data))
        print(f"✅ {os.path.basename(image_path)} with random date")
    except Exception as e:
        print(f"❌ Error processing {image_path}: {e}")


# Traverse folders
for root, dirs, files in os.walk(input_root):
    for file in files:
        if file.lower().endswith((".jpg", ".jpeg")):
            input_path = os.path.join(root, file)

            # Get subfolder name (e.g., CGK05-070)
            relative_path = os.path.relpath(root, input_root)
            output_dir = os.path.join(output_root, relative_path)
            output_path = os.path.join(output_dir, file)

            add_watermark(input_path, output_path)