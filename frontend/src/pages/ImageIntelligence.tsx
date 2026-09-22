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
  Zap,
  Image as ImageIcon,
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
    label: 'Nike Air Zoom Pegasus',
    category: 'Footwear',
    brand: 'Nike',
    url: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=400&q=80',
  },
  {
    label: 'Sony WH-1000XM5',
    category: 'Audio',
    brand: 'Sony',
    url: 'https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=400&q=80',
  },
  {
    label: 'Herman Miller Aeron',
    category: 'Ergonomics',
    brand: 'Herman Miller',
    url: 'https://images.unsplash.com/photo-1580481077197-987823563052?auto=format&fit=crop&w=400&q=80',
  },
  {
    label: 'Apple Watch Series',
    category: 'Smartwatch',
    brand: 'Apple',
    url: 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=400&q=80',
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
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!VALID_IMAGE_EXTENSIONS.includes(ext)) {
      setErrorMessage(
        `Invalid file type (${ext}). Please select an image (${VALID_IMAGE_EXTENSIONS.join(', ')}).`
      );
      return false;
    }
    const maxSizeBytes = 20 * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      setErrorMessage('Image size exceeds 20MB limit. Please choose a smaller photo.');
      return false;
    }
    return true;
  };

  const processImageIdentification = async (fileOrUrl: File | string) => {
    setIsIdentifying(true);
    setErrorMessage(null);
    setIdentifiedProduct(null);
    setSimilarCatalog([]);
    setSelectedCatalogItem(null);

    try {
      const response = await identifyProduct(fileOrUrl);
      if (response && response.identified_product) {
        setIdentifiedProduct(response.identified_product);
        setSimilarCatalog(response.similar_catalog_products || []);
        
        const autoIntroMsg: ChatMessage = {
          id: `asst-intro-${Date.now()}`,
          sender: 'assistant',
          text: `I've analyzed your product image. I identified this as **${response.identified_product.brand} ${response.identified_product.product_name}** (${response.identified_product.category}).\n\nAsk me anything about its features, material specifications, or explore catalog alternatives below.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        setMessages([autoIntroMsg]);
      } else {
        setErrorMessage('Could not analyze the visual details of this product. Please try another image.');
      }
    } catch (err: any) {
      console.error('Identification error:', err);
      setErrorMessage(
        err.message || 'Error communicating with the vision recognition service. Please check your backend connection.'
      );
    } finally {
      setIsIdentifying(false);
      scrollToBottom();
    }
  };

  const handleFileSelection = (file: File) => {
    if (!validateImageFile(file)) return;
    const localUrl = URL.createObjectURL(file);
    setPreviewUrl(localUrl);
    processImageIdentification(file);
  };

  const handleSampleSelect = (sampleUrl: string) => {
    setPreviewUrl(sampleUrl);
    processImageIdentification(sampleUrl);
  };

  const handleSendMessage = async (textToSend?: string) => {
    const queryText = (textToSend || inputPrompt).trim();
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
      {/* Top Hero Showcase Banner matching reference */}
      <div className="page-hero-banner">
        <div className="hero-banner-left">
          <div className="tab-subtitle-tag">
            <Sparkles size={13} />
            <span>OPEN-WORLD VISUAL SEARCH & GROUNDING</span>
          </div>
          <h1 className="hero-banner-title">Image Intelligence</h1>
          <p className="hero-banner-desc">
            Upload any product photo for real-time multimodal recognition powered by{' '}
            <strong>Azure OpenAI GPT-5</strong> and explore catalog alternatives with vector search.
          </p>

          <div className="hero-feature-pills">
            <div className="hero-feature-pill">
              <div className="hero-pill-icon-wrap">
                <Zap size={15} />
              </div>
              <div className="hero-pill-text">
                <div className="hero-pill-heading">Instant Recognition</div>
                <div className="hero-pill-caption">Identify products in seconds</div>
              </div>
            </div>
            <div className="hero-feature-pill">
              <div className="hero-pill-icon-wrap">
                <Package size={15} />
              </div>
              <div className="hero-pill-text">
                <div className="hero-pill-heading">Find Similar Items</div>
                <div className="hero-pill-caption">Explore catalog alternatives</div>
              </div>
            </div>
            <div className="hero-feature-pill">
              <div className="hero-pill-icon-wrap">
                <Target size={15} />
              </div>
              <div className="hero-pill-text">
                <div className="hero-pill-heading">Open-World Search</div>
                <div className="hero-pill-caption">Works beyond fixed catalogs</div>
              </div>
            </div>
          </div>
        </div>

        <div className="hero-banner-right">
          <div className="hero-graphic-cluster">
            <div className="floating-card floating-card-headphones">
              <img
                src="https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=240&q=80"
                alt="Headphones"
              />
            </div>
            <div className="floating-card floating-card-shoe">
              <img
                src="https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=300&q=80"
                alt="Nike Sneaker"
              />
            </div>
            <div className="floating-card floating-card-bag">
              <img
                src="https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=240&q=80"
                alt="Backpack"
              />
            </div>
            <div className="ai-powered-pill">
              <span>AI Powered</span>
            </div>
            <div className="hero-curved-annotation">
              <span className="annotation-line">Detect Products</span>
              <span className="annotation-line">Find Similar Items</span>
              <span className="annotation-line">Explore Alternatives</span>
              <div className="annotation-arrow">⤹</div>
            </div>
          </div>
        </div>
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
          <div className="card upload-card">
            <div className="card-header-row">
              <div className="card-header-title-group">
                <div className="card-header-icon-box">
                  <UploadCloud size={18} />
                </div>
                <div>
                  <h3 className="card-main-heading">Product Image Upload</h3>
                  <p className="card-sub-heading">Drop an image, or browse from your device</p>
                </div>
              </div>
              <div className="card-header-actions">
                {previewUrl ? (
                  <button
                    className="btn-clear-action"
                    onClick={clearSelection}
                    title="Remove image"
                  >
                    <X size={13} />
                    <span>Clear</span>
                  </button>
                ) : (
                  <div className="supported-formats-badge">
                    <HelpCircle size={13} />
                    <span>Supported Formats</span>
                  </div>
                )}
              </div>
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
                  <div className="dropzone-icon-ring">
                    <UploadCloud size={28} />
                  </div>
                  <div className="dropzone-title">Drag & drop your product photo here</div>
                  <div className="dropzone-subtitle-muted">or click to browse</div>
                  <div className="dropzone-meta-tag">
                    Supports JPG, PNG, WEBP • Open-world zero-shot recognition
                  </div>
                  <button type="button" className="btn-browse-primary">
                    <UploadCloud size={14} />
                    <span>Browse Files</span>
                  </button>
                </div>
              )}
            </div>

            {/* Sample Image Presets with Visual Cards */}
            <div className="sample-presets-container">
              <div className="sample-presets-header">
                <div className="sample-header-left">
                  <Sparkles size={13} className="sample-icon-mint" />
                  <span>Try with a sample</span>
                </div>
                <span className="sample-header-right">View more demos →</span>
              </div>
              <div className="sample-cards-row">
                {SAMPLE_IMAGES.map((sample, idx) => {
                  const isCurrent = previewUrl === sample.url;
                  return (
                    <div
                      key={idx}
                      className={`sample-product-card ${isCurrent ? 'is-selected' : ''}`}
                      onClick={() => handleSampleSelect(sample.url)}
                      title={`Analyze ${sample.label}`}
                    >
                      <img src={sample.url} alt={sample.label} className="sample-product-thumb" />
                      <div className="sample-product-text">
                        <span className="sample-product-name">{sample.label}</span>
                      </div>
                    </div>
                  );
                })}
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
                    <span className="agent-badge">FOUNDRY AGENT</span>
                  </div>
                  <div className="chat-subhead">Your multimodal product analysis assistant</div>
                </div>
              </div>
              {selectedCatalogItem ? (
                <div className="active-target-badge target-catalog-badge" title={`Chat context: ${selectedCatalogItem.brand} ${selectedCatalogItem.name}`}>
                  <span className="target-dot target-dot-catalog" />
                  <span className="badge-truncated-text">Catalog: {selectedCatalogItem.brand} {selectedCatalogItem.name}</span>
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
                  <span className="badge-truncated-text">{identifiedProduct.brand} {identifiedProduct.model || identifiedProduct.product_name}</span>
                </div>
              ) : null}
            </div>

            <div className="chat-messages" ref={chatMessagesRef}>
              {messages.length === 0 ? (
                <div className="empty-state-modern">
                  <div className="empty-state-icon-box">
                    <Bot size={28} />
                  </div>
                  <h3 className="empty-state-title">Ready to analyze your product</h3>
                  <p className="empty-state-text">
                    Upload a product photo or try a sample image to start a grounded multimodal conversation. I can identify items, find similar products, extract attributes, and more.
                  </p>

                  <div className="empty-state-prompt-grid">
                    <button
                      type="button"
                      className="empty-prompt-card"
                      onClick={() => handleSendMessage('What is this product and what are its key features?')}
                      disabled={isAgentLoading}
                    >
                      <HelpCircle size={14} className="prompt-card-icon" />
                      <span>What is this product?</span>
                    </button>
                    <button
                      type="button"
                      className="empty-prompt-card"
                      onClick={() => handleSendMessage('Describe key features and physical attributes observed.')}
                      disabled={isAgentLoading}
                    >
                      <Sparkles size={14} className="prompt-card-icon" />
                      <span>Describe key features</span>
                    </button>
                    <button
                      type="button"
                      className="empty-prompt-card"
                      onClick={() => handleSendMessage('Find similar products and catalog alternatives.')}
                      disabled={isAgentLoading}
                    >
                      <Package size={14} className="prompt-card-icon" />
                      <span>Find similar products</span>
                    </button>
                    <button
                      type="button"
                      className="empty-prompt-card"
                      onClick={() => handleSendMessage('Compare with alternative choices in the market.')}
                      disabled={isAgentLoading}
                    >
                      <Layers size={14} className="prompt-card-icon" />
                      <span>Compare with alternatives</span>
                    </button>
                  </div>
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
                        <div className="message-meta-header">
                          <span className="tool-tag">
                            <Wrench size={11} />
                            <span>{msg.toolUsed}</span>
                          </span>
                        </div>
                        {msg.reasoning && (
                          <div className="reasoning-text" title={msg.reasoning}>
                            {msg.reasoning}
                          </div>
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

            {/* Quick Action Suggestion Chips when product is active */}
            {messages.length > 0 && (
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
            )}

            {/* Bottom Input Section */}
            <div className="chat-input-wrapper">
              <form
                className="chat-input-bar"
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendMessage();
                }}
              >
                <button
                  type="button"
                  className="chat-attach-btn"
                  onClick={() => fileInputRef.current?.click()}
                  title="Upload product image"
                >
                  <ImageIcon size={18} />
                </button>
                <input
                  type="text"
                  className="chat-input"
                  placeholder={
                    identifiedProduct || selectedCatalogItem
                      ? `Ask anything about ${identifiedProduct?.brand || selectedCatalogItem?.brand || 'this item'}...`
                      : "Upload an image to start chatting..."
                  }
                  value={inputPrompt}
                  onChange={(e) => setInputPrompt(e.target.value)}
                  disabled={isAgentLoading}
                />
                <button
                  type="submit"
                  className="chat-send-round-btn"
                  disabled={!inputPrompt.trim() || isAgentLoading}
                  title="Send query"
                >
                  {isAgentLoading ? (
                    <span className="spinner spinner-sm" />
                  ) : (
                    <Send size={15} />
                  )}
                </button>
              </form>
              <div className="chat-input-microcopy">
                Supports product images • Get detailed insights, specs, and recommendations
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImageIntelligence;
