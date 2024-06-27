<script setup>
const toggle = ref('light')
const route = useRoute()
const type = computed(() => route.query.type)
const searchType = ref('movies')
const query = computed(() => route.query.query)
const searchTerm = ref('')
const searchLabel = computed(() => {
  return searchType.value == "movies" ? "Search with OMDb API" : " Search with RapidAPI"
})
const loading = ref(false)

import { useTheme } from 'vuetify'

const theme = useTheme()

watch( toggle, (newtoggle) => {
  toggleTheme()
})


function toggleTheme() {
  theme.global.name.value = theme.global.current.value.dark ? 'light' : 'dark'
}


function onClick() {
  loading.value = true
  navigateTo({
    path: '/search',
    query: {
      type: searchType.value,
      query: searchTerm.value,
    }
  })
  console.log("naved")
  loading.value = false



}

</script>


<template>
  <NuxtLayout>
    <v-app>
      <v-app-bar scroll-behavior="elevate" rounded>

        <v-app-bar-title><v-btn variant="text" to="/">
            <label class="text-2xl">JSEARCH</label>
          </v-btn></v-app-bar-title>

        <template v-slot:append>

          <v-btn-toggle v-model="toggle" color="primary" mandatory>
            <v-btn icon="mdi-white-balance-sunny" value="light"></v-btn>
            <v-btn icon="mdi-moon-waning-crescent" value="dark"></v-btn>

          </v-btn-toggle>
        </template>
      </v-app-bar>

      <div class="flex flex-col w-svw items-center justify-center pt-16 px-6 pb-6">
        <v-text-field v-model="searchTerm" class="flex w-full md:w-1/4 h-11 pt-2" :label=searchLabel type="input"
          append-icon="mdi-send" @click:append="onClick" @keyup.enter="onClick" :loading="loading" />

        <v-select v-model="searchType" class="flex w-full pt-6 md:w-1/4" label="Change Search Type"
          :items="['movies', 'google']" variant="underlined" />


        <div class="flex flex-col pt-4 w-full items-center">

          <!-- <v-progress-circular v-if="loading" indeterminate /> -->

          <NuxtPage  />

        </div>

      </div>
    </v-app>
  </NuxtLayout>
</template>
