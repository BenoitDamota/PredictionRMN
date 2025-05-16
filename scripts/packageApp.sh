pyinstaller --onefile \
  --name PredictionRMN \
  --add-data "backend/app/defaults/*.json:defaults" \
  --add-data "frontend/build:frontend/build" \
  --add-data "backend/app/api/services/mock/mockSpectrum.json:mock" \
  --exclude-module tkinter \
  backend/app.py
