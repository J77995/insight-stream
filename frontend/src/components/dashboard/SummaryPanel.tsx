import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Edit } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { useState, useEffect } from "react";
import { ProcessDialog } from "@/components/ProcessDialog";
import type { ProcessState } from "@/types/progress";
import { toast } from "sonner";

interface SummaryPanelProps {
  title: string;
  overview: string;
  detail: string;
  category?: string;
  promptsUsed?: {
    overview: string;
    detail: string;
  };
  onResummarize?: (newPrompts: {
    overview: string;
    detail: string;
  }, signal?: AbortSignal) => Promise<void>;
}

const SummaryPanel = ({ title, overview, detail, category, promptsUsed, onResummarize }: SummaryPanelProps) => {
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [overviewPrompt, setOverviewPrompt] = useState(promptsUsed?.overview || '');
  const [detailPrompt, setDetailPrompt] = useState(promptsUsed?.detail || '');
  const [isResummarizing, setIsResummarizing] = useState(false);
  const [showProcessDialog, setShowProcessDialog] = useState(false);
  const [abortController, setAbortController] = useState<AbortController | null>(null);
  const [processState, setProcessState] = useState<ProcessState>({
    currentStep: 'summarizing',
    progress: 0
  });

  const handleResummarize = async () => {
    if (!onResummarize) return;

    // Create abort controller for cancellation
    const controller = new AbortController();
    setAbortController(controller);

    setIsResummarizing(true);
    setShowProcessDialog(true);
    
    // Simulate progress for resummarize
    setProcessState({
      currentStep: 'summarizing',
      progress: 35
    });
    
    const progressInterval = setInterval(() => {
      setProcessState(prev => ({
        ...prev,
        progress: Math.min(prev.progress + 2, 95)
      }));
    }, 500);

    try {
      await onResummarize({
        overview: overviewPrompt,
        detail: detailPrompt
      }, controller.signal);
      
      clearInterval(progressInterval);
      setProcessState({
        currentStep: 'complete',
        progress: 100
      });
      
      setTimeout(() => {
        setEditDialogOpen(false);
        setShowProcessDialog(false);
        setAbortController(null);
      }, 800);
    } catch (error) {
      clearInterval(progressInterval);
      
      // Check if error was caused by abort
      if (controller.signal.aborted) {
        setShowProcessDialog(false);
        setIsResummarizing(false);
        setAbortController(null);
        return;
      }
      
      setProcessState({
        currentStep: 'summarizing',
        progress: 0,
        error: {
          step: 'summarizing',
          code: 'resummarize_error',
          message: error instanceof Error ? error.message : '재요약 중 오류가 발생했습니다',
          suggestion: '잠시 후 다시 시도해주세요'
        }
      });
      console.error('Resummarize failed:', error);
    } finally {
      setIsResummarizing(false);
    }
  };

  const handleCancelResummarize = () => {
    // Abort the ongoing request
    if (abortController) {
      abortController.abort();
      setAbortController(null);
    }
    setShowProcessDialog(false);
    setIsResummarizing(false);
    toast.info('재요약이 중단되었습니다');
  };

  return (
    <ScrollArea className="h-[calc(100vh-56px)] custom-scrollbar">
      <div className="max-w-3xl mx-auto px-6 py-8">
        {/* Header with Category and Prompt Edit Button */}
        <div className="flex justify-between items-center mb-4 animate-fade-in">
          {category && (
            <Badge variant="secondary" className="text-sm">
              {category}
            </Badge>
          )}
          {onResummarize && promptsUsed && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setEditDialogOpen(true)}
              className="gap-2"
            >
              <Edit className="h-4 w-4" />
              프롬프트 수정
            </Button>
          )}
        </div>

        {/* Title */}
        <h1 className="text-2xl md:text-3xl font-bold text-foreground mb-8 animate-fade-in">
          {title}
        </h1>

        {/* Overview Section */}
        <section className="mb-8 animate-fade-in" style={{ animationDelay: "0.1s" }}>
          <div className="bg-highlight rounded-xl p-4 border border-highlight-foreground/10">
            <div className="flex items-start gap-2.5">
              <span className="text-lg">📌</span>
              <div className="flex-1">
                <h2 className="font-semibold text-sm text-foreground mb-2">
                  핵심 요약 (Overview)
                </h2>
                <p className="text-xs text-foreground/90 leading-relaxed">
                  {overview}
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Detail Section */}
        <section className="animate-fade-in" style={{ animationDelay: "0.2s" }}>
          <div className="flex items-center gap-2 mb-3">
            <span className="text-lg">📝</span>
            <h2 className="font-semibold text-sm text-foreground">
              상세 내용 (Details)
            </h2>
          </div>
          <div className="prose prose-sm max-w-none">
            <MarkdownContent content={detail} />
          </div>
        </section>

        {/* Prompt Edit Dialog */}
        {promptsUsed && onResummarize && (
          <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>프롬프트 수정하기</DialogTitle>
                <DialogDescription>
                  프롬프트를 수정하고 재요약을 요청할 수 있습니다. {'{transcript}'}는 자동으로 영상 스크립트로 대체됩니다.
                </DialogDescription>
              </DialogHeader>

              <Tabs defaultValue="overview" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="overview">Overview 프롬프트</TabsTrigger>
                  <TabsTrigger value="detail">Detail 프롬프트</TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="space-y-2">
                  <Textarea
                    value={overviewPrompt}
                    onChange={(e) => setOverviewPrompt(e.target.value)}
                    rows={15}
                    className="font-mono text-sm"
                    placeholder="Overview 프롬프트를 입력하세요..."
                  />
                  <div className="text-xs text-muted-foreground text-right">
                    {overviewPrompt.length} 글자
                  </div>
                </TabsContent>

                <TabsContent value="detail" className="space-y-2">
                  <Textarea
                    value={detailPrompt}
                    onChange={(e) => setDetailPrompt(e.target.value)}
                    rows={15}
                    className="font-mono text-sm"
                    placeholder="Detail 프롬프트를 입력하세요..."
                  />
                  <div className="text-xs text-muted-foreground text-right">
                    {detailPrompt.length} 글자
                  </div>
                </TabsContent>
              </Tabs>

              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setEditDialogOpen(false)}
                  disabled={isResummarizing}
                >
                  취소
                </Button>
                <Button
                  onClick={handleResummarize}
                  disabled={isResummarizing}
                >
                  {isResummarizing ? '재요약 중...' : '재요약 요청'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}
        
        {/* Process Dialog for Resummarize */}
        <ProcessDialog
          open={showProcessDialog}
          state={processState}
          onClose={() => setShowProcessDialog(false)}
          onCancel={handleCancelResummarize}
        />
      </div>
    </ScrollArea>
  );
};

