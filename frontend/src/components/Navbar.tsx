import React from 'react';

interface NavbarProps {
  activeTab: 'image' | 'video';
  onTabChange: (tab: 'image' | 'video') => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, onTabChange }) => {
  return (
    <header className="navbar">
      <div className="navbar-brand">
        <span className="brand-logo">👁️</span>
        <span className="brand-title">VisionIQ</span>
      </div>
      <nav className="navbar-tabs">
        <button
          id="tab-image-intelligence"
          className={`tab-btn ${activeTab === 'image' ? 'active' : ''}`}
          onClick={() => onTabChange('image')}
        >
          Image Intelligence
        </button>
        <button
          id="tab-video-intelligence"
          className={`tab-btn ${activeTab === 'video' ? 'active' : ''}`}
          onClick={() => onTabChange('video')}
        >
          Video Intelligence
        </button>
      </nav>
    </header>
  );
};

export default Navbar;
