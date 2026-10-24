from fastapi import Depends

from app.domains.talk.repositories import NextcloudRepository
from app.domains.talk.services import NextcloudService


def get_bot_repo():
    return NextcloudRepository()

def get_message_service(repo: NextcloudRepository = Depends(get_bot_repo)):
    return NextcloudService(repo)

