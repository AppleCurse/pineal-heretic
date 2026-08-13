Write-Host "=== GIT GEÇMİŞ TEMİZLİĞİ - 186MB venv siliniyor ===" -ForegroundColor Yellow

cd C:\Users\Administrator\.gemini\antigravity\scratch\pineal_heretic

# 1. Mevcut durumu yedekle
Write-Host "1. Yedek branch oluşturuluyor..." -ForegroundColor Cyan
git branch backup-before-clean 2>$null

# 2. En temiz çözüm: orphan branch ile sıfırdan temiz tarih
Write-Host "2. Temiz orphan branch oluşturuluyor..." -ForegroundColor Cyan
git checkout --orphan clean-main

# 3. Sadece gerçek kaynak kodları ekle, venv ve __pycache__ hariç
Write-Host "3. Sadece kaynak kodlar ekleniyor..." -ForegroundColor Cyan
git add .gitignore
git add agent_core/ backend/ frontend/ memory/ main.py scraper.py baslat.bat requirements.txt .github/ -f
# venv ve cache'i kesinlikle ekleme
git reset -- venv __pycache__ 2>$null

# 4. .gitignore'ı garantile
@"
venv/
__pycache__/
*.pyc
*.pyo
.env
memory/*.json
.DS_Store
a0/
airi_yerel/
home/
Kullanicilar/
"@ | Out-File -Encoding utf8 .gitignore -Force

git add .gitignore -f

# 5. Commit
Write-Host "4. Temiz commit oluşturuluyor..." -ForegroundColor Cyan
git commit -m "clean: rebuild history without venv (186MB removed), Pydantic hardened"

# 6. Main'e taşı
Write-Host "5. Main branch'e taşınıyor..." -ForegroundColor Cyan
git branch -M main

# 7. Force push (geçmişi tamamen temizler)
Write-Host "6. GitHub'a force push..." -ForegroundColor Red
Write-Host "DİKKAT: Bu geçmişi siler, 10 sn içinde iptal için Ctrl+C" -ForegroundColor Red
Start-Sleep -Seconds 10

git push origin main --force

Write-Host "=== TEMİZLİK BİTTİ ===" -ForegroundColor Green
Write-Host "Repo artık 186MB olmadan tertemiz. Clone boyutu 30KB civarı olmalı." -ForegroundColor Green
git log --oneline -n 5
