#!/bin/bash
set -e

# Log file
LOGFILE=build_debug.log

echo "Starting Debug Build..." | tee $LOGFILE

# 1. Install comprehensive dependencies for Python build and Kivy
echo "Installing dependencies..." | tee -a $LOGFILE
# Note: sudo usage assumes user has passwordless sudo or will manage it. 
# Since this runs in run_command which might be non-interactive, fails if password needed.
# We will try to run without sudo if possible regardless, but apt-get needs it.
# We assume the user can run this script themselves if I fail to run it.
if [ "$EUID" -ne 0 ]; then 
  SUDO='sudo'
else
  SUDO=''
fi

$SUDO apt-get update >> $LOGFILE 2>&1
$SUDO apt-get install -y \
    build-essential git zip unzip openjdk-17-jdk python3-pip python3-venv \
    autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev \
    libtinfo6 cmake libffi-dev libssl-dev libsqlite3-dev \
    libreadline-dev libbz2-dev liblzma-dev libgdbm-dev \
    libjpeg-dev libpng-dev libfreetype6-dev \
    >> $LOGFILE 2>&1

# 2. Setup Environment
export PATH=$PATH:~/.local/bin

# 3. Install Python Dependencies
python3 -m pip install --upgrade pip setuptools packaging >> $LOGFILE 2>&1
python3 -m pip install "git+https://github.com/kivy/buildozer.git" --user >> $LOGFILE 2>&1
python3 -m pip install "cython<3" --user >> $LOGFILE 2>&1

# 4. Build
echo "Building (this may take a while)..." | tee -a $LOGFILE
# We use 'yes' to accept license if needed
yes | python3 -m buildozer android debug >> $LOGFILE 2>&1 || {
    echo "BUILD FAILED!" | tee -a $LOGFILE
    echo "Last 200 lines of log:"
    tail -n 200 $LOGFILE
    exit 1
}

echo "Build Successful!" | tee -a $LOGFILE
