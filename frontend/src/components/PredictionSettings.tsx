import { Toggle, NumberInput, Accordion, AccordionItem } from '@carbon/react';
import { Settings } from '@carbon/icons-react';
import type { PredictionSettings } from '../types';

interface PredictionSettingsPanelProps {
  settings: PredictionSettings;
  onSettingsChange: (settings: PredictionSettings) => void;
  disabled?: boolean;
}

export function PredictionSettingsPanel({
  settings,
  onSettingsChange,
  disabled = false,
}: PredictionSettingsPanelProps) {
  const handleRelaxToggle = (checked: boolean) => {
    onSettingsChange({
      ...settings,
      relax_structure: checked,
    });
  };

  const handleRelaxStepsChange = (_e: React.ChangeEvent<HTMLInputElement>, state: { value: string | number }) => {
    const value = typeof state.value === 'string' ? parseInt(state.value, 10) : state.value;
    if (!isNaN(value)) {
      onSettingsChange({
        ...settings,
        relax_steps: Math.min(500, Math.max(1, value)),
      });
    }
  };

  const handleForceThresholdChange = (_e: React.ChangeEvent<HTMLInputElement>, state: { value: string | number }) => {
    const value = typeof state.value === 'string' ? parseFloat(state.value) : state.value;
    if (!isNaN(value)) {
      onSettingsChange({
        ...settings,
        force_threshold: Math.min(1, Math.max(0.001, value)),
      });
    }
  };

  return (
    <div className="simer-card">
      <Accordion>
        <AccordionItem
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Settings size={16} />
              <span>Prediction Settings</span>
            </div>
          }
        >
          <div style={{ padding: '1rem 0' }}>
            <div style={{ marginBottom: '1.5rem' }}>
              <Toggle
                id="relax-toggle"
                labelText="Structure Relaxation"
                labelA="Off"
                labelB="On"
                toggled={settings.relax_structure}
                onToggle={handleRelaxToggle}
                disabled={disabled}
              />
              <p style={{ fontSize: '0.875rem', color: 'var(--simer-text-secondary)', marginTop: '0.5rem' }}>
                Optimize atomic positions before prediction for more accurate results.
                This increases computation time significantly.
              </p>
            </div>

            {settings.relax_structure && (
              <>
                <div style={{ marginBottom: '1.5rem' }}>
                  <NumberInput
                    id="relax-steps"
                    label="Maximum Relaxation Steps"
                    helperText="Number of optimization steps (1-500)"
                    min={1}
                    max={500}
                    step={10}
                    value={settings.relax_steps}
                    onChange={handleRelaxStepsChange}
                    disabled={disabled}
                  />
                </div>

                <div>
                  <NumberInput
                    id="force-threshold"
                    label="Force Convergence Threshold (eV/Å)"
                    helperText="Smaller values = tighter convergence (0.001-1.0)"
                    min={0.001}
                    max={1}
                    step={0.01}
                    value={settings.force_threshold}
                    onChange={handleForceThresholdChange}
                    disabled={disabled}
                  />
                </div>
              </>
            )}
          </div>
        </AccordionItem>
      </Accordion>
    </div>
  );
}
