import { useCallback } from 'react';
import { useDropzone, FileRejection } from 'react-dropzone';
import { Upload, DocumentAdd, TrashCan } from '@carbon/icons-react';
import { Button, Tag } from '@carbon/react';

interface FileUploadProps {
  files: File[];
  onFilesChange: (files: File[]) => void;
  maxFiles?: number;
  disabled?: boolean;
}

export function FileUpload({ 
  files, 
  onFilesChange, 
  maxFiles = 50,
  disabled = false 
}: FileUploadProps) {
  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: FileRejection[]) => {
    if (rejectedFiles.length > 0) {
      console.warn('Rejected files:', rejectedFiles);
    }
    
    const newFiles = [...files, ...acceptedFiles].slice(0, maxFiles);
    onFilesChange(newFiles);
  }, [files, onFilesChange, maxFiles]);

  const { getRootProps, getInputProps, isDragActive, isDragAccept, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'chemical/x-cif': ['.cif'],
      'application/octet-stream': ['.cif'],
    },
    maxFiles: maxFiles - files.length,
    disabled,
  });

  const removeFile = (index: number) => {
    const newFiles = files.filter((_, i) => i !== index);
    onFilesChange(newFiles);
  };

  const clearAll = () => {
    onFilesChange([]);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const dropzoneClass = [
    'dropzone',
    isDragActive && 'dropzone--active',
    isDragAccept && 'dropzone--accept',
    isDragReject && 'dropzone--reject',
    disabled && 'dropzone--disabled',
  ].filter(Boolean).join(' ');

  return (
    <div className="file-upload">
      <div {...getRootProps({ className: dropzoneClass })}>
        <input {...getInputProps()} />
        <div className="dropzone__icon">
          {isDragActive ? <DocumentAdd size={48} /> : <Upload size={48} />}
        </div>
        <p className="dropzone__text">
          {isDragActive
            ? 'Drop CIF files here...'
            : 'Drag & drop CIF files here, or click to select'}
        </p>
        <p className="dropzone__subtext">
          Supports .cif files • Max {maxFiles} files per batch
        </p>
      </div>

      {files.length > 0 && (
        <div className="file-upload__list" style={{ marginTop: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ fontWeight: 600 }}>
              {files.length} file{files.length !== 1 ? 's' : ''} selected
            </span>
            <Button
              kind="ghost"
              size="sm"
              renderIcon={TrashCan}
              onClick={clearAll}
              disabled={disabled}
            >
              Clear all
            </Button>
          </div>
          
          <ul className="file-list">
            {files.map((file, index) => (
              <li key={`${file.name}-${index}`} className="file-list__item">
                <span className="file-list__name">
                  <DocumentAdd size={16} />
                  {file.name}
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <Tag size="sm" type="gray">
                    {formatFileSize(file.size)}
                  </Tag>
                  <Button
                    kind="ghost"
                    size="sm"
                    hasIconOnly
                    iconDescription="Remove file"
                    renderIcon={TrashCan}
                    onClick={() => removeFile(index)}
                    disabled={disabled}
                  />
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
