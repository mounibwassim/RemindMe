#!/bin/bash
echo "Setting up complete build environment (x86_64, Stabilized Legacy Stack)..."

# 1. Install System Dependencies (Ensure we have them)
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    git zip unzip openjdk-17-jdk python3-pip python3-venv \
    autoconf libtool pkg-config zlib1g-dev libncurses5-dev \
    libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev \
    build-essential libsqlite3-dev

# 2. Setup/Activate Venv
if [ ! -d "venv_build" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv_build
fi
source venv_build/bin/activate

# 3. Install Python Dependencies
echo "Installing/Updating Python dependencies..."
pip install --upgrade pip
pip install setuptools packaging
# Install Buildozer from master (needed for Py3.12 support)
pip install git+https://github.com/kivy/buildozer.git

# Install Legacy Cython (Compatible with p4a recipes for older Kivy/PyJNIus)
# Kivy 2.2.1 works with Cython < 3
echo "Installing Cython < 3..."
pip install "cython<3" 

# 4. HARD RESET (MANDATORY per user instruction)
echo "Executing HARD RESET (removing .buildozer and bin)..."
rm -rf .buildozer
rm -rf bin
# Clean specific platform builds if they exist
rm -rf ~/.buildozer/android/platform/build-arm64-v8a

echo "Cleaning buildozer state..."
buildozer android clean

# 5. Run Build
echo "Starting Build (arm64-v8a)..."
yes | buildozer android debug
