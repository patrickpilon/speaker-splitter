# Speaker Splitter

A Python tool to separate audio files by speaker using diarization data or automatic diarization with WhisperX. This tool can either take a WAV audio file with a JSON file containing speaker timestamps, or automatically transcribe and diarize audio using WhisperX, then creates individual WAV files for each speaker, maintaining the original timing and replacing other speakers' segments with silence.

![Speaker Splitter](/assets/images/Speaker-Splitter-workflow.png)

## Features

- **Integrated WhisperX support** for automatic transcription and speaker diarization
- Separates multi-speaker audio into individual speaker files
- Two modes of operation:
  - Manual mode: Use pre-existing JSON diarization files
  - Automatic mode: Use WhisperX for end-to-end processing
- Preserves original timing and audio quality
- Handles timestamps in HH:MM:SS,MMM format
- Creates silence during non-speaking segments
- Supports multiple speakers
- Simple command-line interface
- Web-based JSON diarization editor for manual creation and editing

## Prerequisites

- Python 3.11 or higher
- `pydub` library for audio processing
- FFmpeg (required by pydub)
- `whisperx` library for automatic diarization (optional, required for WhisperX mode)
- PyTorch (required for WhisperX mode)
- HuggingFace account and token (for WhisperX speaker diarization)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/mmaudet/audio-speaker-separator.git
cd audio-speaker-separator
```

2. Create and activate a Conda environment:
```bash
conda create -n audio-splitter python=3.11
conda activate audio-splitter
```

3. Install required Python packages:
```bash
pip install -r requirements.txt
```

Or manually install:
```bash
pip install pydub gradio
```

4. Install FFmpeg:
- Ubuntu/Debian:
  ```bash
  sudo apt-get install ffmpeg
  ```
- macOS:
  ```bash
  brew install ffmpeg
  ```

5. (For WhisperX mode) Get a HuggingFace token:
- Create an account at [HuggingFace](https://huggingface.co)
- Get your token at [HuggingFace Settings](https://huggingface.co/settings/tokens)
- Accept the user agreement for speaker diarization at [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)

## Usage

### Option 1: Web UI (Recommended for Easy Use)

Launch the Gradio web interface for a user-friendly experience:

```bash
python app.py
```

This will start a web server and open a browser window where you can:
1. Upload your WAV audio file
2. Upload your JSON diarization file
3. Click "Split Speakers"
4. Download the individual speaker files

The web UI provides real-time status updates and easy file management.

### Option 2: Command Line Interface

The basic command format is:
```bash
python speaker_splitter.py input.wav diarization.json
```

### Input Files

1. Audio file (`input.wav`):
   - Can be in WAV format or other formats supported by WhisperX (MP3, FLAC, etc.)
   - Contains the multi-speaker audio to be separated

2. JSON file (`diarization.json`) - Optional when using `--use-whisperx`:
   - Contains speaker segments with timestamps
   - Can be generated using various diarization tools such as:
     - This tool's WhisperX integration (with `--save-json`)
     - [WhisperX](https://github.com/m-bain/whisperX) CLI
     - [LinTO](https://linto.app): an enterprise-grade conversational AI platform developed by [LINAGORA](https://www.linagora.com)
   - Format example:
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

#### Generating the JSON File with External Tools

1. Using WhisperX CLI directly:
```bash
# Install WhisperX
pip install whisperx

# Run diarization
whisperx audio.wav --diarize --hf_token YOUR_HF_TOKEN
```

2. Using LinTO:
   - Visit [LinTO Platform](https://linto.app)
   - Upload your audio file
   - Use the transcription and diarization service
   - Export the results in JSON format

Both tools provide accurate speaker diarization and transcription, with the JSON output being compatible with this tool.

### Creating JSON Files Manually

For manual creation or editing of diarization JSON files, use the included **JSON Diarization Editor** - a web-based tool with a user-friendly interface.

#### Starting the Editor

Run the editor with:
```bash
python run_editor.py
```

Or specify a custom port:
```bash
python run_editor.py 8080
```

The editor will automatically open in your default browser at `http://localhost:8000/diarization_editor.html`

Alternatively, you can open `diarization_editor.html` directly in any web browser without running the server.

#### Editor Features

- **Add/Edit Segments**: Create speaker segments with start/end timestamps and optional text
- **Validation**: Automatic validation of timestamp format (HH:MM:SS,MMM)
- **Import/Export**: Load existing JSON files for editing or export your work
- **Visual Preview**: See your segments listed in chronological order
- **JSON Preview**: Real-time preview of the generated JSON structure
- **Time Sorting**: Segments are automatically sorted by start time

#### Using the Editor

1. **Add a Segment**:
   - Enter Speaker ID (e.g., SPEAKER_00, SPEAKER_01)
   - Enter Start Time in HH:MM:SS,MMM format
   - Enter End Time in HH:MM:SS,MMM format
   - Optionally add the spoken text
   - Click "Add Segment"

2. **Edit/Delete Segments**:
   - Click "Edit" on any segment to modify it
   - Click "Delete" to remove a segment

3. **Export**:
   - Click "Export JSON" to download the diarization file
   - Use this file with the speaker_splitter.py tool

4. **Import**:
   - Click "Import JSON" to load an existing diarization file
   - Edit and re-export as needed

### Output

The script generates separate WAV files for each speaker:
- `output-audio-SPEAKER_00.wav`
- `output-audio-SPEAKER_01.wav`
- etc.

Each output file:
- Has the same duration as the input file
- Contains only the specified speaker's segments
- Contains silence during other speakers' segments
- Maintains original timing and audio quality

## Error Handling

The script includes error handling for common issues:
- Invalid input files
- Incorrect JSON format
- Missing audio file
- Invalid timestamps
- Python version verification

## Recent Updates

### v2.0 - WhisperX Integration (Latest)
- ✅ **WhisperX Integration**: Complete integration of WhisperX for automatic transcription and speaker diarization
- ✅ **Dual Mode Operation**: Support for both automatic WhisperX mode and manual JSON mode
- ✅ **Extended Audio Format Support**: Support for MP3, FLAC, and other formats via WhisperX
- ✅ **Flexible Model Selection**: Choose from multiple Whisper models (tiny to large-v3)
- ✅ **GPU Acceleration**: Optional CUDA support for faster processing
- ✅ **JSON Export**: Save diarization results for future use

## Future Developments (not planned yet)
- Cross-fade between segments to reduce abrupt transitions
- Web interface for audio file upload and processing with real-time processing status
- Speech overlap detection and handling
- Process multiple files in batch
- Docker container for easy deployment
- Enhanced integration with LinTO platform

## Contributing

Contributions are welcome! Please feel free to submit pull requests.
- Submit pull requests for any of these features
- Propose new features or improvements
- Report bugs or issues
- Share use cases and requirements

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). This license ensures that:
- You can use, modify, and distribute the software
- If you modify the software and provide it as a service over a network, you must make the source code available
- Any derivative work must also be licensed under AGPL-3.0

See the [LICENSE](https://www.gnu.org/licenses/agpl-3.0.en.html) for the full text of the license.

## Acknowledgments

- Uses `pydub` for audio processing
- Inspired by the need for clean speaker separation in multi-speaker recordings
- Thanks to the WhisperX and LinTO teams for providing excellent diarization tools
