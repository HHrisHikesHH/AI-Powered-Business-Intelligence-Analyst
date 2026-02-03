#!/usr/bin/env python3
"""
Force reload the API key and verify it's being used.
This will help ensure the new key is active.
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("Force Reload API Key")
print("=" * 60)

# Clear environment
if "GROQ_API_KEY" in os.environ:
    del os.environ["GROQ_API_KEY"]
    print("✓ Cleared GROQ_API_KEY from environment")

# Clear module cache
modules_to_clear = ['app.core.config', 'app.core.llm_client']
for mod in modules_to_clear:
    if mod in sys.modules:
        del sys.modules[mod]
        print(f"✓ Cleared {mod} from cache")

# Reload .env
from dotenv import load_dotenv
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"✓ Reloaded .env from: {env_path}")

# Import and check
from app.core.config import settings
from app.core.llm_client import reset_groq_client, get_groq_client

# Reset client
reset_groq_client()
print("✓ Reset Groq client cache")

# Get client (will use new key)
client = get_groq_client()

# Verify key
current_key = settings.GROQ_API_KEY
expected_suffix = "DKToMg"  # Last 6 chars of new key

print("\n" + "=" * 60)
print("Verification")
print("=" * 60)
print(f"Current API Key: {current_key[:12]}...{current_key[-8:]}")
print(f"Key ends with: {current_key[-6:]}")

if current_key.endswith(expected_suffix):
    print("✅ NEW KEY IS LOADED CORRECTLY!")
    print(f"   Key matches expected new key (ends with {expected_suffix})")
else:
    print("⚠️  Key doesn't match expected new key")
    print(f"   Expected to end with: {expected_suffix}")
    print(f"   Actual ends with: {current_key[-6:]}")

print("\n" + "=" * 60)
print("IMPORTANT: Restart your application server!")
print("=" * 60)
print("\nThe running server process needs to be restarted to use the new key.")
print("\nIf running via VS Code/Cursor debugger:")
print("  1. Stop the debug session (click Stop button)")
print("  2. Start it again (F5 or Run > Start Debugging)")
print("\nIf running manually:")
print("  1. Stop the server (Ctrl+C)")
print("  2. Restart: uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload")

