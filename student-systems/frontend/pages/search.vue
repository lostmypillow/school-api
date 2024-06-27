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
  getALl()
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

  const result = await $fetch("https://www.omdbapi.com/?apikey=e9cb394&s=" + query.value);
  data.value = result.Search

  // console.log(result.Search)
  console.log("searched movie")
}

async function getGoogle() {

  const todo = await $fetch('https://google-search74.p.rapidapi.com', {
    method: 'GET',
    params: {
      query: query.value,
      limit: "10",
      related_keywords: "false",
    },
    headers: {
      "X-RapidAPI-Key":
        "4cc2304fb3msh28544a85c39f266p17c92bjsnd635c2ee140a",
      "X-RapidAPI-Host": "google-search74.p.rapidapi.com",
    },
  })
  //   const todo ={
  //     "search_term": "Cat",
  //     "knowledge_panel": {
  //         "name": "Cat",
  //         "label": "Animal",
  //         "description": {
  //             "text": "The cat, commonly referred to as the domestic cat or house cat, is a small domesticated carnivorous mammal. It is the only domesticated species of the family Felidae. Recent advances in archaeology and genetics have shown that the domestication of the cat occurred in the Near East around 7500 BC.",
  //             "url": "https://en.wikipedia.org/wiki/Cat",
  //             "site": "Wikipedia"
  //         },
  //         "image": {
  //             "url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:VRmao7FmvjTB6M",
  //             "width": 277,
  //             "height": 182,
  //             "page_url": "https://en.wikipedia.org/wiki/Cat"
  //         },
  //         "info": [
  //             {
  //                 "title": "Lifespan",
  //                 "labels": [
  //                     "12 – 18 years (Domesticated)"
  //                 ]
  //             },
  //             {
  //                 "title": "Gestation period",
  //                 "labels": [
  //                     "65 days"
  //                 ]
  //             },
  //             {
  //                 "title": "Scientific name",
  //                 "labels": [
  //                     "Felis catus"
  //                 ]
  //             },
  //             {
  //                 "title": "Class",
  //                 "labels": [
  //                     "Mammalia"
  //                 ]
  //             },
  //             {
  //                 "title": "Domain",
  //                 "labels": [
  //                     "Eukaryota"
  //                 ]
  //             },
  //             {
  //                 "title": "Family",
  //                 "labels": [
  //                     "Felidae"
  //                 ]
  //             }
  //         ]
  //     },
  //     "results": [
  //         {
  //             "position": 1,
  //             "url": "https://www.cat.com/global-selector.html",
  //             "title": "Cat.com Global Selector: Language & Region | Cat | Caterpillar",
  //             "description": "Select your region and language for www.cat.com to view the most relevant products and services in your area of the world."
  //         },
  //         {
  //             "position": 2,
  //             "url": "https://en.wikipedia.org/wiki/Cat",
  //             "title": "Cat - Wikipedia",
  //             "description": "The cat (Felis catus), commonly referred to as the domestic cat or house cat, is a small domesticated carnivorous mammal. It is the only domesticated ..."
  //         },
  //         {
  //             "position": 3,
  //             "url": "https://www.cat.com/en_US.html",
  //             "title": "Products & Services – North America | Cat | Caterpillar",
  //             "description": "Cat® equipment and services are backed by the largest, most experienced dealer network in the world. Get the job done with our products, technology and ..."
  //         },
  //         {
  //             "position": 4,
  //             "url": "https://www.caterpillar.com/",
  //             "title": "Caterpillar Inc",
  //             "description": "Caterpillar is the world's leading manufacturer of construction and mining equipment, diesel and natural gas engines, industrial turbines and ..."
  //         },
  //         {
  //             "position": 5,
  //             "url": "https://www.merriam-webster.com/dictionary/cat",
  //             "title": "Cat Definition & Meaning - Merriam-Webster",
  //             "description": "The meaning of CAT is a carnivorous mammal (Felis catus) long domesticated as a pet and for catching rats and mice. How to use cat in a sentence."
  //         },
  //         {
  //             "position": 6,
  //             "url": "https://www.nationalgeographic.com/animals/mammals/facts/domestic-cat",
  //             "title": "Domestic cat - National Geographic",
  //             "description": "As mostly nocturnal animals, cats have excellent vision and hearing, with ears that can turn like satellite dishes. Their reputation for having nine lives stems ..."
  //         },
  //         {
  //             "position": 7,
  //             "url": "https://www.vetstreet.com/cats",
  //             "title": "Cats - Vetstreet",
  //             "description": "15 Best Wet Cat Foods of 2024 Approved By Vets. Wet cat food can offer a variety of benefits to our feline friends. Here..."
  //         },
  //         {
  //             "position": 8,
  //             "url": "https://www.britannica.com/animal/cat",
  //             "title": "Cat | Breeds, Origins, History, Body Types, Senses, Behavior ...",
  //             "description": "Domestic cats are characterized by retractable claws, powerful bodies, acute senses, long tails, and specialized teeth adapted for hunting prey."
  //         },
  //         {
  //             "position": 9,
  //             "url": "https://www.purina.com/cats/cat-breeds",
  //             "title": "All Cat Breed Information | Purina US",
  //             "description": "Trying to decide what type of cat is right for you and your family? Browse through our list of cat breeds, and find the best cat for you."
  //         },
  //         {
  //             "position": 10,
  //             "url": "https://www.catphones.com/",
  //             "title": "Cat phones: Made Mighty",
  //             "description": "Unlike traditional phones, Cat phones are engineered to work under extraordinary conditions; from dust and mud filled construction sites to bustling and heavily ..."
  //         }
  //     ]
  // }
  data.value = todo

  console.log(todo)
  console.log("searched google")
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
