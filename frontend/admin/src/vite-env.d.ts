/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  readonly VITE_INTERNAL_TOKEN?: string
  readonly VITE_DEBUG_ROLE?: string
  readonly VITE_ADMIN_TOKEN?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
