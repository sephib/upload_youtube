# CLI Interface Contract  
  
**Date**: 2026-01-31  
**Purpose**: Define command-line interface for Torah audio-visual synchronization pipeline  
  
## Command: `torah-sync`  
  
**Description**: Main entry point for processing Torah audio files and generating synchronized videos  
  
### Synopsis  
  
```bash  
uv run torah-sync [OPTIONS] AUDIO_FILE  
uv run torah-sync batch [OPTIONS] AUDIO_DIR  
uv run torah-sync --version  
uv run torah-sync --help  
```  
  
### Arguments  
  
**`AUDIO_FILE`** (required for single mode)  
- Path to single audio file to process  
- Must match naming convention: `פרשת {Parasha} - {Aliyah} - נוסח אשכנז.{mp4|mp3|wav}`  
- Example: `פרשת האזינו - ראשון - נוסח אשכנז.mp4`  
  
**`AUDIO_DIR`** (required for batch mode)  
- Directory containing multiple audio files  
- All valid files will be processed  
- Invalid files will be skipped with warning  
  
### Options  
  
**`-o, --output DIR`**  
- Output directory for generated videos  
- Default: `./output/videos`  
- Created if doesn't exist  
  
**`--cache-dir DIR`**  
- Directory for caching timestamp maps and API responses  
- Default: `./data/cache`  
- Enables faster reprocessing  
  
**`--no-cache`**  
- Disable caching (force reprocessing)  
- Useful for testing or when audio has changed  
  
**`--font PATH`**  
- Path to Hebrew font file (.ttf or .otf)  
- Default: SBL Hebrew (bundled)  
- Must support Nikkud and T'amim  
  
**`--resolution WIDTHxHEIGHT`**  
- Video output resolution  
- Default: `640x360` (360p per spec)  
- Not recommended to change without testing text readability  
  
**`--log-level LEVEL`**  
- Logging verbosity  
- Values: DEBUG, INFO, WARNING, ERROR  
- Default: INFO  
  
**`--json`**  
- Output structured JSON to stdout (for programmatic use)  
- Suppresses human-readable progress messages  
- Error details still go to stderr  
  
**`--parallel N`**  
- Number of parallel workers for batch processing  
- Default: 1 (sequential)  
- Max: CPU count  
  
**`--retry-failed MANIFEST`**  
- Retry items from previous failed batch  
- Reads `failed_items.json` manifest  
- Skips successfully processed items  
  
**`--version`**  
- Display version information and exit  
  
**`--help`**  
- Display help message and exit  
  
### Exit Codes  
  
- **0**: Success - all items processed without errors  
- **1**: General error - see stderr for details  
- **2**: Invalid arguments - incorrect usage  
- **3**: Audio file not found or unreadable  
- **4**: Invalid filename format  
- **5**: Hebrew text source unavailable (API error)  
- **6**: Forced alignment failed  
- **7**: Video rendering failed  
- **8**: Output validation failed  
  
### Output  
  
**Standard Output (stdout)**:  
- Progress messages (unless --json specified)  
- JSON output if --json flag used  
  
**Standard Error (stderr)**:  
- Error messages with context  
- Warnings about skipped files  
- Stack traces for unexpected errors  
  
### Examples  
  
**Process single audio file**:  
```bash  
uv run torah-sync data/audio/פרשת האזינו - ראשון - נוסח אשכנז.mp4  
```  
  
**Process single file with custom output directory**:  
```bash  
uv run torah-sync -o /path/to/output data/audio/פרשת האזינו - ראשון - נוסח אשכנז.mp4  
```  
  
**Batch process entire directory**:  
```bash  
uv run torah-sync batch data/audio/  
```  
  
**Batch process with parallelism**:  
```bash  
uv run torah-sync batch --parallel 4 data/audio/  
```  
  
**Retry failed items from previous run**:  
```bash  
uv run torah-sync --retry-failed output/errors/failed_items.json data/audio/  
```  
  
**JSON output for scripting**:  
```bash  
uv run torah-sync --json data/audio/פרשת האזינו - ראשון - נוסח אשכנז.mp4 | jq '.video_path'  
```  
  
### JSON Output Format  
  
When `--json` flag is used:  
  
**Success**:  
```json  
{  
  "status": "success",  
  "audio_file": "data/audio/פרשת האזינו - ראשון - נוסח אשכנז.mp4",  
  "parasha": "Haazinu",  
  "aliyah": "Rishon",  
  "video_path": "output/videos/פרשת האזינו - ראשון - נוסח אשכנז.mp4",  
  "duration_seconds": 245.3,  
  "verse_count": 12,  
  "timestamp_map": "data/timestamp_maps/Haazinu_Rishon.json",  
  "processing_time_seconds": 87.2,  
  "alignment_confidence": 0.96  
}  
```  
  
