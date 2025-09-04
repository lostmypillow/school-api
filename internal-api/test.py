from lib.ipa_client import IPAClient
from lib.csv_store import CSVStore

store = CSVStore()
client = IPAClient()
users = store.load_all_users()
for user in users:
    target = client.get_user_ou_number(user.uid)
    deps = store.load_all_deps()
    for g in deps:
        if g.get("自動編號") == target:
            print(f"Will set {user.uid} ou to {g.get('description')}", end="")
            client.call("user_mod", [str(user.uid)], {"setattr": [f"ou={g.get('description')}"]})
            print("Done")
