// @ts-nocheck
import React, { useState, useEffect } from 'react';
import { uploadFiles, getStatus, downloadZip } from './api';
import Dropzone from './components/Dropzone';
import ProgressBar from './components/ProgressBar';

const App: React.FC = () => {
  const [files, setFiles] = useState<File[]>([]);
  const [jobId, setJobId] = useState<string>('');
  const [progress, setProgress] = useState<number>(0);
  const [status, setStatus] = useState<string>('');
  const [downloadUrl, setDownloadUrl] = useState<string>('');

  useEffect(() => {
    let interval: any;
    if (jobId) {
      interval = setInterval(async () => {
        const res = await getStatus(jobId);
        setProgress(res.progress);
        setStatus(res.status);
        if (res.status === 'complete') {
          clearInterval(interval);
          setDownloadUrl(downloadZip(jobId));
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [jobId]);

  const handleUpload = async () => {
    if (!files.length) return;
    const res = await uploadFiles(files);
    setJobId(res.job_id);
  };

  return (
    <div style={{ padding: 20 }}>
      <h1>SQL Cleanser</h1>
      <Dropzone files={files} setFiles={setFiles} />
      <button onClick={handleUpload} disabled={!files.length || !!jobId}>
        Upload
      </button>
      {jobId && (
        <>
          <p>Status: {status}</p>
          <ProgressBar progress={progress} />
        </>
      )}
      {downloadUrl && (
        <div>
          <a href={downloadUrl}>Download Clean Scripts & Report</a>
        </div>
      )}
    </div>
  );
};

export default App; 