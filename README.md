# PredictionRMN

**PredictionRMN** is a full-stack application designed to **predict and visualize NMR spectra** from user-drawn molecular structures.

It is composed of a **customized frontend** integrating [Ketcher](https://github.com/epam/ketcher), Plotly for the visualization of the spectra, a Flask-based backend for the internal api, and packaging tools for a **standalone executable distribution**.

---

## 🧠 Project Summary

This application allows chemists and researchers to:
- Draw a molecule using an interactive chemical editor (Ketcher)
- Submit the structure to a backend that predicts its NMR spectra
- Visualize the predicted spectrum with interactive tools (Plotly.js)
- Interact with the spectrum peaks to highlight the associated atoms
- Load / export results

---

## 📦 Repository Structure

```

PredictionRMN/
├── backend/           # Flask-based backend for spectrum prediction
│   └── app/           # Contains the main logic (API, routing, default settings)
├── frontend/          # Built static frontend (based on CustomKetcher)
├── dist/              # Standalone packaged app for Linux and Windows
├── docs/              # Documentation for users and developers
├── scripts/           # Scripts for building the application
└── README.md

````

---

## 🌐 Frontend: User Interface

The frontend is **custom-built from a fork of Ketcher**, which has been extended to:
- Interface with the backend NMR prediction API
- Display 1D NMR spectra (1H and 13C)
- Provide interactivity between molecule structure and spectral data

🧩 The source code for the frontend can be found here:
👉 [CustomKetcher GitHub Repository](https://github.com/KreeZeG123/CustomKetcher)

---

## 🧪 Backend: NMR Spectrum Prediction

The backend is a Python/Flask server that:
- Receives molecules from the frontend
- Verify them using RDKit
- Convert the SMILES into a kekulized format
- Runs a prediction algorithm
- Loads JCAMP-DX files
- Calculate NMR peaks and multiplicities for plotting

Located in [`backend/app/`](./backend/app), the backend supports modular configuration and includes default parameters in JSON format.

---

## ⚙️ Packaging & Deployment

This application can be compiled into a **cross-platform executable** using **PyInstaller**.

Build scripts:
```bash
# Linux/Mac
bash scripts/packageApp.sh

# Windows
./scripts/packageApp.bat
````

After building, the executable is located in the `dist/` directory:

```
dist/
└── PredictionRMN.exe   # Windows executable (can run without Python installed)
```

---

## 📄 Documentation

* [`docs/user_guide.md`](./docs/user_guide.md) – User Guide
* [`docs/dev_guide.md`](./docs/dev_guide.md) – Developer Guide

> These guides explain how to run, use, and modify the application.

---

## 🔧 Technologies Used

* **React + Vite** – Frontend SPA build
* **Ketcher** - Molecular editor
* **Plotly.js** – Interactive charting for NMR
* **Python**
* **Flask** – Lightweight web server
* **RDKit** – Chemical structure processing and prediction
* **SciPy** - Spectra processing
* **Jcamp** - JCAMP-DX parser
* **PyInstaller** – Packaging the app as an executable

---

## 🧑‍💻 Author

This project was developed by **Yamis MANFALOTI**
as part of a Master’s internship at **LERIA (University of Angers)**.

---

## ⚖️ License

The code is distributed under the **Apache 2.0 License**.
It uses and extends open-source tools including:

* [Ketcher](https://github.com/epam/ketcher) (licensed under Apache 2.0)
* [RDKit](https://www.rdkit.org/docs/)
* etc.

Please refer to each dependency for its own licensing terms.

---

## 🚀 How to Run Locally (Development Mode)

1. **Install backend dependencies**:

   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Run the Flask server**:

   ```bash
   python app.py
   ```

3. **Serve the frontend (optional if not building static)**:

   * See the [CustomKetcher repo](https://github.com/KreeZeG123/CustomKetcher) for dev instructions.

---

## 📬 Contact

For inquiries or contributions, please contact the developer **Yamis MANFALOTI** [(KreeZeG123)](https://github.com/KreeZeG123/)
