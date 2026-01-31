# Feature Specification: Automated Torah Reading Audio-Visual Sync

## 1. Overview
This feature provides an automated pipeline to synchronize high-quality Torah reading audio with corresponding Hebrew text (Tikkun Korim). The system processes MP4/audio files, aligns the text at the **Pasuk (verse)** level, and generates a visual output where the current verse is highlighted in real-time.

## 2. Objectives
* **Dynamic Highlighting:** Create a "Follow the Reader" experience by highlighting the active Pasuk.
* **Aliyah Segmentation:** Each video/audio is broken into the traditional seven *Aliyot* (Rishon through Shevi'i).
* **Source Integration:** Utilize the recordings of **Yoseph Joseph Bodenhaimer** and open-source Hebrew text.

---

## 3. Data & Source Management

### 3.1 Audio Sources
* **Primary Source:** [Yoseph Joseph Bodenhaimer YouTube Channel](https://www.youtube.com/@%D7%A7%D7%A8%D7%99%D7%90%D7%94%D7%91%D7%AA%D7%95%D7%A8%D7%94%D7%9E%D7%A4%D7%99%D7%99%D7%95%D7%A1%D7%A3%D7%91%D7%95%D7%93%D7%A0%D7%94%D7%99%D7%99%D7%9E%D7%A8)
* **Format:** Support for `.mp4` (YouTube rips) and raw `.wav`/`.mp3` files.
* **Specific Example:** Parashat Haazinu (Rishon + Sheni).
there is an option to get the original audio - if it is anable to downlaod the audio from youtube

### 3.2 Text Sources (Tikkun Korim)
* **Source A (Recommended):** [Sefaria API](https://github.com/Sefaria/Sefaria-Project) (Open source, Creative Commons). Sefaria allows for easier programmatic access to vowelized text and cantillation marks (*T'amim*).
* **Source B:** [Mechon Mamre](https://mechon-mamre.org/c/ct/cu0510.htm) (Strictly for non-commercial/private use).

---

## 4. Technical Architecture

### 4.1 The Pipeline
| Phase | Action | Tooling |
| :--- | :--- | :--- |
| **Ingestion** | Extract audio from YouTube/MP4. | `yt-dlp` / `ffmpeg` |
| **Transcription** | Generate initial timestamps for Hebrew speech. | `OpenAI Whisper` (large-v3 model) |
| **Forced Alignment** | Precisely map the "Tikkun" text to audio timestamps. | `Aeneas` or `Gentle` |
| **Data Structure** | Generate a JSON map of Aliyah -> Pasuk -> Timestamp. | Python Custom Script |
| **Rendering** | Create the video with highlighted overlays. | `Manim` or `FFmpeg Filters` |

### 4.2 Aliyah Logic
each aliya is already broken down and has a single audio file
* **Sync:** If the audio file contains single Aliya, 

---

## 5. Visual Requirements
* **Text Display:** Clear, high-contrast Hebrew font (e.g., "Taamey Ashkenaz" or "Frank Ruehl").
* **Highlight Style:** * *Active Pasuk:* Bold or Background highlight (e.g., light yellow).
    * *Upcoming Text:* Lower opacity or standard black.
* **Metadata Overlay:** Display the name of the Parasha and the current Aliyah and Pasuk in the corner of the frame.

---

## 6. Implementation Roadmap

1.  **Phase 0: use sample audio **
    * use the mp4 fiels in the data folder.
    * each file is of an aliya (hazinu - frist and second Aliya)
    * Scraper to pull the specific verses for the Parasha from the web source.
2.  **Phase 2: The "Sync Engine"**
    * Use **Forced Alignment** to create a `.srt` or `.json` file containing the exact start and end time for every verse.
3.  **Phase 3: Video Generation**
    * Automate the overlay of text onto the video so that at `Time X`, `Verse Y` changes color.
4.  **Phase 4: Review**
    * Manual check to ensure the *T'amim* (cantillation) align with the highlights.
     **Phase 1: Extraction & Scraping**
    * Script to download audio from the Bodenhaimer playlist for each aliya.
    * run on the entire bible - broken down per parasha


---

> **Note on Copyright:** While the text from Mechon Mamre is excellent, ensure that the final output adheres to their "non-commercial" distribution requirements. If you plan to share this widely, Sefaria's database is the safer legal choice for open-source text.