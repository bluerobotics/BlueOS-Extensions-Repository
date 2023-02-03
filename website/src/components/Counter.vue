<template>
  <v-container>
    <v-row>
      <v-col v-for="extension in extensions" :key="extension.identifier">
        <v-card class="mx-auto" width="400px" outlined>
          <v-card-title>
            <v-row no-gutters class="justify-center align-center">
              <v-avatar tile size="50">
                <v-img :src="extension.extension_logo" />
              </v-avatar>
              <v-col>
                <v-card-title>
                  {{ extension.name }}
                </v-card-title>
                <v-card-subtitle> {{ extension.identifier }} </v-card-subtitle>
              </v-col>
            </v-row>
          </v-card-title>
          <v-card-text>{{ extension.description }}</v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";

const extensions = ref();

onMounted(async () => {
  const response = await fetch("manifest.json");
  extensions.value = await response.json();
});
</script>
