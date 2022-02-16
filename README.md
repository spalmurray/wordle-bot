# wordle-bot

A Discord bot to track you and your friends' Wordle scores, so you can see who's the best! To submit a score to wordle-bot, just paste the Wordle score share in a Discord server that wordle-bot is a member of, as shown in the demo photo below. Note that your scores are bound to your Discord user id, not any particular server, so you can submit a score on one server and have it shown in another server's rankings.

To add the bot to your Discord server, click [here](https://discord.com/api/oauth2/authorize?client_id=933891782373158943&permissions=67584&scope=bot)!

Feb 3 Update: The bot has reached 100 servers and cannot be added to any more until Discord verifies the bot. The process has been started, but may take some time. I'm sorry for the inconvenience and hope you'll come back to check in! I will keep this note updated with any news. :)

---

Bot commands are as follows:

- `!wb help` to see this message
- `!wb me` to see your stats
- `!wb average` to see server rankings by average number of guesses
- `!wb rate` to see server rankings by win rate
- `!wb games` to see server rankings by games played
- `!wb deletemydata` to remove all your scores from wordle-bot (warning: this is not reversible!)

---

![demo of wordle-bot](demo.png)

---

## Installation

### Prereqs

- Python 3
- MongoDB

### Pre-Setup

1. Register an applicaiton in the Discord Developer portal.
2. Create a bot within the new application. On the bot page:
   1. Give the bot a name. This will be displayed in the users list on the right in your Discord server.
   2. Enable the "Server Members" intent and the "Message Content" intent. This will allow the bot to access people and messages to keep score.
   3. Click the copy button in the token area of the Build-a-Bot section toward the top.
   4. Paste this token in the config.ini file. This is how the bot will authenticate with Discord when it runs.
3. Generate the OAuth URL for adding the bot to a server.
   1. In the application page, click on OAuth2, then on URL Generator in the left-hand navigation.
   2. Check the "bot" box.
   3. Check "Send Messages" and "Read Message History" in the section that appears below.
   4. Copy the Generated URL and browse to it to authorize the bot in your Discord server. You'll choose the server and confirm the permissions on this page.
4. Start the bot server by running "python main.py" from the command line.
5. In your Discord server, type "!wb" in some text channel to confirm that the bot is responding.
