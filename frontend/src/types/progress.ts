/**
 * Types for video processing progress tracking
 */

export type ProcessStep = 
  | 'validating'     // 링크 검증 중
  | 'verifying'      // 영상 확인 중
  | 'extracting'     // 스크립트 추출 중
  | 'summarizing'    // AI 요약 생성 중
  | 'complete';      // 완료

export interface ProcessState {
  currentStep: ProcessStep;
  progress: number;      // 0-100 진행률
  error?: ProcessError;
}

export interface ProcessError {
  step: ProcessStep;
  code: string;
  message: string;
  suggestion?: string;
}

export const STEP_INFO: Record<ProcessStep, { label: string; description: string }> = {
  validating: {
    label: '링크 검증 중',
    description: 'YouTube URL을 확인하고 있습니다'
  },
  verifying: {
    label: '영상 확인 중',
    description: '영상에 접근하고 있습니다'
  },
  extracting: {
    label: '스크립트 추출 중',
    description: '자막을 가져오고 있습니다'
  },
  summarizing: {
    label: 'AI 요약 생성 중',
    description: '핵심 내용을 정리하고 있습니다'
  },
  complete: {
    label: '완료',
    description: '요약이 완료되었습니다'
  }
};
