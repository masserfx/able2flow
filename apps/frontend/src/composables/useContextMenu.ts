import { ref, onMounted, onUnmounted } from 'vue'

export interface ContextMenuItem {
  label: string
  icon?: string
  action: () => void
  divider?: boolean
  danger?: boolean
}

export function useContextMenu() {
  const isVisible = ref(false)
  const x = ref(0)
  const y = ref(0)
  const items = ref<ContextMenuItem[]>([])

  const show = (event: MouseEvent, menuItems: ContextMenuItem[]) => {
    event.preventDefault()
    event.stopPropagation()
    
    items.value = menuItems
    x.value = event.clientX
    y.value = event.clientY
    isVisible.value = true
  }

  const hide = () => {
    isVisible.value = false
    items.value = []
  }

  const handleClickOutside = (event: MouseEvent) => {
    if (isVisible.value) {
      hide()
    }
  }

  const handleEscape = (event: KeyboardEvent) => {
    if (event.key === 'Escape' && isVisible.value) {
      hide()
    }
  }

  onMounted(() => {
    document.addEventListener('click', handleClickOutside)
    document.addEventListener('contextmenu', handleClickOutside)
    document.addEventListener('keydown', handleEscape)
  })

  onUnmounted(() => {
    document.removeEventListener('click', handleClickOutside)
    document.removeEventListener('contextmenu', handleClickOutside)
    document.removeEventListener('keydown', handleEscape)
  })

  return {
    isVisible,
    x,
    y,
    items,
    show,
    hide
  }
}
