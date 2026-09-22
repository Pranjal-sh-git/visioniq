import React from 'react';
import {
  Sparkles,
  Eye,
  Video,
  ArrowRight,
  Database,
  Cpu,
  ShieldCheck,
  Search,
  Zap,
  Layers,
  FileText,
} from 'lucide-react';

interface LandingPageProps {
  onNavigate: (tab: 'image' | 'video') => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onNavigate }) => {
  return (
    <div className="landing-container">
      {/* Background Lighting Meshes */}
      <div className="landing-mesh-1" />
      <div className="landing-mesh-2" />

      {/* Hero Section */}
      <section className="landing-hero">
        <div className="hero-badge">
          <span className="badge-pulse" />
          <Sparkles size={13} className="badge-icon" />
          <span>Multimodal Agent Platform</span>
        </div>

        <h1 className="hero-title">
          Vision<span className="hero-title-accent">IQ</span>
        </h1>

        <p className="hero-tagline">
          Multimodal AI that sees, understands, and answers.
        </p>

        <p className="hero-description">
          Seamlessly identify real-world products from arbitrary photos, query grounded specifications via vector RAG, 
          and search temporal moments in demonstration videos with exact timestamp retrieval.
        </p>

        <div className="hero-cta-group">
          <button
            id="hero-cta-image"
            className="btn-primary-hero"
            onClick={() => onNavigate('image')}
          >
            <Eye size={18} />
            <span>Launch Image Intelligence</span>
            <ArrowRight size={16} className="btn-arrow" />
          </button>

          <button
            id="hero-cta-video"
            className="btn-secondary-hero"
            onClick={() => onNavigate('video')}
          >
            <Video size={18} />
            <span>Launch Video Intelligence</span>
            <ArrowRight size={16} className="btn-arrow" />
          </button>
        </div>
      </section>

      {/* Two Large Interactive Feature Cards */}
      <section className="landing-cards-grid">
        {/* Card 1: Image Intelligence */}
        <div
          id="feature-card-image"
          className="feature-card feature-card-image"
          onClick={() => onNavigate('image')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && onNavigate('image')}
        >
          <div className="feature-card-glow" />
          <div className="feature-card-header">
            <div className="feature-icon-wrapper icon-cyan">
              <Eye size={26} />
            </div>
            <div className="feature-pill">Open-World Vision</div>
          </div>

          <h3 className="feature-card-title">Image Intelligence</h3>
          <p className="feature-card-desc">
            Upload arbitrary user photos to recognize commercial products, books, apparel, and hardware without closed-set hallucinations.
          </p>

          <ul className="feature-highlights">
            <li>
              <Search size={14} className="highlight-icon" />
              <span>Zero-shot visual entity recognition with OCR</span>
            </li>
            <li>
              <Database size={14} className="highlight-icon" />
              <span>Cosine vector similarity catalog recommendations</span>
            </li>
            <li>
              <FileText size={14} className="highlight-icon" />
              <span>Grounded RAG specification & multi-turn QA</span>
            </li>
          </ul>

          <div className="feature-card-footer">
            <span className="footer-action-text">Explore Image Intelligence</span>
            <div className="action-circle">
              <ArrowRight size={16} />
            </div>
          </div>
        </div>

        {/* Card 2: Video Intelligence */}
        <div
          id="feature-card-video"
          className="feature-card feature-card-video"
          onClick={() => onNavigate('video')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && onNavigate('video')}
        >
          <div className="feature-card-glow" />
          <div className="feature-card-header">
            <div className="feature-icon-wrapper icon-purple">
              <Video size={26} />
            </div>
            <div className="feature-pill">Temporal Moments</div>
          </div>

          <h3 className="feature-card-title">Video Intelligence</h3>
          <p className="feature-card-desc">
            Search natural language queries across timestamped transcripts, extract reviewer insights, and jump straight to relevant moments.
          </p>

          <ul className="feature-highlights">
            <li>
              <Zap size={14} className="highlight-icon" />
              <span>Whisper ASR audio speech transcription</span>
            </li>
            <li>
              <Layers size={14} className="highlight-icon" />
              <span>Segment-level temporal relevance indexing</span>
            </li>
            <li>
              <ArrowRight size={14} className="highlight-icon" />
              <span>Interactive jump-to-timestamp video playback</span>
            </li>
          </ul>

          <div className="feature-card-footer">
            <span className="footer-action-text">Explore Video Intelligence</span>
            <div className="action-circle">
              <ArrowRight size={16} />
            </div>
          </div>
        </div>
      </section>

      {/* Powered by Azure AI Foundry Credibility Strip */}
      <section className="landing-credibility-strip">
        <div className="credibility-header">
          <Cpu size={14} className="credibility-icon" />
          <span>Powered by Microsoft Azure AI & OpenAI Foundation Models</span>
        </div>

        <div className="credibility-badges">
          <div className="cred-badge">
            <Sparkles size={13} />
            <span>Azure OpenAI (gpt-5-mini)</span>
          </div>
          <div className="cred-badge">
            <Database size={13} />
            <span>Azure AI Search (Vector RAG)</span>
          </div>
          <div className="cred-badge">
            <Layers size={13} />
            <span>CLIP ViT-B/32 Embeddings</span>
          </div>
          <div className="cred-badge">
            <ShieldCheck size={13} />
            <span>Microsoft Responsible AI</span>
          </div>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;
