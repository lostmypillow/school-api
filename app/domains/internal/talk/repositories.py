# repositories/nextcloud_global_repo.py
import httpx


class NextcloudRepository:
    def __init__(self):
        self.base_api_url = "https://cloud./ocs/v2.php/apps/spreed/api"
        self.room_api_url = f"{self.base_api_url}/v4/room"
        self.chat_api_url = f"{self.base_api_url}/v1/chat"
        self.headers = {"OCS-APIRequest": "true", "Accept": "application/json"}

    async def return_existing_rooms(self, auth: tuple[str, str])-> list[dict]:
        """Ensure or fetch a one-to-one room between sender and recipient."""
        async with httpx.AsyncClient(verify=False) as client:
            resp = await client.get(url=self.room_api_url, auth=auth, headers=self.headers)
            resp.raise_for_status()
            results = resp.json()['ocs']['data']
        return results


    async def create_room(self, auth: tuple[str, str], recipient: str) -> dict:
        async with httpx.AsyncClient(verify=False) as client:
            create_data = {"roomType": 1, "invite": recipient}
            create_resp = await client.post(
                url=self.room_api_url,
                auth=auth,
                headers=self.headers,
                data=create_data
            )
            create_resp.raise_for_status()
            if create_resp.status_code == 201:
                print("Room created successfully")
            elif create_resp.status_code == 200:
                print("Existing room returned by server")

            created_room = create_resp.json()["ocs"]["data"]
        return created_room

    async def send_message(self, auth: tuple[str, str], message: str, token: str):
        """Send a message on behalf of `sender` to `recipient`."""
        async with httpx.AsyncClient(verify=False) as client:
            url = f"{self.chat_api_url}/{token}"
            data = { "message": message }
            resp = await client.post(url, auth=auth, headers=self.headers, data=data)
            resp.raise_for_status()
            return resp.json()
