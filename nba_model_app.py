import nbaplayerbuilder
import numpy as np
from sklearn import linear_model
import streamlit as st

########################################################
# PAGE CONFIG
st.set_page_config(layout='wide',initial_sidebar_state='expanded')

########################################################
# TITLE
st.title("NBA Player Points Estimator")

########################################################
# SIDEBAR
# add a sidebar for inputs
st.sidebar.subheader("Player Game Simulation Input")

# builds the hashmap into a list of team names
nba_teams_list = []
for key, value in nbaplayerbuilder.team_map.items():
    nba_teams_list.append(value)

nba_teams_list.sort()

player = st.sidebar.text_input("## Player Name (ex: Stephen Curry): ")
opp = st.sidebar.selectbox(
    label="## Opponent Abbreviation (ex: ATL): ",
    options=nba_teams_list)

st.sidebar.markdown('''
---
*by: David Adams*''')

########################################################
# BODY
# verify if a player name was entetered before running
if player:

    # builds the player dataset using nba_api
    playertest = nbaplayerbuilder.NBAPlayer(player)
    player_games_df = playertest.build_game_data_v1(opp)

    # distiguishes the train set for the data
    train_x = player_games_df[00:len(player_games_df) - 1]

    # this is the last line of data that is used as the test set. it is build into the dataframe from the player input.
    # only in dataframe to use for calculations that are later used to build variables below.
    testline = player_games_df.tail(1)

    st.write(train_x)

    ra = testline['RA_PTS_LAST_3_GAMES'].tolist()[0]
    prev_pts_vs_opp = testline['PREV_GAME_V_OPP_PTS'].tolist()[0]
    opp_d_rating = testline['OPP_DEF_RATING'].tolist()[0]
    is_opp_former_team = bool(testline['OPP_IS_FORMER_TEAM'].tolist()[0])

    reg = linear_model.LinearRegression()
    reg.fit(train_x[['RA_PTS_LAST_3_GAMES', 'PREV_GAME_V_OPP_PTS', 'OPP_DEF_RATING', 'OPP_IS_FORMER_TEAM']],
            train_x['PTS'])

    r_squared = round(reg.score(
        train_x[['RA_PTS_LAST_3_GAMES', 'PREV_GAME_V_OPP_PTS', 'OPP_DEF_RATING', 'OPP_IS_FORMER_TEAM']],
        train_x['PTS']), 3)

    x_test = np.array([[ra, prev_pts_vs_opp, opp_d_rating, is_opp_former_team]])
    y_pred = round(reg.predict(x_test)[0], 1)

    st.write(f'*Model training set R-squared Value: :orange[{r_squared}]*')
    st.write(f'*Average of :blue[{player}] previous 3 Games: :orange[{ra}]*')
    st.write(f'*Previous Points Against :blue[{opp}]: :orange[{prev_pts_vs_opp}]*')
    st.write(f'*:blue[{opp}] Defensive Rating: :orange[{opp_d_rating}]*')
    st.write(f'*Is :blue[{opp}] a former recent team of :blue[{player}]? :orange[{is_opp_former_team}]*')

    st.markdown((f'''
    ---'''))
    st.markdown(f"<h1 style='text-align: center; '>Predicted Points for {player} vs {opp} :</h1>",
                unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align: center; '>{y_pred}</h1>", unsafe_allow_html=True)


########################################################
    # CHARTS
    st.markdown(('''
        ---
        ## Current Season Player Performance Chart ##'''))
    # Line Chart
    st.line_chart(train_x, x=None, y=['PTS','RA_PTS_LAST_3_GAMES','SEASON_PPG'],x_label='Games into the Season', y_label='Points')
########################################################

else:
    st.write(":red[Please input a Player Name]")

