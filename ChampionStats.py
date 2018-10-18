
# coding: utf-8

# # Champions general statistics

# Get the saved games data

# In[1]:


import json, os
gamesRawData = []
for i in os.listdir("./games"):
    if i.endswith(".json"):
        with open("./games/"+i,"r") as f:
            gamesRawData.append(json.loads(f.read()))


# Initialize the champion stats data structure.

# In[2]:


import requests

response = requests.get('http://ddragon.leagueoflegends.com/cdn/8.19.1/data/en_US/champion.json')
champonRawData = json.loads(response.text)

championsStats = {}
for key,champion in champonRawData['data'].items():
    championsStats[int(champion['key'])] = {
                    "champion":champion['name'],
                    "games":0,
                    "gamesPlayed":0,
                    "wins":0,
                    "teamKills":0,
                    "kills":0,
                    "deaths":0,
                    "assists":0,
                    "bans":0
                }


# Parse all the games to get statistics by champion

# In[3]:


for game in gamesRawData:
    #Count the champion bans
    for t in game["teams"]:
        for b in t["bans"]:
            championsStats[b["championId"]]["bans"] += 1
            championsStats[b["championId"]]["games"]+=1
    
    #Count the kills of the team to later get the kill participation
    teamKills = {100:0,200:0}
    for p in game["participants"]:
        teamKills[p["teamId"]] += p["stats"]["kills"]
    
    #Count the wins and basic stats like kills, deaths and assits
    for p in game["participants"]:
        championsStats[p["championId"]]["games"]+=1
        championsStats[p["championId"]]["gamesPlayed"]+=1
        if p["stats"]["win"]:
            championsStats[p["championId"]]["wins"] += 1
        
        championsStats[p["championId"]]["teamKills"] += teamKills[p["teamId"]]
        championsStats[p["championId"]]["kills"] += p["stats"]["kills"]
        championsStats[p["championId"]]["deaths"] += p["stats"]["deaths"]
        championsStats[p["championId"]]["assists"] += p["stats"]["assists"]


# We make a difference between games and gamesPlayed where games counts every game where the champion has been either played or banned.

# Use pandas Dataframe to manipulate the data

# In[4]:


import pandas as pd, numpy as np
df = pd.DataFrame(championsStats).T

#Get the winrate for each champion
#wr is the raw winrate
df["wr"] = 0
df.loc[df["gamesPlayed"]>0,"wr"] = df.loc[df["gamesPlayed"]>0]["wins"]/df.loc[df["gamesPlayed"]>0]["gamesPlayed"]
#winrate is the beautified winrate
df["winrate"] = (df["wr"] * 100).map('{:,.2f}'.format).apply(lambda s: str(s)+"%")

#Get the KDA
df["KDA"] = 0
df.loc[df["deaths"]>0,"KDA"] = ((df.loc[df["deaths"]>0]["kills"] + df.loc[df["deaths"]>0]["assists"]) / df.loc[df["deaths"]>0]["deaths"])
#Handling the case when KDA is infinite (deaths=0)
df.loc[df["deaths"]==0,"KDA"]=(df.loc[df["deaths"]==0]["kills"] + df.loc[df["deaths"]==0]["assists"])
#Beautify KDA
df["KDA"] = df["KDA"].map('{:,.2f}'.format)

#Get kill participation and beautify it
df["KP"] = 0
df.loc[df["teamKills"]>0,"KP"] = (((df.loc[df["teamKills"]>0]["kills"] + df.loc[df["teamKills"]>0]["assists"]) / df.loc[df["teamKills"]>0]["teamKills"]) * 100).map('{:,.2f}'.format).apply(lambda s: str(s)+"%")


# Exporting the data to csv

# In[6]:


df.index.name='championId'
df.to_csv("champion.csv")
