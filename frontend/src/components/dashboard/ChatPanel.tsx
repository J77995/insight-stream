import { useState, useEffect } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { MessageCircle, Send, User, Bot } from "lucide-react";
import { chatWithVideo } from "@/services/api";
import { toast } from "sonner";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

interface ChatPanelProps {
  videoId: string;
  aiProvider: string;
  model?: string;
  initialMessages?: Message[];
  // onMessagesChange removed - no longer needed
}

const ChatPanel = ({ videoId, aiProvider, model, initialMessages }: ChatPanelProps) => {
  const [messages, setMessages] = useState<Message[]>(
    initialMessages || [
      {
        id: "1",
        role: "assistant",
        content: "안녕하세요! 영상 내용에 대해 궁금한 점이 있으시면 질문해 주세요. 스크립트를 기반으로 답변해 드리겠습니다.",
      },
    ]
  );
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<
    { role: string; content: string }[]
  >([]);

  // Update messages when videoId changes
  useEffect(() => {
    if (initialMessages) {
      setMessages(initialMessages);
      // Rebuild conversation history from initial messages (excluding first assistant message)
      const history = initialMessages
        .slice(1)
        .map((msg) => ({
          role: msg.role,
          content: msg.content,
        }));
      setConversationHistory(history);
    } else {
      // Reset to default message for new video
      const defaultMessages = [
        {
          id: "1",
          role: "assistant" as const,
          content: "안녕하세요! 영상 내용에 대해 궁금한 점이 있으시면 질문해 주세요. 스크립트를 기반으로 답변해 드리겠습니다.",
        },
      ];
      setMessages(defaultMessages);
      setConversationHistory([]);
    }
  }, [videoId, initialMessages]);

  // REMOVED: onMessagesChange useEffect to prevent infinite loop
  // Parent component no longer needs to track messages in real-time

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);

    // Add to conversation history
    const newHistory = [...conversationHistory, { role: "user", content: input }];
    setConversationHistory(newHistory);

    setInput("");
    setIsLoading(true);

    try {
      const response = await chatWithVideo({
        video_id: videoId,
        message: input,
        conversation_history: conversationHistory,
        ai_provider: aiProvider,
        model: model,
      });

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.reply,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setConversationHistory([...newHistory, { role: "assistant", content: response.reply }]);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "채팅 중 오류가 발생했습니다");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
        <MessageCircle className="h-4 w-4 text-muted-foreground" />
        <span className="font-medium text-sm">Q&A 채팅</span>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 custom-scrollbar">
        <div className="p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex items-start gap-3 ${
                message.role === "user" ? "flex-row-reverse" : ""
              }`}
            >
              <div
                className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                  message.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary text-secondary-foreground"
                }`}
              >
                {message.role === "user" ? (
                  <User className="h-4 w-4" />
                ) : (
                  <Bot className="h-4 w-4" />
                )}
              </div>
              <div
                className={`max-w-[80%] rounded-xl px-4 py-2.5 ${
                  message.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary text-secondary-foreground"
                }`}
              >
                <p className="text-sm leading-relaxed">{message.content}</p>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-secondary text-secondary-foreground">
                <Bot className="h-4 w-4" />
              </div>
              <div className="bg-secondary rounded-xl px-4 py-2.5">
                <div className="flex items-center gap-1">
                  <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input */}
      <div className="p-4 border-t border-border">
        <form onSubmit={handleSubmit} className="flex items-center gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="영상에 대해 질문하세요..."
            className="flex-1 h-10 bg-secondary border-0 focus-visible:ring-1 focus-visible:ring-primary"
            disabled={isLoading}
          />
          <Button
            type="submit"
            size="icon"
            disabled={!input.trim() || isLoading}
            className="h-10 w-10 rounded-lg"
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  );
};

export default ChatPanel;
