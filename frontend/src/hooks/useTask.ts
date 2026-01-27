import { useState, useCallback, useEffect } from 'react'
import { tasksApi } from '@/api'
import type { Task, TaskStatus } from '@/types'

interface UseTaskOptions {
  onComplete?: (task: Task) => void
  onError?: (error: string) => void
  pollingInterval?: number
}

export function useTask(taskId: string | null, options: UseTaskOptions = {}) {
  const { onComplete, onError, pollingInterval = 2000 } = options
  const [task, setTask] = useState<Task | null>(null)
  const [isPolling, setIsPolling] = useState(false)

  const fetchStatus = useCallback(async () => {
    if (!taskId) return null
    
    try {
      const status = await tasksApi.getTaskStatus(taskId)
      setTask(status)
      return status
    } catch (err) {
      const message = err instanceof Error ? err.message : '获取任务状态失败'
      onError?.(message)
      return null
    }
  }, [taskId, onError])

  // 轮询任务状态
  useEffect(() => {
    if (!taskId) {
      setTask(null)
      return
    }

    let intervalId: number | null = null
    
    const poll = async () => {
      const status = await fetchStatus()
      if (!status) return
      
      const completedStatuses: TaskStatus[] = ['completed', 'failed', 'cancelled']
      if (completedStatuses.includes(status.status)) {
        setIsPolling(false)
        if (intervalId) {
          clearInterval(intervalId)
        }
        
        if (status.status === 'completed') {
          onComplete?.(status)
        } else if (status.status === 'failed') {
          onError?.(status.error || '任务执行失败')
        }
      }
    }

    setIsPolling(true)
    poll() // 立即执行一次
    intervalId = window.setInterval(poll, pollingInterval)

    return () => {
      if (intervalId) {
        clearInterval(intervalId)
      }
    }
  }, [taskId, fetchStatus, onComplete, onError, pollingInterval])

  const cancel = useCallback(async () => {
    if (!taskId) return false
    
    try {
      await tasksApi.cancelTask(taskId)
      await fetchStatus()
      return true
    } catch {
      return false
    }
  }, [taskId, fetchStatus])

  return {
    task,
    isPolling,
    isPending: task?.status === 'pending',
    isRunning: task?.status === 'running',
    isCompleted: task?.status === 'completed',
    isFailed: task?.status === 'failed',
    cancel,
    refetch: fetchStatus,
  }
}
