# Quickstart Guide: Torah Audio-Visual Synchronization  
  
**Date**: 2026-01-31  
**Feature**: 001-torah-audio-text-sync  
  
## Prerequisites  
  
- Python 3.13+  
- UV package manager  
- FFmpeg (system dependency)  
- ~2GB RAM for video rendering  
- ~5GB disk space for processing  
  
## System Dependencies  
  
### Install FFmpeg  
  
**macOS**:  
```bash  
brew install ffmpeg  
```  
  
**Ubuntu/Debian**:  
```bash  
sudo apt-get update  
sudo apt-get install ffmpeg  
```  
  
**Verify**:  
```bash  
ffmpeg -version  
```  
  
### Install UV  
  
**macOS/Linux**:  
```bash  
curl -LsSf https://astral.sh/uv/install.sh | sh  
```  
  
**Verify**:  
```bash  
uv --version  
```  
  
## Project Setup  
  
### 1. Clone Repository  
  
```bash  
cd /path/to/upload_youtube  
git checkout 001-torah-audio-text-sync  
```  
  
### 2. Install Dependencies  
  
```bash  
# Create virtual environment and install all dependencies  
uv sync  
  
# Activate virtual environment  
source .venv/bin/activate  # macOS/Linux  
```  
  
### 3. Download Hebrew Font  
  
Download Frank Ruehl CLM or Taamey David CLM:  
  
**Option A: Frank Ruehl CLM** (recommended):  
```bash  
mkdir -p fonts  
curl -L "https://github.com/google/fonts/raw/main/ofl/frankruhl/FrankRuhl-Regular.ttf" \  
  -o fonts/FrankRuhl-Regular.ttf  
```  
  
**Option B: Taamey David CLM**:  
```bash  
mkdir -p fonts  
# Download from Culmus project or Google Fonts  
```  
  
**Verify font supports diacritics**:  
```bash  
# Font should include Unicode ranges U+05B0-U+05BD (Nikkud) and U+0591-U+05AF (T'amim)  
uv run python -c "from PIL import ImageFont; f=ImageFont.truetype('fonts/FrankRuhl-Regular.ttf', 24); print('Font loaded successfully')"  
```  
  
### 4. Prepare Audio Files  
  
Create audio directory and add files following naming convention:  
  
```bash  
mkdir -p data/audio  
```  
  
**Naming Convention**: `פרשת {Parasha} - {Aliyah} - נוסח אשכנז.{ext}`  
  
Examples:  
- `פרשת האזינו - ראשון - נוסח אשכנז.mp4`  
- `פרשת האזינו - שני - נוסח אשכנז.mp3`  
- `פרשת בראשית - ראשון - נוסח אשכנז.wav`  
  
Valid Aliyah names:  
- ראשון, שני, שלישי, רביעי, חמישי, שישי, שביעי, מפטיר, הפטרה  
  
### 5. Create Output Directories  
  
```bash  
mkdir -p output/videos  
mkdir -p output/logs  
mkdir -p output/errors  
mkdir -p data/cache  
mkdir -p data/timestamp_maps  
```  
  
## Quick Test  
  
Process a single audio file:  
  
```bash  
# Ensure you have a sample audio file  
uv run torah-sync "data/audio/פרשת האזינו - ראשון - נוסח אשכנז.mp4"  
  
# Expected output:  
# [2026-01-31 22:10:15] INFO: Processing פרשת האזינו - ראשון - נוסח אשכנז.mp4  
# [2026-01-31 22:10:16] INFO: Retrieved Hebrew text for 12 verses  
# [2026-01-31 22:11:22] INFO: Forced alignment complete (confidence: 0.96)  
# [2026-01-31 22:12:45] INFO: Video rendered successfully  
# [2026-01-31 22:12:46] INFO: Output: output/videos/פרשת האזינו - ראשון - נוסח אשכנז.mp4  
```  
  
