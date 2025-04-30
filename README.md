# SurveyXact TTS Generator

**SurveyXact TTS Generator** is a prototype web-based tool that converts survey text from Excel files into TTS (Text-to-Speech) audio files using either the OpenAI API or Piper (an offline TTS engine). It provides a simple UI for uploading survey content and generates a mapping file and HTML snippet to embed audio into SurveyXact surveys.

---

## Features

- Upload Excel files containing multilingual survey content
- Choose between OpenAI API or Piper for TTS generation
- Generates `.wav` audio files for each text snippet
- Outputs a JSON mapping file of text-to-audio URLs
- Provides an HTML snippet for embedding audio into SurveyXact surveys
- Lightweight Flask web interface for local use

---

## Requirements

Install the following Python packages:

```bash
pip install flask pandas beautifulsoup4 regex openpyxl
```

Additionally, ensure these tools are available if using Piper:

- [Piper TTS](https://github.com/rhasspy/piper) installed locally
- Piper models stored in `~/piper_models/` as expected in the script

For OpenAI TTS support, you’ll need:

- An OpenAI API key
- Internet connection

---

## Usage

### 1. Start the web server

```bash
python app.py
```

By default, it runs at `http://127.0.0.1:5000/`.

### 2. Upload Your Excel File

- Your Excel file must include a `Translations` sheet.
- Columns should be labeled by language codes such as `en`, `da`, etc.

### 3. Select TTS Method

- **Piper**: Uses local models (no internet required).
- **OpenAI API**: Requires an API key; sends text to OpenAI for processing.

### 4. Receive Results

- The tool generates `.wav` files in `TTS_outputs/{lang}/`
- Outputs a `tts_mapping.json` in `docs/{survey_id}/`
- Provides an embeddable HTML snippet with speaker icons and autoplay capability

---

## Output Hosting

Generated audio files and `tts_mapping.json` can be hosted anywhere publicly accessible (e.g., GitHub Pages, S3, etc.). Just replace the placeholder URL in the HTML template accordingly.

---

## Folder Structure

```
uploads/             # Uploaded Excel files
TTS_outputs/         # Intermediate TTS output files
docs/{survey_id}/    # Public files for embedding (JSON + .wav)
```

---

## Contributing

This project is a prototype and not production-ready. 

---
