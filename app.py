import os
import json
import subprocess
import pandas as pd
from flask import Flask, request, render_template_string
from bs4 import BeautifulSoup
import regex
import unicodedata

# Global constants for the TTS models and configs
LANGUAGE_MODELS = {
    "da": os.path.expanduser("~/piper_models/da_DK/da_DK-talesyntese-medium.onnx"),
    "en": os.path.expanduser("~/piper_models/en_US/en_US-hfc_female-medium.onnx")
}
CONFIG_FILES = {
    "da": os.path.expanduser("~/piper_models/da_DK/da_DK-talesyntese-medium.onnx.json"),
    "en": os.path.expanduser("~/piper_models/en_US/en_US-hfc_female-medium.onnx.json")
}

# HTML template for the mapping page (inserted into the generated snippet)
HTML_TEMPLATE = r"""</style>
</head>
<body>
  <!-- 1) CSS for loader animation -->
  <style>
    .loader {
      width: 16px;
      margin-left: 10px;
      aspect-ratio: 1;
      display: inline-block;
      vertical-align: middle;
      --c: no-repeat linear-gradient(#000 0 0);
      background: 
        var(--c) 0% 50%,
        var(--c) 50% 50%,
        var(--c) 100% 50%;
      background-size: 20% 100%;
      animation: l1 1s infinite linear;
    }
    @keyframes l1 {
      0%   { background-size: 20% 100%, 20% 100%, 20% 100% }
      33%  { background-size: 20% 10%,  20% 100%, 20% 100% }
      50%  { background-size: 20% 100%, 20% 10%,  20% 100% }
      66%  { background-size: 20% 100%, 20% 100%, 20% 10%  }
      100% { background-size: 20% 100%, 20% 100%, 20% 100% }
    }
  </style>

  <script>
  document.addEventListener('DOMContentLoaded', async function() {
    // 1) Fetch the TTS mapping
    const TTS_MAPPING_URL = "PLACEHOLDER_FOR_TTS_MAPPING_URL";
    let ttsMapping = {};
    try {
      const response = await fetch(TTS_MAPPING_URL);
      ttsMapping = await response.json();
      console.log("Letter-only TTS Mapping (with NFC) loaded:", ttsMapping);
    } catch (error) {
      console.error("Failed to load TTS mapping:", error);
    }

    // 2) Loader animation functions
    function startReadingAnimation(iconElem) {
      iconElem.style.display = "none";
      const loader = document.createElement("div");
      loader.className = "loader";
      iconElem.parentNode.insertBefore(loader, iconElem.nextSibling);
      iconElem._currentAnim = loader;
    }
    function stopReadingAnimation(iconElem) {
      if (iconElem._currentAnim) {
        iconElem._currentAnim.remove();
        iconElem._currentAnim = null;
      }
      iconElem.style.display = "inline-block";
    }

    // 3) Letter-only cleanup (preserving letters and digits)
    function letterOnlyKey(rawText) {
      let s = rawText.normalize("NFC").toLowerCase();
      s = s.replace(/[^\p{L}\p{N}]/gu, "");
      return s;
    }

    // 4) Play TTS using mapped audio
    function playTTS(rawText, iconElem) {
      if (!ttsMapping) {
        console.warn("ttsMapping is empty or not loaded.");
        return;
      }
      const textKey = letterOnlyKey(rawText);
      if (ttsMapping[textKey]) {
        const audio = new Audio(ttsMapping[textKey]);
        audio.play();
        startReadingAnimation(iconElem);
        audio.onended = () => stopReadingAnimation(iconElem);
      } else {
        console.warn(`No TTS audio found for key: "${textKey}" (raw: "${rawText}")`);
      }
    }

    // 5) Insert speaker icons into target elements
    const SPEAKER_ICON_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Speaker_Icon.svg/480px-Speaker_Icon.svg.png";
    const targetClasses = [
      "text-element",
      "question-title",
      "closed-vertical-choice",
      "row-header-text",
      "battery-grid"
    ];
    const questionsContainer = document.querySelector("div.questions");
    if (!questionsContainer) {
      console.error("Questions container not found.");
      return;
    }
    targetClasses.forEach(cls => {
      const elems = questionsContainer.getElementsByClassName(cls);
      Array.from(elems).forEach(elem => {
        if (elem.classList.contains("audio-icon-added")) return;
        if (!elem.id) {
          elem.id = "elem_" + Math.random().toString(36).substr(2, 9);
        }
        const inBattery = !!elem.closest(".battery-grid");
        if (inBattery && (elem.querySelector("input") || elem.querySelector("label"))) {
          return;
        }
        const inTableCell = !!elem.closest("td");
        if (cls === "closed-vertical-choice") {
          if (elem.tagName.toLowerCase() === "label") {
            elem.style.display = "inline-flex";
            elem.style.alignItems = "center";
            const icon = document.createElement("img");
            icon.src = SPEAKER_ICON_URL;
            icon.alt = "Speaker";
            icon.style.width = "24px";
            icon.style.height = "24px";
            icon.style.marginLeft = "4px";
            icon.style.cursor = "pointer";
            icon.style.display = "inline-block";
            icon.style.verticalAlign = "middle";
            icon.addEventListener("click", function(e) {
              e.preventDefault();
              const text = elem.innerText;
              if (!text) return;
              playTTS(text, icon);
            });
            elem.appendChild(icon);
            elem.insertAdjacentHTML("afterend", "<br>");
            elem.classList.add("audio-icon-added");
          } else {
            const wrapper = document.createElement("span");
            wrapper.style.display = "inline-flex";
            wrapper.style.alignItems = "center";
            elem.parentNode.insertBefore(wrapper, elem);
            wrapper.appendChild(elem);
            const icon = document.createElement("img");
            icon.src = SPEAKER_ICON_URL;
            icon.alt = "Speaker";
            icon.style.width = "24px";
            icon.style.height = "24px";
            icon.style.marginLeft = "4px";
            icon.style.cursor = "pointer";
            icon.style.display = "inline-block";
            icon.style.verticalAlign = "middle";
            icon.addEventListener("click", function(e) {
              e.preventDefault();
              const text = elem.innerText;
              if (!text) return;
              playTTS(text, icon);
            });
            wrapper.appendChild(icon);
            wrapper.insertAdjacentHTML("afterend", "<br>");
            elem.classList.add("audio-icon-added");
          }
        } else if (!inTableCell) {
          const wrapper = document.createElement("div");
          wrapper.style.display = "inline-flex";
          wrapper.style.alignItems = "center";
          elem.parentNode.insertBefore(wrapper, elem);
          wrapper.appendChild(elem);
          const icon = document.createElement("img");
          icon.src = SPEAKER_ICON_URL;
          icon.alt = "Speaker";
          icon.style.width = "24px";
          icon.style.height = "24px";
          icon.style.marginLeft = "8px";
          icon.style.cursor = "pointer";
          icon.style.display = "inline-block";
          icon.style.verticalAlign = "middle";
          icon.addEventListener("click", function(e) {
            e.preventDefault();
            const text = elem.innerText;
            if (!text) return;
            playTTS(text, icon);
          });
          wrapper.appendChild(icon);
          elem.classList.add("audio-icon-added");
        } else {
          const icon = document.createElement("img");
          icon.src = SPEAKER_ICON_URL;
          icon.alt = "Speaker";
          icon.style.width = "24px";
          icon.style.height = "24px";
          icon.style.marginLeft = "4px";
          icon.style.cursor = "pointer";
          icon.style.display = "inline-block";
          icon.style.verticalAlign = "middle";
          icon.addEventListener("click", function(e) {
            e.preventDefault();
            const text = elem.innerText;
            if (!text) return;
            playTTS(text, icon);
          });
          elem.insertAdjacentElement("beforeend", icon);
          elem.classList.add("audio-icon-added");
        }
      });
    });
  });
  </script>
</body>
</html>
"""

