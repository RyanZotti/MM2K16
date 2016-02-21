import pymysql
import numpy as np
from Matrix import MatrixUpdater
from pandas import DataFrame, Series
from sklearn.grid_search import GridSearchCV
from sklearn.metrics import mean_squared_error
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import ElasticNet
con = pymysql.connect(host='localhost', unix_socket='/tmp/mysql.sock', user='root', passwd="", db='NCAABB')
mysql = con.cursor(pymysql.cursors.DictCursor)

'''
def get_teams():
    teams = {}
    for row in mysql.fetchall():
        team_id = row['team_id']
        team_name = row['team_name']
        teams[team_name] = team_id
    return teams
'''

def get_teams(season,day):
    team_to_index = {}
    index_to_team = {}
    mysql.execute("""
    select distinct team_id from
    (select wteam as team_id 
    from RegularSeasonDetailedResults_2016 
    where season = {season} and daynum < {day}
    union
    select lteam as team_id 
    from RegularSeasonDetailedResults_2016 
    where season = {season} and daynum < {day}) as tbl
    """.format(season=season,day=day))
    for row_index, row in enumerate(mysql.fetchall()):
        team = row['team_id']
        index_to_team[row_index]=team
        team_to_index[team]=row_index
    return (team_to_index,index_to_team)

def get_days(season):
    days = []
    mysql.execute("""
        select distinct daynum 
        from RegularSeasonDetailedResults_2016 
        where season = {season}""".format(season=season))
    for row in mysql.fetchall():
        days.append(row['daynum'])
    return days

def get_games(season,day):
    mysql.execute("""
        select wteam, lteam, wscore,lscore 
        from RegularSeasonDetailedResults_2016 
        where season = {season} and daynum < {day}""".format(season=season,day=day))
    games = []
    for row in mysql.fetchall():
        game = {'wteam':row['wteam'],
                'lteam':row['lteam'],
                'wscore':row['wscore'],
                'lscore':row['lscore']}
        games.append(game)
    return games
    
for season in range(1985,2016):
    days = get_days(season)
    for day_index, day_id in enumerate(days):
        team_to_index,index_to_team = get_teams(season,day_id)
        matrix = np.zeros((len(team_to_index),len(team_to_index)))
        target_col = np.zeros(len(team_to_index))
        games = get_games(season,day_id)
        matrix_updater = MatrixUpdater("simple_mov")
        if day_index > 0:
            matrix = matrix_updater.update_matrix(matrix,target_col,games,team_to_index)
            parameters = [{'alpha':np.arange(0.3,1,0.1),'l1_ratio':np.arange(0.1,1,0.1)}]
            model = GridSearchCV(ElasticNet(), parameters,n_jobs=8)
            training = DataFrame(matrix)
            training['target']=Series(target_col)
            predictor_set = [team_id for team_id in index_to_team.keys()]
            model.fit(training[predictor_set], training['target'])
            training['pred']=model.predict(training[predictor_set])
            model_mae = np.mean(np.abs(training['target']-training['pred']))
            print(model_mae)
            print()
        print()    
            
print("Finished.")
