import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  Eye,
  Video,
  ArrowRight,
  Database,
  Cpu,
  Layers,
  CheckCircle,
  UploadCloud,
  Search,
  MessageSquareQuote,
  Zap,
  Mic,
} from 'lucide-react';

interface LandingPageProps {
  onNavigate: (tab: 'image' | 'video') => void;
}

// Smooth quadratic easing for counter
const easeOutQuad = (t: number) => t * (2 - t);

export const LandingPage: React.FC<LandingPageProps> = ({ onNavigate }) => {
  const statsRef = useRef<HTMLDivElement>(null);
  const [hasAnimated, setHasAnimated] = useState(false);

  // Counter States
  const [top1Acc, setTop1Acc] = useState(0);
  const [top3Acc, setTop3Acc] = useState(0);
  const [rejectionRate, setRejectionRate] = useState(0);
  const [latency, setLatency] = useState(0);

  // IntersectionObserver for general scroll-reveal sections
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-revealed');
          }
        });
      },
      { threshold: 0.12 }
    );

    const elements = document.querySelectorAll('.scroll-reveal');
    elements.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, []);

  // IntersectionObserver specifically for Stats count-up
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (entry.isIntersecting && !hasAnimated) {
          setHasAnimated(true);

          const duration = 900; // ms
          const startTime = performance.now();

          const animate = (currentTime: number) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = easeOutQuad(progress);

            setTop1Acc(Math.round(eased * 65));
            setTop3Acc(Math.round(eased * 80));
            setRejectionRate(Math.round(eased * 100));
            setLatency(parseFloat((eased * 3.07).toFixed(2)));

            if (progress < 1) {
              requestAnimationFrame(animate);
            } else {
              setLatency(3.07);
              setTop1Acc(65);
              setTop3Acc(80);
              setRejectionRate(100);
            }
          };

          requestAnimationFrame(animate);
        }
      },
      { threshold: 0.2 }
    );

    if (statsRef.current) {
      observer.observe(statsRef.current);
    }

    return () => observer.disconnect();
  }, [hasAnimated]);

  return (
    <div className="landing-container">
      {/* 1. Hero Section */}
      <section className="landing-hero scroll-reveal is-revealed">
        <div className="hero-badge">
          <span className="badge-pulse" />
          <Sparkles size={14} className="badge-icon" />
          <span>Multimodal Intelligence Platform</span>
        </div>

        <h1 className="hero-title">
          Vision<span className="hero-title-accent">IQ</span>
        </h1>

        <p className="hero-tagline">
          Multimodal AI that <span className="highlight-mint">sees</span>,{' '}
          <span className="highlight-mint">understands</span>, and{' '}
          <span className="highlight-mint">answers</span>.
        </p>

        <p className="hero-description">
          Seamlessly identify real-world products, books, and objects from photos with
          zero-shot vision, query grounded catalog specs with vector RAG, and retrieve
          exact temporal moments in video.
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

      {/* 2. Two Large Interactive Feature Cards (Right Below Hero) */}
      <section className="landing-cards-grid scroll-reveal">
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

      {/* 3. Stats Section (Horizontal Trust Strip) */}
      <section className="landing-stats-section scroll-reveal" ref={statsRef}>
        <div className="stats-section-header">
          <span className="section-eyebrow">TRUSTED & GROUNDED</span>
          <h2 className="stats-section-heading">Numbers that back the claims</h2>
        </div>

        <div className="stats-row">
          <div className="stat-col">
            <div className="stat-number">
              0.0<span className="stat-unit">%</span>
            </div>
            <div className="stat-label">Hallucination Rate</div>
          </div>

          <div className="stat-divider-line" />

          <div className="stat-col">
            <div className="stat-number">
              {top1Acc}% <span className="stat-sub-number">/ {top3Acc}%</span>
            </div>
            <div className="stat-label">Top-1 / Top-3 Accuracy</div>
          </div>

          <div className="stat-divider-line" />

          <div className="stat-col">
            <div className="stat-number">
              {rejectionRate}<span className="stat-unit">%</span>
            </div>
            <div className="stat-label">Out-of-Catalog Rejection</div>
          </div>

          <div className="stat-divider-line" />

          <div className="stat-col">
            <div className="stat-number">
              {latency.toFixed(2)}<span className="stat-unit">s</span>
            </div>
            <div className="stat-label">Mean Query Latency</div>
          </div>
        </div>
      </section>

      {/* 4. How It Works (3-Step Horizontal Flow) */}
      <section className="landing-workflow-section scroll-reveal">
        <div className="workflow-section-header">
          <span className="section-eyebrow">WORKFLOW</span>
          <h2 className="section-heading">From Raw Media to Grounded Answers</h2>
          <p className="section-description">
            A frictionless three-step multimodal pipeline built for sub-second precision.
          </p>
        </div>

        <div className="workflow-steps-grid">
          {/* Step 1 */}
          <div className="workflow-step-card">
            <div className="step-header">
              <div className="step-icon-box">
                <UploadCloud size={20} />
              </div>
              <span className="step-number">01</span>
            </div>
            <h3 className="step-title">Upload & Ingest</h3>
            <p className="step-desc">
              Drop arbitrary product photos, book covers, or video URLs with no prior manual tagging or dataset labeling.
            </p>
          </div>

          {/* Step 2 */}
          <div className="workflow-step-card">
            <div className="step-header">
              <div className="step-icon-box">
                <Search size={20} />
              </div>
              <span className="step-number">02</span>
            </div>
            <h3 className="step-title">Identify & Ground</h3>
            <p className="step-desc">
              Zero-shot vision extracts OCR and visual tokens, querying Azure AI Search vector indexes with cosine similarity.
            </p>
          </div>

          {/* Step 3 */}
          <div className="workflow-step-card">
            <div className="step-header">
              <div className="step-icon-box">
                <MessageSquareQuote size={20} />
              </div>
              <span className="step-number">03</span>
            </div>
            <h3 className="step-title">Ask Anything</h3>
            <p className="step-desc">
              Execute conversational grounded QA with strict catalog citations or jump to exact transcript timestamps.
            </p>
          </div>
        </div>
      </section>

      {/* 5. "Powered By" Minimalist Tech Strip */}
      <section className="landing-tech-strip scroll-reveal">
        <span className="tech-strip-label">BUILT ON FOUNDATION INFRASTRUCTURE</span>
        <div className="tech-badges-row">
          <div className="tech-badge-item">
            <Cpu size={14} className="tech-badge-icon" />
            <span>Azure AI Foundry</span>
          </div>
          <div className="tech-badge-item">
            <Database size={14} className="tech-badge-icon" />
            <span>Azure AI Search</span>
          </div>
          <div className="tech-badge-item">
            <Sparkles size={14} className="tech-badge-icon" />
            <span>gpt-5-mini</span>
          </div>
          <div className="tech-badge-item">
            <Layers size={14} className="tech-badge-icon" />
            <span>CLIP Embeddings</span>
          </div>
          <div className="tech-badge-item">
            <Mic size={14} className="tech-badge-icon" />
            <span>Whisper ASR</span>
          </div>
          <div className="tech-badge-item">
            <Zap size={14} className="tech-badge-icon" />
            <span>Content Understanding</span>
          </div>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;

