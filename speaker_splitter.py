"""
Script to separate audio by speaker using timestamp information from JSON.
Requires input WAV file and JSON file containing speaker segments.
Creates individual WAV files for each speaker with silence during other speakers' segments.

Michel-Marie MAUDET (michel.maudet@protonmail.com)
"""

import json
from pydub import AudioSegment
from pathlib import Path
import datetime
import sys
import argparse
import logging
import os
import warnings

# Suppress warnings from whisperx
warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Check Python version
if sys.version_info < (3, 11):
    raise RuntimeError("This script requires Python 3.11 or higher")

def run_whisperx(audio_path, model_name="base", device="cpu", compute_type="float32", hf_token=None):
    """
    Run WhisperX on an audio file to get transcription and speaker diarization.

    Args:
        audio_path (str): Path to the audio file
        model_name (str): Whisper model to use (tiny, base, small, medium, large-v2, large-v3)
        device (str): Device to use for computation (cpu, cuda)
        compute_type (str): Compute type (float32, float16, int8)
        hf_token (str): HuggingFace token for speaker diarization (optional)

    Returns:
        dict: WhisperX results with diarization
    """
    try:
        import whisperx
        import torch
    except ImportError:
        sys.exit("Error: WhisperX is not installed. Please run: pip install whisperx")

    # Check if CUDA is available
    if device == "cuda" and not torch.cuda.is_available():
        logging.warning("CUDA is not available. Falling back to CPU.")
        device = "cpu"
        compute_type = "float32"

    print(f"Loading WhisperX model '{model_name}' on {device}...")

    # Load audio
    audio = whisperx.load_audio(audio_path)

    # Load model
    model = whisperx.load_model(model_name, device, compute_type=compute_type)

    # Transcribe
    print("Transcribing audio...")
    result = model.transcribe(audio, batch_size=16)

    # Align whisper output
    print("Aligning timestamps...")
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)

    # Perform speaker diarization
    if hf_token:
        print("Performing speaker diarization...")
        diarize_model = whisperx.DiarizationPipeline(use_auth_token=hf_token, device=device)
        diarize_segments = diarize_model(audio)
        result = whisperx.assign_word_speakers(diarize_segments, result)
    else:
        logging.warning("No HuggingFace token provided. Speaker diarization will be skipped.")
        logging.warning("To enable diarization, provide a HuggingFace token with --hf-token")

    return result

