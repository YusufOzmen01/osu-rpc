import threading
import json
import pypresence
import requests
import time

print("Connecting to rpc...")
RPC = pypresence.Presence('1035256182253830204')
RPC.connect()
print("Connected to the rpc")

start = None
last = 0
last_change = None
last_state = -1
last_state_change = 999999999999
paused = False

config = json.load(open("config.json", "r"))
username = requests.get("https://osu.ppy.sh/api/get_user?k={}&u={}&type=u".format(config["osu_token"], config["osu_id"])).json()[0]["username"]

last_update = 0

gamemodes = [
    {
        "name": "osu!",
        "image": "osu_std"
    },
    {
        "name": "osu!taiko",
        "image": "osu_taiko"
    },
    {
        "name": "osu!catch",
        "image": "osu_catch"
    },
    {
        "name": "osu!mania",
        "image": "osu_mania"
    }
]

def update_paused():
    global paused
    global last
    
    while True:
        try:
            msg = requests.get("http://127.0.0.1:24050/json").json()

            if last == msg["menu"]["bm"]["time"]["current"]:
                paused = True
            else:
                last = msg["menu"]["bm"]["time"]["current"]

                paused = False
        
            time.sleep(0.5)
        except:
            print("Error in pause thread")

def get_user_status():
    global config

    user = requests.get("https://osu.ppy.sh/api/get_user?k={}&u={}&type=u".format(config["osu_token"], config["osu_id"])).json()
            
    username = user[0]["username"]
    rank = int(user[0]["pp_rank"])

    return f"{username} (rank #{rank:,d})"

threading.Thread(target=update_paused).start()

