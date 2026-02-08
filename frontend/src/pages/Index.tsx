import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Link2, FileText, Settings, ArrowRight } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { summarizeVideo, getCategories } from "@/services/api";
import { CategoryInfo } from "@/types/prompts";
import { toast } from "sonner";
import { ProcessDialog } from "@/components/ProcessDialog";
import { ProcessState, ProcessStep } from "@/types/progress";

const Index = () => {
  const [url, setUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [category, setCategory] = useState<string>("general");
  const [formatType, setFormatType] = useState<string>("dialogue");
  const [categories, setCategories] = useState<CategoryInfo[]>([
    {
      category: 'general',
      display_name: '기본',
      description: '범용 컨텐츠'
    }
  ]);
  const [processState, setProcessState] = useState<ProcessState>({
    currentStep: 'validating',
    progress: 0
  });
  const [showProcessDialog, setShowProcessDialog] = useState(false);
  const [abortController, setAbortController] = useState<AbortController | null>(null);
  const navigate = useNavigate();

  // Load AI settings from localStorage
  const getAISettings = () => {
    const provider = localStorage.getItem('ai_provider') || 'openai';
    const model = localStorage.getItem('ai_model') || 'gpt-4o-mini';
    return { provider, model };
  };

  // Load categories on mount
  useEffect(() => {
    getCategories()
      .then(setCategories)
      .catch((error) => {
        console.error('Failed to load categories:', error);
        // Set default category if loading fails
        setCategories([{
          category: 'general',
          display_name: '기본',
          description: '범용 컨텐츠'
        }]);
      });
  }, []);

  // 진행률 계산 함수
  const calculateProgress = (step: ProcessStep, stepProgress: number = 0): number => {
    const stepWeights = {
      validating: 5,
      verifying: 10,
      extracting: 20,
      summarizing: 65,
      complete: 100
    };

    const steps: ProcessStep[] = ['validating', 'verifying', 'extracting', 'summarizing', 'complete'];
    const currentIndex = steps.indexOf(step);
    
    let totalProgress = 0;
    for (let i = 0; i < currentIndex; i++) {
      totalProgress += stepWeights[steps[i]];
    }
    
    totalProgress += (stepWeights[step] * stepProgress / 100);
    return totalProgress;
  };

  // 단계별 진행 업데이트
  const updateStep = (step: ProcessStep, stepProgress: number = 0) => {
    setProcessState({
      currentStep: step,
      progress: calculateProgress(step, stepProgress)
    });
  };

  // 에러 메시지에 따라 적절한 제안 반환
  const getSuggestion = (errorMessage: string): string => {
    if (errorMessage.includes('URL')) return '올바른 YouTube URL을 입력해주세요';
    if (errorMessage.includes('자막')) return '자막이 있는 다른 영상을 시도해주세요';
    if (errorMessage.includes('API')) return 'API 키 설정을 확인해주세요';
    if (errorMessage.includes('차단')) return '잠시 후 다시 시도하거나 네트워크를 변경해주세요';
    if (errorMessage.includes('연령 제한')) return '다른 영상을 시도해주세요';
    return '잠시 후 다시 시도해주세요';
  };

  // 에러 메시지를 기반으로 발생 단계 추정
  const getErrorStep = (errorMessage: string, currentStep: ProcessStep): ProcessStep => {
    if (errorMessage.includes('URL') || errorMessage.includes('유효하지')) {
      return 'validating';
    } else if (errorMessage.includes('영상을 찾을 수 없') || 
               errorMessage.includes('연령 제한') || 
               errorMessage.includes('재생할 수 없')) {
      return 'verifying';
    } else if (errorMessage.includes('자막') || 
               errorMessage.includes('스크립트') || 
               errorMessage.includes('차단')) {
      return 'extracting';
    } else if (errorMessage.includes('API') || 
               errorMessage.includes('요약')) {
      return 'summarizing';
    }
    return currentStep;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    // Create abort controller for cancellation
    const controller = new AbortController();
    setAbortController(controller);

    setIsLoading(true);
    setShowProcessDialog(true);

    // 진행 상태 초기화
    setProcessState({
      currentStep: 'validating',
      progress: 0
    });

    try {
      const { provider, model } = getAISettings();

      // 1. 링크 검증 중
      updateStep('validating', 50);
      await new Promise(resolve => setTimeout(resolve, 200)); // 최소 표시 시간

      // 2. 영상 확인 중
      updateStep('verifying', 50);
      await new Promise(resolve => setTimeout(resolve, 200)); // 최소 표시 시간
      
      // 3. 스크립트 추출 중 (실제 API 호출 시작)
      updateStep('extracting', 0);
      
      // API 호출 시작 - 요약 단계로 전환될 것임
      const apiPromise = summarizeVideo(url, provider, model, category, formatType, controller.signal);
      
      // 타이머로 요약 단계 진행률 업데이트 (실제 응답 대기 중)
      const summaryTimer = setInterval(() => {
        setProcessState(prev => {
          // extracting에서 summarizing으로 전환
          if (prev.currentStep === 'extracting' && prev.progress >= calculateProgress('extracting', 80)) {
            return {
              ...prev,
              currentStep: 'summarizing',
              progress: calculateProgress('summarizing', 10)
            };
          }
          // summarizing 단계에서 점진적으로 증가
          if (prev.currentStep === 'summarizing' && prev.progress < 95) {
            return {
              ...prev,
              progress: Math.min(prev.progress + 1.5, 95)
            };
          }
          // extracting 단계에서 점진적으로 증가
          if (prev.currentStep === 'extracting' && prev.progress < calculateProgress('extracting', 80)) {
            return {
              ...prev,
              progress: prev.progress + 1
            };
          }
          return prev;
        });
      }, 300);

      const data = await apiPromise;
      
      clearInterval(summaryTimer);

      // 4. 완료
      updateStep('complete', 100);
      
      setTimeout(() => {
        setShowProcessDialog(false);
        setIsLoading(false);
        navigate(`/dashboard?v=${data.video_id}`, {
          state: { videoData: data }
        });
      }, 800);

    } catch (error) {
      // Check if error was caused by abort
      if (controller.signal.aborted) {
        // User cancelled, just close dialog
        setShowProcessDialog(false);
        setIsLoading(false);
        setAbortController(null);
        return;
      }

      // 에러 발생 시 현재 단계에서 에러 표시
      const errorMessage = error instanceof Error ? error.message : "영상 처리 중 오류가 발생했습니다";
      const errorStep = getErrorStep(errorMessage, processState.currentStep);

      setProcessState({
        ...processState,
        currentStep: errorStep,
        error: {
          step: errorStep,
          code: 'processing_error',
          message: errorMessage,
          suggestion: getSuggestion(errorMessage)
        }
      });

      toast.error(errorMessage);
      setIsLoading(false);
    }
  };

  const handleRetry = () => {
    setProcessState({ currentStep: 'validating', progress: 0 });
    setShowProcessDialog(false);
    // 폼 제출 트리거
    const form = document.querySelector('form');
    if (form) {
      form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
    }
  };

  const handleCloseDialog = () => {
    setShowProcessDialog(false);
    setIsLoading(false);
  };

  const handleCancel = () => {
    // Abort the ongoing request
    if (abortController) {
      abortController.abort();
      setAbortController(null);
    }
    setShowProcessDialog(false);
    setIsLoading(false);
    toast.info('처리가 중단되었습니다');
  };

  const extractVideoId = (url: string): string | null => {
    const patterns = [
      /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/,
    ];
    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match) return match[1];
    }
    return null;
  };

  // Navigate back to last dashboard (if exists)
  const handleBackToSummary = () => {
    const lastDashboardUrl = localStorage.getItem('lastDashboardUrl');
    const lastVideoDataStr = localStorage.getItem('lastVideoData');

    if (lastDashboardUrl && lastVideoDataStr) {
      try {
        const lastVideoData = JSON.parse(lastVideoDataStr);
        navigate(lastDashboardUrl, { state: { videoData: lastVideoData } });
      } catch (error) {
        console.error('Failed to parse video data:', error);
        toast.error('이전 요약을 불러올 수 없습니다');
      }
    } else {
      toast.info('이전 요약이 없습니다');
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-background via-background to-surface px-4">
      {/* Back to Summary Button */}
      <div className="absolute top-6 left-6">
        <Button
          variant="outline"
          size="icon"
          onClick={handleBackToSummary}
          className="rounded-full bg-muted/50 hover:bg-primary hover:text-primary-foreground border-border/50 transition-all shadow-sm"
          title="요약으로 돌아가기"
        >
          <ArrowRight className="h-5 w-5" />
        </Button>
      </div>

      {/* Admin Mode Button */}
      <div className="absolute top-6 right-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/admin')}
          className="gap-2 rounded-2xl hover:bg-accent/50 transition-all"
        >
          <Settings className="h-4 w-4" />
          상세 설정
        </Button>
      </div>

      <div className="w-full max-w-2xl mx-auto animate-fade-in">
        {/* Brand Logo */}
        <div className="text-center mb-12">
          <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-blue-600 to-blue-400 bg-clip-text text-transparent py-4 tracking-tight leading-tight">
            InsightFind
          </h1>
        </div>

        {/* Main Title */}
        <h1 className="text-3xl md:text-4xl font-bold text-center text-foreground mb-16 tracking-tight">
          영상을 요약하고 인사이트를 발견하세요
        </h1>

        {/* Search Form */}
        <form onSubmit={handleSubmit} className="relative mb-10 space-y-5">
          {/* Category and Format Type Selection */}
          <div className="grid grid-cols-2 gap-4">
            <Select value={category} onValueChange={setCategory} disabled={isLoading}>
              <SelectTrigger className="h-14 bg-card/50 backdrop-blur-sm border-border/50 rounded-2xl shadow-apple-sm hover:shadow-apple-md transition-all glass-effect">
                <div className="flex items-center justify-center gap-2 w-full">
                  <span className="text-primary font-semibold">주제</span>
                  <span>
                    {categories.find(cat => cat.category === category)?.display_name || '선택하세요'}
                  </span>
                </div>
              </SelectTrigger>
              <SelectContent className="rounded-xl">
                {categories.map((cat) => (
                  <SelectItem key={cat.category} value={cat.category} className="rounded-lg">
                    {cat.display_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={formatType} onValueChange={setFormatType} disabled={isLoading}>
              <SelectTrigger className="h-14 bg-card/50 backdrop-blur-sm border-border/50 rounded-2xl shadow-apple-sm hover:shadow-apple-md transition-all glass-effect">
                <div className="flex items-center justify-center gap-2 w-full">
                  <span className="text-primary font-semibold">영상 유형</span>
                  <span>
                    {formatType === 'dialogue' ? '대화형 (인터뷰/회의)' : '발표형 (강연/세미나)'}
                  </span>
                </div>
              </SelectTrigger>
              <SelectContent className="rounded-xl">
                <SelectItem value="dialogue" className="rounded-lg">대화형 (인터뷰/회의)</SelectItem>
                <SelectItem value="presentation" className="rounded-lg">발표형 (강연/세미나)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* URL Input */}
          <div className="relative flex items-center">
            <Input
              type="url"
              placeholder="YouTube URL을 입력하세요"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full h-16 pl-6 pr-16 text-base bg-card/50 backdrop-blur-sm border-border/50 rounded-2xl shadow-apple-md focus:ring-2 focus:ring-primary/30 focus:shadow-apple-lg transition-all glass-effect"
              disabled={isLoading}
            />
            <Button
              type="submit"
              size="icon"
              disabled={isLoading || !url.trim()}
              className="absolute right-2 h-12 w-12 rounded-xl bg-primary hover:bg-primary/90 hover:scale-105 transition-all shadow-apple-sm"
            >
              {isLoading ? (
                <div className="h-5 w-5 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin-slow" />
              ) : (
                <Search className="h-5 w-5" />
              )}
            </Button>
          </div>
        </form>

        {/* Divider */}
        <div className="flex items-center gap-6 mb-8">
          <div className="flex-1 h-px bg-gradient-to-r from-transparent via-border to-transparent" />
          <span className="text-sm text-muted-foreground font-medium">지원예정</span>
          <div className="flex-1 h-px bg-gradient-to-r from-transparent via-border to-transparent" />
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-2 gap-4">
          <QuickActionCard
            icon={<Link2 className="h-5 w-5" />}
            title="붙여넣기"
            description="Youtube, 웹, 텍스트"
          />
          <QuickActionCard
            icon={<FileText className="h-5 w-5" />}
            title="업로드"
            description="비디오, 오디오, PDF 등"
          />
        </div>
      </div>

      {/* Process Dialog */}
      <ProcessDialog
        open={showProcessDialog}
        state={processState}
        onClose={handleCloseDialog}
        onRetry={handleRetry}
        onCancel={handleCancel}
      />
    </div>
  );
};

interface QuickActionCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
}

const QuickActionCard = ({ icon, title, description }: QuickActionCardProps) => {
  return (
    <button className="flex flex-col items-start p-5 rounded-2xl border border-border/50 bg-card/50 backdrop-blur-sm hover:bg-accent/50 hover:scale-[1.02] hover:shadow-apple-md transition-all text-left group glass-effect">
      <div className="text-muted-foreground group-hover:text-primary transition-colors mb-3">
        {icon}
      </div>
      <span className="font-semibold text-sm text-foreground mb-1">{title}</span>
      <span className="text-xs text-muted-foreground">{description}</span>
    </button>
  );
};

export default Index;
