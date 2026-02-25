// Type definitions for SIMER Energy AI Platform

export interface LatticeInfo {
  a: number;
  b: number;
  c: number;
  alpha: number;
  beta: number;
  gamma: number;
  volume: number;
}

export interface AtomInfo {
  element: string;
  x: number;
  y: number;
  z: number;
  force_x?: number;
  force_y?: number;
  force_z?: number;
}

export interface PredictionResult {
  filename: string;
  formula: string;
  num_atoms: number;
  lattice: LatticeInfo;
  atoms: AtomInfo[];
  
  // CHGNet predictions - Total energies
  energy_total: number;
  energy_per_atom: number;
  
  // Formation energies (relative to elemental references)
  formation_energy: number;
  formation_energy_per_atom: number;
  
  // Forces and stress
  max_force: number;
  stress_tensor: number[][];
  pressure: number;
  
  // Stability assessment
  is_stable: boolean;
  stability_score: number;
  stability_message: string;
  
  // Relaxation info
  was_relaxed: boolean;
  relaxation_steps?: number;
  energy_change?: number;
}

export interface BatchPredictionResponse {
  total_files: number;
  successful: number;
  failed: number;
  results: PredictionResult[];
  errors: Array<{
    filename: string;
    error: string;
  }>;
}

export interface ModelInfo {
  model: string;
  version: string;
  description: string;
  capabilities: string[];
  supported_formats: string[];
  max_batch_size: number;
}

export interface PredictionSettings {
  relax_structure: boolean;
  relax_steps: number;
  force_threshold: number;
}
