import json
import os
import sys; sys.stdout.reconfigure(encoding='utf-8')

vault_file = ".pineal_vault.json"
vault_data = {}

if os.path.exists(vault_file):
    try:
        with open(vault_file, "r") as f:
            vault_data = json.load(f)
    except Exception:
        pass

# 🔑 Kullanıcı API Anahtarları:
vault_data["api_key"] = os.getenv("OPENROUTER_API_KEY", "")
vault_data["tavily_key"] = os.getenv("TAVILY_API_KEY", "")
vault_data["serpapi_key"] = os.getenv("SERPAPI_API_KEY", "")
vault_data["exa_key"] = os.getenv("EXA_API_KEY", "")
vault_data["x_cookie"] = vault_data.get("x_cookie", "")


with open(vault_file, "w", encoding="utf-8") as f:
    json.dump(vault_data, f, indent=4, ensure_ascii=False)

print("✅ .pineal_vault.json başarıyla güncellendi.")

