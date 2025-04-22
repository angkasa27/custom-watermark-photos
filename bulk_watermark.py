import os
from PIL import Image, ImageDraw, ImageFont
import piexif
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

input_root = "input_images"
output_root = "output_images"
geolocator = Nominatim(user_agent="custom-watermarker")

def convert_gps(gps_data):
    def convert(value):
        return float(value[0]) + float(value[1])/60 + float(value[2])/3600

    if not gps_data or 2 not in gps_data or 4 not in gps_data:
        return None, None

    lat = convert(gps_data[2])
    if gps_data[1] == b'S':
        lat = -lat
    lon = convert(gps_data[4])
    if gps_data[3] == b'W':
        lon = -lon
    return lat, lon

def get_location_name(lat, lon):
    try:
        location = geolocator.reverse((lat, lon), timeout=5)
        return location.address if location else "Address"
    except GeocoderTimedOut:
        return "Address"

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
        exif_data = piexif.load(exif_bytes) if exif_bytes else {"0th": {}, "GPS": {}}

        datetime_raw = exif_data["0th"].get(piexif.ImageIFD.DateTime, b"Unknown")
        datetime_str = datetime_raw.decode() if isinstance(datetime_raw, bytes) else str(datetime_raw)
        date_text = format_datetime(datetime_str)

        gps = exif_data.get("GPS", {})
        lat, lon = convert_gps(gps)
        coords_text = f"{lon:.6f}E {lat:.6f}S" if lat and lon else "Unknown GPS"
        location = get_location_name(lat, lon) if lat and lon else "Address"

        # 🔥 Extract folder name from image path
        folder_name = os.path.basename(os.path.dirname(image_path))
        custom1 = folder_name
        try:
            prefix, number = folder_name.split("-")
            custom2 = f"{prefix}-{int(number) + 1:03}"
        except:
            custom2 = "Custom text2"

        lines = [
            date_text,
            coords_text,
            location,
            custom1,
            custom2
        ]

        draw = ImageDraw.Draw(img)
        font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
        font = ImageFont.truetype(font_path, 32)

        margin = 20
        line_height = font.getbbox("Hg")[3] + 10
        total_height = line_height * len(lines)

        x_base = img.width - margin
        y = img.height - total_height - margin

        for line in lines:
            line_width = draw.textbbox((0, 0), line, font=font)[2]
            draw_text_with_shadow(draw, (x_base - line_width, y), line, font)
            y += line_height

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path)
        print(f"✅ {os.path.basename(image_path)} saved to {output_path}")
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