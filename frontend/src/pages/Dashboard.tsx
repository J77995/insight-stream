import { useSearchParams, useNavigate, useLocation } from "react-router-dom";
import { ArrowLeft, ExternalLink, Copy, Check, Menu, Settings } from "lucide-react";
import { useState, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import VideoPlayer, { VideoPlayerHandle } from "@/components/dashboard/VideoPlayer";
import TranscriptPanel from "@/components/dashboard/TranscriptPanel";
import SummaryPanel from "@/components/dashboard/SummaryPanel";
import ChatPanel from "@/components/dashboard/ChatPanel";
import HistoryDrawer from "@/components/dashboard/HistoryDrawer";
import type { VideoData } from "@/types/prompts";
import { customSummarize } from "@/services/api";
import { toast } from "sonner";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

const Dashboard = () => {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [copied, setCopied] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const videoPlayerRef = useRef<VideoPlayerHandle>(null);

  // Get data from navigation state and manage as state for updates
  const initialData = location.state?.videoData as VideoData | undefined;
  const [videoData, setVideoData] = useState<VideoData | undefined>(initialData);
  const videoId = searchParams.get("v") || videoData?.video_id || "";

  // Chat history management: Map<video_id, Message[]>
  const [chatHistories, setChatHistories] = useState<Map<string, Message[]>>(new Map());

  // Get initial messages for current video
  const initialMessages = videoData?.video_id ? chatHistories.get(videoData.video_id) : undefined;

  // Handle chat messages change
  const handleChatMessagesChange = useCallback((videoId: string, messages: Message[]) => {
    setChatHistories((prev) => {
      const newMap = new Map(prev);
      newMap.set(videoId, messages);
      return newMap;
    });
  }, []);

  // Handle missing data - redirect to home
  if (!videoData) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <h2 className="text-xl font-semibold mb-2">데이터를 불러올 수 없습니다</h2>
          <p className="text-muted-foreground mb-4">
            홈 페이지에서 YouTube URL을 입력하여 다시 시작해주세요
          </p>
          <Button onClick={() => navigate('/')}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            홈으로 돌아가기
          </Button>
        </div>
      </div>
    );
  }

  const handleCopy = async () => {
    if (!videoData) return;
    await navigator.clipboard.writeText(videoData.summary_overview);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleResummarize = async (newPrompts: { overview: string; detail: string }, signal?: AbortSignal) => {
    if (!videoData) return;

    try {
      const updated = await customSummarize({
        video_id: videoData.video_id,
        // transcript removed - backend will use cached version
        custom_overview_prompt: newPrompts.overview,
        custom_detail_prompt: newPrompts.detail,
        ai_provider: videoData.ai_provider || 'gemini',
        model: videoData.model,
        signal
      });

      setVideoData(updated);
      toast.success('재요약이 완료되었습니다');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '재요약 중 오류가 발생했습니다');
      throw error;
    }
  };

  const handleTimestampClick = (seconds: number) => {
    if (videoPlayerRef.current) {
      videoPlayerRef.current.seekTo(seconds);
      toast.success(`${Math.floor(seconds / 60)}:${(seconds % 60).toString().padStart(2, '0')}로 이동`);
    }
  };

  return (
    <div className="min-h-screen bg-surface">
      {/* History Drawer */}
      <HistoryDrawer open={drawerOpen} onOpenChange={setDrawerOpen} />

      {/* Header */}
      <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-sm border-b border-border">
        <div className="flex items-center justify-between px-4 md:px-6 h-14">
          <div className="flex items-center gap-3">
            {/* Hamburger Menu */}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setDrawerOpen(true)}
              className="h-9 w-9"
            >
              <Menu className="h-5 w-5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate("/")}
              className="h-9 w-9"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-muted-foreground">내 지식</span>
              <span className="text-muted-foreground">/</span>
              <span className="font-medium text-foreground truncate max-w-[200px] md:max-w-none">
                {videoData.title}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" className="gap-2" onClick={handleCopy}>
              {copied ? (
                <Check className="h-4 w-4" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
              <span className="hidden md:inline">복사</span>
            </Button>
            <Button variant="ghost" size="sm" className="gap-2">
              <ExternalLink className="h-4 w-4" />
              <span className="hidden md:inline">원본 보기</span>
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="gap-2"
              onClick={() => navigate('/admin')}
            >
              <Settings className="h-4 w-4" />
              <span className="hidden md:inline">상세 설정</span>
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content - 3 Column Layout */}
      <main className="grid grid-cols-1 md:grid-cols-[300px_1fr_320px] h-[calc(100vh-56px)]">
        {/* Column 1 - Video + Transcript */}
        <div className="border-b md:border-b-0 md:border-r border-border bg-background flex flex-col h-[50vh] md:h-full overflow-hidden">
          <VideoPlayer ref={videoPlayerRef} videoId={videoId} />
          <TranscriptPanel 
            transcript={videoData.full_transcript}
            videoId={videoData.video_id}
            aiProvider={videoData.ai_provider || 'gemini'}
            model={videoData.model}
            onTimestampClick={handleTimestampClick}
          />
        </div>

        {/* Column 2 - Summary */}
        <div className="bg-surface-elevated border-b md:border-b-0 md:border-r border-border h-[50vh] md:h-full overflow-hidden">
          <SummaryPanel
            title={videoData.title}
            overview={videoData.summary_overview}
            detail={videoData.summary_detail}
            category={videoData.category}
            promptsUsed={videoData.prompts_used}
            onResummarize={handleResummarize}
          />
        </div>

        {/* Column 3 - Chat */}
        <div className="bg-background h-[50vh] md:h-full overflow-hidden">
          <ChatPanel
            videoId={videoData.video_id}
            aiProvider={videoData.ai_provider || 'gemini'}
            model={videoData.model}
            initialMessages={initialMessages}
          />
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
