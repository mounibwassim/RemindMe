import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend_api", ".env"))

# API Configuration
# Please fill in your keys below.

# Firebase Configuration
# Get this from Firebase Console -> Project Settings
FIREBASE_WEB_API_KEY = "AIzaSyBGJFf7gNliaDG5pzkuFYv2K59iwrjHiz0"

# Additional Firebase Config (Reference)
FIREBASE_CONFIG = {
  "apiKey": "AIzaSyBGJFf7gNliaDG5pzkuFYv2K59iwrjHiz0",
  "authDomain": "remindme-mounib.firebaseapp.com",
  "projectId": "remindme-mounib",
  "storageBucket": "remindme-mounib.firebasestorage.app",
  "messagingSenderId": "617436301602",
  "appId": "1:617436301602:web:7746d7d140a3aa327e3d7b",
  "measurementId": "G-2X31N67E8Q"
}

FIREBASE_DATABASE_URL = "https://remindme-mounib-default-rtdb.asia-southeast1.firebasedatabase.app"

# SMTP Email Configuration
# Update these with your actual SMTP details (e.g., Gmail, Outlook)
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
