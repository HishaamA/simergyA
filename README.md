# SIMER Energy AI Platform

AI-powered crystal structure stability prediction platform using CHGNet (Crystal Hamiltonian Graph Neural Network).

## Features

- **Crystal Structure Analysis**: Upload CIF files and get instant ML predictions
- **Energy Predictions**: Total energy, energy per atom
- **Force Analysis**: Atomic forces and maximum force magnitude
- **Stress Tensor**: Full stress tensor and hydrostatic pressure
- **Stability Assessment**: AI-based stability scoring and classification
- **Structure Relaxation**: Optional geometry optimization before prediction
- **Batch Processing**: Analyze multiple structures at once (up to 50 files)
- **3D Visualization**: Interactive crystal structure viewer

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **CHGNet** - Universal graph neural network for materials
- **Pymatgen** - Python Materials Genomics library
- **PyTorch** - Deep learning framework

### Frontend
- **React 18** - UI library
- **TypeScript** - Type-safe JavaScript
- **IBM Carbon Design System** - UI component library
- **3Dmol.js** - Molecular visualization
- **Vite** - Build tool

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/model/info` | Get model information |
| POST | `/api/predict` | Single file prediction |
| POST | `/api/predict/batch` | Batch prediction |
| GET | `/health` | Health check |

### Single Prediction Request

```bash
curl -X POST "http://localhost:8000/api/predict" \
  -F "file=@structure.cif" \
  -F "relax_structure=false" \
  -F "relax_steps=50" \
  -F "force_threshold=0.05"
```

### Batch Prediction Request

```bash
curl -X POST "http://localhost:8000/api/predict/batch" \
  -F "files=@structure1.cif" \
  -F "files=@structure2.cif" \
  -F "relax_structure=true"
```

## Project Structure

```
simerenergyA/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py          # API endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py         # Pydantic models
│   ├── services/
│   │   ├── __init__.py
│   │   └── chgnet_service.py  # CHGNet integration
│   ├── main.py                # FastAPI app
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── services/          # API client
│   │   ├── styles/            # SCSS styles
│   │   ├── types/             # TypeScript types
│   │   ├── App.tsx            # Main app
│   │   └── main.tsx           # Entry point
│   ├── package.json
│   └── vite.config.ts
├── samples/                   # Sample CIF files
└── README.md
```

## Sample CIF Files

Sample crystal structure files are provided in the `samples/` directory for testing.

## License

MIT License

## Acknowledgments

- [CHGNet](https://github.com/CederGroupHub/chgnet) - Crystal Hamiltonian Graph Neural Network
- [Pymatgen](https://pymatgen.org/) - Python Materials Genomics
- [IBM Carbon Design System](https://carbondesignsystem.com/)
