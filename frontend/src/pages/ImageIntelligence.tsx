import React, { useState, useRef } from 'react';
import {
  identifyProduct,
  queryAgent,
  ProductMatch,
  OpenWorldProductIdentification,
  SimilarCatalogProduct,
  AgentQueryResponse,
} from '../services/api';
import {
  UploadCloud,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  X,
  Send,
  Bot,
  User,
  BatteryCharging,
  Package,
  Eye,
  Wrench,
  ChevronRight,
  Activity,
  Target,
  Layers,
  HelpCircle,
} from 'lucide-react';

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

interface QuickSuggestion {
  label: string;
  prompt: string;
  icon: React.ReactNode;
}

const getCategorySuggestions = (category?: string): QuickSuggestion[] => {
  const cat = (category || '').toLowerCase();

  const observedFeatures: QuickSuggestion = {
    label: 'Observed features',
    prompt: 'What are the key observed visual features of this item?',
    icon: <Eye size={12} />,
  };

  const similarAlternatives: QuickSuggestion = {
    label: 'Similar alternatives',
    prompt: 'Show me similar products in our catalog',
    icon: <Package size={12} />,
  };

  // Headphones / Audio
  if (
    cat.includes('headphone') ||
    cat.includes('audio') ||
    cat.includes('earphone') ||
    cat.includes('earbud') ||
    cat.includes('sound') ||
    cat.includes('speaker')
  ) {
    return [
      {
        label: 'Battery life?',
        prompt: 'What is its battery life and charging capability?',
        icon: <BatteryCharging size={12} />,
      },
      {
        label: 'Noise cancellation?',
        prompt: 'Does this feature active noise cancellation (ANC)?',
        icon: <Sparkles size={12} />,
      },
      observedFeatures,
      similarAlternatives,
    ];
  }

  // Footwear / Shoes
  if (
    cat.includes('shoe') ||
    cat.includes('footwear') ||
    cat.includes('sneaker') ||
    cat.includes('runner') ||
    cat.includes('boot') ||
    cat.includes('athletic')
  ) {
    return [
      {
        label: 'Cushioning & comfort',
        prompt: "What's the cushioning and midsole support like?",
        icon: <Activity size={12} />,
      },
      {
        label: 'Intended surface',
        prompt: 'What surface or terrain is this designed for?',
        icon: <Target size={12} />,
      },
      observedFeatures,
      similarAlternatives,
    ];
  }

  // Chairs / Furniture
  if (
    cat.includes('chair') ||
    cat.includes('furniture') ||
    cat.includes('desk') ||
    cat.includes('ergonomic') ||
    cat.includes('seating')
  ) {
    return [
      {
        label: 'Weight capacity',
        prompt: "What's the weight capacity and adjustability?",
        icon: <Layers size={12} />,
      },
      {
        label: 'Ergonomic comfort',
        prompt: 'Is this suitable for long working hours and back support?',
        icon: <CheckCircle2 size={12} />,
      },
      observedFeatures,
      similarAlternatives,
    ];
  }

  // Watches / Timepieces
  if (
    cat.includes('watch') ||
    cat.includes('smartwatch') ||
    cat.includes('timepiece') ||
    cat.includes('chronograph')
  ) {
    return [
      {
        label: 'Water resistance?',
        prompt: 'What is its water resistance rating and battery performance?',
        icon: <Sparkles size={12} />,
      },
      {
        label: 'Sensors & tracking',
        prompt: 'What health sensors, heart rate tracking, and GPS features does it have?',
        icon: <Activity size={12} />,
      },
      observedFeatures,
      similarAlternatives,
    ];
  }

  // Books & Publications
  if (
    cat.includes('book') ||
    cat.includes('publication') ||
    cat.includes('literature') ||
    cat.includes('novel') ||
    cat.includes('reading')
  ) {
    return [
      {
        label: 'Summary & key lessons',
        prompt: 'Can you summarize the main message, key lessons, and takeaways from this book?',
        icon: <Sparkles size={12} />,
      },
      {
        label: 'Author & background',
        prompt: 'Who is the author and what is the background or premise of this work?',
        icon: <HelpCircle size={12} />,
      },
      observedFeatures,
      {
        label: 'Edition & format',
        prompt: 'What edition and format does this physical copy appear to be?',
        icon: <Layers size={12} />,
      },
    ];
  }

  // Groceries & Food / Beverage
  if (
    cat.includes('food') ||
    cat.includes('grocer') ||
    cat.includes('beverage') ||
    cat.includes('snack') ||
    cat.includes('drink')
  ) {
    return [
      {
        label: 'Flavor & variant',
        prompt: 'What flavor, variant, or product line is this?',
        icon: <Sparkles size={12} />,
      },
      {
        label: 'Ingredients & usage',
        prompt: 'What are typical ingredients, nutritional highlights, or serving suggestions for this?',
        icon: <CheckCircle2 size={12} />,
      },
      observedFeatures,
    ];
  }

  // Personal Care & Beauty
  if (
    cat.includes('beauty') ||
    cat.includes('personal care') ||
    cat.includes('skincare') ||
    cat.includes('cosmetic')
  ) {
    return [
      {
        label: 'Skin type & benefits',
        prompt: 'What skin or hair types is this formulated for and what are its key benefits?',
        icon: <Sparkles size={12} />,
      },
      {
        label: 'How to use',
        prompt: 'How is this product applied and what are active ingredients?',
        icon: <CheckCircle2 size={12} />,
      },
      observedFeatures,
    ];
  }

  // Generic fallback (e.g. Smartphones, Electronics, etc.)
  return [
    observedFeatures,
    {
      label: 'Key features?',
      prompt: 'What are the key specifications and features of this product?',
      icon: <HelpCircle size={12} />,
    },
    {
      label: 'Buying options',
      prompt: 'Can I get buying links or pricing guidance for this item?',
      icon: <Package size={12} />,
    },
  ];
};

