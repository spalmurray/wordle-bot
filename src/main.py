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
        stats_string = f"{player}'s average number of guesses is {stats[0]}. They've played {stats[1]} games and won " \
                       f"{stats[2]} games, making their win rate {stats[3] * 100}%."
        await message.channel.send(stats_string)

    if message.content == "!wb helper":
        await message.channel.send('https://www.spalmurray.com/wordle-helper')

    if message.content == "!wb help" or message.content == "!wb":
        help_string = "`!wb help` to see this message\n" \
                      "`!wb me` to see your stats\n" \
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


if __name__ == "__main__":
    config = configuration.Config()
    client.run(config.token)
