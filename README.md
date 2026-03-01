# RemindMe - Intelligent & Secure Mobile Task Manager

**RemindMe** is a feature-rich, cross-platform mobile application designed to organize personal tasks with a focus on data privacy and local intelligence. Built using Python and KivyMD, it leverages industry-standard encryption protocols and a local SQLite database to ensure data integrity without reliance on cloud services.

---

## 🚀 Key Features

### 🔐 No Server-Side Storage (Fully Local Encryption Model)
- **Local-First Architecture**: All data resides solely on the user's device, eliminating external attack vectors.
- **Industry-Standard Encryption**: Task details (titles, descriptions) are encrypted using **AES-256-GCM**.
- **Secure Key Derivation**: User passwords are secured using **PBKDF2-HMAC-SHA256** with **200,000 iterations**, making brute-force attacks computationally expensive.

### 🤖 AI-Powered Productivity
- **Natural Language Processing**: Tasks can be created via voice or text prompts, parsed locally to extract dates and times.
- **Privacy-Preserving Insights**: The **Audit Analytics** engine runs locally to analyze completion rates and snooze patterns, providing productivity metrics without sharing data.

### 📱 Modern & Adaptive UI
- **Dynamic Theming**: The interface programmatically adapts color schemes based on task priority levels.
- **Accessibility**: Implements high-contrast text rendering algorithms to ensure readability against dynamic background colors.
- **Cross-Platform Compatibility**: Supports Android (API Level 31 / Android 12) and Windows Desktop environments.

### 📊 Analytics & Auditing
- **Visual Dashboard**: Interactive Bar Charts visualize weekly productivity trends.
- **Audit Logging**: A local immutable log tracks all state changes (Creation, Updates, Deletions) for self-auditing.
- **Timezone Awareness**: All logged events are stored in UTC and dynamically converted to the user's local timezone (e.g., Asia/Kuala_Lumpur) for accurate reporting.

### 🔔 Robust Notification System
- **Background Service**: Uses Android's `AlarmManager` (via Plyer) to deliver exact-time notifications even when the application is inactive.
- **Desktop Integration**: Supports native Windows Toast notifications for desktop users.

---

## 🛠️ Technology Stack

- **Core Language**: Python 3.10
- **UI Framework**: Kivy & KivyMD (Material Design)
- **Database**: SQLite (configured with Write-Ahead Logging and thread-safety mechanisms)
- **Cryptography**: `cryptography` library (PBKDF2 + AES-GCM)
- **Build Tool**: Buildozer (Targeting Android API 31)
- **Asynchronous Processing**: formatting data loading off the main thread to prevent Application Not Responding (ANR) errors.

---

## 📦 Installation & Build Instructions

### 1. Running Locally (Desktop - Windows/Linux/macOS)

**Prerequisites**: Python 3.10+, Git.

```bash
# Clone the repository
git clone https://github.com/yourusername/RemindMe.git
cd RemindMe

# Create Virtual Environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt

# Run the Application
python main.py
```

### 2. Building for Android (APK)

This project uses **Buildozer** to package the application.

**Prerequisites**:
- Ubuntu 20.04+ / WSL2
- Java JDK 17
- Python 3.10+

**Build Configuration**:
- **Target API**: 31 (Android 12)
- **Minimum API**: 21 (Android 5.0)
- **Architecture**: ARM64-v8a

**Build Command**:
```bash
buildozer android debug
```

---

## 📖 User Guide

### Dashboard
- **Create Task**: Tap the `+` Floating Action Button.
- **Manage Tasks**: Tap any card to view details.
- **Search**: Real-time filtering by task title.

### Analytics
- **Weekly Overview**: View completion rates.
- **Audit Details**: Tap specific metrics to view detailed logs with local timestamps.

### Settings
- **Theme**: Toggle Light/Dark mode.
- **Account**: Secure password management.

---

## 📄 License

This project is licensed under the MIT License - free for educational and personal use.
