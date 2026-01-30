import { ref, computed, watch } from 'vue'
import { useAuth as useClerkAuth, useUser as useClerkUser, useSession } from '@clerk/vue'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export interface User {
  id: string
  email: string | null
  name: string | null
  image_url: string | null
}

export interface ConnectedIntegration {
  provider: string
  scopes: string[]
  expires_at: string | null
}

// Global state synced with Clerk
const connectedProviders = ref<string[]>([])
const integrations = ref<ConnectedIntegration[]>([])
const backendUser = ref<User | null>(null)

export function useAuth() {
  const { isSignedIn } = useClerkAuth()
  const { user: clerkUser } = useClerkUser()
  const { session } = useSession()

  const error = ref<string | null>(null)
  const googleToken = ref<string | null>(null)

  // Computed user from Clerk
  const user = computed<User | null>(() => {
    if (!clerkUser.value) return null
    return {
      id: clerkUser.value.id,
      email: clerkUser.value.primaryEmailAddress?.emailAddress || null,
      name: clerkUser.value.fullName || null,
      image_url: clerkUser.value.imageUrl || null,
    }
  })

  const isAuthenticated = computed(() => isSignedIn.value === true)
  const isLoading = computed(() => isSignedIn.value === undefined)

  // Check if Google is connected (user signed in with Google)
  const isGoogleConnected = computed(() => {
    if (!clerkUser.value) return false
    return clerkUser.value.externalAccounts?.some(
      (acc: any) => acc.provider === 'oauth_google' || acc.provider === 'google'
    ) ?? false
  })

  // Get auth headers for API requests
  async function getAuthHeaders(): Promise<Record<string, string>> {
    if (!session.value) {
      return {}
    }
    try {
      const token = await session.value.getToken()
      if (token) {
        return { Authorization: `Bearer ${token}` }
      }
    } catch (e) {
      console.error('Failed to get token:', e)
    }
    return {}
  }

  // Fetch current user info from backend
  async function fetchCurrentUser() {
    if (!isSignedIn.value || !session.value) {
      backendUser.value = null
      connectedProviders.value = []
      integrations.value = []
      return
    }

    try {
      const headers = await getAuthHeaders()
      const response = await fetch(`${API_URL}/integrations/oauth/me`, {
        headers,
      })

      if (response.ok) {
        const data = await response.json()
        backendUser.value = data.user
        connectedProviders.value = data.connected_providers || []
        integrations.value = data.integrations || []
      }
    } catch (e) {
      console.error('Failed to fetch user:', e)
      error.value = e instanceof Error ? e.message : 'Failed to fetch user'
    }
  }

  // Update token - called when Clerk auth state changes
  async function updateToken() {
    await fetchCurrentUser()
  }

  // Check if a provider is connected
  function isProviderConnected(provider: string): boolean {
    if (provider === 'google') {
      return isGoogleConnected.value
    }
    return connectedProviders.value.includes(provider)
  }

  // Get Google OAuth token from Clerk external account
  async function getGoogleToken(): Promise<string | null> {
    if (!clerkUser.value) return null

    try {
      const googleAccount = clerkUser.value.externalAccounts?.find(
        (acc: any) => acc.provider === 'oauth_google' || acc.provider === 'google'
      )

      if (googleAccount) {
        // Token is fetched via backend using Clerk Backend API
        return null
      }
      return null
    } catch (e) {
      console.error('Failed to get Google token:', e)
      return null
    }
  }

  // Reauthorize Google with additional scopes
  async function connectGoogle(): Promise<void> {
    if (!clerkUser.value) return

    // Use full URL format for scopes
    const additionalScopes = [
      'https://www.googleapis.com/auth/calendar',
    ]

    const googleAccount = clerkUser.value.externalAccounts?.find(
      (acc: any) => acc.provider === 'oauth_google' || acc.provider === 'google'
    ) as any

    if (googleAccount) {
      try {
        // Reauthorize with additional scopes
        const result = await googleAccount.reauthorize({
          redirectUrl: window.location.href,
          additionalScopes,
        })

        // Manually redirect to OAuth URL
        const redirectUrl = result?.verification?.externalVerificationRedirectURL
        if (redirectUrl) {
          window.location.href = redirectUrl.href || redirectUrl.toString()
        }
      } catch (e) {
        console.error('Failed to reauthorize Google:', e)
        error.value = e instanceof Error ? e.message : 'Failed to connect Google'
        throw e
      }
    } else {
      // No Google account connected - just sign in without extra scopes
      // Extra scopes will be requested via reauthorize after sign-in
      try {
        const result = await clerkUser.value.createExternalAccount({
          strategy: 'oauth_google',
          redirectUrl: window.location.href,
          // NO additionalScopes for initial sign-in
        })

        // Manually redirect to OAuth URL
        const redirectUrl = result?.verification?.externalVerificationRedirectURL
        if (redirectUrl) {
          window.location.href = redirectUrl.href || redirectUrl.toString()
        }
      } catch (e) {
        console.error('Failed to connect Google:', e)
        error.value = e instanceof Error ? e.message : 'Failed to connect Google'
        throw e
      }
    }
  }

  // Save OAuth token to backend
  async function saveOAuthToken(
    provider: string,
    accessToken: string,
    refreshToken?: string,
    scopes?: string[],
    expiresIn?: number
  ) {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/integrations/oauth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
      body: JSON.stringify({
        provider,
        access_token: accessToken,
        refresh_token: refreshToken,
        scopes,
        expires_in: expiresIn,
      }),
    })

    if (response.ok) {
      await fetchCurrentUser()
      return true
    }
    return false
  }

  // Disconnect a provider
  async function disconnectProvider(provider: string) {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/integrations/oauth/token/${provider}`, {
      method: 'DELETE',
      headers,
    })

    if (response.ok) {
      await fetchCurrentUser()
      return true
    }
    return false
  }

  // Placeholder for Clerk instance (not needed with new API)
  function setClerkInstance(_clerk: unknown) {
    // No-op, kept for compatibility
  }

  return {
    // State
    user,
    isAuthenticated,
    isLoading,
    error,
    connectedProviders,
    integrations,
    googleToken,
    isGoogleConnected,

    // Methods
    setClerkInstance,
    getAuthHeaders,
    fetchCurrentUser,
    updateToken,
    isProviderConnected,
    saveOAuthToken,
    disconnectProvider,
    getGoogleToken,
    connectGoogle,
  }
}
