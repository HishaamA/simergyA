from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class PredictionMode(str, Enum):
    SINGLE = "single"
    RELAXED = "relaxed"


class AtomInfo(BaseModel):
    element: str
    x: float
    y: float
    z: float
    force_x: Optional[float] = None
    force_y: Optional[float] = None
    force_z: Optional[float] = None


class LatticeInfo(BaseModel):
    a: float
    b: float
    c: float
    alpha: float
    beta: float
    gamma: float
    volume: float


class PredictionResult(BaseModel):
    filename: str
    formula: str
    num_atoms: int
    lattice: LatticeInfo
    atoms: List[AtomInfo]
    
    energy_total: float = Field(..., description="Total energy in eV")
    energy_per_atom: float = Field(..., description="Energy per atom in eV/atom")
    
    formation_energy: float = Field(..., description="Formation energy in eV")
    formation_energy_per_atom: float = Field(..., description="Formation energy per atom in eV/atom")
    
    max_force: float = Field(..., description="Maximum force magnitude in eV/Å")
    stress_tensor: List[List[float]] = Field(..., description="Stress tensor in GPa")
    pressure: float = Field(..., description="Hydrostatic pressure in GPa")
    
    is_stable: bool = Field(..., description="Whether structure is predicted stable")
    stability_score: float = Field(..., description="Stability score (0-1, higher is better)")
    stability_message: str = Field(..., description="Human-readable stability assessment")
    
    was_relaxed: bool = False
    relaxation_steps: Optional[int] = None
    energy_change: Optional[float] = None


class BatchPredictionResponse(BaseModel):
    total_files: int
    successful: int
    failed: int
    results: List[PredictionResult]
    errors: List[dict]


class PredictionRequest(BaseModel):
    relax_structure: bool = Field(default=False, description="Whether to relax the structure before prediction")
    relax_steps: int = Field(default=50, description="Maximum relaxation steps", ge=1, le=500)
    force_threshold: float = Field(default=0.05, description="Force convergence threshold in eV/Å")