Verify output video:  
```bash  
# Check video exists  
ls -lh output/videos/פרשת האזינו - ראשון - נוסח אשכנז.mp4  
  
# Play video (macOS)  
open output/videos/פרשת האזינו - ראשון - נוסח אשכנז.mp4  
  
# Check video properties  
ffprobe -v error -show_entries stream=width,height,codec_name \  
  output/videos/פרשת האזינו - ראשון - נוסח אשכנז.mp4  
```  
  
Expected properties:  
- Format: MP4  
- Resolution: 640x360 (360p)  
- Video codec: h264  
- Duration: Matches audio duration  
  
## Batch Processing  
  
Process all audio files in directory:  
  
```bash  
uv run torah-sync batch data/audio/  
```  
  
With parallelism:  
```bash  
uv run torah-sync batch --parallel 4 data/audio/  
```  
  
## Troubleshooting  
  
### Error: "Hebrew text source unavailable"  
  
**Cause**: Cannot reach Sefaria API  
  
**Solution**:  
```bash  
# Check internet connection  
ping www.sefaria.org  
  
# Retry with cached data (if available)  
uv run torah-sync --cache-dir data/cache data/audio/Haazinu_Rishon.mp4  
  
# Wait and retry (API might be temporarily down)  
```  
  
### Error: "Invalid filename format"  
  
**Cause**: Audio file doesn't match naming convention  
  
**Solution**:  
```bash  
# Rename file to match pattern: {Parasha}_{Aliyah}.{ext}  
mv "invalid name.mp4" "פרשת האזינו - ראשון - נוסח אשכנז.mp4"  
```  
  
### Error: "Module 'aeneas' not found"  
  
**Cause**: Dependencies not installed correctly  
  
**Solution**:  
```bash  
# Reinstall dependencies  
uv sync --force  
```  
  
### Error: "Font file not found"  
  
**Cause**: Hebrew font not installed  
  
**Solution**:  
```bash  
# Re-download font  
mkdir -p fonts  
curl -L "https://github.com/google/fonts/raw/main/ofl/frankruhl/FrankRuhl-Regular.ttf" \  
  -o fonts/FrankRuhl-Regular.ttf  
  
# Or specify custom font path  
uv run torah-sync --font /path/to/your/font.ttf data/audio/Haazinu_Rishon.mp4  
```  
  
### Error: "FFmpeg not found"  
  
**Cause**: FFmpeg not installed or not in PATH  
  
**Solution**:  
```bash  
# Install FFmpeg (see Prerequisites section)  
# Verify installation  
which ffmpeg  
```  
  
### Low alignment confidence (<0.90)  
  
**Cause**: Poor audio quality or background noise  
  
**Solution**:  
- Check audio file quality  
- Verify audio is clear speech (not music or commentary)  
- Consider manual timestamp correction  
- Check timestamp map in `data/timestamp_maps/{parasha}_{aliyah}.json`  
  
## Development Setup  
  
For contributors:  
  
```bash  
# Install development dependencies  
uv sync --all-extras  
  
# Run tests  
pytest  
  
# Run linting  
uv run ruff check .  
  
# Run type checking  
uv run mypy src/  
  
# Run pre-commit hooks  
uv run pre-commit run --all-files  
```  
  
## Configuration  
  
### Environment Variables  
  
```bash  
# Optional: Custom cache directory  
export TORAH_SYNC_CACHE_DIR=/custom/cache/path  
  
# Optional: Sefaria API base URL (for testing)  
export SEFARIA_API_URL=https://www.sefaria.org/api  
  
# Optional: Log level  
export LOG_LEVEL=DEBUG  
```  
  
### CLI Configuration File  
  
Create `~/.torah-sync.toml`:  
  
```toml  
[defaults]  
output_dir = "~/torah-videos"  
cache_dir = "~/torah-cache"  
font_path = "~/fonts/FrankRuhl-Regular.ttf"  
log_level = "INFO"  
parallel_workers = 2  
  
[video]  
resolution = "640x360"  
fps = 30  
codec = "h264"  
```  
  
## Next Steps  
  
