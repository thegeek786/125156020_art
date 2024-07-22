from dotenv import load_dotenv
load_dotenv()
import os
from flask import Flask, request, jsonify, render_template_string
from googletrans import Translator

app = Flask(__name__)
translator = Translator()

html_code = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Language Translator</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f2f5;
            margin: 0;
            padding: 0;
        }
        .container {
            width: 100%;
            max-width: 600px;
            margin: 50px auto;
            background-color: #fff;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            border-radius: 8px;
        }
        h1 {
            text-align: center;
            color: #333;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #333;
        }
        .form-group input, .form-group select {
            width: calc(100% - 22px);
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        .form-group button {
            width: 100%;
            padding: 10px;
            background-color: #007bff;
            color: #fff;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .form-group button:hover {
            background-color: #0056b3;
        }
        #response {
            margin-top: 20px;
            background-color: #e9ecef;
            padding: 10px;
            border-radius: 4px;
            white-space: pre-line;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Language Translator</h1>
        <div class="form-group">
            <label for="text">Input Text</label>
            <input type="text" id="text">
        </div>
        <div class="form-group">
            <label for="target_lang">Target Language</label>
            <select id="target_lang">
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
                <option value="hi">Hindi</option>
                <option value="ta">Tamil</option>
                <option value="te">Telugu</option>
                <option value="bho">Bhojpuri</option>
                <!-- Add more languages as needed -->
            </select>
        </div>
        <div class="form-group">
            <button onclick="translateText()">Translate</button>
        </div>
        <div id="response"></div>
    </div>

    <script>
        async function translateText() {
            var text = document.getElementById('text').value;
            var targetLang = document.getElementById('target_lang').value;
            if (text) {
                var responseDiv = document.getElementById('response');
                responseDiv.innerHTML = 'Processing...';

                var response = await fetch('/translate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ text: text, target_lang: targetLang })
                });

                var result = await response.json();
                if (result.translated_text) {
                    responseDiv.innerHTML = '<strong>Translated Text:</strong> ' + result.translated_text;
                } else {
                    responseDiv.innerHTML = 'Failed to translate the text.';
                }
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(html_code)

@app.route('/translate', methods=['POST'])
def translate():
    data = request.json
    text = data.get('text')
    target_lang = data.get('target_lang')
    if text and target_lang:
        translated = translator.translate(text, dest=target_lang)
        return jsonify({
            'translated_text': translated.text
        })
    return jsonify({'error': 'Invalid input'}), 400
