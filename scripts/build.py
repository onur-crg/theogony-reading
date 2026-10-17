#!/usr/bin/env python3
"""Rebuild the public static release from the selected recorded inputs."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument('--images', action='store_true', help='Also regenerate optimized artwork from original PNGs')
args = parser.parse_args()
steps = (['optimize_site_images.py'] if args.images else []) + ['build_reader.py', 'check_site_seo.py', 'package_site.py']
for step in steps:
    subprocess.run([sys.executable, str(ROOT/'pipeline'/step)], cwd=ROOT, check=True)
subprocess.run([sys.executable, str(ROOT/'scripts/check_release.py')], cwd=ROOT, check=True)
