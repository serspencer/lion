"""Plugin to manage one's own non-critical roles.

Written by Evan Rupert and Tiger Sachse.
"""
import re
import discord

ADD_COMMAND = "addroles"
LIST_COMMAND = "listroles"
REMOVE_COMMAND = "removeroles"
HAS_ROLE_FORMAT = "--> {0}"
LACKS_ROLE_FORMAT = "    {0}"
LIST_HEADER = "**All server roles:**"
LIST_COMMAND_PATTERN = r"^!{0}$".format(LIST_COMMAND)
ADD_COMMAND_PATTERN = r"^!{0}( \S+)+$".format(ADD_COMMAND)
REMOVE_COMMAND_PATTERN = r"^!{0}( \S+)+$".format(REMOVE_COMMAND)
PERMISSIONS_ERROR = "Insufficent permissions to handle one of your specified roles."
BOT_SPAM_FILE = "data/bot_spam_channel_id.txt"

async def command_addroles(client, message):
    """Give the member new roles."""

    BOT_SPAM_CHANNEL = client.get_channel(int(load_bot_spam_channel_id()))

    roles = await get_roles(client, message, ADD_COMMAND, ADD_COMMAND_PATTERN)
    if roles is None:
        return

    try:
        await message.author.add_roles(*roles)
        response = "{0} Added roles! Check them out with `!{1}`".format(message.author.mention, LIST_COMMAND)
        await message.delete()
        await BOT_SPAM_CHANNEL.send(response)
    except discord.errors.Forbidden:
        user_mention = " {0}".format(message.author.mention)
        perm_error = PERMISSIONS_ERROR + user_mention
        await message.delete()
        await BOT_SPAM_CHANNEL.send(perm_error)


async def command_removeroles(client, message):
    """Remove roles from the member."""

    BOT_SPAM_CHANNEL = client.get_channel(int(load_bot_spam_channel_id()))

    roles = await get_roles(client, message, REMOVE_COMMAND, REMOVE_COMMAND_PATTERN)
    if roles is None:
        return

    try:
        await message.author.remove_roles(*roles)
        response = "{0} Removed roles. Confirm with `!{1}`".format(message.author.mention, LIST_COMMAND)
        await message.delete()
        await BOT_SPAM_CHANNEL.send(response)
    except discord.errors.Forbidden:
        user_mention = " {0}".format(message.author.mention)
        perm_error = PERMISSIONS_ERROR + user_mention
        await message.delete()
        await BOT_SPAM_CHANNEL.send(perm_error)


async def command_listroles(client, message):
    """List all roles available on the server."""

    BOT_SPAM_CHANNEL = client.get_channel(int(load_bot_spam_channel_id()))

    response = get_response(get_server(client), message.author)

    await message.delete()
    await BOT_SPAM_CHANNEL.send(response)


async def get_roles(client, message, command, command_pattern):
    """Get all available roles on the server."""

    BOT_SPAM_CHANNEL = client.get_channel(int(load_bot_spam_channel_id()))

    # First, confirm that the message matches the syntax.
    command_match = re.match(command_pattern, message.content)
    if command_match is None:
        response = "{0}, you've got the {1} syntax wrong. Try `!help`.".format(message.author.mention, command)
        await message.delete()
        await BOT_SPAM_CHANNEL.send(response)

        return None

    # Get all possible roles, and all desired role names from the message content.
    possible_roles = [role for role in get_server(client).roles]
    role_names = set(message.content.split()[1:])

    # Ensure every desired role name is also a possible role. Also save the
    # roles that correspond to the given role names in a list.
    roles = []
    for name in role_names:
        for possible_role in possible_roles:
            if name.lower() == possible_role.name.lower():
                roles.append(possible_role)
                break
        else:
            response = "{0}, `{1}` is not a role. Try `!{2}`.".format(message.author.mention, name, LIST_COMMAND)
            await message.delete()
            await BOT_SPAM_CHANNEL.send(response)

            return None

    return roles


def get_server(client):
    """Get the next (and only) server for the client."""
    return next(iter(client.guilds))


def get_response(server, author):
    """Get a formatted roles list string, with all current roles marked."""
    response = LIST_HEADER + "\n```"
    
    for role in server.roles:
        if role in author.roles:
            response += HAS_ROLE_FORMAT.format(role.name)
        else:
            response += LACKS_ROLE_FORMAT.format(role.name)
        response += "\n"
    response += "```"
    response += "\n{0}, your roles are highlighted with an arrow!".format(author.mention)

    return response

def load_bot_spam_channel_id():
    """Load the Discord API authentication token."""
    with open(BOT_SPAM_FILE, "r") as bot_spam_file:
        return bot_spam_file.read().strip()