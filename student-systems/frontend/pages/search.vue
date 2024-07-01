<script setup>
const route = useRoute()

const expand = ref(false)
// console.log("type value is")
// console.log(type.value)
const data = ref()
// watch(type, query, (newtype, newquery) => {
//   console.log(`new type is ${newtype} ${newquery}`)
// })
const type = computed(() => route.query.type)
const query = computed(() => route.query.query)
// console.log(query.value)
const router = useRouter();

const croute = computed(() => router.currentRoute.value.fullPath)
watch(croute, (newcroute, oldcroute) => {
  if (newcroute !== oldcroute) {
    console.log("changed")
    getALl();
  }
});

onBeforeMount(() => {
  const type = computed(() => route.query.type)
  console.log(`meow ${type.value}`)
  if (type.value) {
    getALl()
  }
  
})



function getALl() {
  // console.log(`type value is ${type.value} within getAll`)
  if (type.value == "movies") {
    getMovies()
    console.log("got movies")
  } else if (type.value == "google") {
    getGoogle()
    console.log("got google")
  }

}


async function getMovies() {

  const result = await fetch("/get-movies/?query="+query.value);
  const response = await result.json()
  console.log(response.results.Search)
  data.value = await response.results.Search
  
  // console.log(result.Search)
  // console.log("searched movie")
}

async function getGoogle() {

  const todo = await fetch('/get-google/?query='+query.value+"&limit=10&related=false")
  const response = await todo.json()
  console.log(response.results)
  data.value = await response.results
}

</script>


<template>

  <h1 class="flex w-fit text-xl md:text-3xl gap-4">
    You searched for:
    <p class="font-mono font-extrabold">
      {{ query }}
    </p>
    in
    <p class="font-mono font-extrabold">
      {{ type }}
    </p>
  </h1>
  <div v-if="data">
    <div v-if="type == 'movies'"
      class="flex flex-col md:flex-row flex-wrap items-center justify-center w-full gap-4 pt-4">

      <v-card class="min-w-full md:w-1/5 " v-for="movie in data" :key="movie.imdbID" :title="movie.Title" :subtitle="movie.Year"
        :text="movie.Type" variant="tonal">

        <v-img height="200px" :src="movie.Poster" cover />

      </v-card>

    </div>

    <div v-else class="flex flex-col flex-wrap items-center justify-center w-full gap-4 pt-4">

      <!-- <v-card v-if="data.knowledge_panel != null" class="md:w-2/3" :title="data.knowledge_panel.name" :subtitle="data.knowledge_panel.label"
        :text="data.knowledge_panel.description.text" variant="tonal">
        <v-img :height="data.knowledge_panel.image.height" :width="data.knowledge_panel.image.width"
          :src="data.knowledge_panel.image.url" cover />

        <a class="px-4 underline text-blue-500" :href="data.knowledge_panel.description.url">
          Source:
          {{ data.knowledge_panel.description.site }}
        </a>

        <div v-if="expand" class="py-2 px-4">
          <v-list lines="one">

            <v-list-item v-for="n in data.knowledge_panel.info" :title="n.title">

              <template v-slot:subtitle>
                <p v-for="s in n.labels">{{ s }}</p>
              </template>

            </v-list-item>

          </v-list>

        </div>

        <v-card-actions>

          <v-btn :text="!expand ? 'More Info' : 'Hide Info'" @click="expand = !expand" />

        </v-card-actions>

      </v-card> -->

      <v-card class="md:w-2/3 " v-for="result in data.results" :key="result.position" :title="result.title"
        :subtitle="result.url" :text="result.description" :href="result.url" variant="tonal" />
    </div>
  </div>

</template>

<style scoped>
img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
</style>
