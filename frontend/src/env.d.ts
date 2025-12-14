// frontend/src/env.d.ts
/// <reference types="vite/client" />

// Add minimal typing for our Vite env variables.
// Extend this if you add more VITE_... variables.
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  // add other VITE_... variables here as readonly strings, e.g.
  // readonly VITE_SOME_FLAG?: 'true' | 'false';
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
