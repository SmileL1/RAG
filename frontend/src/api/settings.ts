import { http } from './client'

export interface AppSettings {
  LLM_PROVIDER: string
  LLM_API_BASE: string
  LLM_MODEL: string
  LLM_TEMPERATURE: number
  LLM_MAX_TOKENS: number
  LLM_API_KEY_SET: boolean
  LLM_API_KEY_MASKED: string
  EMBEDDING_PROVIDER: string
  RETRIEVE_TOP_K: number
  RERANK_ENABLED: boolean
  RERANK_TOP_K: number
  USE_HYDE: boolean
  QDRANT_MODE: string
  INGEST_MODE: string
}

export type SettingsPatch = Partial<
  Pick<
    AppSettings,
    | 'LLM_PROVIDER'
    | 'LLM_API_BASE'
    | 'LLM_MODEL'
    | 'LLM_TEMPERATURE'
    | 'LLM_MAX_TOKENS'
    | 'RETRIEVE_TOP_K'
    | 'RERANK_ENABLED'
    | 'RERANK_TOP_K'
    | 'USE_HYDE'
  >
> & {
  /** 留空表示不修改 */
  LLM_API_KEY?: string
}

export interface TestLLMResult {
  ok: boolean
  message: string
  reply?: string | null
}

export interface OllamaModelsResult {
  ok: boolean
  models: string[]
  message: string
}

export const settingsApi = {
  get: () => http.get<AppSettings>('/settings').then((r) => r.data),
  patch: (body: SettingsPatch) => http.patch<AppSettings>('/settings', body).then((r) => r.data),
  testLlm: () => http.post<TestLLMResult>('/settings/test-llm').then((r) => r.data),
  ollamaModels: (base?: string) =>
    http
      .get<OllamaModelsResult>('/settings/ollama-models', { params: base ? { base } : {} })
      .then((r) => r.data),
}
