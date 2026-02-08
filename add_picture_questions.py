import requests
import time
from db import supabase

WIKIPEDIA_API = "https://en.wikipedia.org/api/rest_v1/page/summary/{}"

TOPIC = "Pictures Of Famous People"
SUBMITTED_BY = "Dave S."
LASTFM_API_KEY = "cbe82079f09b6715630e527386c2ee3a"

def get_20th_century_musicians():

    """
    Famous musicians whose primary cultural impact was in the 20th century.
    Individuals only (no bands).
    """

    return [
        "Louis Armstrong",
        "Ella Fitzgerald",
        "Billie Holiday",
        "Frank Sinatra",
        "Elvis Presley",
        "Chuck Berry",
        "Little Richard",
        "Buddy Holly",
        "Bob Dylan",
        "Jimi Hendrix",
        "Janis Joplin",
        "Jim Morrison",
        "Johnny Cash",
        "Aretha Franklin",
        "Ray Charles",
        "James Brown",
        "Otis Redding",
        "Sam Cooke",
        "Prince",
        "Michael Jackson",
        "Madonna",
        "David Bowie",
        "Freddie Mercury",
        "George Michael",
        "Paul McCartney",
        "John Lennon",
        "Mick Jagger",
        "Stevie Wonder",
        "Marvin Gaye",
        "Tina Turner",
        "Whitney Houston",
        "Dolly Parton",
        "Bruce Springsteen",
        "Neil Young",
        "Leonard Cohen",
        "Eric Clapton",
        "Carlos Santana",
        "Bob Marley",
        "Peter Tosh",
        "Fela Kuti",
        "Miles Davis",
        "John Coltrane",
        "Thelonious Monk",
        "Herbie Hancock",
        "Nina Simone",
        "Patti Smith",
        "Kate Bush",
        "Bjork",
        "Axl Rose",
        "Kurt Cobain",
        "Layne Staley",
        "Chris Cornell",
        "Iggy Pop",
        "Lou Reed",
        "Brian Wilson",
        "George Harrison",
        "Ringo Starr",
        "Roy Orbison",
        "Van Morrison",
        "Tom Waits",
        "Billy Joel",
        "Elton John",
        "Rod Stewart",
        "David Gilmour",
        "Robert Plant",
        "Jimmy Page",
        "Ozzy Osbourne",
        "Ronnie James Dio",
        "James Hetfield",
        "Eddie Van Halen",
        "Neil Peart",
        "Phil Collins",
        "Peter Gabriel",
        "Sting",
        "Mark Knopfler",
        "Sinead O’Connor",
        "Morrissey",
        "Bono",
        "Debbie Harry",
        "Joan Jett",
        "Siouxsie Sioux",
        "Beastie Boys",
        "Grandmaster Flash",
        "Run-DMC",
        "Tupac Shakur",
        "The Notorious B.I.G.",
        "Dr. Dre",
        "Snoop Dogg",
        "Nas",
        "Lauryn Hill",
        "The Beatles", "Elvis Presley", "Michael Jackson", "Madonna", "Prince",
        "David Bowie", "Queen", "Beyoncé", "Taylor Swift", "Kanye West",
        "Bob Dylan", "Led Zeppelin", "Pink Floyd", "The Rolling Stones",
        "Nirvana", "Radiohead", "Adele", "Drake", "Eminem", "Rihanna",
        "U2", "Bruce Springsteen", "Johnny Cash", "Whitney Houston",
        "Metallica", "Red Hot Chili Peppers", "Coldplay", "Ed Sheeran",
        "Daft Punk", "Foo Fighters", "The Who", "Fleetwood Mac",
        "AC/DC", "Black Sabbath", "Oasis", "Blur",
        "The Smiths", "Arctic Monkeys", "Linkin Park", "Green Day",
        "Bon Jovi", "Guns N' Roses", "ABBA", "Bee Gees",
        "The Beach Boys", "Stevie Wonder", "Frank Sinatra",
        ]


# -----------------------------
# Curated list (100 total)
# -----------------------------
TV_FILM = [
    "Tom Hanks", "Meryl Streep", "Leonardo DiCaprio", "Brad Pitt",
    "Angelina Jolie", "Johnny Depp", "Robert De Niro",
    "Al Pacino", "Scarlett Johansson", "Natalie Portman",
    "Morgan Freeman", "Denzel Washington", "Robert Downey Jr.",
    "Chris Hemsworth", "Chris Evans", "Jennifer Lawrence",
    "Anne Hathaway", "Keanu Reeves", "Will Smith",
    "Julia Roberts", "Sandra Bullock", "Harrison Ford",
    "Mark Hamill", "Carrie Fisher", "Hugh Jackman",
    "Christian Bale", "Matt Damon", "Ben Affleck",
    "George Clooney", "Daniel Craig", "Emma Watson",
    "Emma Stone", "Ryan Gosling", "Ryan Reynolds",
    "Benedict Cumberbatch", "Tom Cruise", "Samuel L. Jackson",
    "Bruce Willis", "Jack Nicholson", "Clint Eastwood",
    "Steven Spielberg", "Quentin Tarantino",
    "Martin Scorsese", "Alfred Hitchcock",
]

