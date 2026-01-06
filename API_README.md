# CosyVoice Production Server

🎙️ Production-ready Text-to-Speech service with Web UI + REST API + Voice Cloning

## Features

- ✅ **Folder-based Voice Library** - Organized storage with individual voice folders
- 🔌 **OpenAI Compatible API** - Drop-in replacement for `/v1/audio/speech`
- 👤 **Custom Voice Management** - Upload once, use by `voice_id`
- ⚡ **Real Streaming Output** - PCM chunk-by-chunk streaming (~1.2s TTFB)
- 🖥️ **Gradio WebUI** - Easy-to-use web interface
- 🐳 **Docker Support** - One-command deployment

## Quick Start

### Local Development

```bash
# Install dependencies (in virtual environment)
source cosyenv/bin/activate
pip install -r requirements.txt

# Start both WebUI + API Server
python start_all.py

# Or start individually:
python app_local.py          # WebUI only (port 50000)
python api_server.py         # API only (port 81889)
```

### Docker Deployment

```bash
# Build and run
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f
```

## API Usage

### Create Custom Voice

```bash
# With manual text
curl -X POST http://localhost:81889/v1/voices/create \
  -F "audio=@voice.wav" \
  -F "name=MyVoice" \
  -F "text=Reference text content"

# Auto-transcribe (using ASR)
curl -X POST http://localhost:81889/v1/voices/create \
  -F "audio=@voice.wav" \
  -F "name=MyVoice"

# Response: {"voice_id": "abc12345", "name": "MyVoice", ...}
```

### Generate Speech (OpenAI-compatible)

```bash
# WAV format
curl http://localhost:81889/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello world", "voice": "abc12345"}' \
  -o output.wav

# PCM streaming (lowest latency)
curl http://localhost:81889/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello world", "voice": "abc12345", "response_format": "pcm"}' \
  -o output.pcm

# Convert PCM to WAV
ffmpeg -f s16le -ar 24000 -ac 1 -i output.pcm output.wav
```

### Voice Management

```bash
# List all voices
curl http://localhost:81889/v1/voices/custom

# Get voice details
curl http://localhost:81889/v1/voices/{voice_id}

# Delete voice
curl -X DELETE http://localhost:81889/v1/voices/{voice_id}
```

## Python Example

```python
import requests

# Create voice
with open("voice.wav", "rb") as f:
    resp = requests.post(
        "http://localhost:81889/v1/voices/create",
        files={"audio": f},
        data={"name": "MyVoice"}
    )
    voice_id = resp.json()["voice_id"]

# Generate speech
resp = requests.post(
    "http://localhost:81889/v1/audio/speech",
    json={"input": "Hello world", "voice": voice_id}
)
with open("output.wav", "wb") as f:
    f.write(resp.content)
```

## API Documentation

Interactive API docs available at:
- Swagger UI: http://localhost:81889/docs
- ReDoc: http://localhost:81889/redoc

## Ports

- **50000** - Gradio WebUI
- **81889** - FastAPI Server

## Voice Library Structure

```
custom_voices/
└── {voice_id}/
    ├── metadata.json    # Voice metadata
    └── audio.wav        # Reference audio
```

## Environment Variables

- `MODEL_DIR` - Model directory (default: `pretrained_models/Fun-CosyVoice3-0.5B`)
- `WEBUI_PORT` - WebUI port (default: `50000`)
- `API_PORT` - API server port (default: `81889`)

## Migration

If upgrading from old version, run migration:

```bash
python migrate_voices.py
```

This converts flat file structure to folder-based organization.

## License

Apache 2.0 - See LICENSE file for details

## Acknowledgments

Based on [Fun-CosyVoice3-0.5B](https://www.modelscope.cn/models/FunAudioLLM/Fun-CosyVoice3-0.5B-2512)
