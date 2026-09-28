import React from 'react';
import {
  Sparkles,
  LayoutDashboard,
  Image as ImageIcon,
  Video as VideoIcon,
  Cpu,
  LogOut,
  LogIn,
  User as UserIcon,
} from 'lucide-react';

interface NavbarProps {
  activeTab: 'landing' | 'image' | 'video';
  onTabChange: (tab: 'landing' | 'image' | 'video') => void;
  healthStatus?: string;
  currentUser?: { name: string; email: string; isGuest?: boolean } | null;
  onLogout?: () => void;
  onOpenAuth?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  onTabChange,
  healthStatus = 'ok',
  currentUser,
  onLogout,
  onOpenAuth,
}) => {
  const isHealthy = healthStatus === 'ok';

  return (
    <header className="navbar">
      <div className="navbar-left">
        <div
          className="navbar-brand clickable"
          onClick={() => onTabChange('landing')}
          title="Return to VisionIQ Overview"
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && onTabChange('landing')}
        >
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
          id="tab-overview"
          role="tab"
          aria-selected={activeTab === 'landing'}
          className={`tab-btn ${activeTab === 'landing' ? 'active' : ''}`}
          onClick={() => onTabChange('landing')}
        >
          <LayoutDashboard size={15} />
          <span>Overview</span>
        </button>
        <button
          id="tab-image-intelligence"
          role="tab"
          aria-selected={activeTab === 'image'}
          className={`tab-btn ${activeTab === 'image' ? 'active' : ''}`}
          onClick={() => onTabChange('image')}
        >
          <ImageIcon size={15} />
          <span>Image Intelligence</span>
        </button>
        <button
          id="tab-video-intelligence"
          role="tab"
          aria-selected={activeTab === 'video'}
          className={`tab-btn ${activeTab === 'video' ? 'active' : ''}`}
          onClick={() => onTabChange('video')}
        >
          <VideoIcon size={15} />
          <span>Video Intelligence</span>
        </button>
      </nav>

      <div className="navbar-right">
        {currentUser ? (
          <>
            <div className="user-profile-pill" title={`Signed in as ${currentUser.email}`}>
              <div className="user-avatar-circle">
                <UserIcon size={12} />
              </div>
              <span className="user-profile-name">{currentUser.name}</span>
              {currentUser.isGuest && <span className="guest-badge">Guest</span>}
            </div>

            {onLogout && (
              <button
                id="btn-logout"
                className="navbar-logout-btn"
                onClick={onLogout}
                title="Sign out of current session"
              >
                <LogOut size={13} />
                <span>Sign Out</span>
              </button>
            )}
          </>
        ) : (
          onOpenAuth && (
            <button
              id="btn-navbar-signin"
              className="btn-navbar-signin"
              onClick={onOpenAuth}
              title="Sign in to VisionIQ"
            >
              <LogIn size={13} />
              <span>Sign In</span>
            </button>
          )
        )}

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
