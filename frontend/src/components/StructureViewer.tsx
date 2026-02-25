import { useEffect, useRef } from 'react';
import type { PredictionResult } from '../types';

// Element color mapping for visualization
const ELEMENT_COLORS: Record<string, string> = {
  H: '#FFFFFF', He: '#D9FFFF', Li: '#CC80FF', Be: '#C2FF00', B: '#FFB5B5',
  C: '#909090', N: '#3050F8', O: '#FF0D0D', F: '#90E050', Ne: '#B3E3F5',
  Na: '#AB5CF2', Mg: '#8AFF00', Al: '#BFA6A6', Si: '#F0C8A0', P: '#FF8000',
  S: '#FFFF30', Cl: '#1FF01F', Ar: '#80D1E3', K: '#8F40D4', Ca: '#3DFF00',
  Sc: '#E6E6E6', Ti: '#BFC2C7', V: '#A6A6AB', Cr: '#8A99C7', Mn: '#9C7AC7',
  Fe: '#E06633', Co: '#F090A0', Ni: '#50D050', Cu: '#C88033', Zn: '#7D80B0',
  default: '#FF69B4',
};

const ELEMENT_RADII: Record<string, number> = {
  H: 0.31, He: 0.28, Li: 1.28, Be: 0.96, B: 0.84, C: 0.76, N: 0.71, O: 0.66,
  F: 0.57, Ne: 0.58, Na: 1.66, Mg: 1.41, Al: 1.21, Si: 1.11, P: 1.07, S: 1.05,
  Cl: 1.02, Ar: 1.06, K: 2.03, Ca: 1.76, Ti: 1.60, Fe: 1.52, Ni: 1.24, Cu: 1.32,
  Zn: 1.22, default: 1.0,
};

interface StructureViewerProps {
  result: PredictionResult;
  height?: number;
}

export function StructureViewer({ result, height = 400 }: StructureViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<any>(null);

  useEffect(() => {
    const loadViewer = async () => {
      if (!containerRef.current) return;

      try {
        // Dynamically import 3Dmol
        const $3Dmol = await import('3dmol');
        
        // Clear previous viewer
        if (viewerRef.current) {
          viewerRef.current.clear();
        }
        
        // Create viewer
        const viewer = $3Dmol.createViewer(containerRef.current, {
          backgroundColor: '#1a1a2e',
        });
        viewerRef.current = viewer;

        // Build XYZ string from atoms
        let xyzContent = `${result.atoms.length}\n${result.formula}\n`;
        result.atoms.forEach(atom => {
          xyzContent += `${atom.element} ${atom.x} ${atom.y} ${atom.z}\n`;
        });

        // Add model
        viewer.addModel(xyzContent, 'xyz');

        // Style atoms
        result.atoms.forEach((atom, index) => {
          const color = ELEMENT_COLORS[atom.element] || ELEMENT_COLORS.default;
          const radius = (ELEMENT_RADII[atom.element] || ELEMENT_RADII.default) * 0.4;
          
          viewer.setStyle(
            { serial: index },
            { 
              sphere: { 
                color: color, 
                radius: radius 
              } 
            }
          );
        });

        // Add unit cell if we have lattice info
        const { a, b, c, alpha, beta, gamma } = result.lattice;
        
        // Convert lattice parameters to vectors (simplified for orthogonal cells)
        // For a more accurate representation, we'd need full vector conversion
        const alphaRad = (alpha * Math.PI) / 180;
        const betaRad = (beta * Math.PI) / 180;
        const gammaRad = (gamma * Math.PI) / 180;

        // Simplified orthogonal approximation
        if (Math.abs(alpha - 90) < 5 && Math.abs(beta - 90) < 5 && Math.abs(gamma - 90) < 5) {
          viewer.addBox({
            corner: { x: 0, y: 0, z: 0 },
            dimensions: { w: a, h: b, d: c },
            color: '#00ff00',
            opacity: 0.1,
            wireframe: true,
          });
        }

        // Add coordinate axes
        viewer.addArrow({
          start: { x: 0, y: 0, z: 0 },
          end: { x: 2, y: 0, z: 0 },
          radius: 0.1,
          color: '#ff0000',
        });
        viewer.addArrow({
          start: { x: 0, y: 0, z: 0 },
          end: { x: 0, y: 2, z: 0 },
          radius: 0.1,
          color: '#00ff00',
        });
        viewer.addArrow({
          start: { x: 0, y: 0, z: 0 },
          end: { x: 0, y: 0, z: 2 },
          radius: 0.1,
          color: '#0000ff',
        });

        viewer.zoomTo();
        viewer.render();

        // Set up rotation animation
        viewer.spin('y', 0.5);

      } catch (error) {
        console.error('Failed to load 3Dmol viewer:', error);
      }
    };

    loadViewer();

    return () => {
      if (viewerRef.current) {
        viewerRef.current.clear();
      }
    };
  }, [result]);

  return (
    <div className="structure-viewer" style={{ height }}>
      <div 
        ref={containerRef} 
        className="structure-viewer__canvas"
        style={{ width: '100%', height: '100%' }}
      />
      <div className="structure-viewer__legend" style={{
        position: 'absolute',
        top: '1rem',
        left: '1rem',
        background: 'rgba(0,0,0,0.7)',
        padding: '0.5rem 1rem',
        borderRadius: '4px',
        fontSize: '0.75rem',
        color: '#fff',
      }}>
        <div style={{ marginBottom: '0.25rem', fontWeight: 600 }}>{result.formula}</div>
        <div>{result.num_atoms} atoms</div>
      </div>
    </div>
  );
}
