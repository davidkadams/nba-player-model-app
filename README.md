# nba-player-model-app
# by David Adams

Welcome! This is a small-scale model project I created, combining my interest in sports and data science.

Disclaimer: I am not a sports analyst and am not giving any type of 'betting' advice.


# Findings

You will notice that the R-squared value is overall very low. That is to be expected considering how unpredictable the NBA is, combined with the limited data provided from nba_api
Some players, however, can have R-squared values up to .4, showing that the variables tracked in the model can have some decent correlation for certain players.

# Other Variables I'd consider

--OTHER_STARTERS_OUT--
One variable specifically that I wish I could include (it involved too many API calls) would be tracking if other starters were out in the game the Player played in.
If Starters are out, obviously points would be dispersed throughout the other starters, as well as the bench. 
Player Injury reports can be difficult to judge and keep track of when trying to input real time data for a prediction. 

In a more in-depth analysis, with a wider range of capabilities, I would consider tracking specific opposing team defensive areas (i.e 3-point defense, paint defense, etc)
With this information, you could then track how the given Player generally scores, and see if there is any correlation.


# Overall
The NBA, and sports in general, are full of unpredicabilities. Athletes sometimes will have rough nights, or sometimes surpass expectations.
While this model can track and general trends, your fate for betting will forever be in the Players hands..

There will be some bugs with calling certain players, I will work on adjusting any issues brought up to me.

Best,
David