# HTML form template with enhanced styling, radio buttons, and a loading indicator.
FORM_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <title>SurveyXact TTS Generator</title>
    <style>
      body {
        font-family: Arial, sans-serif;
        background: #f2f2f2;
      }
      .container {
        width: 500px;
        margin: 50px auto;
        background: #fff;
        padding: 20px 30px;
        border-radius: 8px;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
      }
      h1 {
        text-align: center;
        color: #333;
      }
      label {
        display: block;
        margin-top: 10px;
        font-weight: bold;
      }
      input[type="text"],
      input[type="file"] {
        width: 100%;
        padding: 8px;
        margin-top: 5px;
        margin-bottom: 10px;
        border: 1px solid #ccc;
        border-radius: 4px;
      }
      .radio-group {
        margin-top: 10px;
        margin-bottom: 10px;
      }
      .radio-group label {
        display: inline;
        font-weight: normal;
        margin-right: 10px;
      }
      input[type="submit"] {
        background: #007BFF;
        color: white;
        padding: 10px 15px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
      }
      input[type="submit"]:hover {
        background: #0056b3;
      }
      #loading {
        text-align: center;
        margin-top: 20px;
        font-weight: bold;
        color: #007BFF;
        display: none;
      }
    </style>
  </head>
  <body>
    <div class="container">
      <h1>SurveyXact TTS Generator</h1>
      <form id="ttsForm" method="post" enctype="multipart/form-data">
        <label for="survey_id">Survey ID:</label>
        <input type="text" id="survey_id" name="survey_id" required>
        
        <label for="excel_file">Excel File:</label>
        <input type="file" id="excel_file" name="excel_file" accept=".xlsx,.xls" required>
        
        <div class="radio-group">
          <label>TTS Generation Method:</label><br>
          <input type="radio" id="piper" name="tts_method" value="piper" checked>
          <label for="piper">Piper</label>
          <input type="radio" id="openai" name="tts_method" value="openai">
          <label for="openai">OpenAI API</label>
        </div>
        
        <div id="api_key_div" style="display: none;">
          <label for="api_key">OpenAI API Key:</label>
          <input type="text" id="api_key" name="api_key">
        </div>
        
        <input type="submit" value="Generate TTS">
      </form>
      <div id="loading">Generating TTS... please wait.</div>
    </div>
    <script>
      // Use a single change handler for all radio buttons.
      Array.from(document.getElementsByName('tts_method')).forEach(function(radio) {
        radio.addEventListener('change', function(){
          if(document.getElementById('openai').checked){
            document.getElementById('api_key_div').style.display = 'block';
          } else {
            document.getElementById('api_key_div').style.display = 'none';
          }
        });
      });
      // Ensure the correct state on page load.
      window.addEventListener('load', function() {
        if(document.getElementById('openai').checked){
          document.getElementById('api_key_div').style.display = 'block';
        } else {
          document.getElementById('api_key_div').style.display = 'none';
        }
      });
      // Show the loading message on form submission.
      document.getElementById('ttsForm').addEventListener('submit', function(){
        document.getElementById('loading').style.display = 'block';
      });
    </script>
  </body>
