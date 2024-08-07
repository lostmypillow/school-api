# JSearch
## What is it?
A full stack search engine for movies and Google search. Consumes OMDb API and a random rate limited RapidAPI. One of my oldest projects that started from a [React version](https://github.com/lostmypillow/jsearch-react), then I made a [Vue version of the same website](https://github.com/lostmypillow/jsearch-vue), which is actually functional and the version that works with the FastAPI server in this repo.

[**Demo website**](https://lostmypillow.github.io/jsearch-vue)

[**API Documentation**](https://jsearch.lostmypillow.duckdns.org/docs)

[**Backup API Docs (Loads slow!)**](https://jsearch.onrender.com/docs)

## How does it work?
1. User inputs a value in Vue frontend
2. Frontend navigates to search path and sends the data to the FastAPI server
3. FastAPI server sends back the results
4. Vue frontend displays the results
   
## Tech Stack
- **FastAPI** API endpoints
- **Nuxt(Vue)** frontend x **Vuetify** components
