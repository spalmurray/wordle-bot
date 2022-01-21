import configuration
import discord

client = discord.Client()


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("Wordle "):
        await message.channel.send('nice one mate')


if __name__ == "__main__":
    config = configuration.Config()
    client.run(config.token)
