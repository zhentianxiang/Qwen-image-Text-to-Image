import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Trash2, Loader2, AlertTriangle } from "lucide-react"
import { tasksApi } from "@/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { TaskCard } from "@/components/tasks/TaskCard"
import { useToast } from "@/hooks/useToast"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

export function RecycleBinPage() {
  const [page, setPage] = useState(1)
  const [taskToDelete, setTaskToDelete] = useState<string | null>(null)
  const pageSize = 12
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['my-recycle-bin', page],
    queryFn: () => tasksApi.getRecycleBin({
      page,
      page_size: pageSize,
    }),
  })

  const restoreMutation = useMutation({
    mutationFn: tasksApi.restoreTask,
    onSuccess: () => {
      toast({
        title: "已恢复",
        description: "任务已恢复到历史记录",
      })
      queryClient.invalidateQueries({ queryKey: ['my-recycle-bin'] })
      queryClient.invalidateQueries({ queryKey: ['my-history'] })
    },
    onError: (error: any) => {
      toast({
        title: "恢复失败",
        description: error.message || "请稍后重试",
        variant: "destructive",
      })
    },
  })

  const permanentDeleteMutation = useMutation({
    mutationFn: tasksApi.permanentDeleteTask,
    onSuccess: () => {
      toast({
        title: "已永久删除",
        description: "任务已彻底删除",
      })
      queryClient.invalidateQueries({ queryKey: ['my-recycle-bin'] })
      setTaskToDelete(null)
    },
    onError: (error: any) => {
      toast({
        title: "删除失败",
        description: error.message || "请稍后重试",
        variant: "destructive",
      })
    },
  })

  const handleRestore = (taskId: string) => {
    restoreMutation.mutate(taskId)
  }

  const handleDeleteClick = (taskId: string) => {
    setTaskToDelete(taskId)
  }

  const confirmDelete = () => {
    if (taskToDelete) {
      permanentDeleteMutation.mutate(taskToDelete)
    }
  }

  return (
    <div className="space-y-6 animate-in">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">回收站</h1>
        <p className="text-muted-foreground">管理已删除的任务，可以恢复或永久删除</p>
      </div>

      {/* Task List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : data && data.items.length > 0 ? (
        <>
          {data && (
             <div className="text-sm text-muted-foreground">
               共 {data.total} 条已删除记录
             </div>
          )}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {data.items.map((task) => (
              <TaskCard 
                key={task.task_id} 
                task={task} 
                isRecycleBin={true}
                onRestore={handleRestore}
                onDelete={handleDeleteClick}
              />
            ))}
          </div>

          {/* Pagination */}
          {data.total_pages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                上一页
              </Button>
              <span className="text-sm text-muted-foreground">
                {page} / {data.total_pages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(p => Math.min(data.total_pages, p + 1))}
                disabled={page === data.total_pages}
              >
                下一页
              </Button>
            </div>
          )}
        </>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Trash2 className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">回收站为空</p>
          </CardContent>
        </Card>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!taskToDelete} onOpenChange={(open) => !open && setTaskToDelete(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-5 w-5" />
              永久删除确认
            </DialogTitle>
            <DialogDescription>
              此操作将无法撤销。任务记录和相关文件将被永久删除。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setTaskToDelete(null)}>
              取消
            </Button>
            <Button variant="destructive" onClick={confirmDelete} disabled={permanentDeleteMutation.isPending}>
              {permanentDeleteMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              确认删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
