import base64
import sys
import json

def decode_jwt(token):
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return "Invalid token format"
        
        payload = parts[1]
        # Fix padding
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.b64decode(payload).decode('utf-8')
        return json.loads(decoded)
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    token = sys.argv[1]
    print(json.dumps(decode_jwt(token), indent=2))
