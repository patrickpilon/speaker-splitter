"""
Gradio UI for Speaker Splitter Tool
Provides a web interface for separating multi-speaker audio into individual files.

Michel-Marie MAUDET (michel.maudet@protonmail.com)
"""

import gradio as gr
import json
import tempfile
import shutil
from pathlib import Path
from pydub import AudioSegment
import sys

# Import functions from speaker_splitter
from speaker_splitter import timestamp_to_milliseconds, create_speaker_audio, process_audio

def split_speakers(audio_file, json_file):
    """
    Process audio and JSON files to split speakers.

    Args:
        audio_file: Uploaded audio file (Gradio file object)
        json_file: Uploaded JSON file (Gradio file object)

    Returns:
        tuple: (status_message, list of output file paths)
    """
    if audio_file is None or json_file is None:
        return "Error: Please upload both audio and JSON files.", []

    try:
        # Create a temporary directory for outputs
        temp_dir = tempfile.mkdtemp()

        # Get the uploaded file paths
        audio_path = audio_file.name if hasattr(audio_file, 'name') else audio_file
        json_path = json_file.name if hasattr(json_file, 'name') else json_file

        # Validate audio file format
        if not audio_path.lower().endswith('.wav'):
            return "Error: Audio file must be in WAV format.", []

        # Load and validate JSON
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                segments_data = json.load(f)
        except json.JSONDecodeError:
            return f"Error: Invalid JSON format in '{json_path}'", []

        # Validate JSON structure
        if 'segments' not in segments_data:
            return "Error: JSON file must contain 'segments' field.", []

        if not segments_data['segments']:
            return "Error: No speaker segments found in JSON file.", []

        # Load audio
        try:
            audio = AudioSegment.from_wav(audio_path)
        except Exception as e:
            return f"Error loading audio file: {str(e)}", []

        # Identify unique speakers
        speakers = set(segment['speaker'] for segment in segments_data.get('segments', []))

        if not speakers:
            return "Error: No speaker segments found in JSON file.", []

        status_msg = f"Found {len(speakers)} unique speakers: {', '.join(speakers)}\n\n"

        # Process each speaker
        output_files = []
        for speaker in speakers:
            output_path = Path(temp_dir) / f"output-audio-{speaker}.wav"
            status_msg += f"Processing speaker: {speaker}...\n"

            # Create speaker audio
            total_duration = len(audio)
            silent_audio = AudioSegment.silent(duration=total_duration)

            for segment in segments_data['segments']:
                if segment['speaker'] == speaker:
                    start_ms = timestamp_to_milliseconds(segment['start'])
                    end_ms = timestamp_to_milliseconds(segment['end'])
                    segment_audio = audio[start_ms:end_ms]
                    silent_audio = silent_audio.overlay(segment_audio, position=start_ms)

            # Export the audio
            silent_audio.export(str(output_path), format="wav")
            output_files.append(str(output_path))
            status_msg += f"Created: {output_path.name}\n"

        status_msg += f"\nProcess completed successfully!"
        return status_msg, output_files

    except Exception as e:
        return f"Error during processing: {str(e)}", []

# Create Gradio interface
with gr.Blocks(title="Speaker Splitter") as demo:
    gr.Markdown("""
    # Speaker Splitter Tool

    Separate multi-speaker audio recordings into individual speaker files using diarization data.

    ## How to use:
    1. Upload your WAV audio file
    2. Upload your JSON diarization file (from WhisperX, LinTO, etc.)
    3. Click "Split Speakers"
    4. Download the individual speaker files

    ### JSON Format Example:
    ```json
    {
      "segments": [
        {
          "speaker": "SPEAKER_00",
          "start": "00:01:57,000",
          "end": "00:01:59,000",
          "text": "Example text"
        },
        {
          "speaker": "SPEAKER_01",
          "start": "00:02:14,000",
          "end": "00:02:20,000",
          "text": "Another example"
        }
      ]
    }
    ```
    """)

    with gr.Row():
        with gr.Column():
            audio_input = gr.File(
                label="Upload Audio File (WAV)",
                file_types=[".wav"],
                type="filepath"
            )
            json_input = gr.File(
                label="Upload Diarization JSON",
                file_types=[".json"],
                type="filepath"
            )
            submit_btn = gr.Button("Split Speakers", variant="primary", size="lg")

        with gr.Column():
            status_output = gr.Textbox(
                label="Status",
                lines=10,
                interactive=False
            )
            files_output = gr.File(
                label="Download Speaker Audio Files",
                file_count="multiple"
            )

    # Set up the event handler
    submit_btn.click(
        fn=split_speakers,
        inputs=[audio_input, json_input],
        outputs=[status_output, files_output]
    )

    gr.Markdown("""
    ---

    **Note**: This tool preserves original timing and duration. Each output file has the same length as the input,
    with silence during segments where the speaker is not talking.

    Created by Michel-Marie MAUDET
    """)

if __name__ == "__main__":
    demo.launch()
