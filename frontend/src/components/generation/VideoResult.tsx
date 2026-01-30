import { useState } from "react"
import { Download, Copy, Check, Loader2, RefreshCw, AlertCircle, Play } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/utils/cn"
import type { TaskStatus } from "@/types"

interface VideoResultProps {
  taskId: string | null
  status: TaskStatus | null
  videoUrl: string | null
  prompt: string
  error: string | null
  onRetry?: () => void
  className?: string
}

export function VideoResult({
  taskId,
  status,
  videoUrl,
  prompt,
  error,
  onRetry,
  className,
}: VideoResultProps) {
  const [copied, setCopied] = useState(false)

  const copyPrompt = async () => {
    await navigator.clipboard.writeText(prompt)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const downloadResult = () => {
    if (!videoUrl) return
    const link = document.createElement("a")
    link.href = videoUrl
    link.download = `dream-ai-video-${taskId?.slice(0, 8)}.mp4`
    link.click()
  }

  const isLoading = status === "pending" || status === "running"
  const isComplete = status === "completed"
  const isFailed = status === "failed"

  // If no task yet, show placeholder
  if (!taskId) {
    return (
      <Card className={cn("border-dashed", className)}>
        <CardContent className="flex flex-col items-center justify-center min-h-[300px] text-center p-8">
          <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
            <Play className="h-8 w-8 text-muted-foreground ml-1" />
          </div>
          <p className="text-muted-foreground">
            填写提示词后点击生成按钮
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            生成视频将在此显示
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={className}>
      <CardContent className="p-4">
        {/* Status Badge */}
        <div className="flex items-center justify-between mb-4">
          <Badge
            variant={
              isComplete ? "success" :
              isFailed ? "destructive" :
              "secondary"
            }
          >
            {isLoading && <Loader2 className="h-3 w-3 mr-1 animate-spin" />}
            {status === "pending" && "等待中"}
            {status === "running" && "生成中"}
            {status === "completed" && "已完成"}
            {status === "failed" && "失败"}
            {status === "cancelled" && "已取消"}
          </Badge>
          <span className="text-xs text-muted-foreground">
            ID: {taskId.slice(0, 8)}
          </span>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex flex-col items-center justify-center min-h-[300px] gap-4">
            <div className="relative">
              <div className="w-20 h-20 rounded-full border-4 border-primary/20 animate-pulse" />
              <Loader2 className="absolute inset-0 m-auto h-10 w-10 animate-spin text-primary" />
            </div>
            <div className="text-center">
              <p className="font-medium">
                {status === "pending" ? "排队中..." : "正在生成..."}
              </p>
              <p className="text-sm text-muted-foreground">
                视频生成通常需要 1-2 分钟，请耐心等待
              </p>
            </div>
            {status === "running" && (
              <Progress value={undefined} className="w-48 h-2" />
            )}
          </div>
        )}

        {/* Error State */}
        {isFailed && (
          <div className="flex flex-col items-center justify-center min-h-[300px] gap-4">
            <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center">
              <AlertCircle className="h-8 w-8 text-destructive" />
            </div>
            <div className="text-center">
              <p className="font-medium text-destructive">生成失败</p>
              <p className="text-sm text-muted-foreground mt-1">
                {error || "未知错误"}
              </p>
            </div>
            {onRetry && (
              <Button variant="outline" onClick={onRetry}>
                <RefreshCw className="h-4 w-4 mr-2" />
                重试
              </Button>
            )}
          </div>
        )}

        {/* Success State */}
        {isComplete && videoUrl && (
          <div className="space-y-4">
            {/* Video Player */}
            <div className="relative rounded-lg overflow-hidden bg-black aspect-video">
              <video 
                src={videoUrl} 
                controls 
                autoPlay 
                loop 
                className="w-full h-full object-contain"
              />
            </div>

            {/* Actions */}
            <div className="flex gap-2">
              <Button onClick={downloadResult} className="flex-1">
                <Download className="h-4 w-4 mr-2" />
                下载视频
              </Button>
              <Button variant="outline" onClick={copyPrompt}>
                {copied ? (
                  <Check className="h-4 w-4 mr-2" />
                ) : (
                  <Copy className="h-4 w-4 mr-2" />
                )}
                复制提示词
              </Button>
              {onRetry && (
                <Button variant="outline" onClick={onRetry}>
                  <RefreshCw className="h-4 w-4" />
                </Button>
              )}
            </div>

            {/* Prompt Display */}
            <div className="p-3 rounded-lg bg-muted">
              <p className="text-xs text-muted-foreground mb-1">提示词</p>
              <p className="text-sm">{prompt}</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
