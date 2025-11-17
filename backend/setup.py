"""Setup file for Railway deployment."""
from setuptools import setup, find_packages

setup(
    name="dobotcontrol",
    version="0.1.0",
    python_requires=">=3.12,<3.13",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "python-multipart>=0.0.6",
        "pydobot>=1.3.2",
        "pydobot2>=0.1.0",
        "opencv-python>=4.8.0",
        "mediapipe>=0.10.0",
        "numpy>=1.24.0",
        "google-genai>=1.38.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "authlib>=1.3.0",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "httpx>=0.25.0",
    ],
)

