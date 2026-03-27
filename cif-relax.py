from chgnet.model.dynamics import StructOptimizer
from pymatgen.core import Structure
import warnings
warnings.filterwarnings("ignore")

print("Loading V2 AI generated structure...")
struct = Structure.from_file("my_llama_cifs/structure_5.cif")

print("Waking up CHGNet Quantum Force Field...")
relaxer = StructOptimizer()

print("Relaxing atomic coordinates... (This might take a minute)")
result = relaxer.relax(struct)

final_struct = result['final_structure']
final_struct.to(fmt="cif", filename="my_llama_cifs/structure_5_relaxed.cif")

print("Done! Perfectly relaxed CIF saved as structure_5_relaxed.cif")