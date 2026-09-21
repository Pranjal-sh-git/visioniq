import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import ImageIntelligence from './pages/ImageIntelligence';
import VideoIntelligence from './pages/VideoIntelligence';
import { getHealthStatus } from './services/api';
import { Layers, ShieldCheck, Database, Zap } from 'lucide-react';

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
      <div className="ambient-glow" />
      <Navbar activeTab={activeTab} onTabChange={setActiveTab} healthStatus={healthStatus} />
      
      <main className="main-content">
        <div className={`tab-pane ${activeTab === 'image' ? 'active' : 'is-hidden'}`}>
          <ImageIntelligence />
        </div>
        <div className={`tab-pane ${activeTab === 'video' ? 'active' : 'is-hidden'}`}>
          <VideoIntelligence />
        </div>
      </main>

      <footer className="app-footer">
        <div className="footer-content">
          <div className="footer-item">
            <Layers size={13} className="footer-icon" />
            <span>GPT-5 Multimodal Vision</span>
          </div>
          <div className="footer-divider">•</div>
          <div className="footer-item">
            <Database size={13} className="footer-icon" />
            <span>Azure AI Search Vector RAG</span>
          </div>
          <div className="footer-divider">•</div>
          <div className="footer-item">
            <Zap size={13} className="footer-icon" />
            <span>Content Understanding Temporal Pipeline</span>
          </div>
          <div className="footer-divider">•</div>
          <div className="footer-item">
            <ShieldCheck size={13} className="footer-icon" />
            <span>Foundry Agent Service</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
