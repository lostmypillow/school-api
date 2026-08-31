from bs4 import BeautifulSoup


async def scrape(client, url, tag):
    combined_url = "https://aps.ntut.edu.tw/course/tw/" + url
    bs4_mode = "html.parser" if tag == "sem" else "lxml"
    if tag == "sem":
        bs4_function = lambda t: t.name == "a" and t.get("href", "").startswith("Subj")
    else:
        bs4_function = str(tag)
    response = await client.get(combined_url)
    content = response.text
    return BeautifulSoup(content, bs4_mode).find_all(bs4_function)
