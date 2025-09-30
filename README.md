# Video-to-Robot Motion Copying System

A comprehensive Python application that enables both real-time hand gesture control and video-based motion copying for Dobot robotic arms using computer vision, MediaPipe hand tracking, and AI analysis.

## Overview

This project provides two main capabilities:
1. **Real-time Control**: Control a Dobot robotic arm using live hand gestures captured through your webcam
2. **Video-to-Robot Motion Copying**: Upload a video, extract hand movements with MANO-style points, and replay those movements on the robot

## Features

### Real-time Hand Control
- **3D Position Control**: Control X, Y, and Z axes using hand gestures
- **Gripper Control**: Open/close gripper by opening/closing your hand
- **Automatic Homing**: Robot moves to home position before operation
- **Real-time Visual Feedback**: Live camera feed with hand tracking visualization
- **Smooth Movement**: Built-in smoothing algorithms to reduce jitter
- **Safety Ranges**: Configurable movement limits for safe operation

### Video Processing Pipeline
- **Hand Tracking**: Extract 21 MANO-style hand landmarks per hand
- **Color Coding**: Right hand displayed in red, left hand in green
- **AI Analysis**: Gemini AI provides task understanding and movement insights
- **Robot Conversion**: Convert hand positions to robot-compatible coordinates
- **Playback Control**: Replay recorded movements at different speeds with looping
- **Web Interface**: User-friendly upload and processing interface

## System Architecture

```
Video Upload → Hand Tracking → MANO Points → Position Conversion → Robot Playback
      ↓              ↓             ↓               ↓                  ↓
   Web UI     Color-coded     AI Analysis    Robot Commands    Motion Copying
            Video Output
```

## Requirements

- Python 3.12
- Dobot robotic arm (connected via USB)
- Webcam (for real-time control)
- Google Gemini API key (for AI analysis)
- macOS, Linux, or Windows

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd DobotControl
```

2. Install dependencies using uv:
```bash
uv sync
```

Or using pip:
```bash
pip install -r requirements.txt
```

3. Install the correct Google GenAI package:
```bash
pip install -q -U google-genai
```

4. Set up environment variables:
```bash
echo "GEMINI_API_KEY=your_gemini_api_key_here" > .env
```

## Dependencies

- `pydobot>=1.3.2` - Dobot robot control library
- `opencv-python>=4.8.0` - Computer vision and camera handling
- `mediapipe>=0.10.0` - Hand tracking and gesture recognition
- `numpy>=1.24.0` - Numerical computations
- `google-genai>=1.38.0` - AI video analysis (correct package: `from google import genai`)
- `flask>=2.3.0` - Web interface
- `python-dotenv>=1.0.0` - Environment variable management

## Usage Options

### Option 1: Production FastAPI Server (Recommended)

Start the production server:
```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000 in your browser for:
- Production-level FastAPI application
- Modern, responsive web interface  
- Automatic API documentation at `/docs`
- High-performance async processing
- Real-time job status updates
- RESTful API endpoints organized by service
- Upload videos (MP4, AVI, MOV, MKV)
- Download processed files
- Robot control via API

### Option 2: Flask Web Interface (Alternative)

Start the Flask web interface:
```bash
python web_interface.py
```

Then open http://localhost:5000 in your browser to:
- Upload videos (MP4, AVI, MOV, MKV)
- Choose target hand for robot control
- Enable/disable AI analysis
- Download processed files
- Monitor processing progress

### Option 3: Command Line Interface

Process a video directly:
```bash
# Basic processing
python video_to_robot_flow.py your_video.mp4

# Specify target hand and options
python video_processor.py your_video.mp4 left no-ai

# Interactive mode
python video_to_robot_flow.py
```

### Option 4: Real-time Hand Control

For live hand gesture control:
```bash
python Hand_to_robot.py
```

## Hand Gesture Controls

### Position Control
- **Left/Right Wrist Movement** → Robot moves Left/Right (Y-axis)
- **Up/Down Wrist Movement** → Robot moves Up/Down (Z-axis)  
- **Finger Spread/Close** → Robot moves Forward/Back (X-axis)
  - Spread fingers wide = Move Forward
  - Close fingers together = Move Back

### Gripper Control
- **Open Hand** → Open gripper
- **Closed Hand (Fist)** → Close gripper

## Video Processing Workflow

