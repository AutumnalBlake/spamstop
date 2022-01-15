import discord
import os
import datetime

USAGE_WINDOW = datetime.timedelta(0, 60 * 15)
SILENCE_ROLE_NAME = "silence"
MOD_CHANNEL_NAME = "general"

intents = discord.Intents.default()
intents.members = True
intents.guilds = True

client = discord.Client(intents = intents)

silence_role = None
mod_channel = None

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
        # Find silencing role
        try:
            silence_role = [r for r in message.guild.roles if r.name == SILENCE_ROLE_NAME][0]
        except IndexError:
            await message.channel.send('Configured silencing role does not exist')
        await message.channel.send(f'Silencing role set to {silence_role.name}')

        # Find mod channel
        try:
            mod_channel = [c for c in message.guild.channels if c.name == MOD_CHANNEL_NAME][0]
        except IndexError:
            await message.channel.send('Configured mod channel does not exist')
        await message.channel.send(f'Mod channel set to {mod_channel.name}')


    if client.user in message.mentions:
        # Bot has been pinged, find the most recently joined member
        new_user = sorted(message.channel.members, key=lambda x: x.joined_at, reverse=True)[0]
        print(new_user)

        joined_time = datetime.datetime.utcnow() - new_user.joined_at

        if joined_time < USAGE_WINDOW:
            # Silence the user
            await new_user.add_roles(silence_role)

            # Save and delete the user's messages
            user_messages = []
            async for m in message.channel.history(after=new_user.joined_at):
                if m.author == new_user:
                    user_messages.append(m)
                    await m.delete()

            # Send the message list to the mod channel
            await mod_channel.send(f"User {new_user.name} sent ||{', '.join([m.content for m in user_messages])}||")

        else:
            await message.channel.send(f"{new_user.name} joined too long ago. Please alert the moderators if there are any issues.")

client.run(os.getenv('SPAMSTOP_TOKEN'))