/** 任务 Store */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import tasksApi from '@/api/tasks'
import type { Task, TaskCreate } from '@/api/tasks'

export const useTasksStore = defineStore('tasks', () => {
  // State
  const tasks = ref<Task[]>([])
  const currentTask = ref<Task | null>(null)
  const loading = ref(false)

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
  async function fetchTasks(status?: string) {
    loading.value = true
    try {
      tasks.value = await tasksApi.list({ status })
    } finally {
      loading.value = false
    }
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
      task.status = data.status
      task.progress = data.progress
    }
    if (currentTask.value?.id === taskId) {
      currentTask.value.status = data.status
      currentTask.value.progress = data.progress
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
    // Getters
    processingTasks,
    completedTasks,
    failedTasks,
    // Actions
    fetchTasks,
    fetchTask,
    createTask,
    cancelTask,
    updateTaskProgress,
    clearCurrentTask,
  }
})
