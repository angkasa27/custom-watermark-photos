# Rename config
import os
from PIL import Image, ImageDraw, ImageFont
import piexif
from datetime import datetime, timedelta
import random

# Config
input_root = "input"
output_root = "output_static"

watermark_date = "2025:04:23 12:03:24"
lat, lon = map(float, "-6.323015° 107.055986°".replace("°", "").split())
address = "Jln raya Setu"
custom_text1 = "CGK05-0010"

renamed_prefix = "Photo situasi site sisi depan"

# Derived values
custom_text2 = f"{custom_text1[:-3]}{int(custom_text1[-3:]) + 1:03}"

def draw_text_with_shadow(draw, position, text, font, shadow_offset=(2, 2)):
    x, y = position
    draw.text((x + shadow_offset[0], y + shadow_offset[1]), text, font=font, fill="black")
    draw.text((x, y), text, font=font, fill="white")

def to_deg(value, ref_positive, ref_negative):
    ref = ref_positive if value >= 0 else ref_negative
    abs_value = abs(value)
    d = int(abs_value)
    m = int((abs_value - d) * 60)
    s = int((abs_value - d - m / 60) * 3600 * 100)
    return ((d, 1), (m, 1), (s, 100)), ref

def add_static_watermark(image_path, output_path):
    try:
        img = Image.open(image_path)

        exif_bytes = img.info.get("exif")
        exif_data = piexif.load(exif_bytes) if exif_bytes else {"0th": {}, "Exif": {}, "GPS": {}}

        encoded_date = watermark_date.encode()
        exif_data["0th"][piexif.ImageIFD.DateTime] = encoded_date
        exif_data["Exif"][piexif.ExifIFD.DateTimeOriginal] = encoded_date
        exif_data["Exif"][piexif.ExifIFD.DateTimeDigitized] = encoded_date

        lat_data, lat_ref = to_deg(lat, b'N', b'S')
        lon_data, lon_ref = to_deg(lon, b'E', b'W')
        exif_data["GPS"] = {
            piexif.GPSIFD.GPSLatitudeRef: lat_ref,
            piexif.GPSIFD.GPSLatitude: lat_data,
            piexif.GPSIFD.GPSLongitudeRef: lon_ref,
            piexif.GPSIFD.GPSLongitude: lon_data,
        }

        coords_text = f"{lon:.6f}E {lat:.6f}S"
        display_datetime_str = datetime.strptime(watermark_date, "%Y:%m:%d %H:%M:%S").strftime("%d %b %Y %H:%M:%S")

        lines = [
            display_datetime_str,
            coords_text,
            address,
            custom_text1,
            custom_text2
        ]

        draw = ImageDraw.Draw(img)
        font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
        scale_factor = 0.03
        font_size = max(16, int(img.height * scale_factor))
        font = ImageFont.truetype(font_path, font_size)

        margin = 20
        line_height = font.getbbox("Hg")[3] + 10
        total_height = line_height * len(lines)

        x_base = img.width - margin
        y = img.height - total_height - margin - 64

        for line in lines:
            line_width = draw.textbbox((0, 0), line, font=font)[2]
            draw_text_with_shadow(draw, (x_base - line_width, y), line, font)
            y += line_height

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, exif=piexif.dump(exif_data))
        print(f"✅ {os.path.basename(output_path)} watermarked")
    except Exception as e:
        print(f"❌ Error processing {image_path}: {e}")

# Process all images in input_root
for filename in os.listdir(input_root):
    if filename.lower().endswith((".jpg", ".jpeg")):
        input_path = os.path.join(input_root, filename)
        base_filename = f"{renamed_prefix}.jpg"
        output_subfolder = f"{custom_text1} - {custom_text2}"
        output_path = os.path.join(output_root, output_subfolder, base_filename)
        add_static_watermark(input_path, output_path)