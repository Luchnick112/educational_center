import { Capacitor } from '@capacitor/core'
import { SecureStorage } from '@aparajita/capacitor-secure-storage'

export type AuthTokens = {
  access: string
  refresh: string
}

const ACCESS_KEY = 'helper.auth.access'
const REFRESH_KEY = 'helper.auth.refresh'
const useNativeStorage = Capacitor.isNativePlatform()

async function getItem(key: string) {
  return useNativeStorage ? SecureStorage.getItem(key) : localStorage.getItem(key)
}

async function setItem(key: string, value: string) {
  if (useNativeStorage) await SecureStorage.setItem(key, value)
  else localStorage.setItem(key, value)
}

async function removeItem(key: string) {
  if (useNativeStorage) await SecureStorage.removeItem(key)
  else localStorage.removeItem(key)
}

export const tokenStorage = {
  async get(): Promise<AuthTokens | null> {
    const [access, refresh] = await Promise.all([getItem(ACCESS_KEY), getItem(REFRESH_KEY)])
    return access && refresh ? { access, refresh } : null
  },

  async set(tokens: AuthTokens): Promise<void> {
    await Promise.all([setItem(ACCESS_KEY, tokens.access), setItem(REFRESH_KEY, tokens.refresh)])
  },

  async clear(): Promise<void> {
    await Promise.all([removeItem(ACCESS_KEY), removeItem(REFRESH_KEY)])
  },
}
