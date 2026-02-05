import { ref } from 'vue'

export interface Toast {
  id: number
  title: string
  message: string
  type?: 'info' | 'success' | 'warning' | 'error'
  icon?: string
  duration?: number
}

const toasts = ref<Toast[]>([])
let nextId = 1

export function useToast() {
  function show(toast: Omit<Toast, 'id'>) {
    const id = nextId++
    toasts.value.push({ id, ...toast })
    return id
  }

  function info(title: string, message: string, icon?: string) {
    return show({ title, message, type: 'info', icon })
  }

  function success(title: string, message: string, icon?: string) {
    return show({ title, message, type: 'success', icon: icon || '✅' })
  }

  function warning(title: string, message: string, icon?: string) {
    return show({ title, message, type: 'warning', icon: icon || '⚠️' })
  }

  function error(title: string, message: string, icon?: string) {
    return show({ title, message, type: 'error', icon: icon || '❌' })
  }

  function remove(id: number) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  function clear() {
    toasts.value = []
  }

  return {
    toasts,
    show,
    info,
    success,
    warning,
    error,
    remove,
    clear,
  }
}
