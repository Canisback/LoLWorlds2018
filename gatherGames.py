import requests, json, os

urlTournament="http://api.lolesports.com/api/v1/scheduleItems?leagueId=9"
r  = requests.get(urlTournament)
rawTournamentData = json.loads(r.text)

tournamentId = rawTournamentData['highlanderTournaments'][3]["id"]

#Get the bracket for Worlds 2018
brackets = rawTournamentData['highlanderTournaments'][3]["brackets"]

matches = []
games = {}

#Get the list of matches and each of their games
for bracketId in brackets:
    bracket = brackets[bracketId]
    
    for matchId in bracket["matches"]:
        match = bracket["matches"][matchId]
        
        for gameUuid in match['games']:
            
            game = match['games'][gameUuid]
            
            if 'gameId' in game:
                games[gameUuid] = {"matchHistoryId":game['gameId'], "matchId":matchId, "realm":game["gameRealm"], "phase":bracket["groupName"]}
                
                
if os.path.isdir("./games"):
    gamesSaved = [f.split(".")[0] for f in os.listdir("./games")]
else:
    os.makedirs("./games")
    gamesSaved=[]
    
matches = [games[gameUuid]["matchId"] for gameUuid in games if gameUuid not in gamesSaved]

baseMatchUrl = "http://api.lolesports.com/api/v2/highlanderMatchDetails?tournamentId="+tournamentId+"&matchId="

for matchId in matches:
    r  = requests.get(baseMatchUrl + matchId)
    matchData = json.loads(r.text)
    for i in matchData["gameIdMappings"]:
        try:
            games[i["id"]]["hash"] = i["gameHash"]
        except:
            print("Game "+str(i["id"]) + "has no hash")
            
baseMatchHistoryStatsUrl = "https://acs.leagueoflegends.com/v1/stats/game/{}/"

for gameUuid in games:
    if gameUuid in gamesSaved:
        continue
    try:
        
        r  = requests.get(baseMatchHistoryStatsUrl.format(games[gameUuid]["realm"]) + games[gameUuid]["matchHistoryId"] + "?gameHash="+ games[gameUuid]["hash"])
        if r.status_code == 200:
            gameData = json.loads(r.text)
            gameData["phase"] = games[gameUuid]["phase"]
            r = requests.get(baseMatchHistoryStatsUrl.format(games[gameUuid]["realm"]) + games[gameUuid]["matchHistoryId"] + "/timeline?gameHash="+ games[gameUuid]["hash"])
            if r.status_code == 200:
                gameData["timeline"] = json.loads(r.text)

                with open("./games/"+gameUuid+".json","w") as file:
                    file.write(json.dumps(gameData))
        else:
            print("Game "+gameUuid+" code error: "+str( r.status_code))
    except:#for games ongoing
        pass