// Enhanced markdown parser with support for bold, inline code, and links
const MarkdownContent = ({ content }: { content: string }) => {
  const lines = content.split("\n");

  // Parse inline markdown (bold, code, links)
  const parseInline = (text: string) => {
    const parts: (string | JSX.Element)[] = [];
    let currentIndex = 0;
    let keyCounter = 0;

    // Pattern: **bold**, `code`, or [text](url)
    const pattern = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g;
    let match;

    while ((match = pattern.exec(text)) !== null) {
      // Add text before match
      if (match.index > currentIndex) {
        parts.push(text.substring(currentIndex, match.index));
      }

      const matched = match[0];
      
      // Bold: **text**
      if (matched.startsWith('**') && matched.endsWith('**')) {
        parts.push(
          <strong key={`bold-${keyCounter++}`} className="font-semibold text-foreground">
            {matched.slice(2, -2)}
          </strong>
        );
      }
      // Code: `code`
      else if (matched.startsWith('`') && matched.endsWith('`')) {
        parts.push(
          <code key={`code-${keyCounter++}`} className="px-1.5 py-0.5 bg-muted text-foreground rounded text-xs font-mono">
            {matched.slice(1, -1)}
          </code>
        );
      }
      // Link: [text](url)
      else if (matched.startsWith('[')) {
        const linkMatch = matched.match(/\[([^\]]+)\]\(([^)]+)\)/);
        if (linkMatch) {
          parts.push(
            <a
              key={`link-${keyCounter++}`}
              href={linkMatch[2]}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline"
            >
              {linkMatch[1]}
            </a>
          );
        }
      }

      currentIndex = match.index + matched.length;
    }

    // Add remaining text
    if (currentIndex < text.length) {
      parts.push(text.substring(currentIndex));
    }

    return parts.length > 0 ? parts : text;
  };

  return (
    <div className="space-y-3">
      {lines.map((line, index) => {
        // H2
        if (line.startsWith("## ")) {
          return (
            <h3 key={index} className="text-base font-bold text-foreground mt-5 mb-2">
              {line.replace("## ", "")}
            </h3>
          );
        }
        // H3
        if (line.startsWith("### ")) {
          return (
            <h4 key={index} className="text-sm font-semibold text-foreground mt-4 mb-1.5">
              {line.replace("### ", "")}
            </h4>
          );
        }
        // Numbered list: 1. item
        if (line.match(/^\d+\.\s/)) {
          const textContent = line.replace(/^\d+\.\s/, "");
          return (
            <div key={index} className="flex items-start gap-2 pl-1">
              <span className="text-muted-foreground text-xs mt-0.5 font-medium min-w-[1.2rem]">
                {line.match(/^\d+/)?.[0]}.
              </span>
              <span className="text-xs text-foreground/90 leading-relaxed">
                {parseInline(textContent)}
              </span>
            </div>
          );
        }
        // Bullet list: - item or * item
        if (line.startsWith("- ") || line.startsWith("* ")) {
          const textContent = line.replace(/^[*-]\s/, "");
          return (
            <div key={index} className="flex items-start gap-2 pl-1">
              <span className="text-muted-foreground text-xs mt-0.5">•</span>
              <span className="text-xs text-foreground/90 leading-relaxed">
                {parseInline(textContent)}
              </span>
            </div>
          );
        }
        // Blockquote: > text
        if (line.startsWith("> ")) {
          return (
            <blockquote key={index} className="border-l-2 border-primary pl-3 py-1 text-xs italic text-foreground/80">
              {parseInline(line.replace("> ", ""))}
            </blockquote>
          );
        }
        // Horizontal rule: --- or ***
        if (line.trim() === "---" || line.trim() === "***") {
          return <hr key={index} className="my-3 border-border" />;
        }
        // Empty line
        if (line.trim() === "") {
          return <div key={index} className="h-1.5" />;
        }
        // Regular paragraph
        return (
          <p key={index} className="text-xs text-foreground/90 leading-relaxed">
            {parseInline(line)}
          </p>
        );
      })}
    </div>
  );
};

export default SummaryPanel;
