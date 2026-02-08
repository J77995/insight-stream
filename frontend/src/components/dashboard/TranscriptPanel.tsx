import { ScrollArea } from "@/components/ui/scroll-area";
import { FileText, Languages, Download, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { useState } from "react";
import { timestampToSeconds } from "@/utils/timeUtils";
import { translateSegment, translateBatch } from "@/services/api";
import { toast } from "sonner";

interface TranscriptPanelProps {
  transcript: string;
  videoId: string;
  aiProvider: string;
  model?: string;
  onTimestampClick?: (seconds: number) => void;
}

const TranscriptPanel = ({ 
  transcript, 
  videoId, 
  aiProvider, 
  model, 
  onTimestampClick 
}: TranscriptPanelProps) => {
  const [showTranslation, setShowTranslation] = useState(false);
  const [segmentTranslations, setSegmentTranslations] = useState<Map<number, string>>(new Map());
  const [translatingSegments, setTranslatingSegments] = useState<Set<number>>(new Set());
  const [isTranslatingFull, setIsTranslatingFull] = useState(false);

  const lines = transcript.split("\n\n").filter((line) => line.trim());

  const handleTimestampClick = (timestamp: string) => {
    if (onTimestampClick) {
      const seconds = timestampToSeconds(timestamp);
      onTimestampClick(seconds);
    }
  };

  // Download transcript as TXT file
  const handleDownloadTranscript = () => {
    let content = "";

    lines.forEach((line, index) => {
      const match = line.match(/^(\d+:\d{2})\s+([\s\S]+)/);
      const timestamp = match ? match[1] : "";
      const text = match ? match[2].trim() : line;

      // Add original text with timestamp
      if (timestamp) {
        content += `${timestamp} ${text}\n`;
      } else {
        content += `${text}\n`;
      }

      // Add translation if available
      const translation = segmentTranslations.get(index);
      if (translation) {
        content += `번역: ${translation}\n`;
      }

      content += "\n"; // Add blank line between segments
    });

    // Create blob and download
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `transcript_${videoId}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    toast.success('스크립트가 다운로드되었습니다');
  };

  // Translate single segment
  const handleTranslateSegment = async (index: number, text: string) => {
    // Skip if already translating
    if (translatingSegments.has(index)) return;
    
    // If already translated, just show it
    if (segmentTranslations.has(index)) {
      return;
    }

    setTranslatingSegments(prev => new Set(prev).add(index));
    
    try {
      const result = await translateSegment({
        video_id: videoId,
        text: text,
        ai_provider: aiProvider,
        model: model,
      });
      
      setSegmentTranslations(prev => new Map(prev).set(index, result.translation));
      // Translation is displayed immediately, but don't toggle the global switch
      toast.success('번역이 완료되었습니다');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '번역 중 오류가 발생했습니다');
    } finally {
      setTranslatingSegments(prev => {
        const newSet = new Set(prev);
        newSet.delete(index);
        return newSet;
      });
    }
  };

  // Translate full transcript (batch)
  const handleTranslateFull = async () => {
    // If already translated, toggle visibility
    if (segmentTranslations.size === lines.length) {
      setShowTranslation(!showTranslation);
      return;
    }

    // If translations exist but incomplete, just toggle
    if (segmentTranslations.size > 0) {
      setShowTranslation(!showTranslation);
      return;
    }

    // Start translation
    setIsTranslatingFull(true);
    try {
      // Extract text without timestamps
      const segments = lines.map(line => {
        const match = line.match(/^(\d+:\d{2})\s+([\s\S]+)/);
        return match ? match[2].trim() : line;
      });

      const result = await translateBatch({
        video_id: videoId,
        segments: segments,
        ai_provider: aiProvider,
        model: model,
      });

      // Map translations to segment indices
      const newTranslations = new Map<number, string>();
      result.translations.forEach((translation, index) => {
        newTranslations.set(index, translation);
      });

      setSegmentTranslations(newTranslations);
      setShowTranslation(true);
      toast.success('전체 번역이 완료되었습니다');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '전체 번역 중 오류가 발생했습니다');
    } finally {
      setIsTranslatingFull(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-muted-foreground" />
          <Popover>
            <PopoverTrigger asChild>
              <button className="font-medium text-sm hover:text-primary transition-colors cursor-pointer">
                스크립트
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-40 p-2" align="start">
              <Button
                variant="ghost"
                className="w-full justify-start gap-2 hover:bg-accent"
                onClick={handleDownloadTranscript}
              >
                <Download className="h-4 w-4" />
                다운로드
              </Button>
            </PopoverContent>
          </Popover>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={showTranslation && segmentTranslations.size > 0 ? "default" : "outline"}
            size="sm"
            onClick={handleTranslateFull}
            disabled={isTranslatingFull}
            className={`gap-1.5 h-8 text-xs transition-all ${
              showTranslation && segmentTranslations.size > 0
                ? 'bg-primary text-primary-foreground hover:bg-primary/90'
                : ''
            }`}
          >
            {isTranslatingFull ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                번역 중...
              </>
            ) : (
              <>
                <Languages className="h-3.5 w-3.5" />
                {segmentTranslations.size > 0
                  ? (showTranslation ? '숨기기' : '보기')
                  : '전체 번역'}
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Transcript Content */}
      <ScrollArea className="flex-1 custom-scrollbar">
        <div className="p-4 space-y-4">
          {lines.map((line, index) => {
            // Match timestamp format: "0:05 text" or "1:23 text"
            // Use multiline matching to capture all text after timestamp
            const match = line.match(/^(\d+:\d{2})\s+([\s\S]+)/);
            const timestamp = match ? match[1] : null;
            const text = match ? match[2].trim() : line;
            const hasTranslation = segmentTranslations.has(index);
            const isTranslating = translatingSegments.has(index);

            return (
              <div
                key={index}
                className="group hover:bg-accent/50 rounded-lg p-3 -mx-2 transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    {timestamp && (
                      <div
                        className="text-xs text-muted-foreground font-mono mb-1.5 cursor-pointer hover:text-primary transition-colors"
                        onClick={() => handleTimestampClick(timestamp)}
                        role="button"
                        tabIndex={0}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" || e.key === " ") {
                            e.preventDefault();
                            handleTimestampClick(timestamp);
                          }
                        }}
                      >
                        {timestamp}
                      </div>
                    )}
                    <p className="text-sm leading-relaxed text-foreground whitespace-pre-wrap">
                      {text}
                    </p>
                    {hasTranslation && showTranslation && (
                      <p className="text-sm leading-relaxed text-primary mt-2 whitespace-pre-wrap border-l-2 border-primary pl-3">
                        {segmentTranslations.get(index)}
                      </p>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={() => handleTranslateSegment(index, text)}
                    disabled={isTranslating || isTranslatingFull}
                  >
                    <Languages className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      </ScrollArea>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-border flex items-center justify-between">
        <span className="text-xs text-muted-foreground">
          소스 리스트 {lines.length}개
        </span>
      </div>
    </div>
  );
};

export default TranscriptPanel;
