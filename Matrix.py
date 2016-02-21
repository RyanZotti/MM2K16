class MatrixUpdater:
    
    update_type = "simple_mov"
    
    def update_matrix(self,matrix,target_col,games,team_to_index):
        if self.update_type == "simple_mov":
            matrix = self.simple_mov_updater(matrix,target_col,games,team_to_index)
        else:
            matrix = self.simple_mov_updater(matrix,target_col,games,team_to_index)
        return matrix
    
    def simple_mov_updater(self,matrix,target_col,games,team_to_index):
        for team_index in range(len(matrix)):
            matrix[team_index][team_index]=1
        for game in games:
            mov = game['wscore']-game['lscore']
            w_index = team_to_index[game['wteam']]
            l_index = team_to_index[game['lteam']]
            matrix[w_index][l_index]+=1
            matrix[l_index][w_index]+=1
            target_col[w_index]+=mov
            target_col[l_index]+=-1*mov
        # things = [game['wscore']-game['lscore'] for game in games]
        return matrix,target_col
    
    def __init__(self,update_type):
        update_type = update_type