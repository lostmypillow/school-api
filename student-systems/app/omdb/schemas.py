from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_pascal


class BaseOMDBModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_pascal,
        populate_by_name=True,
    )


class Movie(BaseOMDBModel):
    title: str
    year: str
    imdb_id: str = Field(validation_alias=AliasChoices("imdb_id", "imdbID", "ImdbID", "ImdbId"))
    type: str
    poster: str


class OMDBResponse(BaseOMDBModel):
    search: list[Movie]
    total_results: str = Field(validation_alias="totalResults")
    response: str


class SearchResult(BaseModel):
    results: OMDBResponse