</html>
"""

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Replace with a secure key

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Retrieve form data
        survey_id = request.form.get("survey_id").strip()
        tts_method = request.form.get("tts_method")
        api_key = request.form.get("api_key", "").strip() if tts_method == "openai" else None

        # Ensure an Excel file was uploaded
        if "excel_file" not in request.files:
            return "No file part", 400
        excel_file = request.files["excel_file"]
        if excel_file.filename == "":
            return "No selected file", 400

        # Save the uploaded Excel file to a temporary directory
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        excel_path = os.path.join(upload_dir, excel_file.filename)
        excel_file.save(excel_path)

        try:
            df = pd.read_excel(excel_path, sheet_name="Translations")
        except Exception as e:
            return f"Failed to read Excel file: {e}", 500

        output_base = "TTS_outputs"
        os.makedirs(output_base, exist_ok=True)
        hosting_base = f"docs/{survey_id}"
        os.makedirs(hosting_base, exist_ok=True)

        tts_mapping = {}

        # Cleanup function: extract text from HTML and normalize
        def cleanup_for_tts(raw):
            txt = BeautifulSoup(raw, "html.parser").get_text()
            txt = unicodedata.normalize("NFC", txt)
            txt = txt.replace("\u00a0", " ")
            import re
            txt = re.sub(r"\s+", " ", txt)
            return txt.strip()

        # Key function: lowercase and remove non-letter/non-digit characters
        def letter_only_key(raw):
            s = unicodedata.normalize("NFC", raw)
            s = s.lower()
            s = regex.sub(r'[^\p{L}\p{N}]', '', s)
            return s

        try:
            if tts_method == "openai":
                if not api_key:
                    return "Please enter the OpenAI API key.", 400
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                for lang in LANGUAGE_MODELS.keys():
                    if lang not in df.columns:
                        continue
                    lang_folder = os.path.join(output_base, lang)
                    os.makedirs(lang_folder, exist_ok=True)
                    for i, raw_text in enumerate(df[lang].dropna()):
                        text_for_tts = cleanup_for_tts(raw_text)
                        key = letter_only_key(text_for_tts)
                        file_name = f"output_{i}.wav"
                        file_path = os.path.join(lang_folder, file_name)
                        hosted_url = f"https://asw615.github.io/surveyxact-tts/{survey_id}/{lang}/{file_name}"
                        response = client.audio.speech.create(
                            model="tts-1",
                            voice="alloy",
                            input=text_for_tts,
                            response_format="wav"
                        )
                        response.stream_to_file(file_path)
                        lang_hosting_folder = os.path.join(hosting_base, lang)
                        os.makedirs(lang_hosting_folder, exist_ok=True)
                        final_host_path = os.path.join(lang_hosting_folder, file_name)
                        os.rename(file_path, final_host_path)
                        tts_mapping[key] = hosted_url
            else:
                # Piper branch
                for lang, model_path in LANGUAGE_MODELS.items():
                    if lang not in df.columns:
                        continue
                    lang_folder = os.path.join(output_base, lang)
                    os.makedirs(lang_folder, exist_ok=True)
                    for i, raw_text in enumerate(df[lang].dropna()):
                        text_for_tts = cleanup_for_tts(raw_text)
                        key = letter_only_key(text_for_tts)
                        file_name = f"output_{i}.wav"
                        file_path = os.path.join(lang_folder, file_name)
                        hosted_url = f"https://asw615.github.io/surveyxact-tts/{survey_id}/{lang}/{file_name}"
                        cmd = [
                            "/opt/anaconda3/bin/piper",
                            "--model", model_path,
                            "--config", CONFIG_FILES[lang],
                            "--output_file", file_path
                        ]
                        subprocess.run(cmd, input=text_for_tts, text=True, check=True)
                        lang_hosting_folder = os.path.join(hosting_base, lang)
                        os.makedirs(lang_hosting_folder, exist_ok=True)
                        final_host_path = os.path.join(lang_hosting_folder, file_name)
                        os.rename(file_path, final_host_path)
                        tts_mapping[key] = hosted_url

        except Exception as e:
            return f"TTS generation failed: {e}", 500

        mapping_json_path = os.path.join(hosting_base, "tts_mapping.json")
        with open(mapping_json_path, "w", encoding="utf-8") as json_file:
            json.dump(tts_mapping, json_file, indent=4, ensure_ascii=False)

        tts_url = f"https://asw615.github.io/surveyxact-tts/{survey_id}/tts_mapping.json"
        updated_html = HTML_TEMPLATE.replace("PLACEHOLDER_FOR_TTS_MAPPING_URL", tts_url)

        result_template = """
        <!doctype html>
        <html>
          <head>
            <title>TTS Generation Complete</title>
            <style>
              body { font-family: Arial, sans-serif; background: #f2f2f2; }
              .container { width: 600px; margin: 50px auto; background: #fff; padding: 20px 30px;
                           border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
              h1 { text-align: center; color: #333; }
              textarea { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; }
              a { color: #007BFF; text-decoration: none; }
              a:hover { text-decoration: underline; }
            </style>
          </head>
          <body>
            <div class="container">
              <h1>TTS Generation Complete!</h1>
              <p>Mapping saved to: {{ mapping_json_path }}</p>
              <p>Mapping URL: <a href="{{ tts_url }}">{{ tts_url }}</a></p>
              <h2>Generated HTML Snippet:</h2>
              <textarea rows="20">{{ updated_html }}</textarea>
              <br><br>
              <a href="/">Generate another</a>
            </div>
          </body>
        </html>
        """
        return render_template_string(result_template,
                                      mapping_json_path=mapping_json_path,
                                      tts_url=tts_url,
                                      updated_html=updated_html)
    else:
        return render_template_string(FORM_TEMPLATE)

if __name__ == "__main__":
    app.run(debug=True)
