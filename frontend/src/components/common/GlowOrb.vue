<script setup lang="ts">
defineProps<{
  color?: 'purple' | 'cyan'
  size?: number
  top?: string
  left?: string
  right?: string
  bottom?: string
  opacity?: number
}>()
</script>

<template>
  <div
    class="glow-orb"
    :class="`glow-orb--${color ?? 'purple'}`"
    :style="{
      width: `${size ?? 400}px`,
      height: `${size ?? 400}px`,
      top,
      left,
      right,
      bottom,
      opacity,
    }"
  />
</template>
