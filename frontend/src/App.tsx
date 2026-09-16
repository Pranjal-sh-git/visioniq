import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import ImageIntelligence from './pages/ImageIntelligence';
import VideoIntelligence from './pages/VideoIntelligence';
import { getHealthStatus } from './services/api';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'image' | 'video'>('image');
  const [healthStatus, setHealthStatus] = useState<string>('checking...');

  useEffect(() => {
    getHealthStatus()
      .then((data) => setHealthStatus(data.status))
      .catch(() => setHealthStatus('offline'));
  }, []);

  return (
    <div className="app-container">
      <Navbar activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="main-content">
        {activeTab === 'image' && <ImageIntelligence />}
        {activeTab === 'video' && <VideoIntelligence />}

        <div className="health-status-badge">
          <span className={`status-indicator ${healthStatus === 'ok' ? 'ok' : ''}`} />
          Backend API Status: <strong>{healthStatus}</strong>
        </div>
      </main>
    </div>
  );
};

export default App;
