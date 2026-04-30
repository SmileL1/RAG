import { onScopeDispose, ref } from 'vue'

/**
 * 简易轮询：interval 毫秒执行 fn 一次，组件销毁自动停。
 * fn 返回 true 表示"继续轮询"；返回 false 自动停止。
 */
export function usePolling(fn: () => Promise<boolean>, intervalMs = 3000) {
  const running = ref(false)
  let timer: ReturnType<typeof setTimeout> | null = null

  async function loop() {
    if (!running.value) return
    let next = true
    try {
      next = await fn()
    } catch (e) {
      console.error('[polling] error', e)
    }
    if (!next) {
      stop()
      return
    }
    timer = setTimeout(loop, intervalMs)
  }

  function start() {
    if (running.value) return
    running.value = true
    loop()
  }

  function stop() {
    running.value = false
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
  }

  onScopeDispose(stop)

  return { start, stop, running }
}
