import { History, Play, Trash2 } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";

interface HistoryDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const HistoryDrawer = ({ open, onOpenChange }: HistoryDrawerProps) => {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="left" className="w-80 p-0">
        <SheetHeader className="p-4 border-b border-border">
          <SheetTitle className="flex items-center gap-2">
            <History className="h-5 w-5" />
            나의 검색 기록
          </SheetTitle>
        </SheetHeader>

        <div className="flex items-center justify-center h-[calc(100vh-80px)]">
          <div className="text-center p-8">
            <History className="h-12 w-12 text-muted-foreground/50 mx-auto mb-4" />
            <p className="text-sm text-muted-foreground mb-2">검색 기록이 없습니다</p>
            <p className="text-xs text-muted-foreground/70">영상을 요약하면 여기에 기록이 표시됩니다</p>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
};

export default HistoryDrawer;
