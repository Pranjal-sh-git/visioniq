import React from 'react';
import {
  Sparkles,
  Eye,
  Video,
  ArrowRight,
  Database,
  Cpu,
  ShieldCheck,
  Layers,
  CheckCircle,
} from 'lucide-react';

interface LandingPageProps {
  onNavigate: (tab: 'image' | 'video') => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onNavigate }) => {
  return (
    <div className="landing-container">
      {/* Hero Section */}
      <section className="landing-hero">
        <div className="hero-badge">
          <span className="badge-pulse" />
          <Sparkles size={14} className="badge-icon" />
          <span>Multimodal Intelligence Platform</span>
        </div>

        <h1 className="hero-title">
          Vision<span className="hero-title-accent">IQ</span>
        </h1>

        <p className="hero-tagline">
          Multimodal AI that <span className="highlight-mint">sees</span>, <span className="highlight-mint">understands</span>, and <span className="highlight-mint">answers</span>.
        </p>

        <p className="hero-description">
          Seamlessly identify real-world products, books, and objects from photos with zero-shot vision, 
          query grounded catalog specs with vector RAG, and retrieve exact temporal moments in video.
        </p>

        <div className="hero-cta-group">
          <button
            id="hero-cta-primary"
            className="btn-dark-cta"
            onClick={() => onNavigate('image')}
          >
            <span>Try it now</span>
            <ArrowRight size={16} />
          </button>

          <button
            id="hero-cta-video"
            className="btn-light-secondary"
            onClick={() => onNavigate('video')}
          >
            <Video size={16} className="btn-icon-mint" />
            <span>Video Intelligence</span>
          </button>
        </div>
      </section>

      {/* Two Large Interactive Feature Cards */}
      <section className="landing-cards-grid">
        {/* Card 1: Image Intelligence */}
        <div
          id="feature-card-image"
          className="feature-card"
          onClick={() => onNavigate('image')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && onNavigate('image')}
        >
          <div className="feature-card-header">
            <div className="feature-icon-wrapper">
              <Eye size={24} />
            </div>
            <span className="feature-badge">Open-World Vision</span>
          </div>

          <h3 className="feature-card-title">Image Intelligence</h3>
          <p className="feature-card-desc">
            Upload arbitrary user photos to recognize commercial products, books, apparel, and hardware without closed-set hallucinations.
          </p>

          <ul className="feature-highlights">
            <li>
              <CheckCircle size={15} className="highlight-icon" />
              <span>Zero-shot visual entity recognition with OCR</span>
            </li>
            <li>
              <CheckCircle size={15} className="highlight-icon" />
              <span>Cosine vector similarity catalog recommendations</span>
            </li>
            <li>
              <CheckCircle size={15} className="highlight-icon" />
              <span>Grounded RAG specification & multi-turn QA</span>
            </li>
          </ul>

          <div className="feature-card-footer">
            <span className="footer-action-text">Launch Image Intelligence</span>
            <div className="action-circle">
              <ArrowRight size={15} />
            </div>
          </div>
        </div>

        {/* Card 2: Video Intelligence */}
        <div
          id="feature-card-video"
          className="feature-card"
          onClick={() => onNavigate('video')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && onNavigate('video')}
        >
          <div className="feature-card-header">
            <div className="feature-icon-wrapper">
              <Video size={24} />
            </div>
            <span className="feature-badge">Temporal Moments</span>
          </div>

          <h3 className="feature-card-title">Video Intelligence</h3>
          <p className="feature-card-desc">
            Search natural language queries across timestamped transcripts, extract reviewer insights, and jump straight to relevant moments.
          </p>

          <ul className="feature-highlights">
            <li>
              <CheckCircle size={15} className="highlight-icon" />
              <span>Whisper ASR audio speech transcription</span>
            </li>
            <li>
              <CheckCircle size={15} className="highlight-icon" />
              <span>Segment-level temporal relevance indexing</span>
            </li>
            <li>
              <CheckCircle size={15} className="highlight-icon" />
              <span>Interactive jump-to-timestamp video playback</span>
            </li>
          </ul>

          <div className="feature-card-footer">
            <span className="footer-action-text">Launch Video Intelligence</span>
            <div className="action-circle">
              <ArrowRight size={15} />
            </div>
          </div>
        </div>
      </section>

      {/* Powered by Azure AI Foundry - Gradient Pro Strip */}
      <section className="landing-gradient-strip">
        <div className="gradient-strip-left">
          <div className="strip-icon-box">
            <Cpu size={20} />
          </div>
          <div>
            <div className="strip-title">Powered by Azure AI Foundry & OpenAI</div>
            <div className="strip-subtitle">
              Enterprise-grade foundation models (gpt-5-mini), vector search, and Responsible AI guardrails.
            </div>
          </div>
        </div>

        <div className="gradient-strip-badges">
          <div className="glass-badge">
            <Sparkles size={13} />
            <span>Azure OpenAI</span>
          </div>
          <div className="glass-badge">
            <Database size={13} />
            <span>AI Search RAG</span>
          </div>
          <div className="glass-badge">
            <Layers size={13} />
            <span>CLIP Embeddings</span>
          </div>
          <div className="glass-badge">
            <ShieldCheck size={13} />
            <span>Responsible AI</span>
          </div>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;
