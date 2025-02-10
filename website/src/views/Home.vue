<template>
  <v-card class="mx-auto" title="Usage">
    <template v-slot:prepend>
      <v-icon color="info" icon="mdi-information"></v-icon>
    </template>
    <v-card-text>
      Extensions can be installed in <a href="https://blueos.cloud/">BlueOS</a>,
      through the built in
      <a
        href="https://blueos.cloud/docs/latest/usage/advanced/#extensions-manager"
        >Extensions Manager</a
      >.
    </v-card-text>
  </v-card>
  <Counter />
</template>

<script lang="ts" setup>
  import Counter from '@/components/Counter.vue'
</script>
