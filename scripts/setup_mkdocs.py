#!/usr/bin/env python3
"""
MkDocs Setup Script

This script prepares the MkDocs documentation structure by:
1. Calculating paths relative to the project root.
2. Creating necessary directories in the docs/pages folder.
3. Copying markdown files and assets from original locations.

Usage:
    python setup_mkdocs.py
    (Run from anywhere, assuming this script is in Neuroca/scripts)
"""

import os
import shutil
import sys
from pathlib import Path

# --- Path Calculation ---
# Get the absolute path to the directory containing this script (scripts)
SCRIPT_DIR = Path(__file__).parent.resolve()
# Assume the project root is one level above the script directory (Neuroca)
PROJECT_ROOT = SCRIPT_DIR.parent

if not PROJECT_ROOT.name == "Neuroca":
    print(f"Error: Expected script to be in a 'scripts' directory inside 'Neuroca'. Found project root: {PROJECT_ROOT}", file=sys.stderr)
    sys.exit(1)

# Define core directories relative to the project root
DOCS_DIR = PROJECT_ROOT / "docs"
PAGES_DIR = DOCS_DIR / "pages"
ASSETS_DIR = PAGES_DIR / "assets"
IMAGES_DEST_DIR = ASSETS_DIR / "images" # Specific destination for images

# Source locations relative to project root
LOGO_SRC_PATH = PROJECT_ROOT / "src" / "neuroca" / "assets" / "images" / "Neuroca-logo.png"
FAVICON_SRC_PATH = PROJECT_ROOT / "src" / "neuroca" / "assets" / "images" / "favicon.PNG"
BADGE_SRC_PATH = PROJECT_ROOT / "src" / "neuroca" / "assets" / "images" / "Neuroca-badge.png"
DIAGRAMS_SRC_DIR = DOCS_DIR / "architecture" / "diagrams"

# Directory mapping: source (relative to DOCS_DIR) -> destination (relative to PAGES_DIR)
DIR_MAPPING = {
    "user": "user",
    "api": "api",
    "architecture": "architecture",
    "architecture/decisions": "architecture/decisions",
    # "architecture/diagrams": "architecture/diagrams", # Handled separately
    "development": "development",
    "operations": "operations",
    "operations/runbooks": "operations/runbooks",
    "health_system": "health_system",
    "langchain": "langchain",
}

# Files to copy from DOCS_DIR to the root of PAGES_DIR
ROOT_FILES = [
    "index.md",
    # "README.md",  # Do not copy as README.md to avoid nav conflict
]

DOCS_README_SRC = DOCS_DIR / "README.md"
DOCS_README_DEST = PAGES_DIR / "docs-build-info.md"

def create_directory_structure():
    """Create the necessary directory structure in the pages folder."""
    print("Creating directory structure...")

    # Create pages directory
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ensured pages directory exists: {PAGES_DIR}")

    # Create base assets directories
    (ASSETS_DIR / "js").mkdir(parents=True, exist_ok=True)
    (ASSETS_DIR / "css").mkdir(parents=True, exist_ok=True)
    IMAGES_DEST_DIR.mkdir(parents=True, exist_ok=True) # Ensure image dest dir exists early
    print(f"Ensured assets directories exist in: {ASSETS_DIR}")

    # Create other directories based on the mapping
    for dest_subdir in DIR_MAPPING.values():
        dir_path = PAGES_DIR / dest_subdir
        dir_path.mkdir(parents=True, exist_ok=True)

def copy_markdown_files():
    """Copy markdown files from original locations to the pages directory."""
    print("\nCopying markdown files...")
    copied_count = 0
    skipped_count = 0

    # Copy root files
    for filename in ROOT_FILES:
        src_path = DOCS_DIR / filename
        dest_path = PAGES_DIR / filename
        if src_path.exists():
            try:
                shutil.copy2(src_path, dest_path)
                print(f"Copied {src_path.relative_to(PROJECT_ROOT)} to {dest_path.relative_to(PROJECT_ROOT)}")
                copied_count += 1
            except Exception as e:
                print(f"Error copying {src_path} to {dest_path}: {e}", file=sys.stderr)
                skipped_count += 1
        else:
            print(f"Warning: Source file not found, skipping: {src_path}", file=sys.stderr)
            skipped_count += 1

    # Copy docs README.md as docs-build-info.md
    if DOCS_README_SRC.exists():
        try:
            shutil.copy2(DOCS_README_SRC, DOCS_README_DEST)
            print(f"Copied {DOCS_README_SRC.relative_to(PROJECT_ROOT)} to {DOCS_README_DEST.relative_to(PROJECT_ROOT)}")
            copied_count += 1
        except Exception as e:
            print(f"Error copying {DOCS_README_SRC} to {DOCS_README_DEST}: {e}", file=sys.stderr)
            skipped_count += 1
    else:
        print(f"Warning: Source file not found, skipping: {DOCS_README_SRC}", file=sys.stderr)
        skipped_count += 1

    # Copy files from mapped directories
    for src_rel_dir, dest_rel_dir in DIR_MAPPING.items():
        src_abs_dir = DOCS_DIR / src_rel_dir
        dest_abs_dir = PAGES_DIR / dest_rel_dir

        if src_abs_dir.exists() and src_abs_dir.is_dir():
            print(f"Processing directory: {src_abs_dir.relative_to(PROJECT_ROOT)}")
            for file in src_abs_dir.glob("*.md"):
                dest_file = dest_abs_dir / file.name
                try:
                    shutil.copy2(file, dest_file)
                    copied_count += 1
                except Exception as e:
                    print(f"Error copying {file} to {dest_file}: {e}", file=sys.stderr)
                    skipped_count += 1
        elif not src_abs_dir.exists():
            print(f"Warning: Source directory not found, skipping: {src_abs_dir}", file=sys.stderr)
            skipped_count += 1

    print(f"Finished copying markdown files. Copied: {copied_count}, Skipped/Errors: {skipped_count}")

