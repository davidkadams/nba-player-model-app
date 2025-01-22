import math
import pandas as pd
from nba_api.stats.endpoints import playercareerstats, gamerotation
from nba_api.stats.endpoints import leaguedashteamstats
from nba_api.stats.static import teams
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players


# Hashmap of all teams with ids, and abbreviations.
all_teams = teams.get_teams()
team_map = {team['id']: team['abbreviation'] for team in all_teams}

# NBAPlayer Class
# Builds a Player given a First and Last Name in a string
# Builds the player's season stats
class NBAPlayer:

    # builds a dictionary of team related info based on the given player id
    @staticmethod
    def get_player_team_info_api_call(player_id):

        team_info_dict = {}

        player_stats_dfs_list = playercareerstats.PlayerCareerStats(player_id=player_id).get_data_frames()
        player_career_stats_main_df = player_stats_dfs_list[0].iloc[::-1].reset_index(drop=True)
        # print(tabulate(player_career_stats_main_df, headers='keys'))

        career_season_ids = player_career_stats_main_df['SEASON_ID'].to_list()
        career_team_ids = player_career_stats_main_df['TEAM_ID'].to_list()
        career_team_names = player_career_stats_main_df['TEAM_ABBREVIATION'].to_list()

        current_season_id = career_season_ids[0]

        current_team_id = career_team_ids[0]
        current_team_name = career_team_names[0]
        former_team_names = []

        # the threshold to check for a team being 'recent'
        RECENT_YEAR_CAP = 4

        for i in range(0, min(RECENT_YEAR_CAP, len(career_team_names))):
            name = career_team_names[i]
            # print(name)
            if name != current_team_name and name not in former_team_names:
                former_team_names.append(name)

        team_info_dict['current_team_id'] = current_team_id
        team_info_dict['current_team_name'] = current_team_name
        team_info_dict['former_team_names'] = former_team_names
        team_info_dict['current_season_id'] = current_season_id

        return team_info_dict

    def __init__(self, player_name):
        self.player_name = player_name
        # player's id
        self.player_id = self.get_player_id()

        # call the API once and build a dictionary off of player's team info
        team_info_dict = self.get_player_team_info_api_call(self.player_id)

        self.player_team_id = team_info_dict.get('current_team_id')
        # abbreviation name of players current team
        self.player_team_name = team_info_dict.get('current_team_name')
        # a list of previous team names
        self.player_former_team_names = team_info_dict.get('former_team_names')
        # players PPG this season
        self.player_season_ppg = self.get_player_season_ppg()
        # current season the player is in
        self.player_current_season_id = team_info_dict.get('current_season_id')

    def get_player_id(self):
        player_info = players.find_players_by_full_name(self.player_name)
        player_id = player_info[0]['id']
        return player_id

    def get_player_season_ppg(self):
        player_stats_dfs_list = playercareerstats.PlayerCareerStats(player_id=self.player_id).get_data_frames()

        player_career_stats_main_df = player_stats_dfs_list[0].iloc[::-1].reset_index(drop=True)
        current_team_id = player_career_stats_main_df['TEAM_ID'].to_list()[0]

        player_career_stats_main_df['PPG'] = player_career_stats_main_df['PTS'] / player_career_stats_main_df['GP']
        player_ppg_this_season = round(player_career_stats_main_df['PPG'].to_list()[0], 1)
        return player_ppg_this_season

    def build_game_data_v1(self, opponent_abbreviation):

        playerboxgames = playergamelog.PlayerGameLog(self.player_id, 'ALL', ).get_data_frames()

        # cleaning dataframe
        playergamelog_df = playerboxgames[0]
        playergamelog_df['PLAYERTEAM'] = playergamelog_df['MATCHUP'].str[:3]
        playergamelog_df['OPPONENT'] = playergamelog_df['MATCHUP'].str[-3:]

        playergamelog_df.drop(['VIDEO_AVAILABLE', 'MATCHUP', 'PLUS_MINUS'], axis=1, inplace=True)
        # BUILDS AN EXTRA ROW FOR TEST / PREDICT PURPOSES -------------------------------------------------------

        playergamelog_test_data = playergamelog_df.iloc[0:0]
        playergamelog_test_data.loc[0, 'OPPONENT'] = opponent_abbreviation
        playergamelog_test_data.loc[0, 'SEASON_ID'] = '2' + self.player_current_season_id[:4]
        playergamelog_test_data.loc[0, 'PLAYERTEAM'] = self.player_team_name
        playergamelog_test_data.loc[0, 'Player_ID'] = self.player_id

        playergamelog_test_data = playergamelog_test_data.fillna('TESTLINE')

        playergamelog_df = pd.concat([playergamelog_test_data, playergamelog_df], ignore_index=True)

        # VARIABLES-----------------------------------------------------------------------------------------------

        # PlayerPTS (yhat) = RA_PTS_LAST_3_GAMES + PREV_GAME_V_OPP_PTS +
        # SEASON_PPG + OPP_RECENT_TEAM + TEAM_STARTERS_DNP + b

        #################################################################################
        # RA_PTS_LAST_3_GAMES
        # -rolling average of points scored over the previous 3 games.
        playergamelog_df['RA_PTS_LAST_3_GAMES'] = round(
            playergamelog_df['PTS'].shift(-1)[::-1].rolling(window=3, min_periods=1).mean(),
            1)

        #################################################################################
        # PREV_GAME_V_OPP_PTS
        # -finds how many points the player scored in the previous game vs the same opponent. Non-Location based.
        playergamelog_df['PREV_GAME_V_OPP_PTS'] = self.player_season_ppg
        for index, row in playergamelog_df.iterrows():
            oppkey = playergamelog_df.at[index, 'OPPONENT']
            try:
                opploc = playergamelog_df['OPPONENT'].to_list().index(oppkey, index + 1)
                playergamelog_df.at[index, 'PREV_GAME_V_OPP_PTS'] = playergamelog_df.at[opploc, 'PTS']
            except:
                opploc = playergamelog_df['OPPONENT'].to_list().index(oppkey, index)
                playergamelog_df.at[index, 'PREV_GAME_V_OPP_PTS'] = None

        # SEASON_PPG
        # -players points per game for the current season
        playergamelog_df['SEASON_PPG'] = self.player_season_ppg

        # OPP_IS_RECENT_TEAM
        # simple
        playergamelog_df['OPP_IS_FORMER_TEAM'] = [1 if opp in self.player_former_team_names else 0 for opp in
                                                  playergamelog_df['OPPONENT']]
        #################################################################################
        # STARTERS_DNP (Work In Progress)
        # -counts how many starting teammates DNP. This would distribute the ball more towards the given player.
        # playergamelog_df['TEAM_STARTERS_DNP'] = ''

        #################################################################################
        # OPP_DEFENSIVE_RATING
        # -gets the current defensive rating of the opponent. Higher ratings correlate with lower scores.
        team_stats = leaguedashteamstats.LeagueDashTeamStats(
            season=self.player_current_season_id,
            measure_type_detailed_defense="Advanced"
        )

        # Convert the data to a DataFrame
        df = team_stats.get_data_frames()[0]

        # Filter for Defensive Rating
        def_rating_df = df[['TEAM_NAME', 'TEAM_ID', 'DEF_RATING']]

        # Map the team abbreviation for connecting to the playergamelog_df
        def_rating_df['TEAM_ABBREVIATION'] = def_rating_df['TEAM_ID'].map(team_map)

        playergamelog_df_merged = playergamelog_df.merge(def_rating_df, left_on='OPPONENT',
                                                         right_on='TEAM_ABBREVIATION')
        #################################################################################
        # CLEANING DATA SHEET

        player_team = self.player_team_name
        playergamelog_df_clean = playergamelog_df_merged.query('PLAYERTEAM == @player_team')

        formatted_current_season_id = '2' + self.player_current_season_id[:4]
        # print(formatted_current_season_id)
        playergamelog_df_clean = playergamelog_df_merged.query('SEASON_ID == @ formatted_current_season_id')

        playergamelog_df_clean = playergamelog_df_clean.rename(columns={'DEF_RATING': 'OPP_DEF_RATING',
                                                                        'TEAM_ID': 'OPP_TEAM_ID',
                                                                        'TEAM_NAME': 'OPP_TEAM_FULL_NAME'})

        playergamelog_df_clean = playergamelog_df_clean.drop(columns=['MIN', 'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A',
                                                                      'FG3_PCT', 'FTM', 'FTA', 'FT_PCT', 'OREB', 'DREB',
                                                                      'AST', 'STL', 'BLK', 'TOV', 'PF', 'REB',
                                                                      'TEAM_ABBREVIATION', 'WL', 'Game_ID',
                                                                      'SEASON_ID', 'Player_ID'])

        median_ppg_filler = math.floor(playergamelog_df_clean['PREV_GAME_V_OPP_PTS'].mean())
        playergamelog_df_clean.loc[:, 'PREV_GAME_V_OPP_PTS'] = playergamelog_df_clean['PREV_GAME_V_OPP_PTS'].fillna(
            median_ppg_filler)

        playergamelog_df_clean = playergamelog_df_clean.iloc[::-1].reset_index(drop=True)

        # print(self.player_name)
        # print(tabulate(playergamelog_df_clean, headers='keys'))

        return playergamelog_df_clean


