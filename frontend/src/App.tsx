import { useState } from 'react';
import {
  Header,
  HeaderName,
  HeaderGlobalBar,
  HeaderGlobalAction,
  Content,
  Button,
  Loading,
  InlineNotification,
  Grid,
  Column,
} from '@carbon/react';
import { 
  ChemistryReference, 
  Play, 
  Information,
  Renew,
} from '@carbon/icons-react';

import { 
  FileUpload, 
  PredictionSettingsPanel, 
  ResultCard, 
  BatchSummary, 
  ErrorList,
  StructureViewer,
} from './components';
import { predictSingle, predictBatch } from './services/api';
import type { PredictionResult, BatchPredictionResponse, PredictionSettings } from './types';

function App() {
  // State
  const [files, setFiles] = useState<File[]>([]);
  const [settings, setSettings] = useState<PredictionSettings>({
    relax_structure: false,
    relax_steps: 50,
    force_threshold: 0.05,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<PredictionResult[]>([]);
  const [batchResponse, setBatchResponse] = useState<BatchPredictionResponse | null>(null);
  const [selectedResultIndex, setSelectedResultIndex] = useState<number>(0);

  // Handlers
  const handlePredict = async () => {
    if (files.length === 0) {
      setError('Please upload at least one CIF file');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResults([]);
    setBatchResponse(null);

    try {
      if (files.length === 1) {
        // Single file prediction
        const result = await predictSingle(files[0], settings);
        setResults([result]);
      } else {
        // Batch prediction
        const response = await predictBatch(files, settings);
        setBatchResponse(response);
        setResults(response.results);
      }
      setSelectedResultIndex(0);
    } catch (err: any) {
      console.error('Prediction failed:', err);
      setError(
        err.response?.data?.detail || 
        err.message || 
        'Prediction failed. Please check your file and try again.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setFiles([]);
    setResults([]);
    setBatchResponse(null);
    setError(null);
    setSelectedResultIndex(0);
  };

  const hasResults = results.length > 0;
  const selectedResult = results[selectedResultIndex];

  return (
    <div className="app">
      {/* Header */}
      <Header aria-label="SIMER Energy AI" className="simer-header">
        <HeaderName prefix="">
          <ChemistryReference size={20} style={{ marginRight: '0.5rem' }} />
          SIMER Energy AI
        </HeaderName>
        <HeaderGlobalBar>
          <HeaderGlobalAction aria-label="About" tooltipAlignment="end">
            <Information size={20} />
          </HeaderGlobalAction>
        </HeaderGlobalBar>
      </Header>

      {/* Main Content */}
      <Content className="simer-main">
        <Grid>
          {/* Header Section */}
          <Column lg={16} md={8} sm={4}>
            <div style={{ marginBottom: '2rem' }}>
              <h1 className="simer-section-title" style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>
                Crystal Structure Stability Prediction
              </h1>
              <p style={{ color: 'var(--simer-text-secondary)', maxWidth: '800px' }}>
                Upload CIF files to analyze crystal structures using CHGNet, a universal graph neural network 
                for predicting material properties. Get instant predictions for energy, forces, stress, and stability.
              </p>
            </div>
          </Column>

          {/* Left Column - Upload & Settings */}
          <Column lg={6} md={8} sm={4}>
            <div className="simer-card simer-card--elevated">
              <h2 className="simer-section-title">
                <ChemistryReference size={24} />
                Upload Structures
              </h2>
              
              <FileUpload 
                files={files} 
                onFilesChange={setFiles}
                disabled={isLoading}
              />

              <PredictionSettingsPanel
                settings={settings}
                onSettingsChange={setSettings}
                disabled={isLoading}
              />

              {/* Error Display */}
              {error && (
                <InlineNotification
                  kind="error"
                  title="Error"
                  subtitle={error}
                  onClose={() => setError(null)}
                  style={{ marginTop: '1rem' }}
                />
              )}

              {/* Action Buttons */}
              <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
                <Button
                  renderIcon={Play}
                  onClick={handlePredict}
                  disabled={files.length === 0 || isLoading}
                  style={{ flex: 1 }}
                >
                  {isLoading ? 'Analyzing...' : `Analyze ${files.length > 1 ? `${files.length} Files` : 'Structure'}`}
                </Button>
                
                {hasResults && (
                  <Button
                    kind="secondary"
                    renderIcon={Renew}
                    onClick={handleReset}
                    disabled={isLoading}
                  >
                    Reset
                  </Button>
                )}
              </div>
            </div>
          </Column>

          {/* Right Column - Results */}
          <Column lg={10} md={8} sm={4}>
            {isLoading && (
              <div className="loading-overlay">
                <Loading description="Analyzing crystal structure..." withOverlay={false} />
                <p className="loading-overlay__text">
                  {settings.relax_structure 
                    ? 'Running structure relaxation and prediction...' 
                    : 'Running CHGNet prediction...'}
                </p>
                {files.length > 1 && (
                  <p className="loading-overlay__text" style={{ fontSize: '0.875rem' }}>
                    Processing {files.length} files
                  </p>
                )}
              </div>
            )}

            {!isLoading && !hasResults && (
              <div className="simer-card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
                <ChemistryReference size={64} style={{ color: 'var(--simer-primary)', opacity: 0.5, marginBottom: '1rem' }} />
                <h3 style={{ color: 'var(--simer-text-secondary)', marginBottom: '0.5rem' }}>
                  No Results Yet
                </h3>
                <p style={{ color: 'var(--simer-text-secondary)', opacity: 0.8 }}>
                  Upload CIF files and click "Analyze" to get predictions
                </p>
              </div>
            )}

            {!isLoading && hasResults && (
              <>
                {/* Batch Summary */}
                {batchResponse && (
                  <>
                    <BatchSummary response={batchResponse} />
                    <ErrorList errors={batchResponse.errors} />
                  </>
                )}

                {/* Result Selection (for batch) */}
                {results.length > 1 && (
                  <div className="simer-card" style={{ marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                      {results.map((result, index) => (
                        <Button
                          key={index}
                          kind={selectedResultIndex === index ? 'primary' : 'ghost'}
                          size="sm"
                          onClick={() => setSelectedResultIndex(index)}
                        >
                          {result.formula}
                          {result.is_stable ? ' ✓' : ' ⚠'}
                        </Button>
                      ))}
                    </div>
                  </div>
                )}

                {/* 3D Structure Viewer */}
                {selectedResult && (
                  <div className="simer-card simer-card--elevated" style={{ padding: 0, overflow: 'hidden', marginBottom: '1.5rem' }}>
                    <StructureViewer result={selectedResult} height={350} />
                  </div>
                )}

                {/* Result Card */}
                {selectedResult && (
                  <ResultCard result={selectedResult} expanded={true} />
                )}
              </>
            )}
          </Column>
        </Grid>
      </Content>

      {/* Footer */}
      <footer style={{ 
        background: 'var(--simer-primary)', 
        color: 'var(--simer-text-on-primary)',
        padding: '1rem 2rem',
        textAlign: 'center',
        fontSize: '0.875rem'
      }}>
        SIMER Energy AI Platform • Powered by CHGNet • Crystal Structure Stability Prediction
      </footer>
    </div>
  );
}

export default App;
