/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  /** When `"true"`, show Debug / Admin in the sidebar (production builds only; dev always allows). */
  readonly VITE_ENABLE_DEBUG_UI?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare module '*.css' {}
