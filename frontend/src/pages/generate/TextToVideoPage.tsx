import { useState, useCallback } from "react"
import { useMutation } from "@tanstack/react-query"
import { Loader2, Video, Shuffle } from "lucide-react"
import { generationApi, tasksApi } from "@/api"
import { useTask } from "@/hooks/useTask"
import { useQuota } from "@/hooks/useQuota"
import { toast } from "@/hooks/useToast"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Slider } from "@/components/ui/slider"
import { Input } from "@/components/ui/input"
import { PromptInput } from "@/components/generation/PromptInput"
import { VideoResult } from "@/components/generation/VideoResult"
import type { TaskStatus } from "@/types"

export function TextToVideoPage() {
  // Form state
  const [prompt, setPrompt] = useState("")
  const [negativePrompt, setNegativePrompt] = useState("")
  const [numFrames, setNumFrames] = useState(49)
  const [numInferenceSteps, setNumInferenceSteps] = useState(50)
  const [guidanceScale, setGuidanceScale] = useState(6.0)
  const [seed, setSeed] = useState(-1)

  // Task state
  const [taskId, setTaskId] = useState<string | null>(null)
  const [videoUrl, setVideoUrl] = useState<string | null>(null)
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null)
  const [taskError, setTaskError] = useState<string | null>(null)

  const { refetch: refetchQuota, remainingToday } = useQuota()

  // Task polling
  const { task } = useTask(taskId, {
    onComplete: async (completedTask) => {
      setTaskStatus("completed")
      try {
        const result = await tasksApi.getTaskResult(completedTask.task_id)
        if (result instanceof Blob) {
          const url = URL.createObjectURL(result)
          setVideoUrl(url)
        }
        refetchQuota()
        toast({
          title: "生成完成",
          description: "视频已生成成功",
          variant: "success" as const,
        })
      } catch {
        toast({
          title: "获取结果失败",
          description: "无法获取生成的视频",
          variant: "destructive",
        })
      }
    },
    onError: (error) => {
      setTaskStatus("failed")
      setTaskError(error)
      toast({
        title: "生成失败",
        description: error,
        variant: "destructive",
      })
    },
  })

  // Update task status from polling
  if (task && task.status !== taskStatus) {
    setTaskStatus(task.status)
    if (task.error) {
      setTaskError(task.error)
    }
  }

  // Submit mutation
  const submitMutation = useMutation({
    mutationFn: async () => {
      return await generationApi.textToVideo({
        prompt,
        negative_prompt: negativePrompt || undefined,
        num_frames: numFrames,
        num_inference_steps: numInferenceSteps,
        guidance_scale: guidanceScale,
        seed: seed === -1 ? undefined : seed,
      })
    },
    onSuccess: (data) => {
      setTaskId(data.task_id)
      setTaskStatus("pending")
      setVideoUrl(null)
      setTaskError(null)
      toast({
        title: "任务已提交",
        description: `排队中: ${data.queue_info.pending_tasks} 个任务`,
      })
    },
    onError: (error: Error) => {
      toast({
        title: "提交失败",
        description: error.message,
        variant: "destructive",
      })
    },
  })

  const handleSubmit = useCallback(() => {
    if (!prompt.trim()) {
      toast({
        title: "请输入提示词",
        variant: "destructive",
      })
      return
    }
    // 假设视频生成消耗 5 次配额
    const COST = 5
    if (remainingToday < COST) {
      toast({
        title: "配额不足",
        description: `今日剩余配额: ${remainingToday}，视频生成需要: ${COST}`,
        variant: "destructive",
      })
      return
    }
    submitMutation.mutate()
  }, [prompt, remainingToday, submitMutation])

  const handleRetry = useCallback(() => {
    submitMutation.mutate()
  }, [submitMutation])

  const isGenerating = submitMutation.isPending || taskStatus === "pending" || taskStatus === "running"

  return (
    <div className="space-y-6 animate-in">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">文生视频</h1>
        <p className="text-muted-foreground">
          输入文字描述，AI 为您生成精彩视频
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left Panel - Input Form */}
        <div className="space-y-6">
          {/* Prompt */}
          <Card>
            <CardHeader>
              <CardTitle>提示词</CardTitle>
              <CardDescription>描述您想要生成的视频内容</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <PromptInput
                value={prompt}
                onChange={setPrompt}
                disabled={isGenerating}
              />
              
              {/* Negative Prompt */}
              <div className="space-y-2">
                <Label>负面提示词（可选）</Label>
                <Textarea
                  value={negativePrompt}
                  onChange={(e) => setNegativePrompt(e.target.value)}
                  placeholder="描述您不想在视频中出现的内容..."
                  className="min-h-[80px] resize-none"
                  disabled={isGenerating}
                />
              </div>
            </CardContent>
          </Card>

          {/* Parameters */}
          <Card>
            <CardHeader>
              <CardTitle>生成参数</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>生成帧数 ({numFrames})</Label>
                  <span className="text-xs text-muted-foreground">约 {Math.round(numFrames / 8)} 秒</span>
                </div>
                <Slider
                  value={[numFrames]}
                  onValueChange={(vals) => setNumFrames(vals[0])}
                  min={16}
                  max={81}
                  step={1} // CogVideoX prefers specific frame counts, usually 49
                  disabled={isGenerating}
                />
                <p className="text-xs text-muted-foreground">推荐 49 帧 (CogVideoX 标准)</p>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>推理步数 ({numInferenceSteps})</Label>
                </div>
                <Slider
                  value={[numInferenceSteps]}
                  onValueChange={(vals) => setNumInferenceSteps(vals[0])}
                  min={20}
                  max={100}
                  step={1}
                  disabled={isGenerating}
                />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>指导尺度 (Guidance Scale: {guidanceScale})</Label>
                </div>
                <Slider
                  value={[guidanceScale]}
                  onValueChange={(vals) => setGuidanceScale(vals[0])}
                  min={1}
                  max={20}
                  step={0.1}
                  disabled={isGenerating}
                />
              </div>

              {/* Seed */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label>随机种子</Label>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={() => setSeed(Math.floor(Math.random() * 2147483647))}
                    disabled={isGenerating}
                    title="随机生成"
                  >
                    <Shuffle className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex gap-2">
                  <Input
                    type="number"
                    value={seed}
                    onChange={(e) => setSeed(parseInt(e.target.value) || -1)}
                    min={-1}
                    max={2147483647}
                    disabled={isGenerating}
                    className="flex-1"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSeed(-1)}
                    disabled={isGenerating}
                  >
                    随机
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Submit Button */}
          <Button
            size="lg"
            className="w-full"
            onClick={handleSubmit}
            disabled={isGenerating || !prompt.trim()}
          >
            {isGenerating ? (
              <>
                <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                生成中...
              </>
            ) : (
              <>
                <Video className="h-5 w-5 mr-2" />
                生成视频（消耗 5 次配额）
              </>
            )}
          </Button>
        </div>

        {/* Right Panel - Result */}
        <div className="lg:sticky lg:top-20">
          <VideoResult
            taskId={taskId}
            status={taskStatus}
            videoUrl={videoUrl}
            prompt={prompt}
            error={taskError}
            onRetry={handleRetry}
          />
        </div>
      </div>
    </div>
  )
}