def convert_whisperx_to_json(whisperx_result):
    """
    Convert WhisperX output to the JSON format expected by the speaker splitter.

    Args:
        whisperx_result (dict): WhisperX results with diarization

    Returns:
        dict: JSON data in the expected format
    """
    segments = []

    for segment in whisperx_result.get("segments", []):
        # Convert seconds to HH:MM:SS,MMM format
        start_seconds = segment.get("start", 0)
        end_seconds = segment.get("end", 0)

        # Convert to hours, minutes, seconds, milliseconds
        start_hours = int(start_seconds // 3600)
        start_minutes = int((start_seconds % 3600) // 60)
        start_secs = start_seconds % 60
        start_str = f"{start_hours:02d}:{start_minutes:02d}:{start_secs:06.3f}".replace('.', ',')

        end_hours = int(end_seconds // 3600)
        end_minutes = int((end_seconds % 3600) // 60)
        end_secs = end_seconds % 60
        end_str = f"{end_hours:02d}:{end_minutes:02d}:{end_secs:06.3f}".replace('.', ',')

        # Get speaker if available
        speaker = segment.get("speaker", "SPEAKER_00")

        segments.append({
            "speaker": speaker,
            "start": start_str,
            "end": end_str,
            "text": segment.get("text", "")
        })

    return {"segments": segments}

def timestamp_to_milliseconds(time_str):
    """
    Convert time string in format "HH:MM:SS,mmm" to milliseconds.

    Args:
        time_str: String in format "HH:MM:SS,mmm"
    Returns:
        int: Time in milliseconds
    """
    # Replace comma with dot for proper parsing
    time_str = time_str.replace(',', '.')
    # Parse time using datetime
    try:
        time_parts = time_str.split(':')
        hours = int(time_parts[0])
        minutes = int(time_parts[1])
        seconds = float(time_parts[2])

        total_milliseconds = int((hours * 3600 + minutes * 60 + seconds) * 1000)
        return total_milliseconds
    except Exception as e:
        logging.error(f"Error parsing time string '{time_str}': {str(e)}")
        return 0

def create_speaker_audio(input_audio_path, segments_data, speaker_id, output_path):
    """
    Create an audio file for a specific speaker with silence when others are speaking.
    
    Args:
        input_audio_path (str): Path to the input audio file
        segments_data (dict): JSON data containing speech segments
        speaker_id (str): ID of the speaker to extract
        output_path (str): Path for the output file
    """
    # Load the complete audio
    print(f"Loading audio file: {input_audio_path}")
    try:
        audio = AudioSegment.from_wav(input_audio_path)
    except FileNotFoundError:
        sys.exit(f"Error: Audio file '{input_audio_path}' not found")
    except Exception as e:
        sys.exit(f"Error loading audio file: {str(e)}")
    
    total_duration = len(audio)
    
    # Create silent audio of the same duration
    silent_audio = AudioSegment.silent(duration=total_duration)

    # For each segment of the speaker, copy the corresponding audio
    print(f"Processing segments for {speaker_id}...")
    for segment in segments_data['segments']:
        if segment['speaker'] == speaker_id:
            start_ms = timestamp_to_milliseconds(segment['start'])
            end_ms = timestamp_to_milliseconds(segment['end'])
            
            # Extract the audio segment and place it at the correct position
            segment_audio = audio[start_ms:end_ms]
            silent_audio = silent_audio.overlay(segment_audio, position=start_ms)
            #tmp_voice = tmp_voice.append(segment_audio, crossfade=0)
            
    # Save the result
    print(f"Exporting audio file for {speaker_id}")
    silent_audio.export(output_path, format="wav")

def process_audio(input_audio_path, json_path):
    """
    Main function that processes the audio and creates files for each speaker.
    
    Args:
        input_audio_path (str): Path to the input audio file
        json_path (str): Path to the JSON file containing segments
    """
    print("Starting audio separation process...")
    
    # Check if input files exist
    if not Path(input_audio_path).exists():
        sys.exit(f"Error: Input audio file '{input_audio_path}' not found")
    if not Path(json_path).exists():
        sys.exit(f"Error: JSON file '{json_path}' not found")
    
    # Load JSON data
    print(f"Loading JSON data from: {json_path}")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            segments_data = json.load(f)
    except json.JSONDecodeError:
        sys.exit(f"Error: Invalid JSON format in '{json_path}'")
    except Exception as e:
        sys.exit(f"Error reading JSON file: {str(e)}")
    
    # Identify unique speakers
    speakers = set(segment['speaker'] for segment in segments_data.get('segments', []))
    if not speakers:
        sys.exit("Error: No speaker segments found in JSON file")
    
    print(f"Found {len(speakers)} unique speakers: {', '.join(speakers)}")
    
    # Process each speaker
    for speaker in speakers:
        #output_path = output_dir / f"output-audio-{speaker.lower()}.wav"
        output_path = f"output-audio-{speaker}.wav"
        print(f"\nProcessing speaker: {speaker}")
        create_speaker_audio(input_audio_path, segments_data, speaker, str(output_path))
        print(f"Successfully created: {output_path}")

def main():
    """Parse command line arguments and run the audio processing."""
    # Create argument parser
    parser = argparse.ArgumentParser(
        description='Separate audio by speaker using diarization data or WhisperX.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Example usage:

Mode 1 - Using existing JSON diarization file:
  python speaker_splitter.py input.wav diarization.json

Mode 2 - Using WhisperX for automatic diarization:
  python speaker_splitter.py input.wav --use-whisperx --hf-token YOUR_HF_TOKEN

Mode 3 - Using WhisperX with custom model:
  python speaker_splitter.py input.wav --use-whisperx --model large-v3 --device cuda --hf-token YOUR_HF_TOKEN

The script will:
1. Read the input audio file
2. Either use provided JSON or run WhisperX for diarization
3. Create separate WAV files for each speaker

Output files will be named:
- output-audio-SPEAKER_00.wav
- output-audio-SPEAKER_01.wav
etc.

For WhisperX diarization, you need a HuggingFace token.
Get one at: https://huggingface.co/settings/tokens
Then accept the terms at: https://huggingface.co/pyannote/speaker-diarization-3.1
        '''
    )

    # Add arguments
    parser.add_argument('audio_file',
                      help='Input audio file (WAV or other formats supported by WhisperX)')
    parser.add_argument('json_file', nargs='?', default=None,
                      help='Input JSON file containing speaker diarization data (optional if using --use-whisperx)')

    # WhisperX options
    parser.add_argument('--use-whisperx', action='store_true',
                      help='Use WhisperX for automatic transcription and diarization')
    parser.add_argument('--model', type=str, default='base',
                      help='WhisperX model to use (tiny, base, small, medium, large-v2, large-v3). Default: base')
    parser.add_argument('--device', type=str, default='cpu',
                      help='Device to use for computation (cpu, cuda). Default: cpu')
    parser.add_argument('--compute-type', type=str, default='float32',
                      help='Compute type (float32, float16, int8). Default: float32')
    parser.add_argument('--hf-token', type=str, default=None,
                      help='HuggingFace token for speaker diarization (required for WhisperX diarization)')
    parser.add_argument('--save-json', type=str, default=None,
                      help='Save WhisperX diarization output to JSON file')

    # Parse arguments
    args = parser.parse_args()

    # Validate arguments
    if args.use_whisperx:
        # Using WhisperX mode
        if not args.hf_token:
            logging.warning("No HuggingFace token provided. Diarization may not work properly.")
            logging.warning("Get a token at: https://huggingface.co/settings/tokens")
            logging.warning("Then accept terms at: https://huggingface.co/pyannote/speaker-diarization-3.1")

        # Run WhisperX
        whisperx_result = run_whisperx(
            args.audio_file,
            model_name=args.model,
            device=args.device,
            compute_type=args.compute_type,
            hf_token=args.hf_token
        )

        # Convert to JSON format
        segments_data = convert_whisperx_to_json(whisperx_result)

        # Save JSON if requested
        if args.save_json:
            with open(args.save_json, 'w', encoding='utf-8') as f:
                json.dump(segments_data, f, indent=2, ensure_ascii=False)
            print(f"Saved diarization data to: {args.save_json}")

        # Process audio with the generated segments
        print("\nStarting audio separation process...")

        # Check if input file exists
        if not Path(args.audio_file).exists():
            sys.exit(f"Error: Input audio file '{args.audio_file}' not found")

        # Identify unique speakers
        speakers = set(segment['speaker'] for segment in segments_data.get('segments', []))
        if not speakers:
            sys.exit("Error: No speaker segments found in diarization results")

        print(f"Found {len(speakers)} unique speakers: {', '.join(speakers)}")

        # Process each speaker
        for speaker in speakers:
            output_path = f"output-audio-{speaker}.wav"
            print(f"\nProcessing speaker: {speaker}")
            create_speaker_audio(args.audio_file, segments_data, speaker, str(output_path))
            print(f"Successfully created: {output_path}")
    else:
        # Using JSON file mode
        if not args.json_file:
            sys.exit("Error: json_file is required when not using --use-whisperx")

        # Process the audio with JSON file
        process_audio(args.audio_file, args.json_file)

    print("\nProcess completed successfully!")

if __name__ == "__main__":
    print("Audio Speaker Separation Tool")
    print("----------------------------")
    main()