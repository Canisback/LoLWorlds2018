
# coding: utf-8

# # Player Statistics

# Get the saved games

# In[1]:


import json, os
gamesRawData = []
for i in os.listdir("./games"):
    if i.endswith(".json"):
        with open("./games/"+i,"r") as f:
            gamesRawData.append(json.loads(f.read()))


# The rotation score is an experimental metric presentab by Doran's Lab : https://doranslab.gg/articles/location-based-champ-metrics.html

# In[2]:


import numpy as np
np.seterr(divide='ignore', invalid='ignore')

#Calculate the rotation score ffrom one position to another.
def getRotationScore(pos1, pos2, team):
    #Get the spawn point position as the base for the angle
    basePosition = np.array([394, 461]) if team==100 else np.array([14340, 14391])
    
    #Translate position to numpy array
    p1 = np.array([pos1["x"],pos1["y"]])
    p2 = np.array([pos2["x"],pos2["y"]])
    
    #Get the distance for both positions
    p1Distance = np.linalg.norm(p1-basePosition)
    p2Distance = np.linalg.norm(p2-basePosition)
    
    #Get the vector for both positions
    p1vec = p1 - basePosition
    p2vec = p2 - basePosition
    
    #Get the angle value of the two vectors
    cosine_angle = np.dot(p1vec,p2vec) / (np.linalg.norm(p1vec) * np.linalg.norm(p2vec))
    angle = np.arccos(cosine_angle) 
    
    #Return the rotation score, which is the mean distance multiplied by the angle value
    return (p1Distance+p2Distance)/2 * angle


#Get the player rotation score from 5 to 15 minutes
def getPlayerRotationScore(timeline, participantId, teamId):
    score = 0
    for i in range(6,16):
        score += getRotationScore(
            timeline["frames"][i]["participantFrames"][str(p["participantId"])]["position"],
            timeline["frames"][i-1]["participantFrames"][str(p["participantId"])]["position"],
            teamId
        )
    return score


# A simple function to get the role of a player. As it is esport format, it is possible to get them only by the position in the team.

# In[3]:


def getRole(participantId):
    if participantId in [1,6]:
        return "Toplaner"
    elif participantId in [2,7]:
        return "Jungler"
    elif participantId in [3,8]:
        return "Midlaner"
    elif participantId in [4,9]:
        return "ADC"
    elif participantId in [5,10]:
        return "Support"


# Parse all the games and get the player stats

# In[4]:


playersRows=[]

for game in gamesRawData:
    
    #Uncomment to filter playin games
    '''
    if game["gameCreation"]<1539122400000:
        continue
    '''
    #Count some stats of the team
    teamStats = {
        100:{"kills":0,"damagesToChampions":0,"damagesToTurrets":0,"gold":0},
        200:{"kills":0,"damagesToChampions":0,"damagesToTurrets":0,"gold":0}
    }
    for p in game["participants"]:
        teamStats[p["teamId"]]["kills"] += p["stats"]["kills"]
        teamStats[p["teamId"]]["damagesToChampions"] += p["stats"]["totalDamageDealtToChampions"]
        teamStats[p["teamId"]]["damagesToTurrets"] += p["stats"]["damageDealtToTurrets"]
        teamStats[p["teamId"]]["gold"] += p["stats"]["goldEarned"]
        
    pIdToName = {}
    #Player identities
    for p in game["participantIdentities"]:
        pIdToName[p["participantId"]] = p["player"]["summonerName"]
    
    
    for p in game["participants"]:
        #get player frame @15min
        playerFrame = game["timeline"]["frames"][15]["participantFrames"][str(p["participantId"])]
        opponentFrame = game["timeline"]["frames"][15]["participantFrames"][str((int(p["participantId"])+5)%10 if not p["participantId"]==5 else 10)]
        
        player={}
        #Player information
        player["team"], player["name"] = pIdToName[p["participantId"]].split(" ")
        player["role"] = getRole(p["participantId"])
        
        player["gameDuration"] = game["gameDuration"]
        
        #Add team stats
        player["teamKills"] = teamStats[p["teamId"]]["kills"]
        player["teamDamagesToChampions"] = teamStats[p["teamId"]]["damagesToChampions"]
        player["teamDamagesToTurrets"] = teamStats[p["teamId"]]["damagesToTurrets"]
        player["teamGold"] = teamStats[p["teamId"]]["gold"]
        
        #KDA stats
        player["kills"] = p["stats"]["kills"]
        player["deaths"] = p["stats"]["deaths"]
        player["assists"] = p["stats"]["assists"]
        
        #Damages stats
        player["damagesToChampions"] = p["stats"]["totalDamageDealtToChampions"]
        player["damagesToTurrets"] = p["stats"]["damageDealtToTurrets"]
        
        #Gold stats
        player["gold"] = p["stats"]["goldEarned"]
        player["gold@15"] = playerFrame["totalGold"]
        player["goldAdvantage@15"] = playerFrame["totalGold"] - opponentFrame["totalGold"]
        
        #Farm stats
        player["creepScore"] = p["stats"]["neutralMinionsKilled"] + p["stats"]["totalMinionsKilled"]
        player["CS@15"] = playerFrame["minionsKilled"] + playerFrame["jungleMinionsKilled"]
        player["CSAdvantage@15"] = playerFrame["minionsKilled"] + playerFrame["jungleMinionsKilled"] - (opponentFrame["minionsKilled"] + opponentFrame["jungleMinionsKilled"])
        
        #Vision score
        player["visionScore"] = p["stats"]["visionScore"]
        
        #Rotation score
        player["rotationScore"] = getPlayerRotationScore(game["timeline"],p["participantId"],p["teamId"])
        
        playersRows.append(player)


# Get the list of players to a dataframe

# In[5]:


import pandas as pd
dfPlayers = pd.DataFrame(playersRows)


# Add stats representing player share in the team

# In[6]:


dfPlayers["championDamagesPart"] = dfPlayers["damagesToChampions"] / dfPlayers["teamDamagesToChampions"]
dfPlayers["turretDamagesPart"] = dfPlayers["damagesToTurrets"] / dfPlayers["teamDamagesToTurrets"]
dfPlayers["KP"] = (dfPlayers["kills"] + dfPlayers["assists"])/ dfPlayers["teamKills"]


# Note that in this dataframe, each row is stats from a player from a specific game. To get average stats for each player, use the groupby function

# In[7]:


dfPlayersGrouped = dfPlayers.groupby(["name","team","role"]).mean().reset_index()


# KDA is not calculated as a mean, and needs to be done aside, using sums

# In[8]:


dfGroupedSummed = dfPlayers.groupby(["name","team"]).sum().reset_index()

dfPlayersGrouped["KDA"] = 0
dfPlayersGrouped.loc[dfGroupedSummed["deaths"]>0,"KDA"] = ((dfGroupedSummed.loc[dfGroupedSummed["deaths"]>0]["kills"] + dfGroupedSummed.loc[dfGroupedSummed["deaths"]>0]["assists"]) / dfGroupedSummed.loc[dfGroupedSummed["deaths"]>0]["deaths"])
#Handling the case when KDA is infinite (deaths=0)
dfPlayersGrouped.loc[dfGroupedSummed["deaths"]==0,"KDA"]=(dfGroupedSummed.loc[dfGroupedSummed["deaths"]==0]["kills"] + dfGroupedSummed.loc[dfGroupedSummed["deaths"]==0]["assists"])


# As this is the summary of the stats for each player, this is the one that will be exported to csv

# In[9]:


dfPlayersGrouped.to_csv("players.csv", index=False)