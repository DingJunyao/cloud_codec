/** 任务 Store */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import tasksApi from '@/api/tasks'
import type { Task, TaskCreate } from '@/api/tasks'

export const useTasksStore = defineStore('tasks', () => {
  // State
  const tasks = ref<Task[]>([])
  const currentTask = ref<Task | null>(null)
  const loading = ref(false)         // 首次加载状态
  const refreshing = ref(false)      // 后台刷新状态（不影响 UI 显示）

  // Getters
  const processingTasks = computed(() =>
    tasks.value.filter(t => t.status === 'processing')
  )

  const completedTasks = computed(() =>
    tasks.value.filter(t => t.status === 'completed')
  )

  const failedTasks = computed(() =>
    tasks.value.filter(t => t.status === 'failed')
  )

  // Actions
  async function fetchTasks(status?: string, silent = false) {
    // silent=true 时为后台刷新，不改变 loading 状态
    if (!silent) {
      loading.value = true
    } else {
      refreshing.value = true
    }
    try {
      tasks.value = await tasksApi.list({ status })
    } finally {
      if (!silent) {
        loading.value = false
      }
      refreshing.value = false
    }
  }

  // 静默刷新，用于轮询
  async function refreshTasks(status?: string) {
    return fetchTasks(status, true)
  }

  async function fetchTask(taskId: string) {
    loading.value = true
    try {
      currentTask.value = await tasksApi.get(taskId)
    } finally {
      loading.value = false
    }
  }

  async function createTask(data: TaskCreate) {
    const task = await tasksApi.create(data)
    tasks.value.unshift(task)
    return task
  }

  async function cancelTask(taskId: string) {
    await tasksApi.cancel(taskId)
    const task = tasks.value.find(t => t.id === taskId)
    if (task) {
      task.status = 'cancelled'
    }
  }

  function updateTaskProgress(taskId: string, data: any) {
    const task = tasks.value.find(t => t.id === taskId)
    if (task) {
      if (data.status !== undefined) task.status = data.status
      if (data.progress !== undefined) task.progress = data.progress
      if (data.progress_data !== undefined) task.progress_data = data.progress_data
      if (data.output_file !== undefined) task.output_file = data.output_file
      if (data.output_size !== undefined) task.output_size = data.output_size
    }
    if (currentTask.value?.id === taskId) {
      if (data.status !== undefined) currentTask.value.status = data.status
      if (data.progress !== undefined) currentTask.value.progress = data.progress
      if (data.progress_data !== undefined) currentTask.value.progress_data = data.progress_data
      if (data.output_file !== undefined) currentTask.value.output_file = data.output_file
      if (data.output_size !== undefined) currentTask.value.output_size = data.output_size
    }
  }

  function clearCurrentTask() {
    currentTask.value = null
  }

  return {
    // State
    tasks,
    currentTask,
    loading,
    refreshing,
    // Getters
    processingTasks,
    completedTasks,
    failedTasks,
    // Actions
    fetchTasks,
    refreshTasks,
    fetchTask,
    createTask,
    cancelTask,
    updateTaskProgress,
    clearCurrentTask,
  }
})
