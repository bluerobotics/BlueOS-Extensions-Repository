<template>
  <div>
    <h1>Generation Logs</h1>
    <JsonViewer
      :value="data"
      :expand-depth=5
      copyable
      sort
    />
  </div>
</template>

<script lang="ts" setup>
import { onMounted, ref } from 'vue'
// @ts-expect-error Lib does not have types
import JsonViewer from 'vue-json-viewer'

const data = ref({})

onMounted(async () => {
  try {
    const response = await fetch("manifest.log")
    data.value = await response.json()
  } catch (e) {
    console.error('Failed to load manifest.log', e)
  }
})
</script>

<style scoped>
h1 {
  text-align: center;
  margin-bottom: 20px;
}
</style>
