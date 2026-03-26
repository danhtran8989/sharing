# split_medical_records.py
import re
from pathlib import Path
import unicodedata

def normalize_vietnamese(text: str) -> str:
    """Convert Vietnamese to UPPERCASE_SNAKE_CASE, remove numbers at start"""
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = text.upper()
    
    # Remove leading section numbers (I., II., III., 1., 2., IV., etc.)
    text = re.sub(r'^\s*(?:[IVX]+|\d+)\.?\s*', '', text).strip()
    
    # Keep only letters and spaces
    text = re.sub(r'[^A-Z\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.replace(' ', '_')


def should_skip_section(title: str) -> bool:
    """Skip the main header"""
    title_upper = title.strip().upper()
    skip_list = [
        "HỒ SƠ BỆNH ÁN",
        "HỒ SƠ BỆNH ÁN (NỘI TRÚ)",
        "HỒ SƠ BỆNH ÁN NỘI TRÚ"
    ]
    return any(skip in title_upper for skip in skip_list)


def split_medical_record_file(input_path: str):
    input_path = Path(input_path)
    if not input_path.exists():
        print(f"File not found: {input_path}")
        return

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    department = input_path.parent.name
    patient_id = input_path.stem

    output_dir = Path(f"output/{department}/{patient_id}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Split by major sections (# or ##)
    sections = re.split(r'(?=^#{1,2}\s)', content.strip(), flags=re.MULTILINE)

    saved_count = 0

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Extract the first line as title
        match = re.match(r'^#{1,2}\s*(.+?)(?:\n|$)', section, re.MULTILINE)
        if not match:
            continue

        raw_title = match.group(1).strip()

        if should_skip_section(raw_title):
            print(f"⏭️  Skipped: {raw_title}")
            continue

        # Special case for "CÁC TỜ ĐIỀU TRỊ"
        if "CÁC TỜ ĐIỀU TRỊ" in raw_title.upper():
            normalized_name = "CAC_TO_DIEU_TRI"
        else:
            normalized_name = normalize_vietnamese(raw_title)

        if not normalized_name:
            normalized_name = "UNKNOWN_SECTION"

        output_file = output_dir / f"{normalized_name}.txt"

        # FIXED: Keep only ONE header line
        # Remove duplicate header if it appears again at the start of content
        lines = section.splitlines()
        if len(lines) > 1 and lines[0].strip().startswith('#') and lines[1].strip().startswith('#'):
            # Remove the second duplicate header
            cleaned_section = '\n'.join(lines[0:1] + lines[2:])
        else:
            cleaned_section = section

        # Write with single clean header
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"## {raw_title}\n\n")
            # Write the rest of the content (without duplicate header)
            if cleaned_section.startswith(f"## {raw_title}") or cleaned_section.startswith(f"# {raw_title}"):
                # Skip the first header line since we already wrote it
                remaining = '\n'.join(cleaned_section.splitlines()[1:]).strip()
                if remaining:
                    f.write(remaining)
            else:
                f.write(cleaned_section)

        print(f"✓ Saved: {normalized_name}.txt  ←  {raw_title}")
        saved_count += 1

    print(f"\n✅ Completed! Saved {saved_count} sections.")
    print(f"Output folder: {output_dir}\n")


# ========================
# Main Execution
# ========================

if __name__ == "__main__":
    base_dir = Path("data")
    
    if not base_dir.exists():
        print("❌ Error: 'data/' folder not found!")
        exit(1)

    txt_files = list(base_dir.rglob("*.txt"))
    
    print(f"Found {len(txt_files)} .txt files.\n")

    for txt_file in txt_files:
        print(f"Processing: {txt_file}")
        split_medical_record_file(txt_file)

    print("🎉 All files processed successfully!")