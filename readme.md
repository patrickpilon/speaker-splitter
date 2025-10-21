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
- Optional export of diarization results to JSON

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
# Install basic requirements
pip install -r requirements.txt

# OR install manually:
pip install pydub whisperx torch torchaudio
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

Speaker Splitter supports two modes of operation:

### Mode 1: Automatic Diarization with WhisperX (Recommended)

This mode automatically transcribes and diarizes your audio file using WhisperX:

```bash
# Basic usage with WhisperX
python speaker_splitter.py input.wav --use-whisperx --hf-token YOUR_HF_TOKEN

# Using a larger model for better accuracy
python speaker_splitter.py input.wav --use-whisperx --model large-v3 --hf-token YOUR_HF_TOKEN

# Using GPU acceleration (if available)
python speaker_splitter.py input.wav --use-whisperx --device cuda --compute-type float16 --hf-token YOUR_HF_TOKEN

# Save the diarization results to a JSON file for later use
python speaker_splitter.py input.wav --use-whisperx --hf-token YOUR_HF_TOKEN --save-json diarization.json
```

**WhisperX Options:**
- `--use-whisperx`: Enable WhisperX mode
- `--model`: Whisper model size (tiny, base, small, medium, large-v2, large-v3). Default: base
- `--device`: Computation device (cpu, cuda). Default: cpu
- `--compute-type`: Precision type (float32, float16, int8). Default: float32
- `--hf-token`: Your HuggingFace token (required for speaker diarization)
- `--save-json`: Save diarization results to a JSON file

### Mode 2: Using Pre-existing JSON Diarization File

If you already have a diarization JSON file from WhisperX, LinTO, or another tool:

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
- Simple web interface for file upload and processing and real-time processing status
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
