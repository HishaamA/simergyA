"""
API Routes for SIMER Energy AI Platform

Endpoints:
- POST /api/predict - Single file prediction
- POST /api/predict/batch - Batch prediction for multiple files
- GET /api/model/info - Model information
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging

from services.chgnet_service import chgnet_service
from models.schemas import (
    PredictionResult,
    BatchPredictionResponse,
    LatticeInfo,
    AtomInfo,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/model/info")
async def get_model_info():
    return {
        "model": "CHGNet",
        "version": "0.3.8",
        "description": "Crystal Hamiltonian Graph Neural Network for predicting material properties",
        "capabilities": [
            "Energy prediction",
            "Force prediction", 
            "Stress tensor prediction",
            "Structure relaxation",
            "Stability assessment"
        ],
        "supported_formats": [".cif"],
        "max_batch_size": 50
    }


@router.post("/predict", response_model=PredictionResult)
async def predict_single(
    file: UploadFile = File(..., description="CIF file to analyze"),
    relax_structure: bool = Form(default=False, description="Whether to relax the structure"),
    relax_steps: int = Form(default=50, description="Maximum relaxation steps"),
    force_threshold: float = Form(default=0.05, description="Force convergence threshold")
):
    if not file.filename.lower().endswith('.cif'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only .cif files are supported."
        )
    
    try:
        content = await file.read()
        cif_content = content.decode('utf-8')
        
        structure = chgnet_service.parse_cif_content(cif_content, file.filename)
        
        relaxation_info = None
        if relax_structure:
            structure, relaxation_info = chgnet_service.relax_structure(
                structure,
                max_steps=relax_steps,
                fmax=force_threshold
            )
        
        prediction = chgnet_service.predict(structure)
        struct_info = chgnet_service.get_structure_info(structure)
        
        atoms_with_forces = []
        for i, atom in enumerate(struct_info['atoms']):
            forces = prediction['forces'][i]
            atoms_with_forces.append(AtomInfo(
                element=atom['element'],
                x=atom['x'],
                y=atom['y'],
                z=atom['z'],
                force_x=forces[0],
                force_y=forces[1],
                force_z=forces[2],
            ))
        
        result = PredictionResult(
            filename=file.filename,
            formula=struct_info['formula'],
            num_atoms=struct_info['num_atoms'],
            lattice=LatticeInfo(**struct_info['lattice']),
            atoms=atoms_with_forces,
            energy_total=prediction['energy_total'],
            energy_per_atom=prediction['energy_per_atom'],
            formation_energy=prediction['formation_energy'],
            formation_energy_per_atom=prediction['formation_energy_per_atom'],
            max_force=prediction['max_force'],
            stress_tensor=prediction['stress_tensor'],
            pressure=prediction['pressure'],
            is_stable=prediction['is_stable'],
            stability_score=prediction['stability_score'],
            stability_message=prediction['stability_message'],
            was_relaxed=relax_structure,
            relaxation_steps=relaxation_info['steps'] if relaxation_info else None,
            energy_change=relaxation_info['energy_change'] if relaxation_info else None,
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in predict_single: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch(
    files: List[UploadFile] = File(..., description="CIF files to analyze"),
    relax_structure: bool = Form(default=False, description="Whether to relax structures"),
    relax_steps: int = Form(default=50, description="Maximum relaxation steps"),
    force_threshold: float = Form(default=0.05, description="Force convergence threshold")
):
    if len(files) > 50:
        raise HTTPException(
            status_code=400,
            detail="Maximum 50 files allowed per batch request"
        )
    
    results = []
    errors = []
    
    for file in files:
        if not file.filename.lower().endswith('.cif'):
            errors.append({
                "filename": file.filename,
                "error": "Invalid file type. Only .cif files are supported."
            })
            continue
        
        try:
            content = await file.read()
            cif_content = content.decode('utf-8')
            
            structure = chgnet_service.parse_cif_content(cif_content, file.filename)
            
            relaxation_info = None
            if relax_structure:
                structure, relaxation_info = chgnet_service.relax_structure(
                    structure,
                    max_steps=relax_steps,
                    fmax=force_threshold
                )
            
            prediction = chgnet_service.predict(structure)
            struct_info = chgnet_service.get_structure_info(structure)
            
            atoms_with_forces = []
            for i, atom in enumerate(struct_info['atoms']):
                forces = prediction['forces'][i]
                atoms_with_forces.append(AtomInfo(
                    element=atom['element'],
                    x=atom['x'],
                    y=atom['y'],
                    z=atom['z'],
                    force_x=forces[0],
                    force_y=forces[1],
                    force_z=forces[2],
                ))
            
            result = PredictionResult(
                filename=file.filename,
                formula=struct_info['formula'],
                num_atoms=struct_info['num_atoms'],
                lattice=LatticeInfo(**struct_info['lattice']),
                atoms=atoms_with_forces,
                energy_total=prediction['energy_total'],
                energy_per_atom=prediction['energy_per_atom'],
                formation_energy=prediction['formation_energy'],
                formation_energy_per_atom=prediction['formation_energy_per_atom'],
                max_force=prediction['max_force'],
                stress_tensor=prediction['stress_tensor'],
                pressure=prediction['pressure'],
                is_stable=prediction['is_stable'],
                stability_score=prediction['stability_score'],
                stability_message=prediction['stability_message'],
                was_relaxed=relax_structure,
                relaxation_steps=relaxation_info['steps'] if relaxation_info else None,
                energy_change=relaxation_info['energy_change'] if relaxation_info else None,
            )
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error processing {file.filename}: {e}")
            errors.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return BatchPredictionResponse(
        total_files=len(files),
        successful=len(results),
        failed=len(errors),
        results=results,
        errors=errors
    )
