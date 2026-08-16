import json
import os

vault_file = ".pineal_vault.json"
vault_data = {}

if os.path.exists(vault_file):
    try:
        with open(vault_file, "r") as f:
            vault_data = json.load(f)
    except Exception:
        pass

vault_data["api_key"] = "sk-or-v1-YOUR_KEY_HERE"

with open(vault_file, "w") as f:
    json.dump(vault_data, f, indent=4)

print("OpenRouter API key eklendi.")
