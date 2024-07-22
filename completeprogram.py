from flask import Flask, request, jsonify, render_template_string, send_file
import os
import speech_recognition as sr
import pyttsx3
import wave
import sounddevice as sd
import threading
from googletrans import Translator

app = Flask(__name__)

# Initialize text-to-speech engine and translator
engine = pyttsx3.init()
translator = Translator()

# Global variables for recording
recording = False
audio_file = "recorded_audio.wav"
translated_audio_file = "translated_audio.wav"
stop_recording_event = threading.Event()

# HTML Template as a string
html_code = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Speech-to-Text and Translation</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f2f5;
            margin: 0;
            padding: 0;
        }
        .container {
            width: 100%;
            max-width: 800px;
            margin: 50px auto;
            background-color: #fff;
            padding: 20px;
            box-shadow: 0 0 15px rgba(0,0,0,0.1);
            border-radius: 10px;
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 20px;
        }
        .button-group {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-bottom: 20px;
        }
        .button-group button {
            background-color: #007bff;
            color: #fff;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        .button-group button:hover {
            background-color: #0056b3;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #333;
        }
        .form-group input, .form-group select, .form-group button {
            width: calc(100% - 22px);
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        .form-group button {
            background-color: #007bff;
            color: #fff;
            border: none;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        .form-group button:hover {
            background-color: #0056b3;
        }
        #response {
            margin-top: 20px;
            background-color: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            white-space: pre-line;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Speech-to-Text and Translation</h1>
        <div class="button-group">
            <button onclick="startRecording()">Start Recording</button>
            <button onclick="stopRecording()">Stop Recording</button>
            <button onclick="playAudio()">Play Audio</button>
            <button onclick="convertSpeechToText()">Convert Speech to Text</button>
        </div>
        <div class="form-group">
            <label for="text">Text for Translation</label>
            <input type="text" id="text">
            <label for="target_lang">Target Language</label>
            <select id="target_lang">
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
                <option value="hi">Hindi</option>
                <option value="ta">Tamil</option>
                <option value="te">Telugu</option>
                <option value="ar">Arabic</option>
                <!-- Add more languages as needed -->
            </select>
            <button onclick="translateText()">Translate</button>
        </div>
        <div id="response"></div>
    </div>

    <script>
        async function startRecording() {
            var response = await fetch('/start_recording', { method: 'POST' });
            var result = await response.json();
            document.getElementById('response').innerText = result.status;
        }

        async function stopRecording() {
            var response = await fetch('/stop_recording', { method: 'POST' });
            var result = await response.json();
            document.getElementById('response').innerText = result.status;
        }

        async function playAudio() {
            var response = await fetch('/play_audio', { method: 'POST' });
            if (response.ok) {
                var audio = new Audio(URL.createObjectURL(await response.blob()));
                audio.play();
            } else {
                var result = await response.json();
                document.getElementById('response').innerText = result.error;
            }
        }

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

                    // Play translated audio
                    var audioResponse = await fetch('/play_translated_audio', { method: 'POST' });
                    if (audioResponse.ok) {
                        var audio = new Audio(URL.createObjectURL(await audioResponse.blob()));
                        audio.play();
                    } else {
                        responseDiv.innerHTML += '<br>Failed to play translated audio.';
                    }
                } else {
                    responseDiv.innerHTML = 'Failed to translate the text.';
                }
            }
        }

        async function convertSpeechToText() {
            var response = await fetch('/convert_speech_to_text', { method: 'POST' });
            var result = await response.json();
            if (result.transcribed_text) {
                document.getElementById('text').value = result.transcribed_text;
                document.getElementById('response').innerText = 'Transcribed Text: ' + result.transcribed_text;
            } else {
                document.getElementById('response').innerText = result.error;
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(html_code)

@app.route('/start_recording', methods=['POST'])
def start_recording():
    global recording
    if not recording:
        recording = True
        stop_recording_event.clear()
        thread = threading.Thread(target=record_audio)
        thread.start()
        return jsonify({'status': 'Recording started'}), 200
    return jsonify({'status': 'Already recording'}), 400

@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    global recording
    if recording:
        stop_recording_event.set()  # Signal to stop recording
        recording = False
        return jsonify({'status': 'Recording stopped'}), 200
    return jsonify({'status': 'No recording in progress'}), 400

@app.route('/play_audio', methods=['POST'])
def play_audio():
    global audio_file
    if os.path.exists(audio_file):
        return send_file(audio_file, mimetype='audio/wav')
    return jsonify({'error': 'No audio file found'}), 404

@app.route('/play_translated_audio', methods=['POST'])
def play_translated_audio():
    global translated_audio_file
    if os.path.exists(translated_audio_file):
        return send_file(translated_audio_file, mimetype='audio/wav')
    return jsonify({'error': 'No translated audio file found'}), 404

@app.route('/text_to_speech', methods=['POST'])
def text_to_speech():
    text = request.json.get('text')
    if text:
        try:
            engine.save_to_file(text, audio_file)
            engine.runAndWait()
            return jsonify({'status': 'Text converted to speech'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'No text provided'}), 400

@app.route('/convert_speech_to_text', methods=['POST'])
def convert_speech_to_text():
    global audio_file
    if os.path.exists(audio_file):
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data)
                return jsonify({'transcribed_text': text}), 200
            except sr.UnknownValueError:
                return jsonify({'error': 'Speech recognition could not understand audio'}), 400
            except sr.RequestError:
                return jsonify({'error': 'Could not request results from Google Speech Recognition service'}), 500
    return jsonify({'error': 'No audio file found'}), 404

@app.route('/translate', methods=['POST'])
def translate():
    data = request.json
    text = data.get('text')
    target_lang = data.get('target_lang')
    if text and target_lang:
        try:
            # Translate text
            translated = translator.translate(text, dest=target_lang)
            translated_text = translated.text

            # Convert the translated text to speech
            engine.save_to_file(translated_text, translated_audio_file)
            engine.runAndWait()

            return jsonify({'translated_text': translated_text}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Invalid input'}), 400

def record_audio():
    global audio_file
    global stop_recording_event

    samplerate = 44100
    duration = 10  # seconds
    recording = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, dtype='int16')
    
    while not stop_recording_event.is_set():
        pass  # Wait until recording is stopped

    sd.wait()  # Wait until the recording is finished

    with wave.open(audio_file, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(recording.tobytes())

if __name__ == '__main__':
    app.run(debug=True)
