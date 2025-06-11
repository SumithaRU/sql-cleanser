// @ts-nocheck
import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

interface Props {
  files: File[];
  setFiles: (files: File[]) => void;
}

const Dropzone: React.FC<Props> = ({ files, setFiles }) => {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      setFiles([...files, ...acceptedFiles]);
    },
    [files, setFiles]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/sql': ['.sql'] },
  });

  return (
    <div
      {...getRootProps()}
      style={{
        border: '2px dashed #ccc',
        padding: 20,
        textAlign: 'center',
        cursor: 'pointer',
        marginBottom: 20,
      }}
    >
      <input {...getInputProps()} />
      {isDragActive ? <p>Drop the files here ...</p> : <p>Drag 'n' drop SQL files here, or click to select</p>}
      <ul>
        {files.map((file) => (
          <li key={file.name}>{file.name}</li>
        ))}
      </ul>
    </div>
  );
};

export default Dropzone; 