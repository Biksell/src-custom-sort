from speedruncompy.endpoints import GetUserLeaderboard, GetUserSummary, GetGameSummary
import requests, time

PHPSESSID = ""
userUrl = ""
gameUrls = []
delay = 5


with open("config.txt", "r") as f:
    for line in f.readlines():
        if line.startswith("PHPSESSID"):
            PHPSESSID = line.split("=")[1].strip()
        elif line.startswith("USER"):
            userUrl = line.split("=")[1].strip()
        elif line.startswith("GAMES"):
            gameUrls = line.split("=")[1].strip().split(",")
        elif line.startswith("DELAY"):
            delay = int(line.split("=")[1].strip())

if not PHPSESSID or not userUrl or not gameUrls:
    print(f"{time.ctime()}: Config not loaded, exiting")
    input()

print(f"{time.ctime()}: Config loaded for {userUrl} with games: {gameUrls}")

apiUrl = "https://www.speedrun.com/api"

summary = GetUserSummary(url=userUrl).perform()
userId = summary["user"]["id"]

print(f"{time.ctime()}: User ID fetched for user {userUrl}: {userId}")

print(f"{time.ctime()}: Fetching game IDs for games")

try:
    bottom_gameIds = [GetGameSummary(gameUrl=url).perform()["game"]["id"] for url in gameUrls]
except Exception as e:
    print(str(e))
    print(f"{time.ctime()}: Error fetching game IDs, exiting")
    input()

print(f"{time.ctime()}: Game IDs fetched: {bottom_gameIds}")

old_runs = 0

while True:
    print(f"{time.ctime()}: Fetching user leaderboard")
    lb = GetUserLeaderboard(userId=userId).perform()

    # Normal order is ascending, reverse for descending
    runs = lb.get("runs", [])
    if old_runs == len(runs):
        print(f"{time.ctime()}: No new runs found, sleeping for {delay} minutes")
        time.sleep(delay * 60)
        continue
    print(f"{time.ctime()}: Found {len(runs) - old_runs} new runs")
    old_runs = len(runs)
    print(f"{time.ctime()}: Sorting runs")
    runs = sorted(runs, key=lambda run: run["date"], reverse=True)

    print(f"{time.ctime()}: Filtering out obsoletes")
    # Filter out obsoletes
    filtered_runs = [run for run in runs if not run.get("obsolete", False)]

    print(f"{time.ctime()}: Filtering out duplicate games")
    # Filter out duplicates using set()
    gameIds = [run["gameId"] for run in filtered_runs]
    filtered_gameIds = []
    for id in gameIds:
        if id not in filtered_gameIds:
            filtered_gameIds.append(id)


    print(f"{time.ctime()}: Placing games to the end")
    # Remove Quiplash and Quiplash2
    for gameId in bottom_gameIds:
        filtered_gameIds.remove(gameId)

    # Add them to the end
    for gameId in bottom_gameIds:
        filtered_gameIds.append(gameId)

    params = {
        "groups":
            [
                {
                    "editing": "false",
                    "gameIds": filtered_gameIds,
                    "id": "default",
                    "name": "Ungrouped",
                    "open": "true",
                    "sortType": 2
                }
            ],
        "userUrl": userUrl
        }

    headers = {
        "Accept": "application/json",
        "Accept-Language": "en-GB,en;q=0.5",
        "Content-Type": "application/json",
        "Cookie": f"PHPSESSID={PHPSESSID}"
    }

    # Update order
    print(f"{time.ctime()}: Posting game order update")
    response = requests.post(url=f"{apiUrl}/v2/PutUserUpdateGameOrdering", json=params, headers=headers)
    if response.status_code == 200:
        print(f"{time.ctime()}: Game order updated successfully")
    else:
        print(f"{time.ctime()}: {response.status_code}: {response.content}")
    print(f"{time.ctime()}: Sleeping for {delay} minutes")
    time.sleep(delay * 60)
