# RemindMe - Secure & Intelligent Task Manager

**RemindMe** is a cross-platform (Android & Desktop) task management application built with privacy and efficiency in mind. It combines military-grade encryption with an AI-powered assistant to help you organize your life without compromising your data.

## 🚀 Key Features

*   **🔒 Zero-Knowledge Privacy**: All task titles and descriptions are encrypted **locally** using **AES-256 (GCM)**. Your data is readable only by you.
*   **🤖 AI Assistant**: Create tasks using natural language. Just say *"Remind me to buy milk tomorrow at 5pm"* and the AI handles the rest.
*   **📱 Cross-Platform**: Runs natively on Android (via Kivy) and Windows/Linux.
*   **🔔 Reliable Notifications**: persistent background notifications ensure you never miss a deadline.
*   **🎨 Dynamic UI**: A modern Material Design interface that adapts colors based on task priority (High/Red, Medium/Yellow, Low/Green).
*   **📊 Analytics**: Visualize your productivity with built-in charts tracking task completion rates and response times.

## 🛠️ Technology Stack

*   **Language**: Python 3.10
*   **Framework**: Kivy & KivyMD (Material Design)
*   **Database**: SQLite (Local storage)
*   **Encryption**: `cryptography` library (PBKDF2 + AES-GCM)
*   **Build Tool**: Buildozer (Python-for-Android)

## 💻 Running on Desktop (Windows/Linux)

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/RemindMe.git
    cd RemindMe
    ```

2.  **Create a Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the App**:
    ```bash
    python main.py
    ```

## 🤖 Building for Android

This project uses **Buildozer** to compile the Python code into an Android APK.

### Prerequisites (WSL/Linux)
*   Ubuntu 20.04+ (or WSL2 on Windows)
*   Java JDK 17
*   Python 3.10+
*   Git, Zip, Unzip

### One-Step Build Script
We have provided a streamlined script to handle dependencies and building:

1.  **For Physical Phones (ARM64)**:
    Ensure `buildozer.spec` has `android.archs = arm64-v8a`.
    Run:
    ```bash
    bash fix_build.sh
    ```

2.  **For BlueStacks/Emulators (x86_64)**:
    Edit `buildozer.spec` to set `android.archs = x86_64`.
    Run:
    ```bash
    bash fix_build.sh
    ```

The output APK will be located in the `bin/` directory.

## 📂 Project Structure

*   `main.py`: Entry point of the application.
*   `backend/`: Core logic (Encryption, Storage, AI, Scheduler).
*   `screens/`: UI logic for each screen (Dashboard, Create Task, etc.).
*   `utils/`: Helper functions and assets management.
*   `assets/`: Images, fonts, and resource files.

## 📄 License

This project is open-source and available for educational purposes.
