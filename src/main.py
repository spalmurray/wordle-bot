import sys
import configuration
import data
import discord
import re

intents = discord.Intents.default()
intents.members = True
intents.messages = True
client = discord.Client(intents=intents)

database = data.Client()


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("!wb") or message.content.startswith("Wordle"):
        await process_message("wb", ":book: Wordle", "Wordle [0-9]+ [1-6|X]/6", message)
    elif message.content.startswith("!wlb") or message.content.startswith("#Worldle"):
        await process_message("wlb", ":earth_americas: Worldle", "#Worldle #[0-9]+ [1-6|X]/6", message)
    elif message.content.startswith("!sb") or message.content.startswith("Subwaydle"):
        await process_message("sb", ":metro: Subwaydle", "Subwaydle [0-9]+ [1-6|X]/6", message)


async def process_message(game_abbreviation, game_name, game_regex_string, message):
    if message.content == f"!{game_abbreviation} me":
        stats = database.get_player_stats(game_abbreviation, message.author.id)
        player = message.author.nick if message.author.nick is not None else message.author.name
        stats_string = f"For **{game_name}**, {player}'s average number of guesses is **{round(stats[0], 4)}**. " \
                       f"They've played **{stats[1]}** games and won **{stats[2]}** games, making their win rate " \
                       f"**{round(stats[3] * 100, 4)}%**."
        await message.channel.send(stats_string)

    if message.content == f"!{game_abbreviation} average":
        await message.channel.send(f"For **{game_name}**:\n{rankings_by_average(message, game_abbreviation, 10)}")

    if message.content == f"!{game_abbreviation} rate":
        await message.channel.send(f"For **{game_name}**:\n{rankings_by_win_rate(message, game_abbreviation, 10)}")

    if message.content == f"!{game_abbreviation} games":
        await message.channel.send(f"For **{game_name}**:\n{rankings_by_games_played(message, game_abbreviation, 10)}")

    if message.content == f"!{game_abbreviation} deletemydata":
        if database.delete_player(game_abbreviation, message.author.id):
            await message.channel.send(
                f"{message.author.nick if message.author.nick is not None else message.author.name}'s "
                f"data has been deleted.")
        else:
            await message.channel.send("I tried to delete your data, but I couldn't find any data for you!")

    if message.content == f"!{game_abbreviation} helper":
        await message.channel.send('https://www.spalmurray.com/wordle-helper')

    if message.content == f"!{game_abbreviation} help" or message.content == f"!{game_abbreviation}":
        # backticks are Discord/Markdown characters for fixed width code type display
        help_string = f"`!{game_abbreviation} help` to see this message\n" \
                      f"`!{game_abbreviation} me` to see your stats\n" \
                      f"`!{game_abbreviation} average` to see server rankings by average number of guesses\n" \
                      f"`!{game_abbreviation} rate` to see server rankings by win rate\n" \
                      f"`!{game_abbreviation} games` to see server rankings by games played\n" \
                      f"`!{game_abbreviation} deletemydata` to remove all your scores from wordle-bot (warning: this is not reversible!)"
        await message.channel.send(help_string)

    game_regex = re.compile(game_regex_string)
    if re.match(game_regex, message.content) is not None:
        # extract the Wordle number from message
        wordle = message.content.splitlines()[0].split(" ")[1]
        # extract the score from message
        score = message.content.splitlines()[0].split(" ")[2][0]
        if score == "X":
            score = "7"
        score = int(score)

        result = database.add_score(
            game_abbreviation, message.author.id, wordle, score)

        if not result:
            await message.channel.send(f"You've already submitted a score for this {game_name}.")
            return

        if score == 1:
            await message.channel.send("Uh... you should probably go buy a lottery ticket...")
        elif score == 2:
            await message.channel.send("Wow! That's impressive!")
        elif score == 3:
            await message.channel.send("Very nice!")
        elif score == 4:
            await message.channel.send("Not bad!")
        elif score == 5:
            await message.channel.send("Unlucky...")
        elif score == 6:
            await message.channel.send("Cutting it a little close there...")
        else:
            await message.channel.send("I will pretend like I didn't see that one...")


def rankings_by_average(message, game_abbreviation: str, n: int) -> str:
    """Return string formatted leaderboard ordered by average guesses where message is the message data from the
    triggering Discord message and n is the max number of rankings to return.
    """
    members = [(member.nick if member.nick is not None else member.name, member.id)
               for member in message.guild.members]
    scores = []
    for member in members:
        score = database.get_player_stats(game_abbreviation, member[1])
        if score[0] == 0:
            continue
        scores.append((member[0], score))
    scores.sort(key=lambda x: x[1][0])

    scoreboard = "Rankings by average number of guesses:"
    i = 0
    while i < n and i != len(scores):
        scoreboard += f"\n{i + 1}. **{scores[i][0]}** ({round(scores[i][1][0], 4)})"
        i += 1

    return scoreboard


def rankings_by_win_rate(message, game_abbreviation: str, n: int) -> str:
    """Return string formatted leaderboard ordered by win rate where message is the message data from the
    triggering Discord message and n is the max number of rankings to return.
    """
    members = [(member.nick if member.nick is not None else member.name, member.id)
               for member in message.guild.members]
    scores = []
    for member in members:
        score = database.get_player_stats(game_abbreviation, member[1])
        if score[0] == 0:
            continue
        scores.append((member[0], score))
    scores.sort(key=lambda x: x[1][3], reverse=True)

    scoreboard = "Rankings by win rate:"
    i = 0
    while i < n and i != len(scores):
        scoreboard += f"\n{i + 1}. **{scores[i][0]}** ({round(scores[i][1][3] * 100, 4)}%)"
        i += 1

    return scoreboard


def rankings_by_games_played(message, game_abbreviation: str, n: int) -> str:
    """Return string formatted leaderboard ordered by number of games played where message is the message data from the
    triggering Discord message and n is the max number of rankings to return.
    """
    members = [(member.nick if member.nick is not None else member.name, member.id)
               for member in message.guild.members]
    scores = []
    for member in members:
        score = database.get_player_stats(game_abbreviation, member[1])
        if score[0] == 0:
            continue
        scores.append((member[0], score))
    scores.sort(key=lambda x: x[1][1], reverse=True)

    scoreboard = "Rankings by games played:"
    i = 0
    while i < n and i != len(scores):
        scoreboard += f"\n{i + 1}. **{scores[i][0]}** ({scores[i][1][1]})"
        i += 1

    return scoreboard


if __name__ == "__main__":
    config = configuration.Config()

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        client.run(config.testtoken)

    else:
        client.run(config.token)
