"""

import numpy as np
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
import tempfile
import logging

# Materials science imports
from pymatgen.core import Structure, Composition
from pymatgen.io.cif import CifParser

# CHGNet imports
from chgnet.model import CHGNet
from chgnet.model.dynamics import StructOptimizer

logger = logging.getLogger(__name__)

ELEMENTAL_REFERENCE_ENERGIES = {
    'Li': -1.908,
    'Na': -1.312,
    'K': -1.110,
    'Mg': -1.600,
    'Ca': -1.999,
    'Ti': -7.895,
    'V': -9.083,
    'Cr': -9.653,
    'Mn': -9.164,
    'Fe': -8.469,
    'Co': -7.108,
    'Ni': -5.778,
    'Cu': -4.099,
    'Zn': -1.259,
    'Zr': -8.547,
    'Nb': -10.094,
    'Mo': -10.847,
    'Ru': -9.274,
    'Rh': -7.364,
    'Pd': -5.380,
    'Ag': -2.826,
    'Ta': -11.852,
    'W': -12.958,
    'Pt': -6.056,
    'Au': -3.273,
    'Al': -3.745,
    'Si': -5.425,
    'P': -5.409,
    'S': -4.136,
    'Cl': -1.798,
    'O': -4.948,
    'F': -1.910,
    'Br': -1.636,
    'I': -1.524,
    'C': -9.227,
    'N': -8.336,
    'H': -3.392,
    'B': -6.679,
    'La': -4.936,
    'Ce': -5.933,
    'default': -5.0,
}


class CHGNetService:
    _instance: Optional['CHGNetService'] = None
    _model: Optional[CHGNet] = None
    _relaxer: Optional[StructOptimizer] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None:
            self._load_model()
    
    def _load_model(self):
        logger.info("Loading CHGNet model...")
        try:
            self._model = CHGNet.load()
            self._relaxer = StructOptimizer(model=self._model)
            logger.info("CHGNet model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load CHGNet model: {e}")
            raise RuntimeError(f"Failed to load CHGNet model: {e}")
    
    def parse_cif_content(self, cif_content: str, filename: str = "structure.cif") -> Structure:
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.cif', delete=False) as f:
                f.write(cif_content)
                temp_path = f.name
            
            parser = CifParser(temp_path)
            structures = parser.get_structures(primitive=False)
            
            if not structures:
                raise ValueError(f"No valid structures found in CIF file: {filename}")
            
            Path(temp_path).unlink(missing_ok=True)
            
            return structures[0]
            
        except Exception as e:
            logger.error(f"Error parsing CIF file {filename}: {e}")
            raise ValueError(f"Failed to parse CIF file '{filename}': {str(e)}")
    
    def predict(self, structure: Structure) -> Dict[str, Any]:
        try:
            prediction = self._model.predict_structure(structure)
            
            energy_per_atom = float(prediction['e'])
            forces = np.array(prediction['f'])
            stress = np.array(prediction['s'])
            
            n_atoms = len(structure)
            energy_total = energy_per_atom * n_atoms
            max_force = float(np.max(np.linalg.norm(forces, axis=1)))
            
            pressure = -float(np.trace(stress) / 3)
            
            formation_energy, formation_energy_per_atom = self._calculate_formation_energy(
                structure, energy_total
            )
            
            stability_score, is_stable, stability_message = self._assess_stability(
                energy_per_atom, formation_energy_per_atom, max_force, pressure
            )
            
            logger.info(f"Prediction for {structure.composition.reduced_formula}: "
                       f"E_total={energy_total:.4f} eV, E/atom={energy_per_atom:.4f} eV/atom, "
                       f"E_form={formation_energy:.4f} eV, E_form/atom={formation_energy_per_atom:.4f} eV/atom")
            
            return {
                'energy_total': energy_total,
                'energy_per_atom': energy_per_atom,
                'formation_energy': formation_energy,
                'formation_energy_per_atom': formation_energy_per_atom,
                'forces': forces.tolist(),
                'stress_tensor': stress.tolist(),
                'max_force': max_force,
                'pressure': pressure,
                'is_stable': is_stable,
                'stability_score': stability_score,
                'stability_message': stability_message,
            }
            
        except Exception as e:
            logger.error(f"CHGNet prediction failed: {e}")
            raise RuntimeError(f"Prediction failed: {str(e)}")
    
    def _calculate_formation_energy(self, structure: Structure, total_energy: float) -> Tuple[float, float]:
        composition = structure.composition
        n_atoms = len(structure)
        
        reference_energy = 0.0
        for element, count in composition.items():
            element_symbol = str(element)
            ref_e = ELEMENTAL_REFERENCE_ENERGIES.get(
                element_symbol, 
                ELEMENTAL_REFERENCE_ENERGIES['default']
            )
            reference_energy += count * ref_e
            
        formation_energy = total_energy - reference_energy
        formation_energy_per_atom = formation_energy / n_atoms
        
        return formation_energy, formation_energy_per_atom
    
    def relax_structure(
        self, 
        structure: Structure, 
        max_steps: int = 50,
        fmax: float = 0.05
    ) -> Tuple[Structure, Dict[str, Any]]:
        try:
            initial_prediction = self._model.predict_structure(structure)
            initial_energy = float(initial_prediction['e'])
            
            result = self._relaxer.relax(
                structure,
                steps=max_steps,
                fmax=fmax,
                verbose=False
            )
            
            relaxed_structure = result['final_structure']
            trajectory = result.get('trajectory', None)
            
            final_prediction = self._model.predict_structure(relaxed_structure)
            final_energy = float(final_prediction['e'])
            energy_change = final_energy - initial_energy
            
            n_steps = len(trajectory) if trajectory else 0
            
            relaxation_info = {
                'initial_energy': initial_energy,
                'final_energy': final_energy,
                'energy_change': energy_change,
                'steps': n_steps,
                'converged': n_steps < max_steps
            }
            
            return relaxed_structure, relaxation_info
            
        except Exception as e:
            logger.error(f"Structure relaxation failed: {e}")
            raise RuntimeError(f"Relaxation failed: {str(e)}")
    
    def _assess_stability(
        self, 
        energy_per_atom: float,
        formation_energy_per_atom: float,
        max_force: float, 
        pressure: float
    ) -> Tuple[float, bool, str]:
        score = 1.0
        messages = []
        
        if formation_energy_per_atom < -0.5:
            messages.append(f"Very negative formation energy ({formation_energy_per_atom:.3f} eV/atom) - highly stable")
        elif formation_energy_per_atom < -0.1:
            messages.append(f"Negative formation energy ({formation_energy_per_atom:.3f} eV/atom) - stable")
        elif formation_energy_per_atom < 0.0:
            messages.append(f"Slightly negative formation energy ({formation_energy_per_atom:.3f} eV/atom) - marginally stable")
            score -= 0.1
        elif formation_energy_per_atom < 0.1:
            messages.append(f"Near-zero formation energy ({formation_energy_per_atom:.3f} eV/atom) - metastable")
            score -= 0.25
        else:
            messages.append(f"Positive formation energy ({formation_energy_per_atom:.3f} eV/atom) - likely unstable")
            score -= 0.4
        
        if max_force < 0.01:
            messages.append("Very low residual forces - at equilibrium")
        elif max_force < 0.05:
            messages.append("Low residual forces - near equilibrium")
            score -= 0.05
        elif max_force < 0.1:
            messages.append("Moderate forces - may benefit from relaxation")
            score -= 0.15
        else:
            messages.append("High forces detected - structure not at equilibrium")
            score -= 0.3
        
        abs_pressure = abs(pressure)
        if abs_pressure < 1.0:
            messages.append("Pressure near zero")
        elif abs_pressure < 5.0:
            messages.append(f"Moderate pressure ({pressure:.2f} GPa)")
            score -= 0.05
        else:
            messages.append(f"High pressure ({pressure:.2f} GPa) - structure under stress")
            score -= 0.15
        
        score = max(0.0, min(1.0, score))
        
        is_stable = formation_energy_per_atom < 0.05 and max_force < 0.15 and score >= 0.5
        
        if is_stable:
            summary = f"✓ Structure appears STABLE (score: {score:.2f})"
        else:
            summary = f"⚠ Structure may be UNSTABLE (score: {score:.2f})"
        
        full_message = f"{summary}. {'; '.join(messages)}"
        
        return score, is_stable, full_message
    
    def get_structure_info(self, structure: Structure) -> Dict[str, Any]:
        lattice = structure.lattice
        
        atoms = []
        for site in structure:
            atoms.append({
                'element': str(site.specie),
                'x': float(site.coords[0]),
                'y': float(site.coords[1]),
                'z': float(site.coords[2]),
            })
        
        return {
            'formula': structure.composition.reduced_formula,
            'num_atoms': len(structure),
            'lattice': {
                'a': float(lattice.a),
                'b': float(lattice.b),
                'c': float(lattice.c),
                'alpha': float(lattice.alpha),
                'beta': float(lattice.beta),
                'gamma': float(lattice.gamma),
                'volume': float(lattice.volume),
            },
            'atoms': atoms,
        }


chgnet_service = CHGNetService()
