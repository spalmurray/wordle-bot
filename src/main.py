import configuration
import data
import discord
import re

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

database = data.Client()


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content == "!wb members":
        await message.channel.send(message.guild.members)

    if message.content == "!wb me":
        stats = database.get_player_stats(message.author.id)
        player = message.author.nick if message.author.nick is not None else message.author.name
        stats_string = f"{player}'s average number of guesses is {round(stats[0], 4)}. They've played {stats[1]} " \
                       f"games and won {stats[2]} games, making their win rate {round(stats[3] * 100, 4)}%."
        await message.channel.send(stats_string)

    if message.content == "!wb average":
        await message.channel.send(rankings_by_average(message, 10))

    if message.content == "!wb rate":
        await message.channel.send(rankings_by_win_rate(message, 10))

    if message.content == "!wb games":
        await message.channel.send(rankings_by_games_played(message, 10))

    if message.content == "!wb helper":
        await message.channel.send('https://www.spalmurray.com/wordle-helper')

    if message.content == "!wb help" or message.content == "!wb":
        help_string = "`!wb help` to see this message\n" \
                      "`!wb me` to see your stats\n" \
                      "`!wb average` to see server rankings by average number of guesses\n" \
                      "`!wb rate` to see server rankings by win rate\n" \
                      "`!wb games` to see server rankings by games played\n" \
                      "`!wb helper` for a link to wordle-helper"
        await message.channel.send(help_string)

    if re.match(r"Wordle [0-9]+ [1-6|X]/6", message.content) is not None:
        # extract the Wordle number from message
        wordle = message.content.splitlines()[0].split(" ")[1]
        # extract the score from message
        score = message.content.splitlines()[0].split(" ")[2][0]
        if score == "X":
            score = "7"
        score = int(score)

        result = database.add_score(message.author.id, wordle, score)

        if not result:
            await message.channel.send("You've already submitted a score for this Wordle.")
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


def rankings_by_average(message, n: int) -> str:
    """Return string formatted leaderboard ordered by average guesses where message is the message data from the
    triggering Discord message and n is the max number of rankings to return.
    """
    members = [(member.nick if member.nick is not None else member.name, member.id)
               for member in message.guild.members]
    scores = []
    for member in members:
        score = database.get_player_stats(member[1])
        if score[0] == 0:
            continue
        scores.append((member[0], score))
    scores.sort(key=lambda x: x[1][0])

    scoreboard = "Rankings by average number of guesses:"
    i = 0
    while i < n and i != len(scores):
        scoreboard += f"\n{i + 1}. {scores[i][0]} ({round(scores[i][1][0], 4)})"
        i += 1

    return scoreboard


def rankings_by_win_rate(message, n: int) -> str:
    """Return string formatted leaderboard ordered by win rate where message is the message data from the
    triggering Discord message and n is the max number of rankings to return.
    """
    members = [(member.nick if member.nick is not None else member.name, member.id)
               for member in message.guild.members]
    scores = []
    for member in members:
        score = database.get_player_stats(member[1])
        if score[0] == 0:
            continue
        scores.append((member[0], score))
    scores.sort(key=lambda x: x[1][3], reverse=True)

    scoreboard = "Rankings by win rate:"
    i = 0
    while i < n and i != len(scores):
        scoreboard += f"\n{i + 1}. {scores[i][0]} ({round(scores[i][1][3] * 100, 4)}%)"
        i += 1

    return scoreboard


def rankings_by_games_played(message, n: int) -> str:
    """Return string formatted leaderboard ordered by number of games played where message is the message data from the
    triggering Discord message and n is the max number of rankings to return.
    """
    members = [(member.nick if member.nick is not None else member.name, member.id)
               for member in message.guild.members]
    scores = []
    for member in members:
        score = database.get_player_stats(member[1])
        if score[0] == 0:
            continue
        scores.append((member[0], score))
    scores.sort(key=lambda x: x[1][1], reverse=True)

    scoreboard = "Rankings by games played:"
    i = 0
    while i < n and i != len(scores):
        scoreboard += f"\n{i + 1}. {scores[i][0]} ({scores[i][1][1]})"
        i += 1

    return scoreboard


if __name__ == "__main__":
    config = configuration.Config()
    client.run(config.token)
