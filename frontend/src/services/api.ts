/**
 * API Service Layer for Insight Stream
 * Handles all backend communication
 */

import { VideoData, CategoryInfo, PromptTemplate } from '../types/prompts';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ApiErrorDetail {
  error: string;
  message: string;
  suggestion?: string;
}

export interface ApiError {
  detail: ApiErrorDetail;
}

/**
 * Summarize a YouTube video by extracting transcript and generating AI summaries
 *
 * @param url - YouTube video URL
 * @param aiProvider - AI provider to use ('gemini' or 'openai')
 * @param model - Optional model name to use
 * @param category - Content category for prompt selection
 * @param formatType - Format type for modular prompts ('dialogue' or 'presentation')
 * @returns VideoData object with transcript and summaries
 * @throws Error with Korean message if request fails
 */
export const summarizeVideo = async (
  url: string,
  aiProvider: string = 'gemini',
  model?: string,
  category: string = 'default',
  formatType?: string,
  signal?: AbortSignal
): Promise<VideoData> => {
  try {
    const requestBody: {
      url: string;
      ai_provider: string;
      model?: string;
      category?: string;
      format_type?: string;
    } = {
      url,
      ai_provider: aiProvider,
      category,
    };

    if (model) {
      requestBody.model = model;
    }

    if (formatType) {
      requestBody.format_type = formatType;
    }

    const response = await fetch(`${API_BASE_URL}/summarize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
      signal, // Add abort signal
    });

    if (!response.ok) {
      // Parse error response
      const errorData: ApiError = await response.json();
      const message = errorData.detail?.message || '영상 처리 중 오류가 발생했습니다';
      throw new Error(message);
    }

    const data: VideoData = await response.json();
    return data;
  } catch (error) {
    // Network errors or other unexpected errors
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('서버와의 연결에 실패했습니다. 백엔드가 실행 중인지 확인해주세요.');
  }
};

/**
 * Get all available prompt categories
 *
 * @returns List of category information
 */
export const getCategories = async (): Promise<CategoryInfo[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/prompts/categories`);

    if (!response.ok) {
      throw new Error('카테고리 로드 실패');
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching categories:', error);
    throw error;
  }
};

/**
 * Get prompt template for a specific category
 *
 * @param category - Category name
 * @returns Complete prompt template
 */
export const getPrompt = async (category: string): Promise<PromptTemplate> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/prompts/${category}`);

    if (!response.ok) {
      throw new Error('프롬프트 로드 실패');
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching prompt:', error);
    throw error;
  }
};

/**
 * Generate summary with custom prompts (for immediate testing)
 *
 * @param params - Video info, optional transcript, and custom prompts
 * @returns VideoData with new summaries
 */
export const customSummarize = async (params: {
  video_id: string;
  transcript?: string;  // Optional - backend will use cache if not provided
  custom_overview_prompt?: string;
  custom_detail_prompt?: string;
  custom_system_prompt?: string;
  ai_provider: string;
  model?: string;
  signal?: AbortSignal;
}): Promise<VideoData> => {
  try {
    const { signal, ...requestParams } = params;
    const response = await fetch(`${API_BASE_URL}/api/prompts/custom`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestParams),
      signal, // Add abort signal
    });

    if (!response.ok) {
      const errorData: ApiError = await response.json();
      const message = errorData.detail?.message || '재요약 중 오류가 발생했습니다';
      throw new Error(message);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('재요약 요청에 실패했습니다');
  }
};

/**
 * Chat with video based on transcript context
 *
 * @param params - Video ID, message, conversation history, and AI settings
 * @returns ChatResponse with AI reply
 */
export const chatWithVideo = async (params: {
  video_id: string;
  message: string;
  conversation_history: { role: string; content: string }[];
  ai_provider: string;
  model?: string;
}): Promise<{ video_id: string; reply: string }> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    });

    if (!response.ok) {
      const errorData: ApiError = await response.json();
      const message = errorData.detail?.message || '채팅 중 오류가 발생했습니다';
      throw new Error(message);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('채팅 요청에 실패했습니다');
  }
};

/**
 * Translate a single text segment to Korean
 *
 * @param params - Video ID, text, and AI settings
 * @returns Translated text
 */
export const translateSegment = async (params: {
  video_id: string;
  text: string;
  ai_provider: string;
  model?: string;
}): Promise<{ translation: string }> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/translate/segment`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    });

    if (!response.ok) {
      const errorData: ApiError = await response.json();
      const message = errorData.detail?.message || '번역 중 오류가 발생했습니다';
      throw new Error(message);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('번역 요청에 실패했습니다');
  }
};

/**
 * Translate multiple text segments to Korean in batch
 *
 * @param params - Video ID, segments array, and AI settings
 * @returns Array of translated texts
 */
export const translateBatch = async (params: {
  video_id: string;
  segments: string[];
  ai_provider: string;
  model?: string;
}): Promise<{ translations: string[] }> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/translate/batch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    });

    if (!response.ok) {
      const errorData: ApiError = await response.json();
      const message = errorData.detail?.message || '전체 번역 중 오류가 발생했습니다';
      throw new Error(message);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('전체 번역 요청에 실패했습니다');
  }
};
