<script setup lang="ts">
import { watch } from 'vue'
import {
  SignedIn,
  SignedOut,
  UserButton as ClerkUserButton,
  SignInButton,
  useAuth as useClerkAuth,
} from '@clerk/vue'
import { useAuth } from '../composables/useAuth'

const { isSignedIn } = useClerkAuth()
const { fetchCurrentUser } = useAuth()

// Sync Clerk auth state with local auth
watch(
  () => isSignedIn.value,
  async (signedIn) => {
    if (signedIn) {
      await fetchCurrentUser()
    }
  },
  { immediate: true }
)
</script>

<template>
  <div class="user-button">
    <SignedIn>
      <ClerkUserButton
        :appearance="{
          elements: {
            avatarBox: 'w-9 h-9',
          }
        }"
      />
    </SignedIn>

    <SignedOut>
      <SignInButton mode="modal">
        <button class="sign-in-btn">
          Sign In
        </button>
      </SignInButton>
    </SignedOut>
  </div>
</template>

<style scoped>
.user-button {
  display: flex;
  align-items: center;
}

.sign-in-btn {
  padding: 0.5rem 1rem;
  background-color: var(--accent-blue);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.sign-in-btn:hover {
  background-color: var(--accent-blue-hover);
}
</style>