1. **Upload Video**: Use web interface or command line
2. **Hand Tracking**: System extracts 21 hand landmarks per frame
3. **Color Coding**: Right hand = Red, Left hand = Green
4. **AI Analysis**: Gemini analyzes task and provides insights
5. **Position Conversion**: Hand positions → Robot coordinates
6. **Command Generation**: Create smooth, filtered robot commands
7. **Robot Playback**: Execute movements on physical robot

## Generated Files

After processing a video named `example.mp4`, you'll get:
- `example_processed.mp4` - Video with colored hand tracking overlay
- `example_tracking.json` - Raw hand tracking data
- `example_robot_commands.json` - Robot-ready movement commands
- `example_ai_analysis.txt` - AI insights about the task

## Robot Playback Controls

When playing back recorded movements:
- **Speed Control**: Adjust playback speed (0.5x to 2.0x)
- **Loop Mode**: Repeat movements continuously
- **Manual Control**: Start, pause, stop playback
- **Preview**: View commands before execution
- **Safety**: Robot homes before playback starts

## API and Modules

### Production FastAPI API Structure

**Main Server**: `python main.py` → http://localhost:8000

#### Hand Processing Routes (`/hand/*`)
- `POST /hand/process` - Process video for hand tracking with MANO points
- `GET /hand/tracking/{job_id}` - Get hand tracking data  
- `GET /hand/landmarks/{job_id}` - Get detailed landmarks for specific frame
- `GET /hand/stats/{job_id}` - Get processing statistics
- `GET /hand/video/{job_id}` - Download processed video with overlay
- `GET /hand/commands/{job_id}` - Download robot commands (JSON/CSV)
- `POST /hand/reprocess/{job_id}` - Reprocess with different parameters

#### AI Processing Routes (`/ai/*`)
- `POST /ai/analyze` - Analyze video with Gemini AI
- `GET /ai/analysis/{job_id}` - Get AI analysis results
- `GET /ai/insights/{job_id}` - Get movement insights for robot programming
- `GET /ai/models` - Get available AI models
- `POST /ai/reanalyze/{job_id}` - Re-analyze with different parameters
- `POST /ai/feedback/{job_id}` - Submit analysis feedback

#### Robot Control Routes (`/robot/*`)  
- `POST /robot/command` - Send robot commands (connect, home, play, stop, etc.)
- `GET /robot/status` - Get current robot status
- `POST /robot/connect` - Connect to robot (convenience endpoint)
- `POST /robot/home` - Move to home position
- `POST /robot/emergency_stop` - Emergency stop
- `GET /robot/capabilities` - Get robot capabilities
- `GET /robot/position` - Get current position

#### System Routes
- `GET /health` - System health check with detailed status
- `GET /jobs` - List all processing jobs across services
- `GET /jobs/{job_id}` - Get job status
- `DELETE /jobs/{job_id}` - Delete job and files
- `GET /stats` - Get system-wide statistics
- `GET /docs` - Interactive API documentation
- `GET /redoc` - Alternative API documentation

### Application Structure
```
app/
├── main.py                    # FastAPI application factory
├── models/
│   └── schemas.py            # Pydantic models and validation
├── routes/
│   ├── hand_processing.py    # Hand tracking routes
│   ├── ai_processing.py      # AI analysis routes  
│   └── robot_control.py      # Robot control routes
└── services/
    ├── job_manager.py        # Job management and persistence
    ├── hand_service.py       # Hand processing service
    ├── ai_service.py         # AI analysis service
    └── robot_service.py      # Robot control service

frontend/
├── templates/
│   └── index.html           # Modern web interface
└── static/
    ├── style.css           # Professional styling
    └── script.js           # Interactive JavaScript

main.py                      # Production entry point
```

### Legacy Modules (Still Available)
- `video_hand_processor.py` - Hand tracking and MANO point extraction
- `robot_position_converter.py` - Convert hand positions to robot coordinates  
- `robot_playback_controller.py` - Control robot playback of recorded movements
- `video_to_robot_flow.py` - Main orchestration script
- `video_processor.py` - Enhanced processor with AI analysis
- `web_interface.py` - Flask web interface (alternative)
- `fastapi_server.py` - Original FastAPI server (deprecated)

### Usage Examples

#### FastAPI Server Usage