while True:
    try:
        time.sleep(0.5)
        message = requests.get("http://127.0.0.1:24050/json").json()

        match message["menu"]["state"]:
            case 0:
                if last_state != 0:
                    last_state = 0
                    last_state_change = time.time()

                start = None
                status = ""

                if time.time()-last_state_change > 60:
                    status = "(AFK)"

                if paused:
                    s = "Idle"
                    if status != "":
                        s = "AFK"
                    
                    RPC.update(
                        state=s, 
                        large_image="osu_logo", 
                        large_text=get_user_status(), 
                        small_image=gamemodes[message["gameplay"]["gameMode"]]["image"], 
                        small_text=gamemodes[message["gameplay"]["gameMode"]]["name"]
                    )

                    continue
                RPC.update(
                    details=f"{status} " + "Listening to {}".format(message["menu"]["bm"]["metadata"]["title"]), 
                    state="by {}".format(message["menu"]["bm"]["metadata"]["artist"]),
                    large_image="https://assets.ppy.sh/beatmaps/{}/covers/list@2x.jpg".format(message["menu"]["bm"]["set"]), 
                    large_text=get_user_status(), 
                    small_image=gamemodes[message["gameplay"]["gameMode"]]["image"], 
                    small_text=gamemodes[message["gameplay"]["gameMode"]]["name"]
                )
            case 1:
                start = None
                if last_state != 0:
                    last_state = 0
                    RPC.update(state="Editing your ass", large_image="osu_logo", large_text=get_user_status(), small_image=gamemodes[message["gameplay"]["gameMode"]]["image"], small_text=gamemodes[message["gameplay"]["gameMode"]]["name"])
            case 2:
                if start is None or last < message["menu"]["bm"]["time"]["current"]:
                    start = time.time()*1000

                if paused:
                    if last_change is None:
                        last_change = time.time()
                    
                    start = start + time.time()-last_change
                    last_change = time.time()

                    if last_state != 999:
                        RPC.update(
                            state="Paused",
                            details="{} [{}] - {}".format(message["menu"]["bm"]["metadata"]["title"], message["menu"]["bm"]["metadata"]["difficulty"], message["menu"]["mods"]["str"]), 
                            large_image="https://assets.ppy.sh/beatmaps/{}/covers/list@2x.jpg".format(message["menu"]["bm"]["set"]),
                            large_text=get_user_status(),
                            small_image="https://i.imgur.com/UHbb178.png",
                            small_text="Paused"
                        )
                        last_state = 999
                else:
                    last_change = None

                    if last_state != 2:
                        mul = 1

                        if "DT" in  message["menu"]["mods"]["str"] or "NC" in  message["menu"]["mods"]["str"]:
                            mul = 0.8

                        if message["gameplay"]["name"] != username:
                            RPC.update(
                                details="{} [{}]".format(message["menu"]["bm"]["metadata"]["title"], message["menu"]["bm"]["metadata"]["difficulty"]), 
                                state="Spectating {}".format(message["gameplay"]["name"]),
                                large_image="https://assets.ppy.sh/beatmaps/{}/covers/list@2x.jpg".format(message["menu"]["bm"]["set"]),
                                large_text=get_user_status(),
                                small_image=gamemodes[message["gameplay"]["gameMode"]]["image"],
                                small_text=gamemodes[message["gameplay"]["gameMode"]]["name"]
                            )

                            continue

                        RPC.update(
                            state="{} [{}] - {}".format(message["menu"]["bm"]["metadata"]["title"], message["menu"]["bm"]["metadata"]["difficulty"], message["menu"]["mods"]["str"]), 
                            large_image="https://assets.ppy.sh/beatmaps/{}/covers/list@2x.jpg".format(message["menu"]["bm"]["set"]),
                            large_text=get_user_status(),
                            start=start+message["menu"]["bm"]["time"]["current"],
                            end=start+int(message["menu"]["bm"]["time"]["mp3"]*mul),
                            small_image=gamemodes[message["gameplay"]["gameMode"]]["image"],
                            small_text=gamemodes[message["gameplay"]["gameMode"]]["name"]
                        )
                        last_state = 2
            case 4:
                start = None
                if time.time()-last_state_change > 60:
                    RPC.update(
                        state="AFK", 
                        large_image="osu_logo", 
                        large_text=get_user_status(), 
                        small_image=gamemodes[message["gameplay"]["gameMode"]]["image"], 
                        small_text=gamemodes[message["gameplay"]["gameMode"]]["name"]
                    )

                    last_state_change = 999999999999

                if last_state != 0:
                    last_state = 0
                    last_state_change = time.time()

                    status = "Idle"
                    if time.time()-last_state_change > 60:
                        status = "AFK"
                    RPC.update(
                        state="Idle", 
                        large_image="osu_logo", 
                        large_text=get_user_status(), 
                        small_image=gamemodes[message["gameplay"]["gameMode"]]["image"], 
                        small_text=gamemodes[message["gameplay"]["gameMode"]]["name"]
                    )
            case 5:
                start = None
                if time.time()-last_state_change > 60:
                    RPC.update(
                        state="AFK", 
                        large_image="osu_logo", 
                        large_text=get_user_status(), 
                        small_image=gamemodes[message["gameplay"]["gameMode"]]["image"], 
                        small_text=gamemodes[message["gameplay"]["gameMode"]]["name"]
                    )

                    last_state_change = 999999999999

                if last_state != 5:
                    last_state = 5
                    last_state_change = time.time()

                    status = "Idle"
                    if time.time()-last_state_change > 60:
                        status = "AFK"
                    RPC.update(
                        state="Idle", 
                        large_image="osu_logo", 
                        large_text=get_user_status(), 
                        small_image=gamemodes[message["gameplay"]["gameMode"]]["image"], 
                        small_text=gamemodes[message["gameplay"]["gameMode"]]["name"]
                    )
            case 7:
                last_change = None

                if last_state != 7:
                    RPC.update(
                        details="{} [{}]".format(message["menu"]["bm"]["metadata"]["title"], message["menu"]["bm"]["metadata"]["difficulty"]), 
                        state="Checking the score of {}".format(message["resultsScreen"]["name"]),
                        large_image="https://assets.ppy.sh/beatmaps/{}/covers/list@2x.jpg".format(message["menu"]["bm"]["set"]),
                        large_text=get_user_status(),
                        small_image=gamemodes[message["gameplay"]["gameMode"]]["image"],
                        small_text=gamemodes[message["gameplay"]["gameMode"]]["name"]
                    )
                    last_state = 7
            case 11:
                start = None
                if last_state != 0:
                    start = None
                if time.time()-last_state_change > 60:
                    RPC.update(
                        state="AFK", 
                        large_image="osu_logo", 
                        large_text=get_user_status(), 
                        small_image=gamemodes[message["gameplay"]["gameMode"]]["image"], 
                        small_text=gamemodes[message["gameplay"]["gameMode"]]["name"]
                    )

                    last_state_change = 999999999999

                if last_state != 0:
                    last_state = 0
                    last_state_change = time.time()

                    status = "Idle"
                    if time.time()-last_state_change > 60:
                        status = "AFK"
                    RPC.update(state="Looking for a lobby", large_image="osu_logo", large_text=get_user_status(), small_image=gamemodes[message["gameplay"]["gameMode"]]["image"], small_text=gamemodes[message["gameplay"]["gameMode"]]["name"])
                   
            case 12:
                start = None
                if last_state != 0:
                    start = None
                if time.time()-last_state_change > 60:
                    RPC.update(
                        state="AFK", 
                        large_image="osu_logo", 
                        large_text=get_user_status(), 
                        small_image=gamemodes[message["gameplay"]["gameMode"]]["image"], 
                        small_text=gamemodes[message["gameplay"]["gameMode"]]["name"]
                    )

                    last_state_change = 999999999999

                if last_state != 0:
                    last_state = 0
                    last_state_change = time.time()

                    status = "Idle"
                    if time.time()-last_state_change > 60:
                        status = "AFK"
                    RPC.update(state="Idling in a multiplayer lobby", large_image="osu_logo", large_text=get_user_status(), small_image=gamemodes[message["gameplay"]["gameMode"]]["image"], small_text=gamemodes[message["gameplay"]["gameMode"]]["name"])
    except:
        print("Error")