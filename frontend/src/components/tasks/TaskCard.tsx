import { Link } from "react-router-dom"
import { ImagePlus, Pencil, Layers, Clock, ArrowRight, Trash2, RotateCcw, Video, Film } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { TaskStatusBadge } from "./TaskStatusBadge"
import { formatDate, formatDuration, truncateText } from "@/utils/format"
import type { TaskHistory, TaskType } from "@/types"

interface TaskCardProps {
  task: TaskHistory
  onDelete?: (taskId: string) => void
  onRestore?: (taskId: string) => void
  isRecycleBin?: boolean
}

const taskTypeConfig: Record<TaskType, { label: string; icon: React.ElementType; color: string }> = {
  text_to_image: { label: "文生图", icon: ImagePlus, color: "text-blue-500" },
  image_edit: { label: "图像编辑", icon: Pencil, color: "text-green-500" },
  batch_edit: { label: "批量编辑", icon: Layers, color: "text-purple-500" },
  text_to_video: { label: "文生视频", icon: Video, color: "text-orange-500" },
  image_to_video: { label: "图生视频", icon: Film, color: "text-pink-500" },
}

export function TaskCard({ task, onDelete, onRestore, isRecycleBin = false }: TaskCardProps) {
  const config = taskTypeConfig[task.task_type] || taskTypeConfig.text_to_image
  const Icon = config.icon

  return (
    <Card className="hover:shadow-md transition-shadow group relative overflow-hidden">
      <Link to={isRecycleBin ? "#" : `/tasks/${task.task_id}`} className={isRecycleBin ? "cursor-default" : ""}>
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            {/* Icon */}
            <div className={`p-2 rounded-lg bg-muted ${config.color}`}>
              <Icon className="h-5 w-5" />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="text-sm font-medium">{config.label}</span>
                <TaskStatusBadge status={task.status} />
              </div>

              <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
                {truncateText(task.prompt, 80)}
              </p>

              <div className="flex items-center gap-4 text-xs text-muted-foreground">
                <span>{formatDate(task.created_at)}</span>
                {task.execution_time && (
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatDuration(task.execution_time)}
                  </span>
                )}
              </div>
            </div>

            {/* Arrow (Hidden in Recycle Bin) */}
            {!isRecycleBin && (
              <ArrowRight className="h-5 w-5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
            )}
          </div>
        </CardContent>
      </Link>

      {/* Actions */}
      <div className="absolute bottom-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        {onRestore && (
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 hover:bg-green-100 hover:text-green-600"
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              onRestore(task.task_id)
            }}
            title="恢复"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </Button>
        )}
        {onDelete && (
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 hover:bg-red-100 hover:text-red-600"
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              onDelete(task.task_id)
            }}
            title={isRecycleBin ? "永久删除" : "删除"}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        )}
      </div>
    </Card>
  )
}
