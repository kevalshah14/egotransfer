#!/usr/bin/env python3
"""
Video-to-Robot Processing System - Main Entry Point
=================================================
Production-level FastAPI application for processing videos with hand tracking
and controlling robots. This is the main file to run the application.

Usage:
    python main.py                    # Development mode
    uvicorn main:app --host 0.0.0.0   # Production mode

Environment Variables:
    GEMINI_API_KEY: Google Gemini API key for AI analysis
    HOST: Server host (default: 0.0.0.0)
    PORT: Server port (default: 8000)
    LOG_LEVEL: Logging level (default: info)
    RELOAD: Enable auto-reload in development (default: false)
"""

import os
import sys
import logging
from pathlib import Path

# Configure OpenCV to run in headless mode (before any cv2 imports)
os.environ['OPENCV_VIDEOIO_PRIORITY_MSMF'] = '0'
os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import uvicorn
    try:
        from .app import create_app
    except ImportError:
        from app import create_app
except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    print("Please install dependencies:")
    print("  uv sync")
    print("  or")
    print("  pip install -r requirements.txt")
    sys.exit(1)

# Configure logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'info').lower()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print application banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║    🎥 VIDEO-TO-ROBOT PROCESSING SYSTEM                      ║
    ║                                                              ║
    ║    Production-level FastAPI application for:                ║
    ║    • Hand tracking with MANO points                         ║
    ║    • AI-powered video analysis                              ║
    ║    • Robot control and motion copying                       ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_environment():
    """Check environment setup and dependencies."""
    issues = []
    
    # Check for Gemini API key
    if not os.getenv('GEMINI_API_KEY'):
        issues.append("⚠️  GEMINI_API_KEY not set (AI analysis will be disabled)")
    
    # Check required directories
    required_dirs = ['uploads', 'processed', 'feedback', 'logs']
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            logger.info(f"Created directory: {dir_name}")
    
    # Check if robot modules are available
    try:
        from pydobot import Dobot
        logger.info("✅ Robot control modules available")
    except ImportError:
        issues.append("⚠️  Robot control modules not found (robot features will be limited)")
    
    # Check if hand processing modules are available
    try:
        import mediapipe as mp
        import cv2
        logger.info("✅ Hand processing modules available")
    except ImportError:
        issues.append("❌ Hand processing modules not found")
    
    # Check if AI modules are available
    try:
        import google.genai as genai
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            logger.info("✅ AI processing modules available")
        else:
            issues.append("⚠️  GEMINI_API_KEY not set (AI features will be disabled)")
    except ImportError:
        issues.append("⚠️  AI processing modules not found (AI features will be disabled)")
    
    if issues:
        print("\n🔍 Environment Check Results:")
        for issue in issues:
            print(f"   {issue}")
        print()
    
    return len([i for i in issues if i.startswith("❌")]) == 0


def get_server_config():
    """Get server configuration from environment variables."""
    return {
        'host': os.getenv('HOST', '0.0.0.0'),
        'port': int(os.getenv('PORT', 8000)),
        'log_level': LOG_LEVEL,
        'reload': os.getenv('RELOAD', 'false').lower() == 'true',
        'workers': int(os.getenv('WORKERS', 1)),
        'access_log': os.getenv('ACCESS_LOG', 'true').lower() == 'true'
    }


def print_startup_info(config):
    """Print startup information."""
    print("🚀 Starting Video-to-Robot Processing System")
    print("=" * 60)
    print(f"📡 Server: http://{config['host']}:{config['port']}")
    print(f"📚 API Docs: http://{config['host']}:{config['port']}/docs")
    print(f"📖 ReDoc: http://{config['host']}:{config['port']}/redoc")
    print(f"❤️  Health Check: http://{config['host']}:{config['port']}/health")
    print("=" * 60)
    print("🎯 Available Services:")
    print("   • Hand Processing: /hand/* - MANO-style hand tracking")
    print("   • AI Analysis: /ai/* - Gemini-powered video understanding")
    print("   • Robot Control: /robot/* - Direct robot control and playback")
    print("=" * 60)
    print(f"🔧 Configuration:")
    print(f"   • Log Level: {config['log_level'].upper()}")
    print(f"   • Reload: {config['reload']}")
    print(f"   • Workers: {config['workers']}")
    print("=" * 60)
    print("⏹️  Press Ctrl+C to stop the server")
    print()


# Create FastAPI app instance for Railway/uvicorn
# This allows uvicorn to import it directly: uvicorn main:app
app = create_app()


def main():
    """Main entry point."""
    print_banner()
    
    # Check environment
    if not check_environment():
        print("❌ Critical dependencies missing. Please check the installation.")
        return 1
    
    # Get configuration
    config = get_server_config()
    
    # Print startup information
    print_startup_info(config)
    
    try:
        # Run the server
        uvicorn.run(
            app,
            host=config['host'],
            port=config['port'],
            log_level=config['log_level'],
            reload=config['reload'],
            workers=config['workers'] if not config['reload'] else 1,
            access_log=config['access_log']
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
