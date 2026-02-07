/**
 * Type definitions for prompt management
 */

export interface CategoryInfo {
  category: string;
  display_name: string;
  description: string;
}

export interface PromptTemplate {
  category: string;
  display_name: string;
  description: string;
  system_prompt: string;
  overview_prompt: string;
  detail_prompt: string;
}

export interface VideoData {
  video_id: string;
  title: string;
  full_transcript: string;
  summary_overview: string;
  summary_detail: string;
  category?: string;
  format_type?: string;
  prompts_used?: {
    overview: string;
    detail: string;
  };
  ai_provider?: string;
  model?: string;
}
