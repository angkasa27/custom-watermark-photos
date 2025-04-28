import os
from PIL import Image, ImageDraw, ImageFont
import piexif
from datetime import datetime
from datetime import datetime, timedelta
import random
import csv
import shutil

# Config
disable_rotation_for_folders = ["Photo roll meter awal","Photo roll meter akhir", "Photo situasi site sisi kanan", "Photo situasi site sisi kiri", "Photo situasi site sisi depan"]
cgk_prefix = "CGK05"

global_start_date = datetime.strptime("2025-04-23", "%Y-%m-%d")
global_end_date = datetime.strptime("2025-04-23", "%Y-%m-%d")
global_start_time = datetime.strptime("16:48", "%H:%M").time()
global_end_time = datetime.strptime("17:30", "%H:%M").time()
folder_time_span_minutes = 3

input_root = "images"
input_network_root = "images_with_network"
input_named_root = "images_ordered"
input_ordered_random_root = "images_ordered_random"

def load_folder_metadata(csv_path="folder_metadata.csv"):
    metadata = {}
    try:
        with open(csv_path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                folder = row["folder"]
                coords = []
                try:
                    coord_values = row["coords"].replace("°", "").strip().split()
                    for i in range(0, len(coord_values), 2):
                        lat_val = float(coord_values[i])
                        lon_val = float(coord_values[i + 1])
                        coords.append((lat_val, lon_val))
                except Exception as err:
                    print(f"⚠️ Failed to parse coordinates for folder {row['folder']}: {err}")
                address = row["address"]
                metadata[folder] = {
                    "coords": coords,
                    "address": address
                }
    except Exception as e:
        print("⚠️ Error loading folder metadata:", e)
    return metadata

folder_metadata = load_folder_metadata()
output_root = "output_images"

input_category_folders = []
for root in [input_root, input_network_root]:
    input_category_folders += [
        (root, d) for d in os.listdir(root)
        if os.path.isdir(os.path.join(root, d))
    ]


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

def add_watermark(image_path, output_path, folder_name, base_datetime, category):
    try:
        img = Image.open(image_path)
        # Apply random rotation before watermarking, unless category is in disable_rotation_for_folders
        if category not in disable_rotation_for_folders:
            img = img.rotate(random.choice([90, 180, 270]), expand=True)
        exif_bytes = img.info.get("exif")
        exif_data = piexif.load(exif_bytes) if exif_bytes else {"0th": {}, "Exif": {}, "GPS": {}}

        # Generate a random date in the folder's range using base_datetime and folder_time_span_minutes
        if folder_name in folder_metadata:
            random_offset = random.randint(0, folder_time_span_minutes * 60)
            random_dt = base_datetime + timedelta(seconds=random_offset)
            exif_datetime_str = random_dt.strftime("%Y:%m:%d %H:%M:%S")
            display_datetime_str = random_dt.strftime("%d %b %Y %H:%M:%S")

            encoded_date = exif_datetime_str.encode()
            exif_data["0th"][piexif.ImageIFD.DateTime] = encoded_date
            exif_data["Exif"][piexif.ExifIFD.DateTimeOriginal] = encoded_date
            exif_data["Exif"][piexif.ExifIFD.DateTimeDigitized] = encoded_date
        else:
            display_datetime_str = "Unknown Date"

        if folder_name in folder_metadata:
            coords_list = folder_metadata[folder_name].get("coords", [])
            if coords_list:
                lat, lon = coords_list[0]
            else:
                lat, lon = 0.0, 0.0
            # Randomly apply small GPS offset to about half the images
            if random.random() < 0.5:
                lat += random.uniform(-0.00001, 0.000001)
                lon += random.uniform(-0.00001, 0.000001)
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

            # Only update GPS EXIF if original EXIF GPS has both GPSLatitude and GPSLongitude
            original_gps = exif_data.get("GPS", {})
            if piexif.GPSIFD.GPSLatitude in original_gps and piexif.GPSIFD.GPSLongitude in original_gps:
                exif_data["GPS"] = {
                    piexif.GPSIFD.GPSLatitudeRef: lat_ref,
                    piexif.GPSIFD.GPSLatitude: lat_data,
                    piexif.GPSIFD.GPSLongitudeRef: lon_ref,
                    piexif.GPSIFD.GPSLongitude: lon_data,
                }
        else:
            coords_text = "Unknown GPS"
            location = "Address"

        parts = folder_name.split(" - ")
        custom1 = parts[0] if len(parts) > 0 else "Custom text1"
        custom2 = parts[1] if len(parts) > 1 else "Custom text2"

        lines = [
            display_datetime_str,
            coords_text,
            location,
            custom1,
            custom2
        ]

        draw = ImageDraw.Draw(img)
        font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
        scale_factor = 0.03  # 3% of image height
        font_size = max(16, int(img.height * scale_factor))
        font = ImageFont.truetype(font_path, font_size)

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
        print(f"✅ {os.path.basename(output_path)} with random date")
    except Exception as e:
        print(f"❌ Error processing {image_path}: {e}")

output_folders = list(folder_metadata.keys())

# Compute folder_gaps mapping each category to number of images in that folder
folder_gaps = {}
for root_path, category in input_category_folders:
    input_category_path = os.path.join(root_path, category)
    if os.path.isdir(input_category_path):
        files = [f for f in os.listdir(input_category_path) if f.lower().endswith((".jpg", ".jpeg"))]
        folder_gaps[category] = len(files)
    else:
        folder_gaps[category] = 0

recently_used_images = {}

for idx, output_folder_name in enumerate(output_folders):
    output_folder_path = os.path.join(output_root, output_folder_name)
    os.makedirs(output_folder_path, exist_ok=True)

    random_date = global_start_date + timedelta(days=random.randint(0, (global_end_date - global_start_date).days))
    start_seconds = global_start_time.hour * 3600 + global_start_time.minute * 60
    end_seconds = global_end_time.hour * 3600 + global_end_time.minute * 60
    time_seconds = random.randint(start_seconds, end_seconds)
    base_datetime = datetime.combine(random_date, datetime.min.time()) + timedelta(seconds=time_seconds)

    for root_path, category in input_category_folders:
        input_category_path = os.path.join(root_path, category)
        if not os.path.isdir(input_category_path):
            print(f"⚠️ Input category folder not found: {input_category_path}")
            continue

        # Get list of image files in this category folder
        files = [f for f in os.listdir(input_category_path) if f.lower().endswith((".jpg", ".jpeg"))]
        if not files:
            print(f"⚠️ No images found in {input_category_path}")
            continue

        if root_path == input_network_root:
            gap = folder_gaps.get(category, len(files))
            def used_keys(suffix):
                return [
                    f for f in files
                    if recently_used_images.get((category, f, suffix), -gap - 1) <= idx - gap
                ]

            eligible_net2 = used_keys("Network 2")
            eligible_net4 = used_keys("Network 4")

            for f in eligible_net2:
                if f in eligible_net4:
                    eligible_net4.remove(f)

            selected_net2 = random.choice(eligible_net2) if eligible_net2 else random.choice(files)
            selected_net4 = random.choice(eligible_net4) if eligible_net4 else (
                random.choice([f for f in files if f != selected_net2]) if len(files) > 1 else selected_net2
            )

            for suffix, selected_file in zip(["Network 2", "Network 4"], [selected_net2, selected_net4]):
                source_path = os.path.join(input_category_path, selected_file)
                extension = os.path.splitext(selected_file)[1]
                dest_filename = f"{category} ({suffix}){extension}"
                dest_path = os.path.join(output_folder_path, dest_filename)
                shutil.copy2(source_path, dest_path)
                add_watermark(dest_path, dest_path, output_folder_name, base_datetime, category)
                recently_used_images[(category, selected_file, suffix)] = idx
        else:
            # For input_root, just copy images without suffixes
            gap = folder_gaps.get(category, len(files))
            def used_keys():
                return [
                    f for f in files
                    if recently_used_images.get((category, f, "default"), -gap - 1) <= idx - gap
                ]

            eligible_files = used_keys()
            selected_file = random.choice(eligible_files) if eligible_files else random.choice(files)
            source_path = os.path.join(input_category_path, selected_file)
            extension = os.path.splitext(selected_file)[1]
            dest_filename = f"{category}{extension}"
            dest_path = os.path.join(output_folder_path, dest_filename)
            shutil.copy2(source_path, dest_path)
            add_watermark(dest_path, dest_path, output_folder_name, base_datetime, category)
            recently_used_images[(category, selected_file, "default")] = idx

# Handle named input folder
named_input_folders = [
    d for d in os.listdir(input_named_root)
    if os.path.isdir(os.path.join(input_named_root, d))
]

named_mapping = {}
for category in named_input_folders:
    path = os.path.join(input_named_root, category)
    images = sorted([f for f in os.listdir(path) if f.lower().endswith((".jpg", ".jpeg"))])
    named_mapping[category] = images

# Transpose and assign by order to output folders
for idx, output_folder_name in enumerate(output_folders):
    output_folder_path = os.path.join(output_root, output_folder_name)
    os.makedirs(output_folder_path, exist_ok=True)

    random_date = global_start_date + timedelta(days=random.randint(0, (global_end_date - global_start_date).days))
    start_seconds = global_start_time.hour * 3600 + global_start_time.minute * 60
    end_seconds = global_end_time.hour * 3600 + global_end_time.minute * 60
    time_seconds = random.randint(start_seconds, end_seconds)
    base_datetime = datetime.combine(random_date, datetime.min.time()) + timedelta(seconds=time_seconds)

    for category, file_list in named_mapping.items():
        if idx < len(file_list):
            filename = file_list[idx]
            source_path = os.path.join(input_named_root, category, filename)
            extension = os.path.splitext(filename)[1]
            renamed_filename = f"{category}{extension}"
            dest_path = os.path.join(output_folder_path, renamed_filename)
            shutil.copy2(source_path, dest_path)
            add_watermark(dest_path, dest_path, output_folder_name, base_datetime, category)

ordered_random_folders = [
    d for d in os.listdir(input_ordered_random_root)
    if os.path.isdir(os.path.join(input_ordered_random_root, d))
]

ordered_random_mapping = {}
for category in ordered_random_folders:
    path = os.path.join(input_ordered_random_root, category)
    images = sorted([f for f in os.listdir(path) if f.lower().endswith((".jpg", ".jpeg"))])
    for img in images:
        base_name = os.path.splitext(img)[0]  # ignore extension
        if base_name not in ordered_random_mapping:
            ordered_random_mapping[base_name] = {}
        ordered_random_mapping[base_name][category] = img

ordered_random_keys = list(ordered_random_mapping.keys())
random.shuffle(ordered_random_keys)

for idx, output_folder_name in enumerate(output_folders):
    output_folder_path = os.path.join(output_root, output_folder_name)
    os.makedirs(output_folder_path, exist_ok=True)

    random_date = global_start_date + timedelta(days=random.randint(0, (global_end_date - global_start_date).days))
    start_seconds = global_start_time.hour * 3600 + global_start_time.minute * 60
    end_seconds = global_end_time.hour * 3600 + global_end_time.minute * 60
    time_seconds = random.randint(start_seconds, end_seconds)
    base_datetime = datetime.combine(random_date, datetime.min.time()) + timedelta(seconds=time_seconds)

    if idx < len(ordered_random_keys):
        base_image_name = ordered_random_keys[idx]
        for category in ordered_random_folders:
            if category in ordered_random_mapping[base_image_name]:
                filename = ordered_random_mapping[base_image_name][category]
                source_path = os.path.join(input_ordered_random_root, category, filename)
                extension = os.path.splitext(filename)[1]
                renamed_filename = f"{category}{extension}"
                dest_path = os.path.join(output_root, output_folder_name, renamed_filename)
                shutil.copy2(source_path, dest_path)
                add_watermark(dest_path, dest_path, output_folder_name, base_datetime, category)

print("\n🔍 Validating output folders...")

all_expected_categories = {cat for _, cat in input_category_folders}.union(named_mapping.keys())

for folder_name in output_folders:
    folder_path = os.path.join(output_root, folder_name)
    existing_files = [f for f in os.listdir(folder_path) if f.lower().endswith((".jpg", ".jpeg"))]
    found_categories = set()
    for file in existing_files:
        for category in all_expected_categories:
            if category in file:
                found_categories.add(category)
                break
    missing = all_expected_categories - found_categories
    if missing:
        print(f"⚠️ Missing files in '{folder_name}': {', '.join(sorted(missing))}")
    else:
        print(f"✅ All expected files present in '{folder_name}'")