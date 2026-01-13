import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
import nfl_data_py as nfl
import pandas as pd
from rapidfuzz import process, fuzz

# LOAD ENVIRONMENT VARIABLES FROM .ENV FILE
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# BOT SETUP WITH INTENTS
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# GLOBAL VARIABLES TO STORE DATA
player_data = None
player_ids = None

# EVENT: BOT IS READY
@bot.event
async def on_ready():
    global player_data, player_ids
    print(f'{bot.user} has connected to Discord!')
    
    # LOAD NFL DATA WHEN BOT STARTS
    print("Loading 2024 NFL season data...")
    try:
        # LOAD PLAYER IDS/NAMES MAPPING
        print("Loading player ID data...")
        player_ids = nfl.import_ids()
        
        # LOAD 2024 REGULAR SEASON STATS
        print("Loading seasonal stats...")
        player_data = nfl.import_seasonal_data([2024])
        # **NOTE: 2025 REGULAR SEASON DATA NOT YET AVAILABLE, ONCE UPDATED, JUST CHANGE 2024 TO 2025**
        
        # MERGE PLAYER NAMES WITH STATS
        player_data = player_data.merge(
            player_ids[['gsis_id', 'name', 'position']],
            left_on='player_id',
            right_on='gsis_id',
            how='left'
        )
        
        print(f"Loaded data for {len(player_data)} player-season records")
        
    except Exception as e:
        print(f"Error loading NFL data: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# COMMAND: PING
@bot.tree.command(name="ping", description="Check if the bot is online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏈 NFLStatSnap is online and ready!")

# COMMAND: PLAYER STATS
@bot.tree.command(name="playerstats", description="Get season stats for an NFL player")
async def playerstats(interaction: discord.Interaction, player_name: str):
    await interaction.response.defer()
    
    if player_data is None:
        await interaction.followup.send("❌ NFL data is still loading. Please try again in a moment.")
        return
    
    try:
        # FILTER OUT ROWS WITHOUT NAMES
        valid_players = player_data[player_data['name'].notna()].copy()
        
        # USE FUZZY MATCHING TO FIND THE PLAYER
        player_names = valid_players['name'].tolist()
        match = process.extractOne(player_name, player_names, scorer=fuzz.ratio)
        
        if match is None or match[1] < 60:  # 60% SIMILARITY THRESHOLD
            await interaction.followup.send(f"❌ Could not find player: {player_name}")
            return
        
        matched_name = match[0]
        player = valid_players[valid_players['name'] == matched_name].iloc[0]
        
        # CALCULATE STATS
        games_played = int(player.get('games', 0))
        
        # CHECK MINIMUM GAMES THRESHOLD
        if games_played < 6:
            await interaction.followup.send(
                f"⚠️ {player['name']} has only played {games_played} games (minimum 6 required)"
            )
            return
        
        # CALCULATE PER-GAME AVERAGES
        passing_ypg = round(float(player.get('passing_yards', 0)) / games_played, 2) if games_played > 0 else 0
        rushing_ypg = round(float(player.get('rushing_yards', 0)) / games_played, 2) if games_played > 0 else 0
        receiving_ypg = round(float(player.get('receiving_yards', 0)) / games_played, 2) if games_played > 0 else 0
        receptions_pg = round(float(player.get('receptions', 0)) / games_played, 2) if games_played > 0 else 0  # ADD THIS LINE
        pass_td_pg = round(float(player.get('passing_tds', 0)) / games_played, 2) if games_played > 0 else 0
        
        # COMBINED RUSHING + RECEIVING TDS
        rushing_tds = float(player.get('rushing_tds', 0))
        receiving_tds = float(player.get('receiving_tds', 0))
        total_tds_pg = round((rushing_tds + receiving_tds) / games_played, 2) if games_played > 0 else 0
        
        # FANTASY POINTS PER GAME (PPR SCORING)
        fantasy_ppg = round(float(player.get('fantasy_points_ppr', 0)) / games_played, 2) if games_played > 0 else 0
        
        # GET POSITION
        # GET POSITION - CHECK MULTIPLE POSSIBLE COLUMNS
        if 'position_y' in player.index and pd.notna(player.get('position_y')):
            position = player['position_y']
        elif 'position_x' in player.index and pd.notna(player.get('position_x')):
            position = player['position_x']
        elif 'position' in player.index and pd.notna(player.get('position')):
            position = player['position']
        else:
            position = 'N/A'
        
        # CREATE RESPONSE BASED ON POSITION
        stats_message = f"**Player Stats for {player['name']}:**\n"
        stats_message += f"Position: {position}\n"
        stats_message += f"GP: {games_played}\n"
        
        if position == 'QB':
            stats_message += f"PPG: {passing_ypg}\n"
            stats_message += f"RPG: {rushing_ypg}\n"
            stats_message += f"TDPG: {pass_td_pg}\n"
            stats_message += f"RTDPG: {total_tds_pg}\n"
        elif position in ['RB', 'WR']:
            stats_message += f"RECPG: {receiving_ypg}\n"
            stats_message += f"REC/G: {receptions_pg}\n"  # ADD THIS LINE
            stats_message += f"RPG: {rushing_ypg}\n"
            stats_message += f"SCTDPG: {total_tds_pg}\n"
        elif position == 'TE':
            stats_message += f"RECPG: {receiving_ypg}\n"
            stats_message += f"REC/G: {receptions_pg}\n"  # ADD THIS LINE
            stats_message += f"SCTDPG: {total_tds_pg}\n"
        
        stats_message += f"FPPG: {fantasy_ppg}"
        
        await interaction.followup.send(stats_message)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error processing player stats: {str(e)}")
        print(f"Error in playerstats command: {e}")
        import traceback
        traceback.print_exc()

# COMMAND: FILTER BY STAT
@bot.tree.command(name="filterbystat", description="Filter players by a stat threshold")
async def filterbystat(
    interaction: discord.Interaction,
    position: str,
    stat: str,
    threshold: float
):
    await interaction.response.defer()
    
    if player_data is None:
        await interaction.followup.send("❌ NFL data is still loading. Please try again in a moment.")
        return
    
    try:
        # FILTER OUT ROWS WITHOUT NAMES
        valid_players = player_data[player_data['name'].notna()].copy()
        

        # FILTER BY POSITION
        position = position.upper()

        # CHECK WHICH POSITION COLUMN EXISTS
        if 'position_y' in valid_players.columns:
            pos_col = 'position_y'
        elif 'position_x' in valid_players.columns:
            pos_col = 'position_x'
        elif 'position' in valid_players.columns:
            pos_col = 'position'
        else:
            await interaction.followup.send("❌ Error: Position column not found in data")
            return

        position_filtered = valid_players[valid_players[pos_col] == position]

        if position_filtered.empty:
            await interaction.followup.send(f"❌ No players found for position: {position}")
            return
        
        # FILTER BY MINIMUM GAMES (6+)
        position_filtered = position_filtered[position_filtered['games'] >= 6]
        
        # MAP STAT NAMES TO COLUMN NAMES AND CALCULATE PER-GAME STATS
        stat_lower = stat.lower().replace(" ", "_")
        
        # CALCULATE PER-GAME STATS
        if 'ypg' in stat_lower or 'yards_per_game' in stat_lower:
            if 'pass' in stat_lower:
                position_filtered['stat_value'] = position_filtered['passing_yards'] / position_filtered['games']
            elif 'rush' in stat_lower:
                position_filtered['stat_value'] = position_filtered['rushing_yards'] / position_filtered['games']
            elif 'rec' in stat_lower or 'receiv' in stat_lower:
                position_filtered['stat_value'] = position_filtered['receiving_yards'] / position_filtered['games']
        elif 'tdpg' in stat_lower or 'td_per_game' in stat_lower:
            if 'pass' in stat_lower:
                position_filtered['stat_value'] = position_filtered['passing_tds'] / position_filtered['games']
            else:
                position_filtered['stat_value'] = (position_filtered['rushing_tds'] + position_filtered['receiving_tds']) / position_filtered['games']
        elif 'fppg' in stat_lower or 'fantasy' in stat_lower:
            position_filtered['stat_value'] = position_filtered['fantasy_points_ppr'] / position_filtered['games']
        elif 'rec/g' in stat_lower or 'receptions_per_game' in stat_lower:
            position_filtered['stat_value'] = position_filtered['receptions'] / position_filtered['games']
        else:
            await interaction.followup.send(f"❌ Unknown stat: {stat}. Try: passing_ypg, rushing_ypg, receiving_ypg, tdpg, fppg, rec/g")
            return
        
        # FILTER BY THRESHOLD
        filtered = position_filtered[position_filtered['stat_value'] >= threshold]
        
        if filtered.empty:
            await interaction.followup.send(f"❌ No {position} players with {stat} >= {threshold}")
            return
        
        # SORT BY STAT VALUE (DESCENDING)
        filtered = filtered.sort_values('stat_value', ascending=False)
        
        # LIMIT TO TOP 15 RESULTS
        filtered = filtered.head(15)
        
        # CREATE RESPONSE
        response = f"**{position} players with {stat} >= {threshold}:**\n\n"
        
        for idx, player in filtered.iterrows():
            stat_val = round(player['stat_value'], 2)
            games = int(player['games'])
            response += f"• {player['name']}: {stat_val} ({games} GP)\n"
        
        if len(filtered) == 15:
            response += "\n*(Showing top 15 results)*"
        
        await interaction.followup.send(response)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error filtering players: {str(e)}")
        print(f"Error in filterbystat command: {e}")
        import traceback
        traceback.print_exc()


# COMMAND: ROSTER
@bot.tree.command(name="roster", description="Get an NFL team's roster")
async def roster(interaction: discord.Interaction, team: str):
    await interaction.response.defer()
    
    if player_ids is None:
        await interaction.followup.send("❌ Player data is still loading. Please try again in a moment.")
        return
    
    try:
        # LOAD ROSTER DATA FOR 2024
        print(f"Loading roster for team: {team}")
        rosters = nfl.import_seasonal_rosters([2024])  # CHANGED FROM IMPORT_ROSTERS
        
        # MERGE WITH PLAYER NAMES
        rosters = rosters.merge(
            player_ids[['gsis_id', 'name']],
            left_on='player_id',
            right_on='gsis_id',
            how='left'
        )
        
        # NORMALIZE TEAM INPUT
        team_upper = team.upper()
        
        # FILTER BY TEAM
        team_roster = rosters[rosters['team'] == team_upper]
        
        if team_roster.empty:
            await interaction.followup.send(
                f"❌ No roster found for team: {team}. Try team abbreviations like: KC, SF, BAL, BUF, DAL, etc."
            )
            return
        
        # GROUP BY POSITION
        positions_order = ['QB', 'RB', 'WR', 'TE', 'OL', 'DL', 'LB', 'DB', 'K', 'P']
        
        response = f"**{team_upper} Roster (2024 Season):**\n\n"
        
        for pos in positions_order:
            pos_players = team_roster[team_roster['position'] == pos]
            if not pos_players.empty:
                response += f"**{pos}:** "
                # USE 'NAME' COLUMN FROM MERGED DATA
                names = pos_players['name'].dropna().tolist()
                if names:
                    response += ", ".join(names[:10])  # LIMIT TO 10 PLAYERS PER POSITION
                    if len(names) > 10:
                        response += f" (+{len(names)-10} more)"
                response += "\n"
        
        # DISCORD HAS A 2000 CHARACTER LIMIT, SO TRUNCATE IF NEEDED
        if len(response) > 1900:
            response = response[:1900] + "\n\n*(Roster truncated due to length)*"
        
        await interaction.followup.send(response)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error loading roster: {str(e)}")
        print(f"Error in roster command: {e}")
        import traceback
        traceback.print_exc()

# COMMAND: COMPARE STATS
@bot.tree.command(name="comparestats", description="Compare two players side-by-side")
async def comparestats(interaction: discord.Interaction, player1: str, player2: str):
    await interaction.response.defer()
    
    if player_data is None:
        await interaction.followup.send("❌ NFL data is still loading. Please try again in a moment.")
        return
    
    try:
        from rapidfuzz import process, fuzz
        
        # FILTER OUT ROWS WITHOUT NAMES
        valid_players = player_data[player_data['name'].notna()].copy()
        
        # FIND BOTH PLAYERS USING FUZZY MATCHING
        player_names = valid_players['name'].tolist()
        
        match1 = process.extractOne(player1, player_names, scorer=fuzz.ratio)
        match2 = process.extractOne(player2, player_names, scorer=fuzz.ratio)
        
        if match1 is None or match1[1] < 60:
            await interaction.followup.send(f"❌ Could not find player: {player1}")
            return
        
        if match2 is None or match2[1] < 60:
            await interaction.followup.send(f"❌ Could not find player: {player2}")
            return
        
        # GET PLAYER DATA
        p1_data = valid_players[valid_players['name'] == match1[0]].iloc[0]
        p2_data = valid_players[valid_players['name'] == match2[0]].iloc[0]
        
        # DETERMINE POSITION COLUMN
        if 'position_y' in valid_players.columns:
            pos_col = 'position_y'
        elif 'position_x' in valid_players.columns:
            pos_col = 'position_x'
        else:
            pos_col = 'position'
        
        # GET POSITIONS
        p1_pos = p1_data.get(pos_col, 'N/A')
        p2_pos = p2_data.get(pos_col, 'N/A')
        
        # CALCULATE STATS FOR BOTH PLAYERS
        def calc_stats(player):
            games = int(player.get('games', 0))
            if games < 6:
                return None
            
            stats = {
                'games': games,
                'passing_ypg': round(float(player.get('passing_yards', 0)) / games, 2),
                'rushing_ypg': round(float(player.get('rushing_yards', 0)) / games, 2),
                'receiving_ypg': round(float(player.get('receiving_yards', 0)) / games, 2),
                'receptions_pg': round(float(player.get('receptions', 0)) / games, 2),
                'pass_td_pg': round(float(player.get('passing_tds', 0)) / games, 2),
                'total_td_pg': round((float(player.get('rushing_tds', 0)) + float(player.get('receiving_tds', 0))) / games, 2),
                'fppg': round(float(player.get('fantasy_points_ppr', 0)) / games, 2)
            }
            return stats
        
        p1_stats = calc_stats(p1_data)
        p2_stats = calc_stats(p2_data)
        
        if p1_stats is None:
            await interaction.followup.send(f"⚠️ {p1_data['name']} has played fewer than 6 games")
            return
        
        if p2_stats is None:
            await interaction.followup.send(f"⚠️ {p2_data['name']} has played fewer than 6 games")
            return
        
        # CREATE COMPARISON
        response = f"**Player Comparison:**\n\n"
        response += f"**{p1_data['name']}** ({p1_pos}) vs **{p2_data['name']}** ({p2_pos})\n\n"
        
        response += f"**Games Played:** {p1_stats['games']} vs {p2_stats['games']}\n"
        
        # SHOW RELEVANT STATS BASED ON POSITION
        if p1_pos == 'QB' or p2_pos == 'QB':
            response += f"**Passing YPG:** {p1_stats['passing_ypg']} vs {p2_stats['passing_ypg']}\n"
            response += f"**Rushing YPG:** {p1_stats['rushing_ypg']} vs {p2_stats['rushing_ypg']}\n"
            response += f"**Pass TD/G:** {p1_stats['pass_td_pg']} vs {p2_stats['pass_td_pg']}\n"
        
        if p1_pos in ['RB', 'WR', 'TE'] or p2_pos in ['RB', 'WR', 'TE']:
            response += f"**Receiving YPG:** {p1_stats['receiving_ypg']} vs {p2_stats['receiving_ypg']}\n"
            response += f"**Receptions/G:** {p1_stats['receptions_pg']} vs {p2_stats['receptions_pg']}\n"
            response += f"**Rushing YPG:** {p1_stats['rushing_ypg']} vs {p2_stats['rushing_ypg']}\n"
            response += f"**Total TD/G:** {p1_stats['total_td_pg']} vs {p2_stats['total_td_pg']}\n"
        
        response += f"\n**Fantasy PPG (PPR):** {p1_stats['fppg']} vs {p2_stats['fppg']}\n"
        
        # DETERMINE WINNER
        if p1_stats['fppg'] > p2_stats['fppg']:
            winner = p1_data['name']
        elif p2_stats['fppg'] > p1_stats['fppg']:
            winner = p2_data['name']
        else:
            winner = "Tie"
        
        response += f"\n**Fantasy Leader:** {winner}"
        
        await interaction.followup.send(response)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error comparing players: {str(e)}")
        print(f"Error in comparestats command: {e}")
        import traceback
        traceback.print_exc()

# COMMAND: WEEKLY STATS
@bot.tree.command(name="weeklystats", description="Get a player's stats for a specific week")
async def weeklystats(interaction: discord.Interaction, player_name: str, week: int):
    await interaction.response.defer()
    
    if player_ids is None:
        await interaction.followup.send("❌ Player data is still loading. Please try again in a moment.")
        return
    
    try:
        from rapidfuzz import process, fuzz
        
        # LOAD WEEKLY DATA FOR 2024
        print(f"Loading weekly data for week {week}...")
        weekly_data = nfl.import_weekly_data([2024])
        
        # MERGE WITH PLAYER NAMES
        weekly_data = weekly_data.merge(
            player_ids[['gsis_id', 'name', 'position']],
            left_on='player_id',
            right_on='gsis_id',
            how='left'
        )
        
        # FILTER OUT ROWS WITHOUT NAMES
        valid_players = weekly_data[weekly_data['name'].notna()].copy()
        
        # USE FUZZY MATCHING TO FIND THE PLAYER
        player_names = valid_players['name'].unique().tolist()
        match = process.extractOne(player_name, player_names, scorer=fuzz.ratio)
        
        if match is None or match[1] < 60:
            await interaction.followup.send(f"❌ Could not find player: {player_name}")
            return
        
        matched_name = match[0]
        
        # FILTER FOR SPECIFIC PLAYER AND WEEK
        player_week_data = valid_players[
            (valid_players['name'] == matched_name) & 
            (valid_players['week'] == week)
        ]
        
        if player_week_data.empty:
            await interaction.followup.send(f"❌ No data found for {matched_name} in week {week}")
            return
        
        player = player_week_data.iloc[0]
        
        # GET STATS
        passing_yards = int(player.get('passing_yards', 0))
        rushing_yards = int(player.get('rushing_yards', 0))
        receiving_yards = int(player.get('receiving_yards', 0))
        receptions = int(player.get('receptions', 0))
        passing_tds = int(player.get('passing_tds', 0))
        rushing_tds = int(player.get('rushing_tds', 0))
        receiving_tds = int(player.get('receiving_tds', 0))
        fantasy_points = round(float(player.get('fantasy_points_ppr', 0)), 2)
        
        # GET POSITION
        position = player.get('position_y', player.get('position_x', player.get('position', 'N/A')))
        
        # CREATE RESPONSE
        response = f"**Week {week} Stats for {matched_name}:**\n"
        response += f"Position: {position}\n"
        response += f"Opponent: {player.get('opponent_team', 'N/A')}\n\n"
        
        if position == 'QB':
            response += f"Passing Yards: {passing_yards}\n"
            response += f"Passing TDs: {passing_tds}\n"
            response += f"Rushing Yards: {rushing_yards}\n"
            response += f"Rushing TDs: {rushing_tds}\n"
        elif position in ['RB', 'WR']:
            response += f"Receiving Yards: {receiving_yards}\n"
            response += f"Receptions: {receptions}\n"
            response += f"Receiving TDs: {receiving_tds}\n"
            response += f"Rushing Yards: {rushing_yards}\n"
            response += f"Rushing TDs: {rushing_tds}\n"
        elif position == 'TE':
            response += f"Receiving Yards: {receiving_yards}\n"
            response += f"Receptions: {receptions}\n"
            response += f"Receiving TDs: {receiving_tds}\n"
        
        response += f"\nFantasy Points (PPR): {fantasy_points}"
        
        await interaction.followup.send(response)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error loading weekly stats: {str(e)}")
        print(f"Error in weeklystats command: {e}")
        import traceback
        traceback.print_exc()

# COMMAND: INJURY REPORT
@bot.tree.command(name="injuryreport", description="Get injury/availability info for a player in 2024")
async def injuryreport(interaction: discord.Interaction, player_name: str):
    await interaction.response.defer()
    
    if player_data is None or player_ids is None:
        await interaction.followup.send("❌ Player data is still loading. Please try again in a moment.")
        return
    
    try:
        from rapidfuzz import process, fuzz
        
        # FILTER OUT ROWS WITHOUT NAMES
        valid_players = player_data[player_data['name'].notna()].copy()
        
        # USE FUZZY MATCHING TO FIND THE PLAYER
        player_names = valid_players['name'].tolist()
        match = process.extractOne(player_name, player_names, scorer=fuzz.ratio)
        
        if match is None or match[1] < 60:
            await interaction.followup.send(f"❌ Could not find player: {player_name}")
            return
        
        matched_name = match[0]
        player = valid_players[valid_players['name'] == matched_name].iloc[0]
        
        # GET GAMES PLAYED
        games_played = int(player.get('games', 0))
        total_games = 17  # 2024 REGULAR SEASON
        
        # DETERMINE POSITION COLUMN
        if 'position_y' in player.index:
            position = player['position_y']
        elif 'position_x' in player.index:
            position = player['position_x']
        else:
            position = player.get('position', 'N/A')
        
        # CREATE RESPONSE
        response = f"**2024 Season Availability for {matched_name}:**\n"
        response += f"Position: {position}\n"
        response += f"Games Played: {games_played}/{total_games}\n"
        
        if games_played == total_games:
            response += f"\n✅ **Status:** Played full season (all {total_games} games)"
        elif games_played >= 14:
            missed = total_games - games_played
            response += f"\n⚠️ **Status:** Missed {missed} game(s) - mostly available"
        elif games_played >= 10:
            missed = total_games - games_played
            response += f"\n⚠️ **Status:** Missed {missed} games - significant time missed"
        elif games_played >= 6:
            missed = total_games - games_played
            response += f"\n🔴 **Status:** Missed {missed} games - major availability issues"
        else:
            response += f"\n🔴 **Status:** Only played {games_played} games - season-ending/long-term injury"
        
        response += "\n\n*Note: This shows 2024 historical data. For current/live injury reports, check official NFL sources.*"
        
        await interaction.followup.send(response)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error loading injury report: {str(e)}")
        print(f"Error in injuryreport command: {e}")
        import traceback
        traceback.print_exc()


# RUN THE BOT
bot.run(TOKEN)

