/**
 * ProcessDialog Component
 * 
 * Displays the progress of video processing with step-by-step visualization
 */

import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { ProcessState, STEP_INFO, ProcessStep } from "@/types/progress";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ProcessDialogProps {
  open: boolean;
  state: ProcessState;
  onClose?: () => void;
  onRetry?: () => void;
  onCancel?: () => void;
}

export const ProcessDialog = ({ open, state, onClose, onRetry, onCancel }: ProcessDialogProps) => {
  const currentStepInfo = STEP_INFO[state.currentStep];
  const hasError = !!state.error;
  const isProcessing = !hasError && state.currentStep !== 'complete';

  // 각 단계의 상태 계산
  const steps = Object.keys(STEP_INFO) as ProcessStep[];
  const currentIndex = steps.indexOf(state.currentStep);

  return (
    <DialogPrimitive.Root open={open} onOpenChange={hasError ? onClose : undefined}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/80 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <DialogPrimitive.Content
          className={cn(
            "fixed left-[50%] top-[50%] z-50 grid w-full max-w-md translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:rounded-lg"
          )}
        >
          {/* Header */}
          <div className="flex flex-col space-y-1.5 text-center sm:text-left">
            <DialogPrimitive.Title className="text-lg font-semibold leading-none tracking-tight flex items-center gap-2">
              {hasError ? (
                <>
                  <AlertCircle className="h-5 w-5 text-destructive" />
                  <span>오류 발생</span>
                </>
              ) : state.currentStep === 'complete' ? (
                <>
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                  <span>완료</span>
                </>
              ) : (
                <>
                  <Loader2 className="h-5 w-5 animate-spin text-primary" />
                  <span>영상 처리 중</span>
                </>
              )}
            </DialogPrimitive.Title>
            <DialogPrimitive.Description className="text-sm text-muted-foreground">
              {hasError ? state.error!.message : currentStepInfo.description}
            </DialogPrimitive.Description>
          </div>

          {/* 에러 상세 정보 */}
          {hasError && state.error && (
            <Alert variant="destructive">
              <AlertDescription>
                <div className="space-y-2">
                  <p className="font-medium">발생 단계: {STEP_INFO[state.error.step].label}</p>
                  {state.error.suggestion && (
                    <p className="text-sm">{state.error.suggestion}</p>
                  )}
                </div>
              </AlertDescription>
            </Alert>
          )}

          {/* 진행 단계 표시 */}
          {!hasError && (
            <div className="space-y-4">
              {/* 단계별 상태 */}
              <div className="space-y-2">
                {steps.slice(0, -1).map((step, index) => {
                  const stepInfo = STEP_INFO[step];
                  const isComplete = index < currentIndex;
                  const isCurrent = index === currentIndex;
                  const isPending = index > currentIndex;

                  return (
                    <div
                      key={step}
                      className={cn(
                        "flex items-center gap-3 p-3 rounded-lg transition-colors",
                        isCurrent && "bg-primary/10"
                      )}
                    >
                      {/* 상태 아이콘 */}
                      <div className="flex-shrink-0">
                        {isComplete ? (
                          <CheckCircle2 className="h-5 w-5 text-green-500" />
                        ) : isCurrent ? (
                          <Loader2 className="h-5 w-5 animate-spin text-primary" />
                        ) : (
                          <div className="h-5 w-5 rounded-full border-2 border-muted" />
                        )}
                      </div>

                      {/* 단계 정보 */}
                      <div className="flex-1 min-w-0">
                        <p className={cn(
                          "text-sm font-medium",
                          isCurrent && "text-foreground",
                          isComplete && "text-muted-foreground",
                          isPending && "text-muted-foreground/50"
                        )}>
                          {stepInfo.label}
                        </p>
                        {isCurrent && (
                          <p className="text-xs text-muted-foreground mt-0.5">
                            {stepInfo.description}
                          </p>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 에러 시 액션 버튼 */}
          {hasError && (
            <div className="flex gap-2">
              <Button variant="outline" onClick={onClose} className="flex-1">
                취소
              </Button>
              {onRetry && (
                <Button onClick={onRetry} className="flex-1">
                  다시 시도
                </Button>
              )}
            </div>
          )}
          
          {/* 처리 중 취소 버튼 */}
          {isProcessing && onCancel && (
            <div className="flex justify-center">
              <Button variant="outline" onClick={onCancel} className="w-full">
                중단
              </Button>
            </div>
          )}
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
};
