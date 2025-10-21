"""
Flask web application for speaker separation.
Provides a web interface for uploading audio and JSON files.

Michel-Marie MAUDET (michel.maudet@protonmail.com)
"""

from flask import Flask, render_template, request, send_file, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
import json
from pathlib import Path
import sys
from speaker_splitter import process_audio, timestamp_to_milliseconds, run_whisperx, convert_whisperx_to_json
import zipfile
import io
import logging

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['OUTPUT_FOLDER'] = '/tmp/outputs'

# Allowed file extensions
ALLOWED_AUDIO_EXTENSIONS = {'wav'}
ALLOWED_JSON_EXTENSIONS = {'json'}

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

def allowed_file(filename, allowed_extensions):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/')
def index():
    """Render the main upload page."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file upload and processing."""
    # Check if audio file is present (required)
    if 'audio_file' not in request.files:
        return jsonify({'error': 'Audio file is required'}), 400

    audio_file = request.files['audio_file']

    # Check if audio file is selected
    if audio_file.filename == '':
        return jsonify({'error': 'No audio file selected'}), 400

    # Validate audio file extension
    if not allowed_file(audio_file.filename, ALLOWED_AUDIO_EXTENSIONS):
        return jsonify({'error': 'Audio file must be in WAV format'}), 400

    audio_path = None
    json_path = None

    try:
        # Save uploaded audio file
        audio_filename = secure_filename(audio_file.filename)
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
        audio_file.save(audio_path)

        # Check if JSON file is provided
        json_file = request.files.get('json_file')
        use_whisperx = False

        if json_file and json_file.filename != '':
            # Manual mode: JSON file provided
            if not allowed_file(json_file.filename, ALLOWED_JSON_EXTENSIONS):
                return jsonify({'error': 'Diarization file must be in JSON format'}), 400

            json_filename = secure_filename(json_file.filename)
            json_path = os.path.join(app.config['UPLOAD_FOLDER'], json_filename)
            json_file.save(json_path)

            # Load JSON to get speaker info
            with open(json_path, 'r', encoding='utf-8') as f:
                segments_data = json.load(f)
        else:
            # Automatic mode: Use WhisperX for transcription and diarization
            use_whisperx = True
            logging.info("No JSON file provided. Running WhisperX for automatic diarization...")

            # Get WhisperX parameters from request
            model_name = request.form.get('model', 'base')
            device = request.form.get('device', 'cpu')
            compute_type = request.form.get('compute_type', 'float32')
            hf_token = request.form.get('hf_token', os.environ.get('HF_TOKEN'))

            try:
                # Run WhisperX
                whisperx_result = run_whisperx(
                    audio_path,
                    model_name=model_name,
                    device=device,
                    compute_type=compute_type,
                    hf_token=hf_token
                )

                # Convert to JSON format
                segments_data = convert_whisperx_to_json(whisperx_result)

                # Save JSON for reference
                session_id = os.path.splitext(audio_filename)[0]
                output_dir = os.path.join(app.config['OUTPUT_FOLDER'], session_id)
                os.makedirs(output_dir, exist_ok=True)
                json_path = os.path.join(output_dir, 'diarization.json')
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(segments_data, f, indent=2, ensure_ascii=False)

            except Exception as e:
                logging.error(f"WhisperX processing failed: {str(e)}")
                return jsonify({'error': f'WhisperX processing failed: {str(e)}'}), 500

        speakers = set(segment['speaker'] for segment in segments_data.get('segments', []))

        if not speakers:
            return jsonify({'error': 'No speaker segments found'}), 400

        # Create output directory for this session
        session_id = os.path.splitext(audio_filename)[0]
        output_dir = os.path.join(app.config['OUTPUT_FOLDER'], session_id)
        os.makedirs(output_dir, exist_ok=True)

        # Process audio for each speaker
        output_files = []
        for speaker in speakers:
            output_path = os.path.join(output_dir, f"output-audio-{speaker}.wav")

            # Use the existing process logic from speaker_splitter.py
            from speaker_splitter import create_speaker_audio
            create_speaker_audio(audio_path, segments_data, speaker, output_path)

            output_files.append({
                'speaker': speaker,
                'filename': f"output-audio-{speaker}.wav",
                'path': output_path
            })

        # Create a ZIP file with all outputs (including diarization JSON if WhisperX was used)
        zip_path = os.path.join(output_dir, 'separated_audio.zip')
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for output_file in output_files:
                zipf.write(output_file['path'], arcname=output_file['filename'])
            # Include diarization JSON if it was generated
            if use_whisperx and json_path and os.path.exists(json_path):
                zipf.write(json_path, arcname='diarization.json')

        return jsonify({
            'success': True,
            'message': f'Successfully processed {len(speakers)} speakers',
            'speakers': [f['speaker'] for f in output_files],
            'session_id': session_id,
            'method': 'whisperx' if use_whisperx else 'manual'
        })

    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON format'}), 400
    except Exception as e:
        logging.error(f"Processing error: {str(e)}")
        return jsonify({'error': f'Processing error: {str(e)}'}), 500
    finally:
        # Clean up uploaded files
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
        if json_path and os.path.exists(json_path) and not use_whisperx:
            # Don't delete JSON if it was generated by WhisperX (it's in output folder)
            os.remove(json_path)

@app.route('/download/<session_id>')
def download_results(session_id):
    """Download the ZIP file containing all separated audio files."""
    zip_path = os.path.join(app.config['OUTPUT_FOLDER'], session_id, 'separated_audio.zip')

    if not os.path.exists(zip_path):
        return jsonify({'error': 'Results not found'}), 404

    return send_file(zip_path, as_attachment=True, download_name='separated_audio.zip')

@app.route('/download/<session_id>/<speaker>')
def download_speaker(session_id, speaker):
    """Download a specific speaker's audio file."""
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], session_id, f"output-audio-{speaker}.wav")

    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    return send_file(file_path, as_attachment=True, download_name=f"output-audio-{speaker}.wav")

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
