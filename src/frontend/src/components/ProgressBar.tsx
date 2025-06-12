// @ts-nocheck
import React from 'react';

interface Props {
  progress: number;
}

const ProgressBar: React.FC<Props> = ({ progress }) => {
  return (
    <div style={{ width: '100%', background: '#eee', borderRadius: 4, overflow: 'hidden', margin: '10px 0' }}>
      <div style={{ width: `${progress}%`, background: '#007acc', height: '10px' }}></div>
    </div>
  );
};

export default ProgressBar; 