1. **Read the spec**: [spec.md](spec.md) for full requirements  
2. **Review data model**: [data-model.md](data-model.md) for entity definitions  
3. **Check contracts**: [contracts/](contracts/) for API and CLI interfaces  
4. **Follow TDD**: Write tests before implementation  
5. **Process sample data**: Start with Haazinu Rishon and Sheni  
  
## Resources  
  
- **Sefaria API Docs**: https://developers.sefaria.org/docs/  
- **aeneas Documentation**: https://www.readbeyond.it/aeneas/  
- **moviepy Documentation**: https://zulko.github.io/moviepy/  
- **Hebrew Fonts**: https://culmus.sourceforge.io/  
- **Unicode Hebrew Ranges**:  
  - Nikkud (vowels): U+05B0–U+05BD  
  - T'amim (cantillation): U+0591–U+05AF  
  
## Support  
  
For issues or questions:  
- Check [research.md](research.md) for technical decisions  
- Review [plan.md](plan.md) for architecture overview  
- File bug reports with error logs and sample files  
  
## Configuration  
  
The application uses dynaconf for flexible configuration management.  
  
### Configuration Files  
  
**Default settings** (`settings.toml`):  
```toml  
[default]  
cache_dir = "data/cache"  
output_dir = "output/videos"  
log_level = "INFO"  
font_path = "fonts/FrankRuhl-Regular.ttf"  
  
[default.video]  
resolution = [640, 360]  
fps = 30  
codec = "h264"  
  
[default.sefaria]  
base_url = "https://www.sefaria.org/api"  
retry_attempts = 3  
cache_responses = true  
```  
  
**User overrides** (`~/.torah-sync.toml`):  
```toml  
[default]  
output_dir = "~/torah-videos"  
parallel_workers = 4  
```  
  
**Secrets** (`.secrets.toml`, gitignored):  
```toml  
[default]  
# Add any API keys or sensitive config here  
```  
  
### Configuration Priority  
  
1. CLI arguments (highest priority)  
2. Environment variables (`TORAH_SYNC_*`)  
3. User config file (`~/.torah-sync.toml`)  
4. Project config file (`settings.toml`)  
5. Defaults (lowest priority)  
  
### Environment Variables  
  
All settings can be overridden with environment variables:  
  
```bash  
export TORAH_SYNC_CACHE_DIR=/custom/cache  
export TORAH_SYNC_LOG_LEVEL=DEBUG  
export TORAH_SYNC__VIDEO__RESOLUTION="[1280, 720]"  # Note: double underscore for nested  
```  
  
## Running with UV  
  
Per project standards, all Python commands must be executed with `uv run`:  
  
```bash  
# Run the CLI  
uv run torah-sync "data/audio/פרשת האזינו - ראשון - נוסח אשכנז.mp4"  
  
# Run tests  
uv run pytest  
  
# Run linting  
uv run ruff check .  
  
# Run type checking  
uv run mypy src/  
  
# Run pre-commit hooks  
uv run pre-commit run --all-files  
```  
  
**Why uv run?**  
- Ensures correct virtual environment activation  
- Manages dependencies automatically  
- Consistent across all development environments  
- Per constitution requirement (Section VI)  
  
## Using Just Commands  
  
The project includes a `.justfile` with common commands for easier workflow management.  
  
**View all available commands**:  
```bash  
just  
```  
  
**Common workflows**:  
```bash  
# Setup project  
just setup  
  
# Process single file  
just sync "data/audio/פרשת האזינו - ראשון - נוסח אשכנז.mp4"  
  
# Batch process  
just batch data/audio/  
  
# Run tests  
just test  
  
# Run all quality checks  
just check  
  
# Clean temporary files  
just clean  
```  
  
**Development**:  
```bash  
# Install dependencies  
just install  
  
# Run linting with auto-fix  
just lint-fix  
  
# Format code  
just format  
  
# Type checking  
just types  
  
# Watch tests  
just watch  
```  
  
**Validation**:  
```bash  
# Validate audio filenames  
just validate-audio  
  
# List audio files  
just list-audio  
  
# Show video info  
just video-info output/videos/פרשת_האזינו_ראשון.mp4  
```  
  
See all commands with `just --list` or view the `.justfile` directly.  
