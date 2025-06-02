pyinstaller --onefile \
  --name PredictionRMN \
  --add-data "backend/app/defaults/*.json:defaults" \
  --add-data "frontend/build:frontend/build" \
  --add-data "backend/app/models/simpleModel/H/trained_model_v3.pkl:app/models/simpleModel/H" \
  --exclude-module tkinter \
  backend/app.py
