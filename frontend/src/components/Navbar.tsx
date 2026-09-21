import React from 'react';
import { Sparkles, Image as ImageIcon, Video as VideoIcon, Cpu } from 'lucide-react';

interface NavbarProps {
  activeTab: 'image' | 'video';
  onTabChange: (tab: 'image' | 'video') => void;
  healthStatus?: string;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, onTabChange, healthStatus = 'ok' }) => {
  const isHealthy = healthStatus === 'ok';

  return (
    <header className="navbar">
      <div className="navbar-left">
        <div className="navbar-brand">
          <div className="brand-icon-wrapper">
            <Sparkles className="brand-icon" size={18} />
          </div>
          <div className="brand-text-group">
            <div className="brand-title">
              Vision<span className="brand-accent">IQ</span>
            </div>
            <div className="brand-subtitle">Multimodal Intelligence</div>
          </div>
        </div>

        <div className="navbar-tag">
          <Cpu size={12} />
          <span>Azure AI Foundry</span>
        </div>
      </div>

      <nav className="navbar-tabs" role="tablist" aria-label="Main Navigation">
        <button
          id="tab-image-intelligence"
          role="tab"
          aria-selected={activeTab === 'image'}
          className={`tab-btn ${activeTab === 'image' ? 'active' : ''}`}
          onClick={() => onTabChange('image')}
        >
          <ImageIcon size={16} />
          <span>Image Intelligence</span>
        </button>
        <button
          id="tab-video-intelligence"
          role="tab"
          aria-selected={activeTab === 'video'}
          className={`tab-btn ${activeTab === 'video' ? 'active' : ''}`}
          onClick={() => onTabChange('video')}
        >
          <VideoIcon size={16} />
          <span>Video Intelligence</span>
        </button>
      </nav>

      <div className="navbar-right">
        <div className="status-pill" title={`Backend Status: ${healthStatus}`}>
          <span className={`status-indicator ${isHealthy ? 'ok' : 'offline'}`} />
          <span className="status-label">
            {isHealthy ? 'API Connected' : `Backend: ${healthStatus}`}
          </span>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
