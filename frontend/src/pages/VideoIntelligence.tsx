import React, { useState, useRef } from 'react';
import {
  analyzeVideo,
  searchVideo,
  getVideoSummary,
  VideoAnalysisResult,
  VideoSearchResponse,
} from '../services/api';
import {
  Film,
  Play,
  Clock,
  Layers,
  Image as ImageIcon,
  Sparkles,
  Search,
  Bot,
  User,
  AlertCircle,
  X,
  FileText,
  Tag,
  Hash,
  Target,
  MessageSquare,
  RefreshCw,
  CheckCircle2,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Volume2,
} from 'lucide-react';

interface VideoChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  contextStart?: number | null;
  matchedTimestamp?: number | null;
  contextEnd?: number | null;
  startTime?: number | null;
  endTime?: number | null;
  evidence?: Array<{ timestamp: number; text: string }>;
  supportingSegment?: string;
  confidenceScore?: number;
  foundMatch?: boolean;
}


const VALID_VIDEO_EXTENSIONS = ['.mp4', '.mov', '.webm', '.avi', '.mkv'];

const formatTimestamp = (seconds: number): string => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

export const VideoIntelligence: React.FC = () => {
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Video Analysis & Summary State
  const [analysisResult, setAnalysisResult] = useState<VideoAnalysisResult | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [keyTopics, setKeyTopics] = useState<string[]>([]);
  const [keyTakeaways, setKeyTakeaways] = useState<string[]>([]);
  const [isRegeneratingSummary, setIsRegeneratingSummary] = useState<boolean>(false);
  const [showTranscript, setShowTranscript] = useState<boolean>(false);
  const [isCopiedTranscript, setIsCopiedTranscript] = useState<boolean>(false);

  // Video Chat State
  const [messages, setMessages] = useState<VideoChatMessage[]>([]);
  const [inputPrompt, setInputPrompt] = useState<string>('');
  const [isSearching, setIsSearching] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoPlayerRef = useRef<HTMLVideoElement>(null);
  const chatMessagesRef = useRef<HTMLDivElement>(null);

  const isApiActive = isAnalyzing || isSearching;

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

  const validateVideoFile = (file: File): boolean => {
    const hasVideoMime = file.type.startsWith('video/');
    const fileNameLower = file.name.toLowerCase();
    const hasValidExtension = VALID_VIDEO_EXTENSIONS.some((ext) => fileNameLower.endsWith(ext));

    if (!hasVideoMime && !hasValidExtension) {
      setErrorMessage(
        `Invalid file type: "${file.name}". Please upload a valid video file (${VALID_VIDEO_EXTENSIONS.join(', ')}).`
      );
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      return false;
    }
    return true;
  };

  const handleVideoFileSelect = async (file: File) => {
    if (!validateVideoFile(file)) {
      return;
    }

    setErrorMessage(null);
    const objectUrl = URL.createObjectURL(file);
    setVideoUrl(objectUrl);
    setAnalysisResult(null);
    setSummary(null);
    setKeyTopics([]);
    setKeyTakeaways([]);
    setShowTranscript(false);
    setMessages([]);

    await runVideoAnalysis(file);
  };

  const runVideoAnalysis = async (file: File) => {
    setIsAnalyzing(true);
    setErrorMessage(null);

    try {
      const result = await analyzeVideo(file);
      setAnalysisResult(result);

      try {
        const summaryData = await getVideoSummary(result.video_id);
        setSummary(summaryData.summary);
        setKeyTopics(summaryData.key_topics || []);
        setKeyTakeaways(summaryData.key_takeaways || []);
      } catch (sumErr) {
        console.warn('Could not load summary:', sumErr);
        setSummary(
          result.full_transcript
            ? `Processed video "${file.name}" with ${result.chunks_count} indexed temporal segments.`
            : null
        );
      }

      setMessages([
        {
          id: 'v-init-1',
          sender: 'assistant',
          text: `Video analyzed successfully (**${result.duration_seconds}s duration**, **${result.chunks_count} segments** indexed). You can now ask questions about statements made, topics discussed, or specific scenes!`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } catch (err: any) {
      console.error('Video analysis failed:', err);
      setErrorMessage(
        err.message || "Couldn't connect to the backend server. Please ensure the backend is running."
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleRegenerateSummary = async () => {
    if (!analysisResult?.video_id || isRegeneratingSummary) return;
    setIsRegeneratingSummary(true);
    try {
      const summaryData = await getVideoSummary(analysisResult.video_id, true);
      setSummary(summaryData.summary);
      setKeyTopics(summaryData.key_topics || []);
      setKeyTakeaways(summaryData.key_takeaways || []);
    } catch (err: any) {
      console.error('Failed to regenerate summary:', err);
      setErrorMessage(err.message || 'Failed to regenerate AI summary.');
    } finally {
      setIsRegeneratingSummary(false);
    }
  };

  const handleCopyTranscript = () => {
    if (!analysisResult?.full_transcript) return;
    navigator.clipboard.writeText(analysisResult.full_transcript);
    setIsCopiedTranscript(true);
    setTimeout(() => setIsCopiedTranscript(false), 2000);
  };

  const handleSeekToTime = (timeInSeconds: number) => {
    if (videoPlayerRef.current) {
      videoPlayerRef.current.currentTime = timeInSeconds;
      videoPlayerRef.current.play();
    }
  };

  const handleSendQuestion = async (queryTextOverride?: string) => {
    const questionText = (queryTextOverride || inputPrompt).trim();
    if (!questionText || isSearching) return;

    if (!analysisResult?.video_id) {
      const promptMsg: VideoChatMessage = {
        id: `v-user-${Date.now()}`,
        sender: 'user',
        text: questionText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      const guidanceMsg: VideoChatMessage = {
        id: `v-guide-${Date.now()}`,
        sender: 'assistant',
        text: 'Please upload and analyze a video first before searching for spoken dialogue or scene timestamps.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, promptMsg, guidanceMsg]);
      setInputPrompt('');
      scrollToBottom();
      return;
    }

    const userMsg: VideoChatMessage = {
      id: `v-user-${Date.now()}`,
      sender: 'user',
      text: questionText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputPrompt('');
    setIsSearching(true);
    scrollToBottom();

    try {
      const searchResult: VideoSearchResponse = await searchVideo(
        analysisResult.video_id,
        questionText,
        3,
        0.50
      );

      const replyText = searchResult.answer || "I couldn't find that in the video. The topic does not appear in the transcribed audio or indexed timeline.";

      const assistantMsg: VideoChatMessage = {
        id: `v-asst-${Date.now()}`,
        sender: 'assistant',
        text: replyText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        contextStart: searchResult.context_start ?? searchResult.start_time,
        matchedTimestamp: searchResult.matched_timestamp ?? searchResult.start_time,
        contextEnd: searchResult.context_end ?? searchResult.end_time,
        startTime: searchResult.context_start ?? searchResult.start_time,
        endTime: searchResult.context_end ?? searchResult.end_time,
        evidence: searchResult.evidence,
        supportingSegment: searchResult.supporting_segment,
        confidenceScore: searchResult.confidence_score,
        foundMatch: searchResult.found_match,
      };


      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      console.error('Video search error:', err);
      const errMsg: VideoChatMessage = {
        id: `v-err-${Date.now()}`,
        sender: 'assistant',
        text: err.message || "Couldn't connect to the server. Please check your backend connection.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsSearching(false);
      scrollToBottom();
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleVideoFileSelect(e.dataTransfer.files[0]);
    }
  };

  const clearVideo = () => {
    setVideoUrl(null);
    setAnalysisResult(null);
    setSummary(null);
    setKeyTopics([]);
    setKeyTakeaways([]);
    setShowTranscript(false);
    setIsCopiedTranscript(false);
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
            <Film size={13} />
            <span>Temporal Speech & Video Indexing</span>
          </div>
          <h1>Video Intelligence</h1>
          <p>
            Upload a video to transcribe speech with Whisper, index temporal timeline chunks into{' '}
            <strong>Azure AI Search</strong>, and query exact timestamped moments with clickable playback.
          </p>
        </div>

        {isApiActive && (
          <div className="api-live-indicator">
            <span className="pulse-dot" />
            <span>{isAnalyzing ? 'Processing video pipeline...' : 'Searching timeline...'}</span>
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
          <button className="error-close-btn" onClick={() => setErrorMessage(null)} title="Dismiss error">
            <X size={16} />
          </button>
        </div>
      )}

      {/* Main Grid */}
      <div className="dashboard-grid">
        {/* Left Column: Video Player & Summary */}
        <div className="dashboard-column">
          <div className="card">
            <div className="card-header-row">
              <div className="card-header-title">
                <Film size={18} className="header-icon" />
                <span>Video Player & Input</span>
              </div>
              {videoUrl && (
                <button
                  className="btn btn-ghost-danger btn-sm"
                  onClick={clearVideo}
                  title="Upload another video"
                >
                  <X size={14} />
                  <span>Upload New</span>
                </button>
              )}
            </div>

            {!videoUrl ? (
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
                <div className="dropzone-empty-state">
                  <div className="dropzone-icon-badge">
                    <Film size={28} />
                  </div>
                  <div className="dropzone-title">Drag & drop your video file here</div>
                  <div className="dropzone-subtitle">
                    Supports MP4, MOV, WEBM, AVI, MKV · Azure Whisper Transcription & Keyframes
                  </div>
                  <div className="dropzone-cta-btn">
                    <span>Select Video File</span>
                  </div>
                </div>
                <input
                  type="file"
                  ref={fileInputRef}
                  style={{ display: 'none' }}
                  accept="video/mp4,video/webm,video/quicktime,video/x-msvideo,video/x-matroska"
                  onChange={(e) => {
                    if (e.target.files && e.target.files.length > 0) {
                      handleVideoFileSelect(e.target.files[0]);
                    }
                  }}
                />
              </div>
            ) : (
              <div className="video-player-container">
                <video
                  ref={videoPlayerRef}
                  src={videoUrl}
                  controls
                  className="video-player-element"
                />
              </div>
            )}
          </div>

          {/* Loading State for Video Processing */}
          {isAnalyzing && (
            <div className="card loading-card">
              <div className="radar-spinner">
                <div className="radar-circle" />
                <Film size={24} className="radar-icon" />
              </div>
              <div className="loading-card-title">Processing Video Pipeline</div>
              <div className="loading-card-subtitle">
                Extracting audio, transcribing speech with Whisper, extracting timeline keyframes, and generating vector embeddings in Azure AI Search...
              </div>
            </div>
          )}

          {/* Video Overview & Summary */}
          {!isAnalyzing && analysisResult && (
            <div className="card">
              <div className="card-header-row">
                <div className="card-header-title">
                  <FileText size={18} className="header-icon" />
                  <span>Video Intelligence Overview</span>
                </div>
                <span className="mono-badge">ID: {analysisResult.video_id.substring(0, 8)}</span>
              </div>

              {/* Stat Metric Cards */}
              <div className="metrics-grid">
                <div className="metric-card">
                  <div className="metric-icon-wrap">
                    <Clock size={16} />
                  </div>
                  <div>
                    <div className="metric-value">{analysisResult.duration_seconds}s</div>
                    <div className="metric-label">Duration</div>
                  </div>
                </div>

                <div className="metric-card">
                  <div className="metric-icon-wrap">
                    <Layers size={16} />
                  </div>
                  <div>
                    <div className="metric-value">{analysisResult.chunks_count}</div>
                    <div className="metric-label">Indexed Chunks</div>
                  </div>
                </div>

                <div className="metric-card">
                  <div className="metric-icon-wrap">
                    <ImageIcon size={16} />
                  </div>
                  <div>
                    <div className="metric-value">{analysisResult.total_keyframes}</div>
                    <div className="metric-label">Keyframes</div>
                  </div>
                </div>
              </div>

              {summary && (
                <div className="video-summary-box">
                  <div className="summary-box-title-row">
                    <div className="summary-box-title">
                      <Sparkles size={15} className="sparkle-gold" />
                      <span>Executive AI Summary</span>
                      <span className="summary-grounding-pill">Whisper Grounded</span>
                    </div>
                    <button
                      className="btn-regenerate-summary"
                      onClick={handleRegenerateSummary}
                      disabled={isRegeneratingSummary}
                      title="Regenerate AI summary from full transcript"
                    >
                      <RefreshCw size={12} className={isRegeneratingSummary ? 'spin' : ''} />
                      <span>{isRegeneratingSummary ? 'Generating...' : 'Regenerate'}</span>
                    </button>
                  </div>

                  <p className="video-summary-text">{summary}</p>

                  {/* Key Takeaways */}
                  {keyTakeaways && keyTakeaways.length > 0 && (
                    <div className="summary-takeaways-section">
                      <div className="takeaways-title">
                        <CheckCircle2 size={13} />
                        <span>Key Discussion Takeaways</span>
                      </div>
                      <ul className="takeaways-list">
                        {keyTakeaways.map((takeaway, idx) => (
                          <li key={idx} className="takeaway-item">
                            <span className="takeaway-bullet">•</span>
                            <span className="takeaway-text">{takeaway}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Key Topics */}
                  {keyTopics.length > 0 && (
                    <div className="topics-section">
                      <div className="topics-title">
                        <Tag size={12} />
                        <span>Extracted Key Topics (Click to query timeline)</span>
                      </div>
                      <div className="topics-list">
                        {keyTopics.map((topic, i) => (
                          <button
                            key={i}
                            className="topic-chip"
                            onClick={() => handleSendQuestion(`Tell me what is discussed about "${topic}"`)}
                            title={`Ask about ${topic}`}
                          >
                            <Hash size={11} />
                            <span>{topic}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Full Spoken Transcript Explorer Accordion */}
                  {analysisResult.full_transcript && (
                    <div className="transcript-accordion">
                      <div
                        className="transcript-accordion-header"
                        onClick={() => setShowTranscript(!showTranscript)}
                      >
                        <div className="transcript-header-left">
                          <Volume2 size={14} />
                          <span>Full Audio Transcription ({analysisResult.chunks_count} segments)</span>
                        </div>
                        <div className="transcript-header-right">
                          <button
                            type="button"
                            className="btn-copy-transcript"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleCopyTranscript();
                            }}
                            title="Copy full transcription"
                          >
                            {isCopiedTranscript ? <Check size={12} /> : <Copy size={12} />}
                            <span>{isCopiedTranscript ? 'Copied' : 'Copy'}</span>
                          </button>
                          {showTranscript ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                        </div>
                      </div>

                      {showTranscript && (
                        <div className="transcript-body">
                          {analysisResult.chunks && analysisResult.chunks.length > 0 ? (
                            <div className="transcript-chunks-list">
                              {analysisResult.chunks.map((chunk, cIdx) => (
                                <div
                                  key={cIdx}
                                  className="transcript-chunk-item"
                                  onClick={() => handleSeekToTime(chunk.start_time)}
                                  title={`Click to jump to ${formatTimestamp(chunk.start_time)}`}
                                >
                                  <span className="chunk-timestamp">[{formatTimestamp(chunk.start_time)}]</span>
                                  <span className="chunk-text">{chunk.transcript}</span>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="transcript-raw-text">{analysisResult.full_transcript}</p>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Grounded Video Chat */}
        <div className="dashboard-column">
          <div className="chat-container">
            <div className="chat-header">
              <div className="chat-title">
                <div className="chat-bot-avatar">
                  <Search size={18} />
                </div>
                <div>
                  <div className="chat-name-row">
                    <span className="chat-name">Temporal Video Search</span>
                    <span className="agent-badge">Temporal RAG</span>
                  </div>
                  <div className="chat-subhead">Timestamp-Grounded Dialogue</div>
                </div>
              </div>
              {analysisResult && (
                <div className="active-target-badge" title={analysisResult.filename}>
                  <Film size={12} />
                  <span>{analysisResult.filename.substring(0, 18)}...</span>
                </div>
              )}
            </div>

            <div className="chat-messages" ref={chatMessagesRef}>
              {messages.length === 0 ? (
                <div className="chat-empty-state">
                  <div className="empty-bot-icon">
                    <Film size={36} />
                  </div>
                  <div className="empty-title">
                    {videoUrl ? 'Video Indexed & Ready' : 'Awaiting Video Upload'}
                  </div>
                  <p className="empty-description">
                    {videoUrl
                      ? 'Ask questions to locate spoken dialogue, reviewer opinions, scene timestamps, and conclusions.'
                      : 'Upload a video file on the left to transcribe audio and enable temporal vector search.'}
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
                        <span>{msg.sender === 'user' ? 'You' : 'Temporal Search Assistant'}</span>
                      </div>
                      <span className="message-timestamp">{msg.timestamp}</span>
                    </div>

                    <div className="message-body" style={{ whiteSpace: 'pre-line' }}>
                      {msg.text}
                    </div>

                    {/* Clickable Seek Timestamp Button (Seeks to context_start) */}
                    {(msg.contextStart !== undefined && msg.contextStart !== null) || (msg.startTime !== undefined && msg.startTime !== null) ? (
                      <div className="timestamp-btn-wrapper">
                        {(() => {
                          const seekTarget = msg.contextStart ?? msg.startTime!;
                          const endTarget = msg.contextEnd ?? msg.endTime;
                          const hasKeywordDiff = msg.matchedTimestamp !== undefined && msg.matchedTimestamp !== null && Math.abs(msg.matchedTimestamp - seekTarget) > 1.0;

                          return (
                            <>
                              <button
                                className="timestamp-btn"
                                onClick={() => handleSeekToTime(seekTarget)}
                                title={`Click to start playback from context start at ${formatTimestamp(seekTarget)}`}
                              >
                                <Play size={13} className="play-icon" />
                                <span>
                                  Play Context: {formatTimestamp(seekTarget)}
                                  {endTarget !== null && endTarget !== undefined ? ` – ${formatTimestamp(endTarget)}` : ''}
                                </span>
                              </button>
                              {hasKeywordDiff && (
                                <span
                                  className="matched-ts-pill"
                                  onClick={() => handleSeekToTime(msg.matchedTimestamp!)}
                                  title={`Core answer/keyword occurs at ${formatTimestamp(msg.matchedTimestamp!)}. Click to jump directly.`}
                                >
                                  Core point: {formatTimestamp(msg.matchedTimestamp!)}
                                </span>
                              )}
                            </>
                          );
                        })()}
                      </div>
                    ) : null}

                    {/* Supporting Lecture Evidence */}
                    {msg.evidence && msg.evidence.length > 0 ? (
                      <div className="supporting-segment-box">
                        <div className="supporting-quote-label">Grounded Lecture Evidence:</div>
                        <div className="evidence-list">
                          {msg.evidence.map((ev, i) => (
                            <div
                              key={i}
                              className="evidence-item"
                              onClick={() => handleSeekToTime(ev.timestamp)}
                              title={`Click to jump to ${formatTimestamp(ev.timestamp)}`}
                            >
                              <span className="evidence-time">[{formatTimestamp(ev.timestamp)}]</span>
                              <span className="evidence-text">"{ev.text}"</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : msg.supportingSegment ? (
                      <div className="supporting-segment-box">
                        <div className="supporting-quote-label">Grounded Transcript Segment:</div>
                        <div className="supporting-quote-content">"{msg.supportingSegment}"</div>
                      </div>
                    ) : null}
                  </div>
                ))
              )}


              {isSearching && (
                <div className="message-bubble message-assistant message-loading">
                  <div className="typing-indicator">
                    <span />
                    <span />
                    <span />
                  </div>
                  <span className="typing-text">Searching timeline segments & grounding response...</span>
                </div>
              )}
            </div>

            {/* Quick Action Suggestion Chips */}
            <div className="quick-prompts">
              <button
                className="quick-chip"
                onClick={() => handleSendQuestion("What was the main conclusion or verdict in the video?")}
                disabled={isSearching || !analysisResult}
                title={!analysisResult ? "Upload a video first" : undefined}
              >
                <Target size={12} />
                <span>Main conclusion</span>
              </button>
              <button
                className="quick-chip"
                onClick={() => handleSendQuestion("What is the speaker's main purpose or goal in this video?")}
                disabled={isSearching || !analysisResult}
                title={!analysisResult ? "Upload a video first" : undefined}
              >
                <MessageSquare size={12} />
                <span>Speaker's purpose</span>
              </button>
              <button
                className="quick-chip"
                onClick={() => handleSendQuestion("Summarize the key highlights and takeaways")}
                disabled={isSearching || !analysisResult}
                title={!analysisResult ? "Upload a video first" : undefined}
              >
                <Sparkles size={12} />
                <span>Key highlights</span>
              </button>
            </div>

            {/* Input Bar */}
            <form
              className="chat-input-bar"
              onSubmit={(e) => {
                e.preventDefault();
                handleSendQuestion();
              }}
            >
              <input
                type="text"
                className="chat-input"
                placeholder={
                  analysisResult
                    ? "Ask what was said, query a topic, or locate a timestamp..."
                    : "Upload a video first to search timeline..."
                }
                value={inputPrompt}
                onChange={(e) => setInputPrompt(e.target.value)}
                disabled={isSearching}
              />
              <button
                type="submit"
                className="chat-send-btn"
                disabled={!inputPrompt.trim() || isSearching}
                title="Search timeline"
              >
                {isSearching ? (
                  <span className="spinner spinner-sm" />
                ) : (
                  <>
                    <Search size={15} />
                    <span>Search</span>
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

export default VideoIntelligence;
