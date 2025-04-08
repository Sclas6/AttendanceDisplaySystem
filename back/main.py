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
import requests
import json

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

def fix_json(data_raw: requests.Response):
    """data = data_raw.json()
    data_fixed = dict()
    data_fixed["content"] = list()
    for d in data["results"]:
        user = dict()
        #print(data)
        user["name"] = d["properties"]["名前"]["title"][0]["text"]["content"]
        user["status"] = d["properties"]["区分"]["select"]["name"]
        time_str = d["properties"]["時間"]["date"]["start"] # Like '2024-11-11T11:45:00.000+09:00'
        user["time"] = datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.000+09:00")
        data_fixed["content"].append(user)"""
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

NOTION_ACCESS_TOKEN = 'secret_BwVBrA563VsRztJHEEhwck1Xtik5dg6fyOkTUv91hiS'
NOTION_DATABASE_ID = "1289f9f8038b809bbfe4c4087bf598f6"

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
    url = f"http://172.16.15.9:8000/v1/attendance"
    r = requests.get(url)
    data_fixed = fix_json(r)
    data_fixed = add_grade(data_fixed)
    
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
