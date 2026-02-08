import csv
import time
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://en.wikipedia.org/wiki/Billboard_Year-End_Hot_100_singles_of_{}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; BillboardDataBot/1.0; +https://example.com/bot)"
}

def parse_year_page(year):
    """
    Fetches the Wikipedia Year-End Hot 100 page for `year`,
    returns a list of dicts: rank, song, artist, year, decade
    """
    url = BASE_URL.format(year)
    print(f"Downloading {url}")
    resp = requests.get(url, headers=HEADERS, timeout=10)
    if resp.status_code != 200:
        print(f"  ❌ Failed to download for {year}: {resp.status_code}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # Find the first table containing year-end list
    table = soup.find("table", {"class": "wikitable"})
    if not table:
        print(f"  ❌ No table found for {year}")
        return []

    songs = []
    for row in table.find_all("tr")[1:]:
        cols = row.find_all(["td", "th"])
        if len(cols) < 3:
            continue

        rank = cols[0].text.strip()
        title = cols[1].text.strip().strip('"')
        artist = cols[2].text.strip()

        songs.append({
            "year": year,
            "decade": f"{(year//10)*10}s",
            "rank": rank,
            "title": title,
            "artist": artist
        })

    print(f"  ✅ Found {len(songs)} songs for {year}")
    return songs


def main():
    # CSV output
    out_file = "billboard_year_end_hot100_1960_2025.csv"
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["year", "decade", "rank", "title", "artist"])

        for year in range(1960, 2026):
            songs = parse_year_page(year)
            for s in songs:
                writer.writerow([s["year"], s["decade"], s["rank"], s["title"], s["artist"]])

            # Be polite: small delay
            time.sleep(1)

    print(f"Done — saved to {out_file}")


if __name__ == "__main__":
    main()
