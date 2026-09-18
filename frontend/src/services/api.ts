/**
 * VisionIQ Frontend API Client & Type Definitions
 * Connects the React UI to FastAPI endpoints for Product & Video Intelligence.
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface HealthStatusResponse {
  status: string;
}

export interface ProductSpec {
  battery_life?: string;
  noise_cancellation?: string;
  weight?: string;
  driver_size?: string;
  connectivity?: string;
  material?: string;
  dimensions?: string;
  warranty?: string;
  water_resistance?: string;
  [key: string]: string | undefined;
}

export interface ProductMatch {
  id: string;
  name: string;
  brand: string;
  category: string;
  description: string;
  specifications: ProductSpec;
  features?: string[];
  image_urls?: string[];
  similarity_score: number;
  is_confident_match: boolean;
  confidence_threshold?: number;
  match_status?: string;
}

export interface OpenWorldProductIdentification {
  brand: string;
  model: string;
  product_name: string;
  category: string;
  visual_description: string;
  confidence: 'high' | 'medium' | 'low';
  key_features_observed: string[];
  is_open_world?: boolean;
}

export interface SimilarCatalogProduct extends ProductMatch {
  is_exact_catalog_match?: boolean;
  recommendation_reason?: string;
}

export interface IdentifyProductResponse {
  success: boolean;
  identified_product?: OpenWorldProductIdentification;
  similar_catalog_products?: SimilarCatalogProduct[];
  catalog_match?: SimilarCatalogProduct | null;
  best_match: ProductMatch | null;
  all_matches: ProductMatch[];
  is_confident_match: boolean;
  count: number;
}

export interface AgentToolOutput {
  product_id?: string;
  product_name?: string;
  question?: string;
  answer?: string;
  requires_clarification?: boolean;
  is_available?: boolean;
  grounded_field?: string;
  catalog_value?: string;
  hallucination?: boolean;

  source_product_id?: string;
  source_product_name?: string;
  category?: string;
  similar_products?: ProductMatch[];
  count?: number;

  video_id?: string;
  found_match?: boolean;
  start_time?: number | null;
  end_time?: number | null;
  supporting_segment?: string;
  confidence_score?: number;

  best_match?: ProductMatch;
  all_matches?: ProductMatch[];
  is_confident?: boolean;
  [key: string]: any;
}

export interface AgentQueryResponse {
  query: string;
  selected_tool: string;
  tool_parameters: Record<string, any>;
  routing_reasoning: string;
  tool_output: AgentToolOutput;
}

export interface KeyframeInfo {
  time_sec: number;
  filename: string;
  relative_path: string;
}

export interface VideoChunk {
  chunk_id: string;
  video_id: string;
  start_time: number;
  end_time: number;
  topic: string;
  transcript: string;
  keyframe_path?: string;
}

export interface VideoAnalysisResult {
  video_id: string;
  filename: string;
  duration_seconds: number;
  fps: number;
  resolution: string;
  total_keyframes: number;
  keyframes: KeyframeInfo[];
  full_transcript: string;
  chunks_count: number;
  chunks: VideoChunk[];
  cached: boolean;
  indexed_segments_count?: number;
}

export interface VideoSummaryResponse {
  video_id: string;
  summary: string;
  key_topics: string[];
}

export interface VideoSearchResponse {
  video_id: string;
  question: string;
  answer: string;
  found_match: boolean;
  start_time: number | null;
  end_time: number | null;
  supporting_segment?: string;
  confidence_score?: number;
  candidate_segments?: any[];
}

/**
 * Normalizes network or HTTP errors into friendly user messages.
 */
function handleNetworkError(err: any, defaultContext: string): Error {
  if (err instanceof TypeError && err.message.toLowerCase().includes('fetch')) {
    return new Error(
      `Couldn't connect to the backend server. Please verify that the backend API is running at ${API_BASE_URL}.`
    );
  }
  if (err.message && err.message.includes('Failed to fetch')) {
    return new Error(
      `Couldn't connect to the server at ${API_BASE_URL}. Please ensure backend/main.py is running.`
    );
  }
  return new Error(err.message || defaultContext);
}

/**
 * Health check endpoint
 */
export async function getHealthStatus(): Promise<HealthStatusResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
      throw new Error(`Health check failed with status: ${response.status}`);
    }
    return await response.json();
  } catch (err: any) {
    throw handleNetworkError(err, 'Health check failed');
  }
}

/**
 * Uploads an image file or passes an image URL to identify products.
 */
export async function identifyProduct(
  fileOrUrl: File | string,
  topK: number = 3
): Promise<IdentifyProductResponse> {
  try {
    let response: Response;

    if (typeof fileOrUrl === 'string') {
      const formData = new FormData();
      formData.append('image_url', fileOrUrl);
      formData.append('top_k', topK.toString());

      response = await fetch(`${API_BASE_URL}/api/product/identify`, {
        method: 'POST',
        body: formData,
      });
    } else {
      const formData = new FormData();
      formData.append('file', fileOrUrl);
      formData.append('top_k', topK.toString());

      response = await fetch(`${API_BASE_URL}/api/product/identify`, {
        method: 'POST',
        body: formData,
      });
    }

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`Product identification failed (${response.status}): ${errorBody || response.statusText}`);
    }

    return await response.json();
  } catch (err: any) {
    throw handleNetworkError(err, 'Product identification failed');
  }
}

/**
 * Queries the Microsoft Foundry Agent with natural language prompt and optional context.
 */
export async function queryAgent(
  prompt: string,
  productId?: string,
  videoId?: string,
  mediaUrl?: string
): Promise<AgentQueryResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/agent/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt,
        product_id: productId || null,
        video_id: videoId || null,
        media_url: mediaUrl || null,
      }),
    });

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`Agent query failed (${response.status}): ${errorBody || response.statusText}`);
    }

    return await response.json();
  } catch (err: any) {
    throw handleNetworkError(err, 'Agent query failed');
  }
}

/**
 * Uploads a video file for transcription, keyframe extraction, and timeline indexing.
 */
export async function analyzeVideo(
  file: File,
  forceReprocess: boolean = false
): Promise<VideoAnalysisResult> {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const url = `${API_BASE_URL}/api/video/analyze?force_reprocess=${forceReprocess}`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`Video analysis failed (${response.status}): ${errorBody || response.statusText}`);
    }

    return await response.json();
  } catch (err: any) {
    throw handleNetworkError(err, 'Video analysis failed');
  }
}

/**
 * Searches a processed video's timestamped segments for grounded Q&A.
 */
export async function searchVideo(
  videoId: string,
  query: string,
  topK: number = 3,
  confidenceThreshold: number = 0.65
): Promise<VideoSearchResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/video/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        video_id: videoId,
        query,
        top_k: topK,
        confidence_threshold: confidenceThreshold,
      }),
    });

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`Video search failed (${response.status}): ${errorBody || response.statusText}`);
    }

    return await response.json();
  } catch (err: any) {
    throw handleNetworkError(err, 'Video search failed');
  }
}

/**
 * Fetches auto-generated summary and key topics for a processed video.
 */
export async function getVideoSummary(videoId: string): Promise<VideoSummaryResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/video/${videoId}/summary`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`Failed to load video summary (${response.status}): ${errorBody || response.statusText}`);
    }

    return await response.json();
  } catch (err: any) {
    throw handleNetworkError(err, 'Failed to retrieve video summary');
  }
}
