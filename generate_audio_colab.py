# Chinese App — Piper TTS audio regeneration
# Voice: zh_CN-chaowen-medium (CC0 dataset — fully open, no attribution needed)
#
# HOW TO RUN:
#   1. Go to https://colab.research.google.com and open a new notebook
#   2. Paste this entire file into a single code cell, or split at each "# %%" line
#   3. Run top to bottom — it will ask you to upload index.html once
#   4. At the end it downloads audio.zip (~50–80 MB)
#   5. Unzip it and replace your "Chinese App/audio/" folder with the contents
#
# One-time only. If it stops partway, re-run — it skips already-finished files.
# Expected runtime: ~25–35 minutes on Colab free tier.

# %% ── 1. Install dependencies ────────────────────────────────────────────────

import subprocess, sys

subprocess.run(["apt-get", "install", "-q", "-y", "ffmpeg"], check=True)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "tqdm", "huggingface_hub"], check=True)
print("Dependencies ready.")

# %% ── 2. Download Piper binary (Linux x86_64) ────────────────────────────────

import os
from pathlib import Path

PIPER_RELEASE = "2023.11.14-2"
PIPER_TAR = "piper_linux_x86_64.tar.gz"
PIPER_URL = f"https://github.com/rhasspy/piper/releases/download/{PIPER_RELEASE}/{PIPER_TAR}"

if not Path("piper/piper").exists():
    subprocess.run(["wget", "-q", PIPER_URL], check=True)
    subprocess.run(["tar", "-xzf", PIPER_TAR], check=True)
    print("Piper downloaded.")
else:
    print("Piper already present, skipping.")

os.chmod("piper/piper", 0o755)   # ensure executable bit is set

# %% ── 3. Download chaowen voice (CC0 dataset) ────────────────────────────────

import shutil
from huggingface_hub import hf_hub_download

VOICE = "zh_CN-chaowen-medium"
HF_REPO = "rhasspy/piper-voices"
HF_DIR = "zh/zh_CN/chaowen/medium"   # correct path inside the repo
os.makedirs("voice", exist_ok=True)

for ext in [".onnx", ".onnx.json"]:
    dest = Path(f"voice/{VOICE}{ext}")
    if not dest.exists():
        cached = hf_hub_download(
            repo_id=HF_REPO,
            filename=f"{HF_DIR}/{VOICE}{ext}",
        )
        shutil.copy(cached, dest)
        print(f"Downloaded {dest.name}")
    else:
        print(f"{dest.name} already present, skipping.")

# %% ── 4. Upload index.html from your Mac ─────────────────────────────────────
#
# When this cell runs, a "Choose Files" button appears.
# Upload:  ~/Desktop/Chinese App/index.html
#
# (index.html contains the full text→filename map used to generate all clips)

from google.colab import files as colab_files
print("Please upload your index.html …")
uploaded = colab_files.upload()
HTML_FILE = next(k for k in uploaded if k.endswith(".html"))
print(f"Got: {HTML_FILE}")

# %% ── 5. Parse the audio map ─────────────────────────────────────────────────

import re, json

raw = open(HTML_FILE, encoding="utf-8").read()
m = re.search(r"const AUDIO=(\{.*?\});", raw, re.DOTALL)
if not m:
    raise RuntimeError("Could not find AUDIO map in index.html — make sure you uploaded the right file.")

audio_map = json.loads(m.group(1))   # {"游": "00000.mp3", "鱼会游泳。": "00001.mp3", …}
print(f"Loaded {len(audio_map)} text→filename entries.")

# %% ── 6. Synthesize all clips ────────────────────────────────────────────────

import tempfile
from tqdm.auto import tqdm

os.makedirs("audio", exist_ok=True)
MODEL = f"./voice/{VOICE}.onnx"
PIPER_BIN = "./piper/piper"

# Piper bundles its own libonnxruntime.so — tell the linker where to find it
PIPER_ENV = os.environ.copy()
PIPER_ENV["LD_LIBRARY_PATH"] = f"./piper:{PIPER_ENV.get('LD_LIBRARY_PATH', '')}"

# ── Quick smoke-test before committing to 4k iterations ──────────────────────
print("Testing piper…")
with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
    _test_wav = tmp.name
_test = subprocess.run(
    [PIPER_BIN, "--model", MODEL, "--output_file", _test_wav],
    input="你好".encode("utf-8"),
    capture_output=True,
    env=PIPER_ENV,
)
if _test.returncode != 0 or not Path(_test_wav).exists():
    print("PIPER STDERR:", _test.stderr.decode(errors="replace"))
    raise RuntimeError("Piper smoke-test failed — see error above before running the full loop.")
os.unlink(_test_wav)
print("Piper OK.")

errors = []
skipped = 0

for text, filename in tqdm(audio_map.items(), desc="Synthesizing"):
    mp3_path = Path("audio") / filename

    if mp3_path.exists() and mp3_path.stat().st_size > 200:
        skipped += 1
        continue

    # piper: text → WAV
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name

    piper_result = subprocess.run(
        [PIPER_BIN, "--model", MODEL, "--output_file", wav_path],
        input=text.encode("utf-8"),
        capture_output=True,
        env=PIPER_ENV,
    )

    if piper_result.returncode != 0 or not Path(wav_path).exists():
        if len(errors) < 3:   # print stderr for first few failures only
            print(f"piper stderr [{filename}]:", piper_result.stderr.decode(errors="replace")[:300])
        errors.append((filename, text, "piper failed"))
        if Path(wav_path).exists():
            os.unlink(wav_path)
        continue

    # ffmpeg: WAV → MP3 (-q:a 4 ≈ 165 kbps VBR, good quality, small size)
    ffmpeg_result = subprocess.run(
        ["ffmpeg", "-y", "-i", wav_path, "-q:a", "4", str(mp3_path)],
        capture_output=True,
    )
    os.unlink(wav_path)

    if ffmpeg_result.returncode != 0 or mp3_path.stat().st_size < 200:
        errors.append((filename, text, "ffmpeg failed"))

print(f"\nDone. Skipped (already existed): {skipped}")
if errors:
    print(f"Errors ({len(errors)}):")
    for fname, txt, reason in errors[:20]:
        print(f"  {fname}  {txt!r}  — {reason}")
else:
    print("No errors — all clips generated successfully.")

# %% ── 7. Download the finished audio folder as a zip ─────────────────────────

print("Zipping audio/ …")
subprocess.run(["zip", "-q", "-r", "audio.zip", "audio/"], check=True)
size_mb = Path("audio.zip").stat().st_size / 1_048_576
print(f"audio.zip is {size_mb:.1f} MB — starting download …")
colab_files.download("audio.zip")
print("Done! Unzip and replace your 'Chinese App/audio/' folder with the contents.")