# -----------------------------
# Helpers
# -----------------------------
def get_wikipedia_image(title: str) -> str | None:

    url = "https://en.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "format": "json",
        "prop": "pageimages",
        "piprop": "thumbnail",
        "pithumbsize": 600,
        "titles": title,
    }

    headers = {
        "User-Agent": "TriviaOnTapBot/1.0 (contact: dave@example.com)"
    }

    r = requests.get(url, params=params, headers=headers, timeout=10)
    if r.status_code != 200:
        return None

    data = r.json()
    pages = data.get("query", {}).get("pages", {})
    page = next(iter(pages.values()), {})
    return page.get("thumbnail", {}).get("source")


def get_wikidata_image(title: str) -> str | None:

    """
    Uses Wikidata entity linked to the Wikipedia page to fetch P18 image.
    """

    url = "https://www.wikidata.org/w/api.php"

    params = {
        "action": "wbgetentities",
        "sites": "enwiki",
        "titles": title,
        "props": "claims",
        "format": "json",
    }

    headers = {
        "User-Agent": "TriviaOnTapBot/1.0 (contact: dave@example.com)"
    }

    r = requests.get(url, params=params, headers=headers, timeout=10)
    if r.status_code != 200:
        return None

    entities = r.json().get("entities", {})
    entity = next(iter(entities.values()), None)
    if not entity:
        return None

    claims = entity.get("claims", {})
    image_claim = claims.get("P18")
    if not image_claim:
        return None

    image_name = image_claim[0]["mainsnak"]["datavalue"]["value"]
    image_name = image_name.replace(" ", "_")

    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{image_name}"



def get_lastfm_artist_image(artist: str) -> str | None:

    url = "http://ws.audioscrobbler.com/2.0/"

    params = {
        "method": "artist.getinfo",
        "artist": artist,
        "api_key": LASTFM_API_KEY,
        "format": "json",
    }

    r = requests.get(url, params=params, timeout=10)
    if r.status_code != 200:
        return None

    data = r.json()
    images = data.get("artist", {}).get("image", [])
    for img in reversed(images):
        if img.get("#text"):
            return img["#text"]

    return None



def get_best_image(name: str, category: str) -> str | None:

    # 1. Wikipedia
    img = get_wikipedia_image(name)
    if img:
        return img

    # 2. Wikidata
    img = get_wikidata_image(name)
    if img:
        return img

    # 3. Last.fm (music only)
    if category == "Music":
        img = get_lastfm_artist_image(name)
        if img:
            return img

    return None


def insert_question(name, category):

    # CHECK IF QUESTION ALREADY EXISTS
    existing = supabase.table("questions").select("*").eq("question", f"Who is this a picture of?").eq("answer", name).execute().data
    if existing and len(existing) > 0:
        print(f"⚠️  Question for {name} already exists, skipping.")
        return

    image_url = get_best_image(name, category)

    if not image_url:
        print(f"⚠️  No image found for {name}, skipping.")
        return
    
    supabase.table("questions").insert({
        "question": "Who is this a picture of?",
        "answer": name,
        "category": category,
        "topic": TOPIC,
        "submitted_by": SUBMITTED_BY,
        "image_url": image_url,
        "upvotes": 0,
        "downvotes": 0,
    }).execute()

    print(f"✅ Added: {name} ({category})")


# -----------------------------85
# Main
# -----------------------------
def main():

    print("🎵 Seeding Music questions...")
    artists = get_20th_century_musicians()
    artists = list(set(artists))

    # load in additional artists from .csv file
    billboard_artists = set()
    with open("billboard_year_end_hot100_1960_2025.csv", "r", encoding="utf-8") as f:
        next(f)  # skip header
        for line in f:
            parts = line.strip().split(",")
            if len(parts) >= 4:
                artist = parts[4].strip('"')
                billboard_artists.add(artist)

    # add any billboard artists not already in the list
    for artist in billboard_artists:
        if artist not in artists:
            artists.append(artist)    

    for artist in artists:
        time.sleep(0.5)  # be polite to APIs
        insert_question(artist, "Music")

    print("🎬 Seeding TV & Film questions...")
    for person in TV_FILM:
        insert_question(person, "TV & Film")

    print("🎉 Done!")


if __name__ == "__main__":
    main()
