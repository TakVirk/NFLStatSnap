# NFLStatSnap
Discord bot providing instant NFL player stats and fantasy football analytics. Features player season averages, weekly performance, player comparisons, team stats, and advanced filtering. Built with Python, discord.py, and nfl-data-py. Uses 2024 season data with PPR scoring (2025 data not yet available).

---

## 📋 Features

### Player Statistics
- **Season Averages**: View comprehensive per-game statistics for any NFL player
  - Passing/Rushing/Receiving yards per game
  - Touchdowns per game
  - Receptions per game
  - Fantasy points per game (PPR scoring)
- **Weekly Performance**: Check individual game stats for any week of the season
- **Player Comparisons**: Side-by-side stat comparisons between two players

### Team Information
- **Team Stats**: Offensive statistics and scoring summaries
- **Team Rosters**: View complete rosters by position

### Advanced Filtering
- **Filter by Stats**: Find all players at a position who meet specific stat thresholds
  - Example: All RBs with 80+ rushing yards per game
  - Example: All WRs with 20+ fantasy points per game

### Player Availability
- **Injury Reports**: Historical availability data showing games played/missed during 2024 season

---

## 🎮 Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/ping` | Check if bot is online | `/ping` |
| `/playerstats` | Get season stats for a player | `/playerstats player_name:Lamar Jackson` |
| `/filterbystat` | Filter players by position and stat threshold | `/filterbystat position:RB stat:rushing_ypg threshold:80` |
| `/comparestats` | Compare two players side-by-side | `/comparestats player1:Josh Allen player2:Patrick Mahomes` |
| `/weeklystats` | Get player stats for a specific week | `/weeklystats player_name:Saquon Barkley week:10` |
| `/teamstats` | Get team offensive statistics | `/teamstats team:KC` |
| `/roster` | View a team's roster | `/roster team:SF` |
| `/injuryreport` | Check player availability history | `/injuryreport player_name:Christian McCaffrey` |

---

## 🛠️ Tech Stack

- **Python 3.11+**: Core programming language
- **discord.py**: Discord API wrapper for bot functionality
- **nfl-data-py**: NFL statistics data provider
- **pandas**: Data manipulation and analysis
- **rapidfuzz**: Fuzzy string matching for player name search
- **python-dotenv**: Environment variable management

---

## 📊 Data & Methodology

### Data Source
All NFL statistics are sourced from the **nfl-data-py** library, which provides official NFL data including:
- Player statistics (passing, rushing, receiving)
- Team information and rosters
- Weekly and seasonal performance data

### Fantasy Scoring
- Uses **PPR (Point Per Reception)** scoring system
- Standard fantasy football scoring rules applied

### Eligibility Threshold
- Players must have played at least **6 games** in the 2024 season to appear in stats
- Prevents skewed averages from players with minimal participation

### Fuzzy Search
- Handles typos and variations in player names
- Example: "lamar jackson", "Lamar", "L Jackson" all work

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.11 or higher
- Discord account
- Discord bot token ([Create one here](https://discord.com/developers/applications))

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/NFLStatSnap.git
cd NFLStatSnap
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Set Up Environment Variables
Create a `.env` file in the project root:
```
DISCORD_TOKEN=your_bot_token_here
```

### Step 4: Run the Bot
```bash
python bot.py
```

The bot will load NFL data (takes 1-3 minutes on first run) and connect to Discord.

---

## 🔧 Configuration

### Discord Bot Setup
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section and create a bot
4. Enable these Privileged Gateway Intents:
   - Message Content Intent
   - Server Members Intent
5. Copy the bot token to your `.env` file
6. Generate invite URL with these permissions:
   - `bot` and `applications.commands` scopes
   - Send Messages, Embed Links, Use Slash Commands permissions

### Team Abbreviations
Use standard NFL team abbreviations (e.g., KC, SF, BAL, BUF, DAL)

---

## 📝 Usage Examples

### Finding Top Running Backs
```
/filterbystat position:RB stat:rushing_ypg threshold:80
```
Returns all running backs averaging 80+ rushing yards per game.

<img width="411" height="247" alt="Screen Shot 2026-01-13 at 5 27 41 PM" src="https://github.com/user-attachments/assets/b46ce77b-9fae-4a75-96f8-be2f08e22d95" />

### Comparing Quarterbacks
```
/comparestats player1:Josh Allen player2:Lamar Jackson
```
Shows side-by-side comparison of stats and fantasy performance.

<img width="419" height="319" alt="Screen Shot 2026-01-13 at 5 28 38 PM" src="https://github.com/user-attachments/assets/270c2d93-d7c4-48b9-ae42-1e6d05b2f84d" />

### Checking Weekly Performance
```
/weeklystats player_name:Justin Jefferson week:5
```
Displays stats from Week 5 for Justin Jefferson.

<img width="442" height="336" alt="Screen Shot 2026-01-13 at 5 28 09 PM" src="https://github.com/user-attachments/assets/2486bdf5-d235-4810-9b9b-f060d0ac0570" />

---

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📧 Contact

For questions or suggestions, please open an issue on GitHub.

---