const SAMPLE_IMAGES = [
  {
    label: 'Sony WH-1000XM5',
    category: 'Audio',
    url: 'https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=800&q=80',
  },
  {
    label: 'Herman Miller Aeron',
    category: 'Ergonomics',
    url: 'https://images.unsplash.com/photo-1580481077197-987823563052?auto=format&fit=crop&w=800&q=80',
  },
  {
    label: 'Nike Air Zoom Pegasus',
    category: 'Footwear',
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
  const chatMessagesRef = useRef<HTMLDivElement>(null);

  const isApiActive = isIdentifying || isAgentLoading;

  const scrollToBottom = () => {
    setTimeout(() => {
      if (chatMessagesRef.current) {
        chatMessagesRef.current.scrollTo({
          top: chatMessagesRef.current.scrollHeight,
          behavior: 'smooth',
        });
      }
    }, 50);
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
        // By default, do NOT select a catalog item — keep open-world identified product as active chat context
        setSelectedCatalogItem(null);

        const prod = result.identified_product;
        const welcomeText = `Identified as **${prod.product_name}** (${prod.brand} · ${prod.category}) with **${prod.confidence} confidence**.\n\n${prod.visual_description}`;

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
        setSimilarCatalog(result.all_matches || []);
        setSelectedCatalogItem(result.best_match);
        setMessages([
          {
            id: 'init-legacy',
            sender: 'assistant',
            text: `Closest match in catalog: **${result.best_match.brand} ${result.best_match.name}**. Ask any follow-up questions!`,
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
      // If a catalog item was explicitly selected by user, target its ID and catalog data;
      // otherwise use the open-world identifiedProduct with activeProductId = undefined.
      const activeProductId = selectedCatalogItem ? selectedCatalogItem.id : undefined;
      const mediaContext = typeof previewUrl === 'string' && previewUrl.startsWith('http') ? previewUrl : undefined;
      const productInfo = selectedCatalogItem
        ? {
            brand: selectedCatalogItem.brand,
            model: selectedCatalogItem.name,
            product_name: selectedCatalogItem.name,
            category: selectedCatalogItem.category,
            visual_description: selectedCatalogItem.description,
            key_features_observed: selectedCatalogItem.features || [],
            specifications: selectedCatalogItem.specifications,
          }
        : (identifiedProduct || undefined);

      const response: AgentQueryResponse = await queryAgent(
        queryText,
        activeProductId,
        undefined,
        mediaContext,
        productInfo
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
          <div className="tab-subtitle-tag">
            <Sparkles size={13} />
            <span>Open-World Visual Search & Grounding</span>
          </div>
          <h1>Image Intelligence</h1>
          <p>
            Upload any product photo for real-time multimodal recognition powered by{' '}
            <strong>Azure OpenAI GPT-5</strong> and explore catalog alternatives with vector search.
          </p>
        </div>
        {isApiActive && (
          <div className="api-live-indicator">
            <span className="pulse-dot" />
            <span>{isIdentifying ? 'Analyzing visual features...' : 'Agent reasoning...'}</span>
          </div>
        )}
      </div>

      {/* Inline Error Banner */}
      {errorMessage && (
        <div className="error-banner">
          <div className="error-msg">
            <AlertCircle size={18} />
            <span>{errorMessage}</span>
          </div>
          <button
            className="error-close-btn"
            onClick={() => setErrorMessage(null)}
            title="Dismiss error"
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* Main Grid */}
      <div className="dashboard-grid">
        {/* Left Column: Upload & Identification Display */}
        <div className="dashboard-column">
          {/* Upload Card */}
          <div className="card">
            <div className="card-header-row">
              <div className="card-header-title">
                <UploadCloud size={18} className="header-icon" />
                <span>Product Image Upload</span>
              </div>
              {previewUrl && (
                <button
                  className="btn btn-ghost-danger btn-sm"
                  onClick={clearSelection}
                  title="Remove image"
                >
                  <X size={14} />
                  <span>Clear</span>
                </button>
              )}
            </div>

            {/* Drag and Drop Zone */}
            <div
              className={`dropzone ${isDragging ? 'dragover' : ''} ${previewUrl ? 'has-preview' : ''}`}
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
                <div className="preview-box">
                  <img src={previewUrl} alt="Uploaded product preview" className="preview-image" />
                  <div className="preview-overlay-tag">
                    <span>Click or drop new image to replace</span>
                  </div>
                </div>
              ) : (
                <div className="dropzone-empty-state">
                  <div className="dropzone-icon-badge">
                    <UploadCloud size={28} />
                  </div>
                  <div className="dropzone-title">Drop your product photo here</div>
                  <div className="dropzone-subtitle">
                    Supports JPG, PNG, WEBP · Open-world zero-shot recognition
                  </div>
                  <div className="dropzone-cta-btn">
                    <span>Browse Files</span>
                  </div>
                </div>
              )}
            </div>

            {/* Sample Image Presets */}
            <div className="sample-presets">
              <span className="sample-title">Quick Demo Samples</span>
              <div className="sample-chips">
                {SAMPLE_IMAGES.map((sample, idx) => (
                  <button
                    key={idx}
                    className="sample-chip"
                    onClick={() => handleSampleSelect(sample.url)}
                    disabled={isIdentifying}
                  >
                    <span className="sample-category-dot" />
                    <span className="sample-label-text">{sample.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Loading State with Shimmer Skeleton */}
          {isIdentifying && (
            <div className="card loading-card">
              <div className="radar-spinner">
                <div className="radar-circle" />
                <Sparkles size={24} className="radar-icon" />
              </div>
              <div className="loading-card-title">Analyzing Visual Features</div>
              <div className="loading-card-subtitle">
                Multimodal GPT-5 extracting brand, physical attributes, model silhouette, and catalog vector matches...
              </div>
              <div style={{ width: '100%', marginTop: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                <div className="skeleton-shimmer skeleton-line medium" />
                <div className="skeleton-shimmer skeleton-line long" />
                <div className="skeleton-shimmer skeleton-line short" />
              </div>
            </div>
          )}

          {/* Open-World Recognition Card */}
          {!isIdentifying && identifiedProduct && (
            <div className="card open-world-card">
              <div className="open-world-header">
                <div className="ai-vision-tag">
                  <Sparkles size={13} />
                  <span>Open-World Visual AI</span>
                </div>
                <div className={`confidence-pill confidence-${identifiedProduct.confidence}`}>
                  <span className="confidence-dot" />
                  <span>
                    {identifiedProduct.confidence === 'high'
                      ? 'High Confidence'
                      : identifiedProduct.confidence === 'medium'
                      ? 'Medium Confidence'
                      : 'Low Confidence'}
                  </span>
                </div>
              </div>

              <div className="product-summary-meta">
                <div className="product-brand-tag">{identifiedProduct.brand}</div>
                <h2 className="product-display-name">{identifiedProduct.product_name}</h2>
                <span className="badge badge-category">{identifiedProduct.category}</span>
              </div>

              {/* Visual Observations Summary */}
              {identifiedProduct.visual_description && (
                <div className="visual-obs-box">
                  <div className="visual-obs-title">
                    <Eye size={14} />
                    <span>Visual Analysis & Physical Profile</span>
                  </div>
                  <p className="visual-obs-text">{identifiedProduct.visual_description}</p>
                </div>
              )}

              {/* Key Features Observed */}
              {identifiedProduct.key_features_observed && identifiedProduct.key_features_observed.length > 0 && (
                <div className="features-section">
                  <div className="features-section-title">Observed Physical Attributes</div>
                  <div className="feature-pills-wrap">
                    {identifiedProduct.key_features_observed.map((feat, idx) => (
                      <span key={idx} className="feature-pill">
                        <CheckCircle2 size={13} className="feature-pill-icon" />
                        <span>{feat}</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Similar Options in Our Catalog */}
              {similarCatalog.length > 0 ? (
                <div className="similar-catalog-section">
                  <div className="similar-catalog-header">
                    <div>
                      <div className="similar-catalog-title">
                        <Package size={16} />
                        <span>Indexed Catalog Recommendations</span>
                      </div>
                      <div className="similar-catalog-subtitle">
                        Vector nearest-neighbors indexed in Azure AI Search
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
                          onClick={() => setSelectedCatalogItem(isSelected ? null : item)}
                          title={
                            isSelected
                              ? `Currently active context. Click to return to ${identifiedProduct?.brand || 'identified product'}`
                              : `Click to switch chat context to ${item.brand} ${item.name}`
                          }
                        >
                          <div className="similar-card-left">
                            {item.image_urls && item.image_urls.length > 0 ? (
                              <img src={item.image_urls[0]} alt={item.name} className="similar-thumb" />
                            ) : (
                              <div className="similar-thumb-fallback">
                                <Package size={20} />
                              </div>
                            )}
                            <div className="similar-details">
                              <div className="similar-info-name">
                                {item.brand} {item.name}
                              </div>
                              <div className="similar-info-meta">
                                <span className="category-meta">{item.category}</span>
                                {item.specifications?.battery_life && (
                                   <span className="spec-meta">
                                     <BatteryCharging size={11} />
                                     {item.specifications.battery_life}
                                   </span>
                                )}
                              </div>
                            </div>
                          </div>
                          <div className="similar-card-right">
                            <span className="similar-score-badge">
                              {item.is_exact_catalog_match
                                ? 'Exact Match'
                                : `${(item.similarity_score * 100).toFixed(0)}% Visual Match`}
                            </span>
                            {isSelected && (
                              <div className="active-context-pill">
                                <span>Catalog Context</span>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <div className="no-catalog-match-box">
                  <div className="no-catalog-icon-wrap">
                    <Package size={16} />
                  </div>
                  <div className="no-catalog-content">
                    <div className="no-catalog-title">No Catalog Match for Category</div>
                    <div className="no-catalog-desc">
                      No similar items available in our catalog for this product category ({identifiedProduct.category}).
                      You can ask full open-world questions in the chat assistant.
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Agent Chat Interface */}
        <div className="dashboard-column">
          <div className="chat-container">
            <div className="chat-header">
              <div className="chat-title">
                <div className="chat-bot-avatar">
                  <Bot size={18} />
                </div>
                <div>
                  <div className="chat-name-row">
                    <span className="chat-name">VisionIQ Copilot</span>
                    <span className="agent-badge">Foundry Agent</span>
                  </div>
                  <div className="chat-subhead">Grounded Multimodal RAG</div>
                </div>
              </div>
              {selectedCatalogItem ? (
                <div className="active-target-badge target-catalog-badge" title={`Chat context: ${selectedCatalogItem.brand} ${selectedCatalogItem.name}`}>
                  <span className="target-dot target-dot-catalog" />
                  <span>Catalog: {selectedCatalogItem.brand} {selectedCatalogItem.name.substring(0, 16)}</span>
                  <button
                    className="badge-clear-btn"
                    onClick={() => setSelectedCatalogItem(null)}
                    title={`Click to reset chat context back to identified ${identifiedProduct?.brand || 'product'}`}
                  >
                    ✕
                  </button>
                </div>
              ) : identifiedProduct ? (
                <div className="active-target-badge" title={`Active open-world context: ${identifiedProduct.product_name}`}>
                  <span className="target-dot" />
                  <span>{identifiedProduct.brand} {identifiedProduct.model || identifiedProduct.product_name.substring(0, 16)}</span>
                </div>
              ) : null}
            </div>

            <div className="chat-messages" ref={chatMessagesRef}>
              {messages.length === 0 ? (
                <div className="empty-state-modern">
                  <div className="empty-state-icon-ring">
                    <Bot size={30} />
                  </div>
                  <div className="empty-state-title">
                    {previewUrl ? 'Product Analyzed & Ready' : 'Awaiting Product Input'}
                  </div>
                  <p className="empty-state-text">
                    {previewUrl
                      ? 'Ask questions about observed physical features, specifications, durability, or catalog alternatives.'
                      : 'Upload a product photo or select a quick demo sample on the left to start grounded multimodal dialogue.'}
                  </p>
                </div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`message-bubble ${msg.sender === 'user' ? 'message-user' : 'message-assistant'}`}
                  >
                    <div className="message-header-row">
                      <div className="message-sender-tag">
                        {msg.sender === 'user' ? <User size={13} /> : <Bot size={13} />}
                        <span>{msg.sender === 'user' ? 'You' : 'VisionIQ Assistant'}</span>
                      </div>
                      <span className="message-timestamp">{msg.timestamp}</span>
                    </div>

                    <div className="message-body" style={{ whiteSpace: 'pre-line' }}>
                      {msg.text}
                    </div>

                    {/* Similar Products Carousel / Cards if returned */}
                    {msg.similarProducts && msg.similarProducts.length > 0 && (
                      <div className="similar-cards-grid">
                        {msg.similarProducts.map((p) => (
                          <div
                            key={p.id}
                            className="similar-card"
                            onClick={() => setSelectedCatalogItem(p as SimilarCatalogProduct)}
                            title={`Select ${p.name} as active context`}
                          >
                            <div className="similar-card-brand">{p.brand}</div>
                            <div className="similar-card-name">{p.name}</div>
                            <div className="similar-card-footer">
                              <span className="similar-card-score">
                                {(p.similarity_score * 100).toFixed(0)}% match
                              </span>
                              <ChevronRight size={14} className="similar-card-arrow" />
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {msg.toolUsed && (
                      <div className="message-meta">
                        <span className="tool-tag">
                          <Wrench size={11} />
                          <span>{msg.toolUsed}</span>
                        </span>
                        {msg.reasoning && (
                          <span className="reasoning-text" title={msg.reasoning}>
                            {msg.reasoning.substring(0, 60)}...
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                ))
              )}

              {isAgentLoading && (
                <div className="message-bubble message-assistant message-loading">
                  <div className="typing-indicator">
                    <span />
                    <span />
                    <span />
                  </div>
                  <span className="typing-text">Agent reasoning & grounding with catalog vectors...</span>
                </div>
              )}
            </div>

            {/* Quick Action Suggestion Chips */}
            <div className="quick-prompts">
              {getCategorySuggestions(identifiedProduct?.category || selectedCatalogItem?.category).map((s, idx) => (
                <button
                  key={idx}
                  className="quick-chip"
                  onClick={() => handleSendMessage(s.prompt)}
                  disabled={isAgentLoading || (!identifiedProduct && !selectedCatalogItem)}
                  title={!identifiedProduct && !selectedCatalogItem ? 'Upload an image first' : undefined}
                >
                  {s.icon}
                  <span>{s.label}</span>
                </button>
              ))}
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
                    ? `Ask anything about ${identifiedProduct?.brand || selectedCatalogItem?.brand || 'this item'}...`
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
                title="Send query"
              >
                {isAgentLoading ? (
                  <span className="spinner spinner-sm" />
                ) : (
                  <>
                    <Send size={15} />
                    <span>Send</span>
                  </>
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
