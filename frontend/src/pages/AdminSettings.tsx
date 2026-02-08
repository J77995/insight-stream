import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { getCategories, getPrompt } from "@/services/api";
import type { CategoryInfo, PromptTemplate } from "@/types/prompts";
import { toast } from "sonner";

const AdminSettings = () => {
  const navigate = useNavigate();
  const [categories, setCategories] = useState<CategoryInfo[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [currentTemplate, setCurrentTemplate] = useState<PromptTemplate | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // AI Model Settings
  const [aiProvider, setAiProvider] = useState<string>(() => {
    return localStorage.getItem('ai_provider') || 'openai';
  });
  const [aiModel, setAiModel] = useState<string>(() => {
    return localStorage.getItem('ai_model') || 'gpt-4o-mini';
  });

  // Load categories on mount
  useEffect(() => {
    getCategories()
      .then((data) => {
        setCategories(data);
        if (data.length > 0) {
          setSelectedCategory(data[0].category);
        }
      })
      .catch((error) => {
        console.error('Failed to load categories:', error);
        toast.error('카테고리 로드 실패');
      });
  }, []);

  // Load prompt when category changes
  useEffect(() => {
    if (!selectedCategory) return;

    setIsLoading(true);
    getPrompt(selectedCategory)
      .then(setCurrentTemplate)
      .catch((error) => {
        console.error('Failed to load prompt:', error);
        toast.error('프롬프트 로드 실패');
      })
      .finally(() => setIsLoading(false));
  }, [selectedCategory]);

  // Handle AI provider change
  const handleProviderChange = (newProvider: string) => {
    setAiProvider(newProvider);
    localStorage.setItem('ai_provider', newProvider);
    
    // Set default model based on provider
    const defaultModel = newProvider === 'gemini' ? 'gemini-2.0-flash-exp' : 'gpt-4o-mini';
    setAiModel(defaultModel);
    localStorage.setItem('ai_model', defaultModel);
    toast.success('AI Provider가 변경되었습니다');
  };

  // Handle model change
  const handleModelChange = (newModel: string) => {
    setAiModel(newModel);
    localStorage.setItem('ai_model', newModel);
    toast.success('모델이 변경되었습니다');
  };

  // Get model options based on provider
  const getModelOptions = () => {
    if (aiProvider === 'gemini') {
      return [
        { value: 'gemini-2.0-flash-exp', label: 'Gemini 2.0 Flash (기본, 빠름)' },
        { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash (저비용)' },
        { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro (표준)' },
        { value: 'gemini-2.0-pro-exp', label: 'Gemini 2.0 Pro (최상위, 실험)' },
      ];
    } else {
      return [
        { value: 'gpt-4o-mini', label: 'GPT-4o Mini (기본, 저비용)' },
        { value: 'gpt-4o', label: 'GPT-4o (표준)' },
        { value: 'gpt-4-turbo', label: 'GPT-4 Turbo (빠름)' },
        { value: 'gpt-4', label: 'GPT-4 (원본)' },
        { value: 'o1-preview', label: 'o1-preview (추론 특화, 최상위)' },
        { value: 'o1-mini', label: 'o1-mini (추론 특화, 경량)' },
      ];
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-sm border-b border-border">
        <div className="flex items-center justify-between px-4 md:px-6 h-14">
          <h1 className="text-xl font-bold">상세 설정</h1>
          <Button variant="outline" onClick={() => navigate(-1)} className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            뒤로가기
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto p-6 space-y-6">
        {/* AI Model Settings Section */}
        <div className="bg-card rounded-lg border p-6 space-y-6">
          <div>
            <h2 className="text-lg font-semibold mb-2">AI 모델 설정</h2>
            <p className="text-sm text-muted-foreground mb-6">
              요약에 사용할 AI Provider와 모델을 선택하세요. 설정은 모든 요약에 자동으로 적용됩니다.
            </p>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="ai-provider">AI Provider</Label>
                <Select value={aiProvider} onValueChange={handleProviderChange}>
                  <SelectTrigger id="ai-provider" className="w-full mt-2">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="openai">OpenAI</SelectItem>
                    <SelectItem value="gemini">Google Gemini</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="ai-model">모델</Label>
                <Select value={aiModel} onValueChange={handleModelChange}>
                  <SelectTrigger id="ai-model" className="w-full mt-2">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {getModelOptions().map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-950 rounded-lg">
              <p className="text-sm">
                <strong>현재 설정:</strong> {aiProvider === 'openai' ? 'OpenAI' : 'Google Gemini'} - {aiModel}
              </p>
            </div>
          </div>
        </div>

        {/* Prompt Template Section */}
        <div className="bg-card rounded-lg border p-6 space-y-6">
          <div>
            <h2 className="text-lg font-semibold mb-4">프롬프트 템플릿 조회</h2>
            <p className="text-sm text-muted-foreground mb-4">
              카테고리별 프롬프트를 확인할 수 있습니다. 현재는 읽기 전용이며, 추후 수정 및 저장 기능이 추가됩니다.
            </p>

            {/* Category Selection */}
            <div className="mb-6">
              <Label htmlFor="category-select">카테고리 선택</Label>
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger id="category-select" className="w-full mt-2">
                  <SelectValue placeholder="카테고리를 선택하세요" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((cat) => (
                    <SelectItem key={cat.category} value={cat.category}>
                      <div className="flex flex-col">
                        <span className="font-medium">{cat.display_name}</span>
                        <span className="text-xs text-muted-foreground">
                          {cat.description}
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Prompt Display */}
            {isLoading ? (
              <div className="text-center py-12">
                <div className="inline-block h-8 w-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
                <p className="mt-4 text-muted-foreground">프롬프트 로드 중...</p>
              </div>
            ) : currentTemplate ? (
              <div className="space-y-6">
                {/* Basic Info */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>카테고리명</Label>
                    <div className="mt-2 p-3 bg-muted rounded-md">
                      {currentTemplate.display_name}
                    </div>
                  </div>
                  <div>
                    <Label>설명</Label>
                    <div className="mt-2 p-3 bg-muted rounded-md">
                      {currentTemplate.description}
                    </div>
                  </div>
                </div>

                {/* Prompt Tabs */}
                <Tabs defaultValue="overview" className="w-full">
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="overview">Overview</TabsTrigger>
                    <TabsTrigger value="detail">Detail</TabsTrigger>
                    <TabsTrigger value="system">System</TabsTrigger>
                  </TabsList>

                  <TabsContent value="overview" className="space-y-2">
                    <Label>Overview 프롬프트</Label>
                    <Textarea
                      value={currentTemplate.overview_prompt}
                      readOnly
                      rows={15}
                      className="font-mono text-sm bg-muted cursor-not-allowed"
                    />
                    <div className="text-xs text-muted-foreground text-right">
                      {currentTemplate.overview_prompt.length} 글자
                    </div>
                    <div className="bg-blue-50 dark:bg-blue-950 p-3 rounded text-sm">
                      <strong>참고:</strong> {'{transcript}'}는 실제 요약 시 영상 스크립트로 자동 대체됩니다.
                    </div>
                  </TabsContent>

                  <TabsContent value="detail" className="space-y-2">
                    <Label>Detail 프롬프트</Label>
                    <Textarea
                      value={currentTemplate.detail_prompt}
                      readOnly
                      rows={15}
                      className="font-mono text-sm bg-muted cursor-not-allowed"
                    />
                    <div className="text-xs text-muted-foreground text-right">
                      {currentTemplate.detail_prompt.length} 글자
                    </div>
                  </TabsContent>

                  <TabsContent value="system" className="space-y-2">
                    <Label>System 프롬프트</Label>
                    <Textarea
                      value={currentTemplate.system_prompt}
                      readOnly
                      rows={10}
                      className="font-mono text-sm bg-muted cursor-not-allowed"
                    />
                    <div className="text-xs text-muted-foreground text-right">
                      {currentTemplate.system_prompt.length} 글자
                    </div>
                    <div className="bg-amber-50 dark:bg-amber-950 p-3 rounded text-sm">
                      <strong>주의:</strong> System 프롬프트는 AI 모델의 역할과 행동을 정의합니다.
                    </div>
                  </TabsContent>
                </Tabs>

                <div className="bg-muted p-4 rounded-lg">
                  <p className="text-sm text-muted-foreground">
                    💡 <strong>추후 기능:</strong> 프롬프트 수정 및 저장 기능이 추가될 예정입니다.
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                카테고리를 선택하면 프롬프트를 확인할 수 있습니다
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminSettings;
