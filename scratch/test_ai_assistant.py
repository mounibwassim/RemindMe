import os
import sys
from datetime import datetime
import json

# Add project root to python path
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)

import backend.ai_assistant as ai

def test_assistant():
    print("Testing local parsing...")
    text = "study tomorrow at 6 pm"
    res = ai.handle_user_input(text, client_time=datetime.now().isoformat())
    print("Result for 'study tomorrow at 6 pm':")
    print(json.dumps(res, ensure_ascii=True))

    print("\nTesting Gemini enhancement...")
    text_gemini = "remind me to call mom in 3 hours"
    res_gemini = ai.handle_user_input(text_gemini, client_time=datetime.now().isoformat())
    print("Result for 'remind me to call mom in 3 hours':")
    print(json.dumps(res_gemini, ensure_ascii=True))

if __name__ == "__main__":
    test_assistant()
