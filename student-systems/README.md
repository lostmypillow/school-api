# JSearch0 Backend
> This is a prototype website, denoted by the 0 in the name "JSearch0". Expect bugs.

> This is the repository for the FastAPI backend, if you're looking for JSearch0 API's  GitHub repository, it's here: https://github.com/lostmypillow/jsearch

## What is it?

![image](https://github.com/user-attachments/assets/84740b26-ff7c-4f75-837e-4f2ebd6bebb5)

- A full stack search engine for movies and Google search. Consumes OMDb API and a rate limited RapidAPI that returns Google search results.

- Works with the API hosted on Render.

- Features dark/light mode switch.

- [**Demo website**](https://jsearch0.chodanpillow.com)

- [**API Documentation**](https://jsearch-api.onrender.com/docs)

## How does it work?
1. User inputs a value in Vue frontend
2. Frontend navigates to search path and sends the data to the FastAPI server
3. FastAPI server sends back the results
4. Vue frontend displays the results
   
## Tech Stack
- **FastAPI** API endpoints
- **Nuxt(Vue)** frontend x **Vuetify** components