<template>
  <v-container>
    <v-row 
      v-for="(section, index) in sections"
      :key="index"
    >
      <v-row class="ma-1">
        <h1>{{ section.replace("-"," ").replace(/\b\w/g, s => s.toUpperCase()) + "s" }}</h1>
      </v-row>
      <v-row class="ma-1" align="center">
        <template v-for="extension in extensions" :key="extension.identifier">
          <v-col v-if="highestVersion(extension).type === section">
            <v-card class="mx-auto" width="400px" outlined>
              <v-card-title>
                <v-row no-gutters class="justify-center align-center">
                  <v-avatar tile size="65" class="ma-2">
                    <v-img :src="extension.extension_logo" />
                  </v-avatar>
                  <v-col>
                    <v-card-title>
                      <a v-bind:href="extension.website">{{ extension.name }}</a>
                    </v-card-title>
                    <v-card-subtitle>
                      <a v-bind:href="'https://hub.docker.com/r/' + extension.docker">{{ extension.identifier }}</a>
                    </v-card-subtitle>
                  </v-col>
                  <v-slide-group class="mt-2" v-if="highestVersion(extension).filter_tags.length > 0">
                    <v-chip label class="ma-1" density="compact" color="blue" v-for="tag in highestVersion(extension).filter_tags">
                      {{ tag }}
                    </v-chip>
                  </v-slide-group>
                </v-row>
              </v-card-title>
              <v-card-text>{{ extension.description }}</v-card-text>
            </v-card>
          </v-col>
        </template>
      </v-row>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ExtensionType, RepositoryEntry, Version } from "@/types/manifest"

const extensions = ref();

onMounted(async () => {
  const response = await fetch("manifest.json");
  extensions.value = await response.json() as [RepositoryEntry];
});

const sections = computed(() => {
  return ExtensionType
})

function highestVersion(extension: RepositoryEntry) : Version {
  // Assumes versions are pre-sorted by semver, highest first
  return Object.values(extension.versions)[0];
}
</script>
