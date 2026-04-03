# services/message_service.py
from app.features.talk.repositories import NextcloudRepository


class NextcloudService:
    def __init__(self, repo: NextcloudRepository):
        self.repo = repo

    async def send_message(self, sender: str, recipient: str, message: str, password: str):
        try:
            auth: tuple[str, str] = (sender, password)
            room_api_results = await self.repo.return_existing_rooms(auth=auth)
            existing_room = next(
                (room for room in room_api_results if recipient in room['displayName']),
                None
            )
            if not existing_room:
                print("No existing room, creating one-on-one conversation...")
                existing_room = await self.repo.create_room(auth=auth, recipient=recipient)
            token = existing_room['token']
            print(f"Existing room found, token is {token}")
            result = await self.repo.send_message(auth=auth, message=message, token=token)
            return {"success": True, "detail": f"Message sent as {sender}", "result": result}
        except Exception as e:
            return {"success": False, "detail": str(e)}