```python
import requests

# Upload video for processing
files = {'file': open('my_video.mp4', 'rb')}
data = {'target_hand': 'right', 'include_ai': True}
response = requests.post('http://localhost:8000/upload', files=files, data=data)
job_id = response.json()['job_id']

# Check job status
status = requests.get(f'http://localhost:8000/jobs/{job_id}').json()
print(f"Status: {status['status']}, Progress: {status['progress']}%")

# Download processed files
if status['status'] == 'completed':
    for file_type, filename in status['processed_files'].items():
        download_type = 'video' if 'video' in file_type else 'data'
        file_url = f'http://localhost:8000/download/{download_type}/{filename}'
        response = requests.get(file_url)
        with open(f'downloaded_{filename}', 'wb') as f:
            f.write(response.content)

# Control robot via API
robot_cmd = {'action': 'connect'}
requests.post('http://localhost:8000/robot/command', json=robot_cmd)

robot_cmd = {'action': 'play', 'speed': 1.0, 'loop': False, 'commands_file': 'robot_commands.json'}
requests.post('http://localhost:8000/robot/command', json=robot_cmd)
```

#### Direct Python Usage

```python
# Process video programmatically
from video_to_robot_flow import VideoToRobotFlow

flow = VideoToRobotFlow()
success = flow.process_video_file("my_video.mp4", target_hand="right")
if success:
    flow.play_on_robot(speed=1.0, loop=False)

# Custom hand tracking
from video_hand_processor import VideoHandProcessor

processor = VideoHandProcessor()
processor.process_video("input.mp4", "output.mp4", "tracking.json")
```

## Configuration

### Robot Movement Ranges
Default ranges can be modified in the code:
- X-axis (forward/back): 200-300mm
- Y-axis (left/right): -100 to 100mm  
- Z-axis (up/down): 50-250mm

### Processing Parameters
- Hand detection confidence: 0.7
- Tracking confidence: 0.5
- Movement smoothing: 3-frame window
- Minimum movement threshold: 2mm

## Troubleshooting

### Common Issues

1. **Robot not found**: Ensure Dobot is connected via USB and drivers are installed
2. **Hand tracking poor**: Ensure good lighting and clear view of hands
3. **Web interface not loading**: Check if port 5000 is available
4. **AI analysis failing**: Verify GEMINI_API_KEY is set correctly
5. **Video processing slow**: Large videos take time; monitor progress in web UI

### Error Messages
- "Could not find Dobot": Check USB connection and port permissions
- "Video file not found": Verify file path and format (MP4, AVI, MOV, MKV)
- "Processing modules not available": Check all dependencies are installed
- "File upload failed": Ensure file size is under 100MB

## Safety Considerations

- Always clear the robot workspace before playback
- Start with slow playback speeds (0.5x) for new movements
- Monitor robot during playback and be ready to emergency stop
- Ensure robot is properly homed before starting playback
- Keep hands away from robot during automated movements

## Development

### Adding New Features
1. Hand tracking: Modify `video_hand_processor.py`
2. Robot control: Update `robot_position_converter.py`
3. Web interface: Edit `web_interface.py`
4. AI analysis: Enhance prompts in `video_processor.py`

### Testing
```bash
# Test with sample video
python video_processor.py test.mp4

# Test robot connection
python robot_playback_controller.py

# Test web interface
python web_interface.py

# Test real-time hand control
python Hand_to_robot.py
```

- Always ensure the robot has sufficient clearance before operation
- The robot will automatically move to home position on startup
- Movement ranges are limited to prevent unsafe operations
- Keep hands clear of the robot arm during operation

## Troubleshooting

### Robot Connection Issues
- Ensure the Dobot is connected via USB
- Check that the correct drivers are installed
- Try different USB ports

### Camera Issues
- Ensure webcam is not being used by other applications
- Check camera permissions
- Try different camera indices (0, 1, 2, etc.)

### Hand Tracking Issues
- Ensure good lighting conditions
- Keep hand within the camera frame
- Avoid cluttered backgrounds
- Ensure hand is clearly visible

## Project Structure

```
DobotControl/
├── Hand_to_robot.py    # Main application file
├── pyproject.toml      # Project configuration and dependencies
├── README.md          # This file
└── uv.lock           # Dependency lock file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Add your license information here]

## Acknowledgments

- Dobot for the robotic arm hardware
- MediaPipe team for hand tracking capabilities
- OpenCV community for computer vision tools
