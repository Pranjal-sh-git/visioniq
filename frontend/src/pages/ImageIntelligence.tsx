import React, { useState, useRef } from 'react';
import {
  identifyProduct,
  queryAgent,
  ProductMatch,
  OpenWorldProductIdentification,
  SimilarCatalogProduct,
  AgentQueryResponse,
} from '../services/api';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  toolUsed?: string;
  reasoning?: string;
  similarProducts?: ProductMatch[];
  isClarification?: boolean;
}

const SAMPLE_IMAGES = [
  {
    label: 'Sony WH-1000XM5 (Catalog Match)',
    url: 'https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=800&q=80',
  },
  {
    label: 'Herman Miller Aeron Chair',
    url: 'https://images.unsplash.com/photo-1580481077197-987823563052?auto=format&fit=crop&w=800&q=80',
  },
  {
    label: 'Nike Air Zoom Shoe',
    url: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80',
  },
];

const VALID_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'];

export const ImageIntelligence: React.FC = () => {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [isIdentifying, setIsIdentifying] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Open-World Identification & Catalog Recommendations
  const [identifiedProduct, setIdentifiedProduct] = useState<OpenWorldProductIdentification | null>(null);
  const [similarCatalog, setSimilarCatalog] = useState<SimilarCatalogProduct[]>([]);
  const [selectedCatalogItem, setSelectedCatalogItem] = useState<SimilarCatalogProduct | null>(null);

  // Agent Chat State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputPrompt, setInputPrompt] = useState<string>('');
  const [isAgentLoading, setIsAgentLoading] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  const isApiActive = isIdentifying || isAgentLoading;

  const scrollToBottom = () => {
    setTimeout(() => {
      chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  const validateImageFile = (file: File): boolean => {
    const hasImageMime = file.type.startsWith('image/');
    const fileNameLower = file.name.toLowerCase();
    const hasValidExtension = VALID_IMAGE_EXTENSIONS.some((ext) => fileNameLower.endsWith(ext));

    if (!hasImageMime && !hasValidExtension) {
      setErrorMessage(
        `Invalid file type: "${file.name}". Please upload a valid image file (${VALID_IMAGE_EXTENSIONS.join(', ')}).`
      );
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      return false;
    }
    return true;
  };

  const handleFileSelection = async (file: File) => {
    if (!validateImageFile(file)) {
      return;
    }

    setErrorMessage(null);
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);
    setIdentifiedProduct(null);
    setSimilarCatalog([]);
    setSelectedCatalogItem(null);
    setMessages([]);

    await runIdentification(file);
  };

  const handleSampleSelect = async (sampleUrl: string) => {
    setErrorMessage(null);
    setPreviewUrl(sampleUrl);
    setIdentifiedProduct(null);
    setSimilarCatalog([]);
    setSelectedCatalogItem(null);
    setMessages([]);

    await runIdentification(sampleUrl);
  };

  const runIdentification = async (fileOrUrl: File | string) => {
    setIsIdentifying(true);
    setErrorMessage(null);

    try {
      const result = await identifyProduct(fileOrUrl, 3);
      if (result.success && result.identified_product) {
        setIdentifiedProduct(result.identified_product);
        const catalogList = result.similar_catalog_products || result.all_matches || [];
        setSimilarCatalog(catalogList);
        setSelectedCatalogItem(result.catalog_match || (catalogList.length > 0 ? catalogList[0] : null));

        const prod = result.identified_product;
        const welcomeText = `Identified as **${prod.product_name}** (${prod.brand} · ${prod.category}) with ${prod.confidence} confidence.\n\n${prod.visual_description}`;

        setMessages([
          {
            id: 'init-1',
            sender: 'assistant',
            text: welcomeText,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            similarProducts: catalogList,
          },
        ]);
      } else if (result.best_match) {
        // Fallback for legacy format
        setSimilarCatalog(result.all_matches || []);
        setSelectedCatalogItem(result.best_match);
        setMessages([
          {
            id: 'init-legacy',
            sender: 'assistant',
            text: `Closest match: **${result.best_match.brand} ${result.best_match.name}**. You can ask follow-up questions!`,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
      } else {
        setMessages([
          {
            id: 'init-empty',
            sender: 'assistant',
            text: 'No product could be visually identified. Feel free to try another photo.',
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
      }
    } catch (err: any) {
      console.error('Identification error:', err);
      setErrorMessage(err.message || "Couldn't connect to the backend server. Please verify the backend is running.");
    } finally {
      setIsIdentifying(false);
    }
  };

  const handleSendMessage = async (promptToSend?: string) => {
    const queryText = (promptToSend || inputPrompt).trim();
    if (!queryText || isAgentLoading) return;

    // Check if an image or product has been loaded first
    if (!identifiedProduct && !previewUrl && !selectedCatalogItem) {
      const promptMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        sender: 'user',
        text: queryText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      const guidanceMsg: ChatMessage = {
        id: `guide-${Date.now()}`,
        sender: 'assistant',
        text: 'Please upload or select a product image first so I can inspect its visual details and ground technical specifications.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, promptMsg, guidanceMsg]);
      setInputPrompt('');
      scrollToBottom();
      return;
    }

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: queryText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputPrompt('');
    setIsAgentLoading(true);
    scrollToBottom();

    try {
      const activeProductId = selectedCatalogItem?.id;
      const mediaContext = typeof previewUrl === 'string' && previewUrl.startsWith('http') ? previewUrl : undefined;

      const response: AgentQueryResponse = await queryAgent(
        queryText,
        activeProductId,
        undefined,
        mediaContext
      );

      const toolOutput = response.tool_output || {};
      let replyText = toolOutput.answer || 'I could not find an answer for that request.';
      const isClarification = Boolean(toolOutput.requires_clarification);
      const similarProds = toolOutput.similar_products || [];

      const assistantMsg: ChatMessage = {
        id: `asst-${Date.now()}`,
        sender: 'assistant',
        text: replyText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        toolUsed: response.selected_tool,
        reasoning: response.routing_reasoning,
        similarProducts: similarProds.length > 0 ? similarProds : undefined,
        isClarification,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      console.error('Agent query error:', err);
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: 'assistant',
        text: err.message || "Couldn't connect to the server. Please check your backend connection.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsAgentLoading(false);
      scrollToBottom();
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const clearSelection = () => {
    setPreviewUrl(null);
    setIdentifiedProduct(null);
    setSimilarCatalog([]);
    setSelectedCatalogItem(null);
    setMessages([]);
    setErrorMessage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="tab-page">
      {/* Top Header */}
      <div className="tab-header">
        <div className="tab-header-titles">
          <h1>Open-World Image Intelligence</h1>
          <p>
            Upload any product image for real-time multimodal visual identification via{' '}
            <strong>Azure OpenAI gpt-5-mini</strong>, and explore similar catalog alternatives.
          </p>
        </div>
        {isApiActive && (
          <div className="api-live-indicator">
            <span className="pulse-dot" />
            <span>Processing with Azure AI...</span>
          </div>
        )}
      </div>

      {/* Inline Error Banner */}
      {errorMessage && (
        <div className="error-banner">
          <div className="error-msg">
            <span>⚠️</span>
            <span>{errorMessage}</span>
          </div>
          <button
            className="error-close-btn"
            onClick={() => setErrorMessage(null)}
            title="Dismiss error"
          >
            ×
          </button>
        </div>
      )}

      {/* Main Grid */}
      <div className="dashboard-grid">
        {/* Left Column: Upload & Identification Display */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Upload Card */}
          <div className="card">
            <div className="card-title">
              <span>Product Image Upload</span>
              {previewUrl && (
                <button
                  className="btn btn-secondary"
                  style={{ fontSize: '0.8rem', padding: '0.3rem 0.7rem' }}
                  onClick={clearSelection}
                >
                  Clear Image
                </button>
              )}
            </div>

            {/* Drag and Drop Zone */}
            <div
              className={`dropzone ${isDragging ? 'dragover' : ''}`}
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                type="file"
                ref={fileInputRef}
                style={{ display: 'none' }}
                accept="image/*"
                onChange={(e) => {
                  if (e.target.files && e.target.files.length > 0) {
                    handleFileSelection(e.target.files[0]);
                  }
                }}
              />

              {previewUrl ? (
                <div style={{ position: 'relative' }}>
                  <img src={previewUrl} alt="Uploaded preview" className="preview-image" />
                  <div style={{ marginTop: '0.75rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                    Click or drop another image to replace
                  </div>
                </div>
              ) : (
                <>
                  <div className="dropzone-icon">📷</div>
                  <div className="dropzone-title">Drop your product photo here</div>
                  <div className="dropzone-subtitle">
                    Supports JPG, PNG, WEBP · Open-world recognition for ANY item
                  </div>
                </>
              )}
            </div>

            {/* Sample Image Presets */}
            <div className="sample-presets">
              <span className="sample-title">Try quick samples:</span>
              <div className="sample-chips">
                {SAMPLE_IMAGES.map((sample, idx) => (
                  <button
                    key={idx}
                    className="sample-chip"
                    onClick={() => handleSampleSelect(sample.url)}
                    disabled={isIdentifying}
                  >
                    {sample.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Loading Spinner State */}
          {isIdentifying && (
            <div className="card" style={{ textAlign: 'center', padding: '2.5rem' }}>
              <div className="spinner" style={{ margin: '0 auto 1.25rem' }} />
              <div style={{ fontWeight: 600, fontSize: '1.05rem', color: 'var(--text-primary)' }}>
                Analyzing Visual Features with gpt-5-mini...
              </div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '0.4rem' }}>
                Extracting brand, model, silhouette, and querying catalog vectors
              </div>
            </div>
          )}

          {/* PRIMARY: Open-World Recognition Card */}
          {!isIdentifying && identifiedProduct && (
            <div className="card open-world-card">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                <span className="ai-vision-tag">✨ Open-World AI Recognition</span>
                <span className={`confidence-pill confidence-${identifiedProduct.confidence}`}>
                  {identifiedProduct.confidence === 'high' ? '● High Confidence' : identifiedProduct.confidence === 'medium' ? '◐ Medium Confidence' : '○ Low Confidence'}
                </span>
              </div>

              <div style={{ marginBottom: '0.5rem' }}>
                <div style={{ fontSize: '0.85rem', color: 'var(--accent-color)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  {identifiedProduct.brand}
                </div>
                <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-primary)', margin: '0.2rem 0 0.5rem' }}>
                  {identifiedProduct.product_name}
                </h2>
                <span className="badge badge-category">{identifiedProduct.category}</span>
              </div>

              {/* Visual Observations Summary */}
              {identifiedProduct.visual_description && (
                <div className="visual-obs-box">
                  <div className="visual-obs-title">Visual Analysis & Observations</div>
                  <div>{identifiedProduct.visual_description}</div>
                </div>
              )}

              {/* Key Features Observed */}
              {identifiedProduct.key_features_observed && identifiedProduct.key_features_observed.length > 0 && (
                <div>
                  <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Observed Physical Attributes
                  </div>
                  <div className="feature-pills-wrap">
                    {identifiedProduct.key_features_observed.map((feat, idx) => (
                      <span key={idx} className="feature-pill">
                        ✓ {feat}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* SECONDARY: Similar Options in Our Catalog */}
              {similarCatalog.length > 0 && (
                <div className="similar-catalog-section">
                  <div className="similar-catalog-header">
                    <div>
                      <div className="similar-catalog-title">
                        <span>📦 Similar Options in Our Catalog</span>
                      </div>
                      <div className="similar-catalog-subtitle">
                        Closest matching items indexed in Azure AI Search
                      </div>
                    </div>
                  </div>

                  <div className="similar-catalog-grid">
                    {similarCatalog.map((item) => {
                      const isSelected = selectedCatalogItem?.id === item.id;
                      return (
                        <div
                          key={item.id}
                          className={`similar-catalog-card ${isSelected ? 'active-catalog-item' : ''}`}
                          onClick={() => setSelectedCatalogItem(item)}
                          title={`Click to set ${item.name} as active chat context`}
                        >
                          <div className="similar-card-left">
                            {item.image_urls && item.image_urls.length > 0 ? (
                              <img src={item.image_urls[0]} alt={item.name} className="similar-thumb" />
                            ) : (
                              <div className="similar-thumb" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(51, 65, 85, 0.5)' }}>
                                📦
                              </div>
                            )}
                            <div>
                              <div className="similar-info-name">
                                {item.brand} {item.name}
                              </div>
                              <div className="similar-info-meta">
                                <span>{item.category}</span>
                                {item.specifications?.battery_life && (
                                  <span>• 🔋 {item.specifications.battery_life}</span>
                                )}
                                {item.specifications?.weight && (
                                  <span>• ⚖️ {item.specifications.weight}</span>
                                )}
                              </div>
                            </div>
                          </div>
                          <div style={{ textAlign: 'right' }}>
                            <span className="similar-score-badge">
                              {item.is_exact_catalog_match ? '★ Exact Match' : `${(item.similarity_score * 100).toFixed(0)}% Visual Match`}
                            </span>
                            {isSelected && (
                              <div style={{ fontSize: '0.7rem', color: 'var(--accent-color)', marginTop: '0.2rem', fontWeight: 600 }}>
                                Active Context
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Agent Chat Interface */}
        <div>
          <div className="chat-container">
            <div className="chat-header">
              <div className="chat-title">
                <span>💬 VisionIQ Assistant</span>
                <span className="agent-badge">Foundry Agent</span>
              </div>
              {identifiedProduct ? (
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Active: {identifiedProduct.brand} {identifiedProduct.model || identifiedProduct.product_name.substring(0, 18)}
                </span>
              ) : selectedCatalogItem ? (
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Target: {selectedCatalogItem.name.substring(0, 24)}...
                </span>
              ) : null}
            </div>

            <div className="chat-messages">
              {messages.length === 0 ? (
                <div style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: '5rem', fontSize: '0.9rem' }}>
                  {previewUrl
                    ? 'Image loaded. Ask questions about observed features, specs, or catalog alternatives!'
                    : 'Upload a product image to start chatting about open-world recognition and catalog specs.'}
                </div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`message-bubble ${msg.sender === 'user' ? 'message-user' : 'message-assistant'}`}
                  >
                    <div style={{ whiteSpace: 'pre-line' }}>{msg.text}</div>

                    {/* Similar Products Carousel / Cards if returned */}
                    {msg.similarProducts && msg.similarProducts.length > 0 && (
                      <div className="similar-cards-grid">
                        {msg.similarProducts.map((p) => (
                          <div
                            key={p.id}
                            className="similar-card"
                            onClick={() => setSelectedCatalogItem(p as SimilarCatalogProduct)}
                            style={{ cursor: 'pointer' }}
                            title={`Select ${p.name}`}
                          >
                            <div className="similar-card-brand">{p.brand}</div>
                            <div className="similar-card-name">{p.name}</div>
                            <div className="similar-card-score">
                              {(p.similarity_score * 100).toFixed(0)}% similar
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {msg.toolUsed && (
                      <div className="message-meta">
                        <span className="tool-tag">🔧 {msg.toolUsed}</span>
                      </div>
                    )}
                  </div>
                ))
              )}

              {isAgentLoading && (
                <div className="message-bubble message-assistant" style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <div className="spinner spinner-sm-light" />
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    Agent reasoning & synthesizing answer...
                  </span>
                </div>
              )}
              <div ref={chatBottomRef} />
            </div>

            {/* Quick Action Suggestion Chips */}
            <div className="quick-prompts">
              <button
                className="quick-chip"
                onClick={() => handleSendMessage("What are the key observed visual features of this item?")}
                disabled={isAgentLoading || (!identifiedProduct && !selectedCatalogItem)}
                title={!identifiedProduct ? "Upload an image first" : undefined}
              >
                🔍 Observed features?
              </button>
              <button
                className="quick-chip"
                onClick={() => handleSendMessage("What is its battery life?")}
                disabled={isAgentLoading || (!identifiedProduct && !selectedCatalogItem)}
                title={!identifiedProduct ? "Upload an image first" : undefined}
              >
                🔋 Battery life?
              </button>
              <button
                className="quick-chip"
                onClick={() => handleSendMessage("Show me similar products in our catalog")}
                disabled={isAgentLoading || (!identifiedProduct && !selectedCatalogItem)}
                title={!identifiedProduct ? "Upload an image first" : undefined}
              >
                🔄 Similar catalog items
              </button>
              <button
                className="quick-chip"
                onClick={() => handleSendMessage("Is this comfortable for long working hours or travel?")}
                disabled={isAgentLoading || (!identifiedProduct && !selectedCatalogItem)}
                title={!identifiedProduct ? "Upload an image first" : undefined}
              >
                ✈️ Travel / Comfort?
              </button>
            </div>

            {/* Input Bar */}
            <form
              className="chat-input-bar"
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
            >
              <input
                type="text"
                className="chat-input"
                placeholder={
                  identifiedProduct || selectedCatalogItem
                    ? `Ask anything about ${identifiedProduct?.brand || selectedCatalogItem?.brand || 'this product'}...`
                    : "Upload a product image first to start chatting..."
                }
                value={inputPrompt}
                onChange={(e) => setInputPrompt(e.target.value)}
                disabled={isAgentLoading}
              />
              <button
                type="submit"
                className="chat-send-btn"
                disabled={!inputPrompt.trim() || isAgentLoading}
              >
                {isAgentLoading ? (
                  <>
                    <span className="spinner spinner-sm" />
                    <span>Sending...</span>
                  </>
                ) : (
                  'Send'
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImageIntelligence;
