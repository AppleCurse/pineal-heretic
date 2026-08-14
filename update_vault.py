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

vault_data["tavily_key"] = "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"
vault_data["serpapi_key"] = "52837b71b411fcf1ba9f7a282cd6354b1236747cbb747268afb792b13c0b400d"
vault_data["exa_key"] = "80c5b496-434e-4069-9e99-073a13d02833"

with open(vault_file, "w") as f:
    json.dump(vault_data, f, indent=4)

print("Vault guncellendi.")
