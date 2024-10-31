"""
Script to separate audio by speaker using timestamp information from JSON.
Requires input WAV file and JSON file containing speaker segments.
Creates individual WAV files for each speaker with silence during other speakers' segments.
"""

import json
from pydub import AudioSegment
from pathlib import Path
import datetime
import sys
import argparse

# Check Python version
if sys.version_info < (3, 11):
    raise RuntimeError("This script requires Python 3.11 or higher")

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
        description='Separate audio by speaker using diarization data.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Example usage:
  python speaker-splitter.py input.wav diarization.json
  
The script will:
1. Read the input WAV file and diarization JSON
2. Create separate WAV files for each speaker
3. Place files in a 'speaker_outputs' directory

Output files will be named:
- speaker_outputs/output-audio-speaker_00.wav
- speaker_outputs/output-audio-speaker_01.wav
etc.

JSON format should contain segments with:
- speaker: Speaker identifier
- start: Start time in format HH:MM:SS,MMM
- end: End time in format HH:MM:SS,MMM
        '''
    )
    
    # Add arguments
    parser.add_argument('audio_file', 
                      help='Input WAV audio file')
    parser.add_argument('json_file',
                      help='Input JSON file containing speaker diarization data')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Process the audio
    process_audio(args.audio_file, args.json_file)
    print("\nProcess completed successfully!")

if __name__ == "__main__":
    print("Audio Speaker Separation Tool")
    print("----------------------------")
    main()