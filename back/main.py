import datetime
import os
import matplotlib
import matplotlib.pyplot as plt
import japanize_matplotlib
import pandas as pd
from pathlib import Path
import pickle
import uuid
from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import multiprocessing
import json
import websockets
import asyncio
import uvicorn
import asyncio
import json
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials
import requests
import schedule

matplotlib.use('Agg')

class User():
    def __init__(self, name: str, status: str) -> None:
        self.name = name
        self.total = pd.DataFrame()
        self.status_now = status
        self.elapsed = datetime.timedelta()
        
    def set_status(self, status: str):
        self.status_last = self.status_now
        self.status_now = status
        now = datetime.datetime.now()
        if (self.status_now == "break_out" and self.status_last == "break_in") or (self.status_now == "clock_in" and self.status_last == "clock_out"):
            self.last_regester = now
        try:
            self.last_regester
        except Exception as _:
            self.last_regester = datetime.datetime.now()
        if f"{now.month}/{now.day}" not in self.total.index:
            df_newline = pd.DataFrame([0.0], index=[f"{now.month}/{now.day}"], columns=["elapsed"])
            self.total = pd.concat([self.total, df_newline])
            self.last_regester = datetime.datetime.now()
            self.elapsed = datetime.timedelta()
        if (self.status_now == "clock_in" or self.status_now == "break_out"):
            self.elapsed += now - self.last_regester
            self.total.loc[f"{now.month}/{now.day}"] = self.elapsed / datetime.timedelta(seconds=1)
        elif (self.status_now == "break_in" and self.status_last == "clock_in") or (self.status_now == "clock_out" and (self.status_last == "clock_in") or (self.status_last == "break_out")):
            self.elapsed += now - self.last_regester
            self.total.loc[f"{now.month}/{now.day}"] = self.elapsed / datetime.timedelta(seconds=1)
        self.last_regester = now

def gen_graph(df):
    filename = uuid.uuid4()
    yticks = ["00:00", "01:00", "02:00", "03:00", "04:00", "05:00", "06:00", "07:00", "08:00", "09:00", "10:00", "11:00", "12:00"]
    plt.cla()
    df_last30 = df.tail(30)
    df_last30.plot.bar()
    sum_elapsed = df_last30.cumsum().iat[-1, 0] / 3600
    plt.title(f'総clock_in時間: {sum_elapsed:.2f}時間\n平均勤務時間: {sum_elapsed/len(df_last30):.2f}時間\n\n過去30日間のclock_in時間')
    plt.xlabel("日付")
    plt.ylabel("時間")
    plt.yticks([i * 3600 for i in range(13)], yticks)
    plt.legend(["clock_in時間"])
    plt.tight_layout()
    plt.savefig(f"graphs/{filename}.png")
    plt.close()
    max_file=10
    paths = list(Path('.').glob(r'graphs/*.png'))
    paths.sort(key=os.path.getmtime)
    if len(paths) > max_file:
        for i in range(5):
            os.remove(f"graphs/{paths[i].name}")
    return filename

def fix_json(data_raw: dict):
    users = json.load(open("users.json", 'r'))
    grade_dict = {user["name"]: user["grade"] for user in users["users"]}
    
    if not os.path.exists("data.json"):
        data = dict()
        data["content"] = list()
    else:
        data = json.load(open("data.json", 'r'))
    user = data_raw
    if user["name"][0] == ' ':
        user["name"] = user["name"][1:]
    if user["name"] in grade_dict.keys():
        user["grade"] = grade_dict[user["name"]]
    else:
        user["grade"] = "UNKNOWN"
        
    updated = False
    for i, d in enumerate(data["content"]):
        if d["name"] == user["name"]:
            data["content"][i] = user
            updated = True
    if not updated:
        data["content"].append(user)

    with open("data.json", 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    return data

def fix_full_json(data_raw: requests.Response):
    data = data_raw.json()
    data_fixed = dict()
    data_fixed["content"] = list()
    for d in data["data"]:
        if d["name"][0] == ' ':
            d["name"] = d["name"][1:]
        data_fixed["content"].append(d)
    return data_fixed

def add_grade(data_fixed):
    users = json.load(open("users.json", 'r'))
    grade_dict = {user["name"]: user["grade"] for user in users["users"]}
    for user in data_fixed["content"]:
        if user["name"] in grade_dict.keys():
            user["grade"] = grade_dict[user["name"]]
        else:
            user["grade"] = "UNKNOWN"
    return data_fixed
 
def update():
    url = f"http://172.16.15.9:8000/v1/attendance"
    r = requests.get(url)
    data_fixed = fix_full_json(r)
    data_fixed = add_grade(data_fixed)
    with open("data.json", 'w') as f:
        json.dump(data_fixed, f, indent=2, ensure_ascii=False)

app = FastAPI()
origins = [
    "http://172.16.15.7:3000",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/items/{path}", responses={200:{"content":{"image/png": {}}}}, response_class=Response)
async def read_items(path):
    print(path)
    if os.path.exists(f"graphs/{path}"):
        return FileResponse(f"graphs/{path}")
    else: return "ERROR"
    
@app.get("/update/{user}")
async def update_graph(user):
    if not os.path.exists("users.pkl"):
        users = dict()
        with open("users.pkl", "wb") as f:
            pickle.dump(users, f)
    else:
        with open("users.pkl", "rb") as f:
            users = pickle.load(f)
    if user not in users:
        return "ERROR NO USER FOUND"
    else:
        filename = gen_graph(users[user].total)
        return {"url": f"http://172.16.15.7:8000/items/{filename}.png"}


@app.get("/")
def Hello():
    data_fixed = json.load(open("data.json", 'r'))
    
    if not os.path.exists("users.pkl"):
        users = dict()
        with open("users.pkl", "wb") as f:
            pickle.dump(users, f)
    else:
        with open("users.pkl", "rb") as f:
            users = pickle.load(f)

    for user in data_fixed["content"]:
        if user["name"] not in users:
            users[user["name"]] = User(user["name"], user["status"])
        users[user["name"]].set_status(user["status"])

    with open("users.pkl", "wb") as f:
        pickle.dump(users, f)
    
    return data_fixed


async def client():
    access_key=os.environ.get("ACCESS_KEY")
    secret_key=os.getenv("SECRET_KEY")
    resource_id=os.getenv("RESOURCE_ID")
    service_name="execute-api"
    region_name="ap-northeast-1"
    x_api_key=os.getenv("X_API_KEY")
    
    host = f"{resource_id}.{service_name}.{region_name}.amazonaws.com"
    credentials = Credentials(access_key=access_key, secret_key=secret_key)
    url     = f"wss://{host}/v1/"
    request = AWSRequest(method="GET", url=url)
    SigV4Auth(credentials, service_name, region_name).add_auth(request)
    uri = request.url
    
    headers = {
        "X-Api-Key": x_api_key
    }
 
    while True:
        try:
            async with websockets.connect(uri, additional_headers=headers) as ws:
                print("WebSocket connected.")
                while True:
                    msg = await ws.recv()
                    fix_json(json.loads(msg))
                    print(msg)
                
        except websockets.ConnectionClosed:
            continue

def run_uvicorn():
    uvicorn.run("main:app", host="172.16.15.7", port=8000)

def run_asyncio():
    asyncio.run(client())

if __name__ == "__main__":
    update()
    schedule.every().hour.do(update)
    
    process_uvicorn = multiprocessing.Process(target=run_uvicorn)
    process_asyncio = multiprocessing.Process(target=run_asyncio)

    process_uvicorn.start()
    process_asyncio.start()

