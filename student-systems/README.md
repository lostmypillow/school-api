# JSearch
## What is it?
A FastAPI search engine for movies and Google search. Consumes OMDb API and a random rate limited RapidAPI. 



[**Vue frontend**](https://github.com/lostmypillow/jsearch-vue)


[**Demo website**](https://lostmypillow.github.io/jsearch-vue)

[**API Documentation**](https://jsearch.lostmypillow.duckdns.org/docs)

[**Backup API Docs (Loads slow!)**](https://jsearch-latest.onrender.com/docs)

[React frontend (broken)](https://github.com/lostmypillow/jsearch-react)

## How does it work?
1. User inputs a value in Vue frontend
2. Frontend navigates to search path and sends the data to the FastAPI server
3. FastAPI server sends back the results
4. Vue frontend displays the results
   
## Tech Stack
- **FastAPI** API endpoints
- **Nuxt(Vue)** frontend x **Vuetify** components
