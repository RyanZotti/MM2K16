import pymysql
import numpy as np
from Matrix import MatrixUpdater
from pandas import DataFrame, Series
from sklearn.grid_search import GridSearchCV
from sklearn.metrics import mean_squared_error
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, ElasticNet
con = pymysql.connect(host='localhost', unix_socket='/tmp/mysql.sock', user='root', passwd="", db='NCAABB')
mysql = con.cursor(pymysql.cursors.DictCursor)

# Interview with 2014 winners: http://blog.kaggle.com/2014/04/21/qa-with-gregory-and-michael-1st-place-in-march-ml-mania/

def target_day_teams(season,day):
    mysql.execute("""
    select daynum, wteam, lteam, wscore,lscore 
    from RegularSeasonCompactResult_2016 
    where season = {season} and daynum = {day}
    """.format(season=season,day=day))
    target_teams = []
    for row in mysql.fetchall():
        target_teams.append(row['wteam'])
        target_teams.append(row['lteam'])
    return target_teams
        
def get_teams(season,day):
    team_to_index = {}
    index_to_team = {}
    mysql.execute("""
    select distinct team_id from
    (select wteam as team_id 
    from RegularSeasonCompactResult_2016 
    where season = {season} and daynum < {day}
    union
    select lteam as team_id 
    from RegularSeasonCompactResult_2016 
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
        from RegularSeasonCompactResult_2016 
        where season = {season}""".format(season=season))
    for row in mysql.fetchall():
        days.append(row['daynum'])
    return days

def get_games(season,day):
    mysql.execute("""
        select wteam, lteam, wscore,lscore 
        from RegularSeasonCompactResult_2016 
        where season = {season} and daynum < {day}""".format(season=season,day=day))
    games = []
    for row in mysql.fetchall():
        game = {'wteam':row['wteam'],
                'lteam':row['lteam'],
                'wscore':row['wscore'],
                'lscore':row['lscore']}
        games.append(game)
    return games
    
def build_model(model_type,training):
    if model_type == "Elastic Net":
        parameters = [{'alpha':np.arange(0.3,1,0.1),'l1_ratio':np.arange(0.1,1,0.1)}]
        model = GridSearchCV(ElasticNet(), parameters,n_jobs=8)
        model.fit(training[predictor_set], training['target'])
        return model.best_estimator_
    elif model_type == "Linear Regression":
        model = LinearRegression().fit(training[predictor_set], training['target'])
        return model
    
for season in range(2015,2016):
    days = get_days(season)
    for day_index, day_id in enumerate(days):
        team_to_index,index_to_team = get_teams(season,day_id)
        matrix = np.zeros((len(team_to_index),len(team_to_index)))
        target_col = np.zeros(len(team_to_index))
        games = get_games(season,day_id)
        matrix_updater = MatrixUpdater("simple_mov")
        if day_index > 5:
            matrix,target_col = matrix_updater.update_matrix(matrix,target_col,games,team_to_index)
            training = DataFrame(matrix)
            training['target']=Series(target_col)
            predictor_set = [team_id for team_id in index_to_team.keys()]
            model = build_model("Elastic Net",training)
            training['pred']=model.predict(training[predictor_set])
            model_mae = np.mean(np.abs(training['target']-training['pred']))
            target_teams = target_day_teams(season,day_id)
            coeffs = model.coef_
            for team in target_teams:
                # Only enter teams with a rating available (i.e., teams not playing for the first time)
                if team in team_to_index:
                    rating = coeffs[team_to_index[team]]
                    mysql.execute("""insert into SimpleRating(season, target_day, target_day_index, team_id, rating) values("{season}","{target_day}","{target_day_index}","{team_id}","{rating}")""".format(season=season,target_day=day_id,target_day_index=day_index,team_id=team,rating=rating))
                    con.commit()
            #print(model_mae)
            print(day_index)
    print(season)
            
print("Finished.")
