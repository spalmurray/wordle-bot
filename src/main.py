import configuration
import data
import discord
import re
from apscheduler.schedulers.asyncio import AsyncIOScheduler

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

    if message.content == "!wb me":
        stats = database.get_player_stats(message.author.id)
        player = message.author.nick if message.author.nick is not None else message.author.name
        stats_string = f"{player}'s average number of guesses is {round(stats[0], 4)}. They've played {stats[1]} " \
                       f"games and won {stats[2]} games, making their win rate {round(stats[3] * 100, 4)}%. Their " \
                       f"current win streak is {stats[4]} games and their maximum win streak is {stats[5]} games."
        await message.channel.send(stats_string)

    if message.content == "!wb average":
        await message.channel.send(rankings_by_average(message, 10))

    if message.content == "!wb rate":
        await message.channel.send(rankings_by_win_rate(message, 10))

    if message.content == "!wb played" or message.content == "!wb games":
        await message.channel.send(rankings_by_games_played(message, 10))

    if message.content == "!wb streak":
        await message.channel.send(rankings_by_current_win_streak(message, 10))

    if message.content == "!wb maxstreak":
        await message.channel.send(rankings_by_max_win_streak(message, 10))

    if message.content == "!wb missing":
        missing = database.get_missing_scores(message.author.id)
        player = message.author.nick if message.author.nick is not None else message.author.name
        if not missing:
            await message.channel.send(f"{player} is not missing any Wordle games!")
        else:
            missing_string = f"{player} is missing Wordle games: "
            for game in missing:
                missing_string += str(game) + ", "
            missing_string = missing_string[:-2] + "."
            await message.channel.send(missing_string)

    if message.content == "!wb deletemydata":
        if database.delete_player(message.author.id):
            await message.channel.send(
                f"{message.author.nick if message.author.nick is not None else message.author.name}'s "
                f"data has been deleted.")
        else:
            await message.channel.send("I tried to delete your data, but I couldn't find any data for you!")

    if message.content == "!wb helper":
        await message.channel.send('https://www.spalmurray.com/wordle-helper')

    if message.content == "!wb help" or message.content == "!wb":
        help_string = "`!wb help` to see this message\n" \
                      "`!wb me` to see your stats\n" \
                      "`!wb average` to see server rankings by average number of guesses\n" \
                      "`!wb rate` to see server rankings by win rate\n" \
                      "`!wb played` to see server rankings by games played\n" \
                      "`!wb streak` to see server rankings by current win streak\n" \
                      "`!wb maxstreak` to see server rankings by maximum win streak\n" \
                      "`!wb missing` to see which Wordles you have not submitted a score for\n" \
                      "`!wb deletemydata` to remove all your scores from wordle-bot (warning: this is not reversible!)"
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
            await message.channel.send("That was lucky!")
        elif score == 2:
            await message.channel.send("Amazing!")
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


def get_member_scores(message) -> list:
    """Return a list of tuples containing member names and their scores."""
    members = [(member.nick if member.nick is not None else member.name, member.id)
               for member in message.guild.members]
    scores = []
    for member in members:
        score = database.get_player_stats(member[1])
        if score[0] == 0:
            continue
        scores.append((member[0], score))
    return scores


def rankings_by_average(message, n: int) -> str:
    """Return a string formatted leaderboard ordered by average guesses where message is the message data from the
    triggering Discord message and n is the max number of rankings to return.
    """
    scores = get_member_scores(message)
    scores.sort(key=lambda x: x[1][0])

    scoreboard = "Rankings by average number of guesses:"
    i = 0
    while i < n and i != len(scores):
        scoreboard += f"\n{i + 1}. {scores[i][0]} ({round(scores[i][1][0], 4)})"
        i += 1

    return scoreboard


def rankings_by_win_rate(message, n: int) -> str:
    """Return a string formatted leaderboard ordered by win rate where message is the message data from the
    triggering Discord message and n is the max number of rankings to return.
    """
    scores = get_member_scores(message)
    scores.sort(key=lambda x: x[1][3], reverse=True)

    scoreboard = "Rankings by win rate:"
    i = 0
    while i < n and i != len(scores):
        scoreboard += f"\n{i + 1}. {scores[i][0]} ({round(scores[i][1][3] * 100, 4)}%)"
        i += 1

    return scoreboard


def rankings_by_games_played(message, n: int) -> str:
    """Return a string formatted leaderboard ordered by number of games played where message is the message data from
    the triggering Discord message and n is the max number of rankings to return.
    """
    scores = get_member_scores(message)
    scores.sort(key=lambda x: x[1][1], reverse=True)

    scoreboard = "Rankings by games played:"
    i = 0
    while i < n and i != len(scores):
        scoreboard += f"\n{i + 1}. {scores[i][0]} ({scores[i][1][1]})"
        i += 1

    return scoreboard


def rankings_by_current_win_streak(message, n: int) -> str:
    """Return a string formatted leaderboard ordered by the length of current win streak where message is the message
    data from the triggering Discord message and n is the maximum number of rankings to return.
    """
    scores = get_member_scores(message)
    scores.sort(key=lambda x: x[1][4], reverse=True)

    scoreboard = "Rankings by current win streak:"
    i = 0
    while i < n and i != len(scores):
        scoreboard += f"\n{i + 1}. {scores[i][0]} ({scores[i][1][4]})"
        i += 1

    return scoreboard


def rankings_by_max_win_streak(message, n: int) -> str:
    """Return a string formatted leaderboard ordered by the length of maximum win streak where message is the message
    data from the triggering Discord message and n is the maximum number of rankings to return.
    """
    scores = get_member_scores(message)
    scores.sort(key=lambda x: x[1][5], reverse=True)

    scoreboard = "Rankings by maximum win streak:"
    i = 0
    while i < n and i != len(scores):
        scoreboard += f"\n{i + 1}. {scores[i][0]} ({scores[i][1][5]})"
        i += 1

    return scoreboard


async def run_player_checks() -> None:
    """Check whether each player has reached or is nearing the 30-day data deletion period and notify the user of the
    relevant information through a DM. If the user is inaccessible through a Discord DM (this happens in the case that
    a user shares no common guild with the bot), then continue as if the user had been notified.

    This is only required for access to Discord's privileged intents, so if you are not using this bot on more than 100
    servers, you can delete this function!

    User data will be deleted after 30 days of inactivity.
    """
    # Get a list of users ids who have not submitted a score in the last 15-29 days:
    nearing_expiry = database.get_nearing_expiry()
    for player in nearing_expiry:
        user = client.get_user(player[0])
        await user.send(f"Hey {user.name}! You haven't submitted a score in {player[1]} days. All of your wordle-bot "
                        f"scores will be permanently deleted after 30 days of inactivity. Please submit a score in the "
                        f"next {29 - player[1]} days if you wish to keep your score data!")

    # Get a list of user ids who have not submitted a score in the last 30 days:
    expired = database.get_expired()
    for player in expired:
        user = client.get_user(player)
        await user.send(f"Hi {user.name}! Unfortunately, since you haven't submitted a new score in the last 30 days, "
                        f"I have deleted your score data from my database in accordance with Discord's user privacy "
                        f"rules. I'll be here if you ever want to start fresh! :)")


# Start up the scheduled player checks to run every 5 days
scheduler = AsyncIOScheduler()
scheduler.add_job(run_player_checks, 'interval', days=5)
scheduler.start()


if __name__ == "__main__":
    print("Starting wordle-bot!")
    config = configuration.Config()
    client.run(config.token)
