import { 
  CheckmarkFilled, 
  WarningFilled, 
  Chemistry, 
  Cube, 
  Activity,
  Meter
} from '@carbon/icons-react';
import { Tag, Tooltip, ProgressBar } from '@carbon/react';
import type { PredictionResult } from '../types';

interface ResultCardProps {
  result: PredictionResult;
  expanded?: boolean;
}

export function ResultCard({ result, expanded = true }: ResultCardProps) {
  const formatNumber = (num: number, decimals: number = 4): string => {
    return num.toFixed(decimals);
  };

  return (
    <div className="result-card">
      <div className="result-card__header">
        <div className="result-card__title">
          <Chemistry size={20} />
          <span style={{ marginLeft: '0.5rem' }}>{result.formula}</span>
          <Tag size="sm" type="outline" style={{ marginLeft: '0.75rem' }}>
            {result.filename}
          </Tag>
        </div>
        <div className={`stability-badge stability-badge--${result.is_stable ? 'stable' : 'unstable'}`}>
          {result.is_stable ? (
            <>
              <CheckmarkFilled size={16} />
              Stable
            </>
          ) : (
            <>
              <WarningFilled size={16} />
              Unstable
            </>
          )}
        </div>
      </div>

      <div className="result-card__body">
        {/* Stability Assessment */}
        <div className="result-card__section">
          <h4 className="result-card__section-title">
            <Meter size={16} style={{ marginRight: '0.5rem' }} />
            Stability Assessment
          </h4>
          <div style={{ marginBottom: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span>Stability Score</span>
              <span style={{ fontWeight: 600 }}>{(result.stability_score * 100).toFixed(0)}%</span>
            </div>
            <ProgressBar
              value={result.stability_score * 100}
              max={100}
              status={result.stability_score >= 0.6 ? 'finished' : 'error'}
              hideLabel
            />
          </div>
          <p style={{ fontSize: '0.875rem', color: 'var(--simer-text-secondary)' }}>
            {result.stability_message}
          </p>
        </div>

        {/* Energy Properties */}
        <div className="result-card__section">
          <h4 className="result-card__section-title">
            <Activity size={16} style={{ marginRight: '0.5rem' }} />
            Energy Properties
          </h4>
          <div className="property-grid">
            <Tooltip label="Formation energy relative to elemental references - negative values indicate thermodynamic stability">
              <div className="property-item" style={{ 
                background: result.formation_energy_per_atom < 0 
                  ? 'rgba(25, 128, 56, 0.1)' 
                  : 'rgba(218, 30, 40, 0.1)' 
              }}>
                <div className="property-item__label">Formation Energy</div>
                <div className="property-item__value" style={{
                  color: result.formation_energy_per_atom < 0 
                    ? 'var(--simer-success)' 
                    : 'var(--simer-error)'
                }}>
                  {formatNumber(result.formation_energy_per_atom, 4)}
                  <span className="property-item__unit">eV/atom</span>
                </div>
              </div>
            </Tooltip>
            <Tooltip label="Total formation energy for the unit cell">
              <div className="property-item">
                <div className="property-item__label">Formation Energy (Total)</div>
                <div className="property-item__value">
                  {formatNumber(result.formation_energy, 4)}
                  <span className="property-item__unit">eV</span>
                </div>
              </div>
            </Tooltip>
            <Tooltip label="Total potential energy of the crystal structure (DFT-level)">
              <div className="property-item">
                <div className="property-item__label">Total Energy</div>
                <div className="property-item__value">
                  {formatNumber(result.energy_total, 4)}
                  <span className="property-item__unit">eV</span>
                </div>
              </div>
            </Tooltip>
            <Tooltip label="Energy normalized by number of atoms">
              <div className="property-item">
                <div className="property-item__label">Energy per Atom</div>
                <div className="property-item__value">
                  {formatNumber(result.energy_per_atom, 4)}
                  <span className="property-item__unit">eV/atom</span>
                </div>
              </div>
            </Tooltip>
            <Tooltip label="Maximum force magnitude on any atom - low values indicate equilibrium">
              <div className="property-item">
                <div className="property-item__label">Max Force</div>
                <div className="property-item__value">
                  {formatNumber(result.max_force, 4)}
                  <span className="property-item__unit">eV/Å</span>
                </div>
              </div>
            </Tooltip>
            <Tooltip label="Hydrostatic pressure from stress tensor">
              <div className="property-item">
                <div className="property-item__label">Pressure</div>
                <div className="property-item__value">
                  {formatNumber(result.pressure, 2)}
                  <span className="property-item__unit">GPa</span>
                </div>
              </div>
            </Tooltip>
          </div>
        </div>

        {/* Relaxation Info */}
        {result.was_relaxed && (
          <div className="result-card__section">
            <h4 className="result-card__section-title">Relaxation Results</h4>
            <div className="property-grid">
              <div className="property-item">
                <div className="property-item__label">Relaxation Steps</div>
                <div className="property-item__value">{result.relaxation_steps}</div>
              </div>
              <div className="property-item">
                <div className="property-item__label">Energy Change</div>
                <div className="property-item__value">
                  {formatNumber(result.energy_change ?? 0, 4)}
                  <span className="property-item__unit">eV</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Lattice Parameters */}
        {expanded && (
          <div className="result-card__section">
            <h4 className="result-card__section-title">
              <Cube size={16} style={{ marginRight: '0.5rem' }} />
              Lattice Parameters
            </h4>
            <div className="property-grid">
              <div className="property-item">
                <div className="property-item__label">a</div>
                <div className="property-item__value">
                  {formatNumber(result.lattice.a, 4)}
                  <span className="property-item__unit">Å</span>
                </div>
              </div>
              <div className="property-item">
                <div className="property-item__label">b</div>
                <div className="property-item__value">
                  {formatNumber(result.lattice.b, 4)}
                  <span className="property-item__unit">Å</span>
                </div>
              </div>
              <div className="property-item">
                <div className="property-item__label">c</div>
                <div className="property-item__value">
                  {formatNumber(result.lattice.c, 4)}
                  <span className="property-item__unit">Å</span>
                </div>
              </div>
              <div className="property-item">
                <div className="property-item__label">α</div>
                <div className="property-item__value">
                  {formatNumber(result.lattice.alpha, 2)}
                  <span className="property-item__unit">°</span>
                </div>
              </div>
              <div className="property-item">
                <div className="property-item__label">β</div>
                <div className="property-item__value">
                  {formatNumber(result.lattice.beta, 2)}
                  <span className="property-item__unit">°</span>
                </div>
              </div>
              <div className="property-item">
                <div className="property-item__label">γ</div>
                <div className="property-item__value">
                  {formatNumber(result.lattice.gamma, 2)}
                  <span className="property-item__unit">°</span>
                </div>
              </div>
              <div className="property-item">
                <div className="property-item__label">Volume</div>
                <div className="property-item__value">
                  {formatNumber(result.lattice.volume, 2)}
                  <span className="property-item__unit">Å³</span>
                </div>
              </div>
              <div className="property-item">
                <div className="property-item__label">Atoms</div>
                <div className="property-item__value">{result.num_atoms}</div>
              </div>
            </div>
          </div>
        )}

        {/* Stress Tensor */}
        {expanded && (
          <div className="result-card__section">
            <h4 className="result-card__section-title">Stress Tensor (GPa)</h4>
            <div style={{ 
              fontFamily: 'monospace', 
              fontSize: '0.875rem',
              background: 'var(--simer-background)',
              padding: '1rem',
              borderRadius: '4px',
              overflowX: 'auto'
            }}>
              <table style={{ borderCollapse: 'collapse' }}>
                <tbody>
                  {result.stress_tensor.map((row, i) => (
                    <tr key={i}>
                      {row.map((val, j) => (
                        <td key={j} style={{ 
                          padding: '0.25rem 1rem',
                          textAlign: 'right'
                        }}>
                          {formatNumber(val, 4)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
