import { clerkPlugin } from '@clerk/vue'
import type { App } from 'vue'

const CLERK_PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

if (!CLERK_PUBLISHABLE_KEY) {
  console.warn('Missing VITE_CLERK_PUBLISHABLE_KEY in environment variables')
}

export function setupClerk(app: App) {
  if (CLERK_PUBLISHABLE_KEY) {
    app.use(clerkPlugin, {
      publishableKey: CLERK_PUBLISHABLE_KEY,
    })
  }
}

export { CLERK_PUBLISHABLE_KEY }