**Error**:  
```json  
{  
  "status": "error",  
  "audio_file": "data/audio/פרשת האזינו - ראשון - נוסח אשכנז.mp4",  
  "error_code": 5,  
  "error_message": "Hebrew text source unavailable: Connection to Sefaria API failed",  
  "error_details": {  
    "exception": "httpx.ConnectError",  
    "url": "https://www.sefaria.org/api/texts/Deuteronomy.32.1"  
  }  
}  
```  
  
**Batch Summary**:  
```json  
{  
  "status": "partial",  
  "total_files": 14,  
  "successful": 12,  
  "failed": 2,  
  "skipped": 0,  
  "total_processing_time_seconds": 1245.7,  
  "failed_items": [  
    {  
      "audio_file": "data/audio/Invalid Name.mp4",  
      "error_code": 4,  
      "error_message": "Invalid filename format"  
    },  
    {  
      "audio_file": "data/audio/פרשת בראשית - ראשון - נוסח אשכנז.mp4",  
      "error_code": 5,  
      "error_message": "Hebrew text source unavailable"  
    }  
  ]  
}  
```  
  
### Error Manifest Format  
  
When batch processing fails, a manifest is written to `output/errors/failed_items.json`:  
  
```json  
{  
  "failed_at": "2026-01-31T22:15:30Z",  
  "command": "torah-sync batch data/audio/",  
  "total_attempted": 14,  
  "failed_count": 2,  
  "failed_items": [  
    {  
      "audio_file": "data/audio/Invalid Name.mp4",  
      "error_code": 4,  
      "error_message": "Invalid filename format",  
      "retry_recommended": false  
    },  
    {  
      "audio_file": "data/audio/פרשת בראשית - ראשון - נוסח אשכנז.mp4",  
      "error_code": 5,  
      "error_message": "Hebrew text source unavailable: Connection timeout",  
      "retry_recommended": true  
    }  
  ]  
}  
```  
  
### Logging Format  
  
**Console (human-readable)**:  
```  
[2026-01-31 22:10:15] INFO: Processing פרשת האזינו - ראשון - נוסח אשכנז.mp4  
[2026-01-31 22:10:16] INFO: Retrieved Hebrew text for 12 verses  
[2026-01-31 22:11:22] INFO: Forced alignment complete (confidence: 0.96)  
[2026-01-31 22:12:45] INFO: Video rendered successfully  
[2026-01-31 22:12:46] INFO: Output: output/videos/פרשת האזינו - ראשון - נוסח אשכנז.mp4  
```  
  
**JSON (structured logging)**:  
```json  
{"timestamp": "2026-01-31T22:10:15Z", "level": "INFO", "message": "Processing פרשת האזינו - ראשון - נוסח אשכנז.mp4", "audio_file": "data/audio/פרשת האזינו - ראשון - נוסח אשכנז.mp4"}  
{"timestamp": "2026-01-31T22:10:16Z", "level": "INFO", "message": "Retrieved Hebrew text", "verse_count": 12}  
{"timestamp": "2026-01-31T22:11:22Z", "level": "INFO", "message": "Forced alignment complete", "confidence": 0.96}  
{"timestamp": "2026-01-31T22:12:45Z", "level": "INFO", "message": "Video rendered successfully"}  
{"timestamp": "2026-01-31T22:12:46Z", "level": "INFO", "message": "Output", "video_path": "output/videos/פרשת האזינו - ראשון - נוסח אשכנז.mp4"}  
```  
  
## Testing Contract  
  
**Contract Tests** must verify:  
1. CLI accepts all valid argument combinations  
2. CLI rejects invalid arguments with exit code 2  
3. CLI outputs help text when --help specified  
4. CLI outputs version when --version specified  
5. JSON output conforms to schema when --json specified  
6. Exit codes match documented values  
7. Stdout/stderr separation respected (progress → stdout, errors → stderr)  
8. Batch mode generates error manifest on failures  
  
**Example Test**:  
```python  
def test_cli_invalid_filename():  
    """CLI should exit with code 4 for invalid filename"""  
    result = subprocess.run(  
        ["torah-sync", "invalid_name.mp4"],  
        capture_output=True,  
        text=True  
    )  
    assert result.returncode == 4  
    assert "Invalid filename format" in result.stderr  
```  
  
## UV Execution  
  
Per project constitution (Section VI: Dependency Management & Tooling Standards), all Python commands MUST be executed with `uv run`:  
  
```bash  
# Correct usage  
uv run torah-sync "data/audio/פרשת האזינו - ראשון - נוסח אשכנז.mp4"  
uv run torah-sync batch --parallel 4 data/audio/  
  
# Incorrect usage (will fail in proper setup)  
torah-sync data/audio/file.mp4  # Missing 'uv run'  
```  
  
**Testing with UV**:  
```python  
def test_cli_with_uv():  
    """CLI should be invoked via uv run"""  
    result = subprocess.run(  
        ["uv", "run", "torah-sync", "data/audio/פרשת האזינו - ראשון - נוסח אשכנז.mp4"],  
        capture_output=True,  
        text=True  
    )  
    assert result.returncode == 0  
```  
