<template>
  <v-app-bar flat>
    <v-app-bar-title>
      BlueOS Store Apps
    </v-app-bar-title>
    <v-spacer></v-spacer>
    <v-btn @click="navigateTo">{{ buttonText }}</v-btn>
  </v-app-bar>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const navigateTo = () => {
  router.push(route.path.endsWith('/logs') ? './' : './logs')
}

const buttonText = computed(() => {
  return route.path.endsWith('/logs') ? 'Home' : 'Logs'
})
</script>
