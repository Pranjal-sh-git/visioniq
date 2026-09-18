import React, { useState, useRef } from 'react';
import {
  analyzeVideo,
  searchVideo,
  getVideoSummary,
  VideoAnalysisResult,
  VideoSearchResponse,
} from '../services/api';

interface VideoChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  startTime?: number | null;
  endTime?: number | null;
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

  // Video Analysis State
  const [analysisResult, setAnalysisResult] = useState<VideoAnalysisResult | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [keyTopics, setKeyTopics] = useState<string[]>([]);

  // Video Chat State
  const [messages, setMessages] = useState<VideoChatMessage[]>([]);
  const [inputPrompt, setInputPrompt] = useState<string>('');
  const [isSearching, setIsSearching] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoPlayerRef = useRef<HTMLVideoElement>(null);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  const isApiActive = isAnalyzing || isSearching;

  const scrollToBottom = () => {
    setTimeout(() => {
      chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
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
    setMessages([]);

    await runVideoAnalysis(file);
  };

  const runVideoAnalysis = async (file: File) => {
    setIsAnalyzing(true);
    setErrorMessage(null);

    try {
      const result = await analyzeVideo(file);
      setAnalysisResult(result);

      // Fetch auto-generated summary and key topics
      try {
        const summaryData = await getVideoSummary(result.video_id);
        setSummary(summaryData.summary);
        setKeyTopics(summaryData.key_topics || []);
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
          text: `Video analyzed successfully (${result.duration_seconds}s, ${result.chunks_count} segments indexed). You can now ask questions about statements made, topics discussed, or specific scenes!`,
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

  const handleSeekToTime = (timeInSeconds: number) => {
    if (videoPlayerRef.current) {
      videoPlayerRef.current.currentTime = timeInSeconds;
      videoPlayerRef.current.play();
    }
  };

  const handleSendQuestion = async (queryTextOverride?: string) => {
    const questionText = (queryTextOverride || inputPrompt).trim();
    if (!questionText || isSearching) return;

    // Check if a video has been uploaded first
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
        0.65
      );

      let replyText = searchResult.answer;
      if (!searchResult.found_match) {
        replyText = "I couldn't find that in the video. The topic does not appear in the transcribed audio or indexed timeline.";
      }

      const assistantMsg: VideoChatMessage = {
        id: `v-asst-${Date.now()}`,
        sender: 'assistant',
        text: replyText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        startTime: searchResult.start_time,
        endTime: searchResult.end_time,
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
    setSelectedFileUrl();
  };

  const setSelectedFileUrl = () => {
    setVideoUrl(null);
    setAnalysisResult(null);
    setSummary(null);
    setKeyTopics([]);
    setMessages([]);
    setErrorMessage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div>
      {/* Small top progress bar when API call is active */}
      {isApiActive && <div className="api-progress-bar" />}

      <div className="tab-header">
        <div className="tab-header-titles">
          <h1>Video Intelligence</h1>
          <p>Upload a video to transcribe speech, index timeline chunks, extract key topics, and perform grounded temporal Q&A with clickable timestamp playback.</p>
        </div>

        {isApiActive && (
          <div className="api-live-indicator">
            <span className="pulse-dot" />
            <span>{isAnalyzing ? 'Processing Video Pipeline...' : 'Searching Timeline...'}</span>
          </div>
        )}
      </div>

      {errorMessage && (
        <div className="error-banner">
          <span className="error-msg">⚠️ {errorMessage}</span>
          <button className="error-close-btn" onClick={() => setErrorMessage(null)}>×</button>
        </div>
      )}

      <div className="dashboard-grid">
        {/* Left Column: Video Player & Summary */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="card">
            <div className="card-title">
              <span>Video Input</span>
              {videoUrl && (
                <button
                  className="sample-chip"
                  onClick={clearVideo}
                  style={{ fontSize: '0.75rem' }}
                >
                  Upload New
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
                <div className="dropzone-icon">🎬</div>
                <div className="dropzone-title">Drag & drop your video file here</div>
                <div className="dropzone-subtitle">or click to browse (.mp4, .mov, .webm, .avi)</div>
                <input
                  type="file"
                  ref={fileInputRef}
                  className="file-input"
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

          {/* Loading Spinner for Video Processing */}
          {isAnalyzing && (
            <div className="card loading-box">
              <div className="spinner" />
              <div className="loading-text">Processing Video Pipeline...</div>
              <div className="loading-subtext">
                Extracting audio, transcribing speech with Whisper, extracting timeline keyframes, and generating Azure AI Search embeddings.
              </div>
            </div>
          )}

          {/* Video Summary & Key Topics Card */}
          {!isAnalyzing && analysisResult && (
            <div className="card">
              <div className="card-title">
                <span>Video Intelligence Overview</span>
                <span className="tool-tag">ID: {analysisResult.video_id}</span>
              </div>

              <div className="badges-row" style={{ marginBottom: '1rem' }}>
                <span className="badge badge-confident">
                  ⏱️ {analysisResult.duration_seconds}s Duration
                </span>
                <span className="badge badge-category">
                  🎞️ {analysisResult.chunks_count} Timestamped Chunks
                </span>
                <span className="badge badge-category">
                  📸 {analysisResult.total_keyframes} Keyframes
                </span>
              </div>

              {summary && (
                <div className="video-summary-box">
                  <div className="specs-title">Executive Summary</div>
                  <p className="video-summary-text">{summary}</p>

                  {keyTopics.length > 0 && (
                    <div>
                      <div className="topics-title">Key Topics</div>
                      <div className="topics-list">
                        {keyTopics.map((topic, i) => (
                          <span
                            key={i}
                            className="topic-chip"
                            style={{ cursor: 'pointer' }}
                            onClick={() => handleSendQuestion(`Tell me about ${topic}`)}
                            title="Click to ask about this topic"
                          >
                            🏷️ {topic}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Grounded Video Chat */}
        <div>
          <div className="chat-container">
            <div className="chat-header">
              <div className="chat-title">
                <span>🔍 Video Temporal Search</span>
                <span className="agent-badge">Temporal RAG</span>
              </div>
              {analysisResult && (
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {analysisResult.filename}
                </span>
              )}
            </div>

            <div className="chat-messages">
              {messages.length === 0 ? (
                <div style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: '5rem', fontSize: '0.9rem' }}>
                  {videoUrl
                    ? 'Video loaded. Ask questions about spoken dialogue or key statements!'
                    : 'Upload a video to search for spoken dialogue, key reviewer statements, and exact timestamped moments.'}
                </div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`message-bubble ${msg.sender === 'user' ? 'message-user' : 'message-assistant'}`}
                  >
                    <div>{msg.text}</div>

                    {/* Clickable Seek Timestamp Button */}
                    {msg.startTime !== undefined && msg.startTime !== null && (
                      <div>
                        <button
                          className="timestamp-btn"
                          onClick={() => handleSeekToTime(msg.startTime!)}
                          title={`Click to seek video to ${formatTimestamp(msg.startTime!)}`}
                        >
                          ▶ Jump to {formatTimestamp(msg.startTime!)}
                          {msg.endTime !== null && msg.endTime !== undefined ? ` - ${formatTimestamp(msg.endTime)}` : ''}
                        </button>
                      </div>
                    )}

                    {/* Supporting Transcript Snippet */}
                    {msg.supportingSegment && (
                      <div className="supporting-segment-box">
                        "{msg.supportingSegment}"
                      </div>
                    )}
                  </div>
                ))
              )}

              {isSearching && (
                <div className="message-bubble message-assistant" style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <div className="spinner spinner-sm-light" />
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    Searching timeline segments and grounding response...
                  </span>
                </div>
              )}
              <div ref={chatBottomRef} />
            </div>

            {/* Quick Action Suggestion Chips */}
            <div className="quick-prompts">
              <button
                className="quick-chip"
                onClick={() => handleSendQuestion("What did the speaker say about audience capacity?")}
                disabled={isSearching || !analysisResult}
                title={!analysisResult ? "Upload a video first" : undefined}
              >
                👥 Audience capacity?
              </button>
              <button
                className="quick-chip"
                onClick={() => handleSendQuestion("What was the main conclusion?")}
                disabled={isSearching || !analysisResult}
                title={!analysisResult ? "Upload a video first" : undefined}
              >
                🎯 Main conclusion?
              </button>
              <button
                className="quick-chip"
                onClick={() => handleSendQuestion("What did the reviewer say about battery life?")}
                disabled={isSearching || !analysisResult}
              >
                🔋 Battery review?
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
                    ? "Ask what was said, locate a scene, or query a topic..."
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
              >
                {isSearching ? (
                  <>
                    <span className="spinner spinner-sm" />
                    <span>Searching...</span>
                  </>
                ) : (
                  'Search'
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
