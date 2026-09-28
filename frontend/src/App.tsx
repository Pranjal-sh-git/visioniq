import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import LandingPage from './pages/LandingPage';
import ImageIntelligence from './pages/ImageIntelligence';
import VideoIntelligence from './pages/VideoIntelligence';
import AuthPage from './pages/AuthPage';
import { getHealthStatus } from './services/api';
import { Layers, ShieldCheck, Database, Zap } from 'lucide-react';

export const App: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    return localStorage.getItem('visioniq_demo_session') === 'true';
  });

  const [currentUser, setCurrentUser] = useState<{ name: string; email: string; isGuest?: boolean } | null>(() => {
    try {
      const stored = localStorage.getItem('visioniq_user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const [activeTab, setActiveTab] = useState<'landing' | 'image' | 'video'>('landing');
  const [showAuthPage, setShowAuthPage] = useState<boolean>(false);
  const [pendingTargetTab, setPendingTargetTab] = useState<'image' | 'video' | null>(null);
  const [healthStatus, setHealthStatus] = useState<string>('checking...');

  useEffect(() => {
    let isMounted = true;

    const checkHealth = () => {
      getHealthStatus()
        .then((data) => {
          if (isMounted) setHealthStatus(data.status);
        })
        .catch(() => {
          if (isMounted) setHealthStatus('offline');
        });
    };

    checkHealth();
    const interval = setInterval(checkHealth, 4000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleNavigate = (tab: 'landing' | 'image' | 'video') => {
    if (tab === 'landing') {
      setShowAuthPage(false);
      setActiveTab('landing');
      return;
    }

    // If accessing image or video intelligence without auth, show login page
    if (!isAuthenticated) {
      setPendingTargetTab(tab);
      setShowAuthPage(true);
    } else {
      setShowAuthPage(false);
      setActiveTab(tab);
    }
  };

  const handleOpenAuth = (defaultTarget: 'image' | 'video' = 'image') => {
    setPendingTargetTab(defaultTarget);
    setShowAuthPage(true);
  };

  const handleLoginSuccess = (user: { name: string; email: string; isGuest?: boolean }) => {
    setCurrentUser(user);
    setIsAuthenticated(true);
    setShowAuthPage(false);
    const target = pendingTargetTab || 'image';
    setActiveTab(target);
    setPendingTargetTab(null);
  };

  const handleBackToOverview = () => {
    setShowAuthPage(false);
    setActiveTab('landing');
    setPendingTargetTab(null);
  };

  const handleLogout = () => {
    localStorage.removeItem('visioniq_demo_session');
    localStorage.removeItem('visioniq_user');
    setCurrentUser(null);
    setIsAuthenticated(false);
    setShowAuthPage(false);
    setActiveTab('landing');
    setPendingTargetTab(null);
  };

  if (showAuthPage) {
    return (
      <div className="app-container">
        <div className="ambient-glow" />
        <AuthPage
          onLoginSuccess={handleLoginSuccess}
          onBack={handleBackToOverview}
          intendedTab={pendingTargetTab || 'image'}
        />
      </div>
    );
  }

  return (
    <div className="app-container">
      <div className="ambient-glow" />
      <Navbar
        activeTab={activeTab}
        onTabChange={handleNavigate}
        healthStatus={healthStatus}
        currentUser={currentUser}
        onLogout={handleLogout}
        onOpenAuth={() => handleOpenAuth('image')}
      />
      
      <main className="main-content">
        <div className={`tab-pane ${activeTab === 'landing' ? 'active' : 'is-hidden'}`}>
          <LandingPage onNavigate={(tab) => handleNavigate(tab)} />
        </div>
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
