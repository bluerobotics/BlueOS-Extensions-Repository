<template>
  <v-app-bar flat>
    <v-app-bar-title>
      BlueOS Store Apps
    </v-app-bar-title>
    <v-spacer></v-spacer>
    <v-btn :to="buttonRoute">{{ buttonText }}</v-btn>
  </v-app-bar>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const buttonText = computed(() => {
  return route.path === '/logs' ? 'Home' : 'Logs'
})

const buttonRoute = computed(() => {
  return route.path === '/logs' ? '/' : '/logs'
})
</script>
