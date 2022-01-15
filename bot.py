from time import sleep
import discord
import os
import datetime

# Parameters
USAGE_WINDOW = datetime.timedelta(0, 60 * 15)
VOTE_DURATION = datetime.timedelta(0, 60)
SILENCE_ROLE_NAME = "silence"
MOD_CHANNEL_NAME = "general"
NUM_VOTES = 1

# Initialisation
intents = discord.Intents.default()
intents.members = True
intents.guilds = True

client = discord.Client(intents = intents)

silence_role = None
mod_channel = None

# Get the mod channel and silence role from the guild.
async def setup(message):
    global silence_role
    global mod_channel

    # Find silencing role
    silence_role = discord.utils.get(message.guild.roles, name=SILENCE_ROLE_NAME)
    if silence_role == None:
        await message.channel.send('Configured silencing role does not exist')
        return
    await message.channel.send(f'Silencing role set to {silence_role.name}')

    # Find mod channel
    mod_channel = discord.utils.get(message.guild.channels, name=MOD_CHANNEL_NAME)
    if mod_channel == None:
        await message.channel.send('Configured mod channel does not exist')
        return
    await message.channel.send(f'Mod channel set to {mod_channel.name}')

# Clear up the messages sent by the spammer.
async def cleanup(user, channel):
    # Save and delete the user's messages
    user_messages = []
    async for m in channel.history(after=user.joined_at):
        if m.author == user:
            user_messages.append(m)
            await m.delete()

    # Send the message list to the mod channel
    await mod_channel.send(f"User {user.name} sent ||{', '.join([m.content for m in user_messages])}||")


# Events
@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    global silence_role
    global mod_channel
    
    if message.author == client.user:
        return

    if message.content.startswith("!spamstop setup") and message.author.permissions_in(message.channel).manage_channels:
        await setup(message)

    if client.user in message.mentions:
        # Bot has been pinged, find the most recently joined member
        new_user = sorted(message.channel.members, key=lambda x: x.joined_at, reverse=True)[0]

        if datetime.datetime.utcnow() - new_user.joined_at < USAGE_WINDOW:
            # Silence the user temporarily
            await new_user.add_roles(silence_role)

            # Start the vote
            vote = await message.channel.send(f"React ✅ to silence, {NUM_VOTES} needed")
            await vote.add_reaction("✅")

            vote_start = datetime.datetime.utcnow()

            while datetime.datetime.utcnow() < vote_start + VOTE_DURATION:
                vote = await message.channel.fetch_message(vote.id)
                vote_count = discord.utils.get(vote.reactions, emoji="✅").count

                if vote_count >= NUM_VOTES + 1:
                    await cleanup(new_user, message.channel)
                    return

                sleep(1)

            await message.channel.send("Vote expired.")

            # Unsilence the user
            await new_user.remove_roles(silence_role)

        else:
            await message.channel.send(f"{new_user.name} joined too long ago. Please alert the moderators if there are any issues.")

client.run(os.getenv('SPAMSTOP_TOKEN'))