def create_placeholder_files():
    """Create placeholder JS and CSS files if they don't exist."""
    print("\nCreating placeholder asset files...")
    js_files = ["mathjax.js", "analytics.js", "consent.js"]
    css_files = ["custom.css"]
    created_count = 0

    for js_file in js_files:
        file_path = ASSETS_DIR / "js" / js_file
        if not file_path.exists():
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, "w") as f:
                    f.write(f"// Placeholder for {js_file}\n")
                print(f"Created placeholder {file_path.relative_to(PROJECT_ROOT)}")
                created_count += 1
            except Exception as e:
                 print(f"Error creating placeholder {file_path}: {e}", file=sys.stderr)

    for css_file in css_files:
        file_path = ASSETS_DIR / "css" / css_file
        if not file_path.exists():
             try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, "w") as f:
                    f.write(f"/* Placeholder for {css_file} */\n")
                print(f"Created placeholder {file_path.relative_to(PROJECT_ROOT)}")
                created_count += 1
             except Exception as e:
                 print(f"Error creating placeholder {file_path}: {e}", file=sys.stderr)

    if created_count == 0:
        print("No placeholder files needed to be created.")

def copy_assets():
    """Copy essential assets like logo, favicon, and badge."""
    print("\nCopying assets (logo, favicon, badge)...")
    copied_count = 0
    skipped_count = 0

    # Ensure destination directory exists
    IMAGES_DEST_DIR.mkdir(parents=True, exist_ok=True)

    # Copy logo
    if LOGO_SRC_PATH.exists():
        try:
            dest_path = IMAGES_DEST_DIR / LOGO_SRC_PATH.name
            shutil.copy2(LOGO_SRC_PATH, dest_path)
            print(f"Copied logo to {dest_path.relative_to(PROJECT_ROOT)}")
            copied_count += 1
        except Exception as e:
            print(f"Error copying logo from {LOGO_SRC_PATH}: {e}", file=sys.stderr)
            skipped_count += 1
    else:
        print(f"Warning: Source logo file not found, skipping: {LOGO_SRC_PATH}", file=sys.stderr)
        skipped_count += 1

    # Copy favicon
    if FAVICON_SRC_PATH.exists():
         try:
            dest_path = IMAGES_DEST_DIR / FAVICON_SRC_PATH.name
            shutil.copy2(FAVICON_SRC_PATH, dest_path)
            print(f"Copied favicon to {dest_path.relative_to(PROJECT_ROOT)}")
            copied_count += 1
         except Exception as e:
            print(f"Error copying favicon from {FAVICON_SRC_PATH}: {e}", file=sys.stderr)
            skipped_count += 1
    else:
        print(f"Warning: Source favicon file not found, skipping: {FAVICON_SRC_PATH}", file=sys.stderr)
        skipped_count += 1

    # Copy badge
    if BADGE_SRC_PATH.exists():
         try:
            dest_path = IMAGES_DEST_DIR / BADGE_SRC_PATH.name
            shutil.copy2(BADGE_SRC_PATH, dest_path)
            print(f"Copied badge to {dest_path.relative_to(PROJECT_ROOT)}")
            copied_count += 1
         except Exception as e:
            print(f"Error copying badge from {BADGE_SRC_PATH}: {e}", file=sys.stderr)
            skipped_count += 1
    else:
        print(f"Warning: Source badge file not found, skipping: {BADGE_SRC_PATH}", file=sys.stderr)
        skipped_count += 1

    # Copy diagrams
    diagrams_dest_dir = PAGES_DIR / "architecture" / "diagrams"
    if DIAGRAMS_SRC_DIR.exists() and DIAGRAMS_SRC_DIR.is_dir():
        try:
            diagrams_dest_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(DIAGRAMS_SRC_DIR, diagrams_dest_dir, dirs_exist_ok=True)
            print(f"Copied diagrams to {diagrams_dest_dir.relative_to(PROJECT_ROOT)}")
            copied_count += 1
        except Exception as e:
            print(f"Error copying diagrams from {DIAGRAMS_SRC_DIR}: {e}", file=sys.stderr)
            skipped_count += 1
    else:
        print(f"Warning: Source diagrams directory not found, skipping: {DIAGRAMS_SRC_DIR}", file=sys.stderr)

    print(f"Finished copying assets. Copied: {copied_count}, Skipped/Errors: {skipped_count}")

def main():
    """Main function to set up MkDocs."""
    print(f"Setting up MkDocs structure in: {DOCS_DIR.relative_to(PROJECT_ROOT)}")
    print(f"Project Root detected as: {PROJECT_ROOT}\n")

    create_directory_structure()
    copy_markdown_files()
    create_placeholder_files()
    copy_assets()

    print("\n-----------------------------")
    print("MkDocs setup script complete!")
    print("-----------------------------")
    print("\nTo preview the documentation site, navigate to the project root and run:")
    print(f"cd \"{PROJECT_ROOT}\"")
    print("mkdocs serve")
    print("\nOr, to build the static site:")
    print("mkdocs build")

if __name__ == "__main__":
    main()
