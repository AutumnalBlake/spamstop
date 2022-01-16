from time import sleep
import discord
import os
import datetime
import asyncio

# Parameters
USAGE_WINDOW = datetime.timedelta(0, 60 * 15)
VOTE_DURATION = datetime.timedelta(0, 60)
SILENCE_ROLE_NAME = "silence"
NUM_VOTES = 1

# Initialisation
intents = discord.Intents.default()
intents.members = True
intents.guilds = True

client = discord.Client(intents = intents)


# Clear up the messages sent by the spammer.
async def cleanup(user, guild):
    # Save and delete the user's messages
    user_messages = []
    for ch in guild.channels:
        async for m in ch.history(after=user.joined_at):
            if m.author == user:
                user_messages.append(f"#{ch.name}: ||{m.content}||")
                await m.delete()

    # Send the message list to the mod channel
    update_ch = guild.public_updates_channel if guild.public_updates_channel else guild.channels[0]
    await update_ch.send(f"Removed messages from user {user.name}.")
    for ln in user_messages:
        await update_ch.send(ln)


# Events
@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))
    print(f'Active in {", ".join(g.name for g in client.guilds)}')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if client.user in message.mentions:
        # Bot has been pinged, find the most recently joined member
        new_user = sorted(message.channel.members, key=lambda x: x.joined_at, reverse=True)[0]

        silence_role = discord.utils.get(message.guild.roles, name="Timeout Corner")
        # If there is no silence role, create one

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

                asyncio.sleep(1)

            await message.channel.send("Vote expired.")

            # Unsilence the user
            await new_user.remove_roles(silence_role)

        else:
            await message.channel.send(f"{new_user.name} joined too long ago. Please alert the moderators if there are any issues.")

client.run(os.getenv('SPAMSTOP_TOKEN'))

