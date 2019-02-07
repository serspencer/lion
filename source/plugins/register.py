"""Register and unregister from classes to show/hide
them in the sidebar

Written by Sam Shannon
"""

import re
import discord

LIST_COMMAND = "listclasses"
REGISTER_COMMAND = "register"
UNREGISTER_COMMAND = "unregister"

LIST_COMMAND_FORMAT = r"^!{0}$".format(LIST_COMMAND)
REGISTER_COMMAND_FORMAT = r"^!{0}( [a-zA-Z0-9_ ]+)$".format(REGISTER_COMMAND)
UNREGISTER_COMMAND_FORMAT = r"^!{0}( [a-zA-Z0-9_ ]+)$".format(UNREGISTER_COMMAND)

CLASS_PATTERN = re.compile(r"(?P<short>[a-z0-9_]+)_(?P<prof>[a-z]+)$")

ALLOWED_CATEGORIES = ["CLASSES"]

BOT_SPAM_FILE = "data/bot_spam_channel_id.txt"

class Class:
    def __init__(self, name, channel):
        self.name = name
        self.channel = channel

        match = CLASS_PATTERN.match(self.name)
        if match:
            self.short = match.group("short")
            self.prof = match.group("prof")

    def contains_member(self, member):
        return self.channel.permissions_for(member).read_messages


async def command_list(client, message):
    """List the available classes"""

    BOT_SPAM_CHANNEL = client.get_channel(load_bot_spam_channel_id())
    
    response = "**All classes:**\n```\n"

    # show class details
    classes = await get_classes(message.guild)
    for class_ in classes:
        arrow = "-->" if class_.contains_member(message.author) else ""
        response += "{:4}{}\n".format(arrow, class_.name)

    response += "```\n{}, your classes are highlighted with an arrow.\n" \
        "You can manage your classes with `!{}` and `!{}`".format(message.author.mention, REGISTER_COMMAND, UNREGISTER_COMMAND)
    
    await BOT_SPAM_CHANNEL.send(response)
    await message.delete()


async def command_register(client, message):
    """Give member access to requested class channels"""

    BOT_SPAM_CHANNEL = client.get_channel(load_bot_spam_channel_id())

    # check command syntax
    command_match = re.match(REGISTER_COMMAND_FORMAT, message.content)
    if command_match is None:
        response = "{}, that is the incorrect command syntax. Try `!help`.".format(message.author.mention)
        await message.delete()
        await BOT_SPAM_CHANNEL.send(response)
        return

    # get the requested classes
    cfm = await get_classes_from_message(client, message)
    if cfm is None:
        return
    classes = cfm[0]
    isAll = cfm[1]

    # give permissions
    if isAll:
        for category in get_categories(message.guild):
            await category.set_permissions(message.author, read_messages=True)
    else:
        for class_ in classes:
            await class_.channel.set_permissions(message.author, read_messages=True)

    # output the registered classes
    if not isAll:
        response = "{} **Registered classes:**".format(message.author.mention)
        for class_ in classes:
            response += "\n<#{}>".format(class_.channel.id)
    else:
        response = "{}, you have registered all classes.".format(message.author.mention)

    await BOT_SPAM_CHANNEL.send(response)
    await message.delete()

async def command_unregister(client, message):
    """Remove access to requested class channels"""

    BOT_SPAM_CHANNEL = client.get_channel(load_bot_spam_channel_id())
    
    # check command syntax
    command_match = re.match(UNREGISTER_COMMAND_FORMAT, message.content)
    if command_match is None:
        response = "{}, incorrect command syntax. Try `!help`.".format(message.author.mention)
        await BOT_SPAM_CHANNEL.send(response)
        await message.delete()
        return

    # get the requested classes
    cfm = await get_classes_from_message(client, message)
    if cfm is None:
        return
    classes = cfm[0]
    isAll = cfm[1]

    # remove permissions
    if isAll:
        for category in get_categories(message.guild):
            await category.set_permissions(message.author, read_messages=False)
    for class_ in classes:
        await class_.channel.set_permissions(message.author, read_messages=False)

    # reply
    response = "{}, you have unregistered from classes.".format(message.author.mention)
    await BOT_SPAM_CHANNEL.send(response)
    await message.delete()


async def get_classes_from_message(client, message):
    """Get classes user referenced in their message"""

    BOT_SPAM_CHANNEL = client.get_channel(load_bot_spam_channel_id())

    possible_classes = await get_classes(message.guild)
    req_class_names = message.content.split()[1:]

    # if only "all", return all classes
    if len(req_class_names) == 1 and req_class_names[0].lower() == "all":
        return (possible_classes, True)

    # find the requested classes
    req_class_names = set(req_class_names)
    classes = []
    for req_class_name in req_class_names:
        req_class_name = req_class_name.lower()

        # class group
        if "_" not in req_class_name:
            for possible_class in possible_classes:
                if possible_class.short == req_class_name.strip():
                    classes.append(possible_class)
            if len(classes) == 0:
                response = "{}, `{}` is not an available class group. Try `!{}`." \
                    .format(message.author.mention, req_class_name, LIST_COMMAND)
                await BOT_SPAM_CHANNEL.send(response)
                await message.delete()
                return

        # individual class
        else:
            for possible_class in possible_classes:
                if req_class_name == possible_class.name:
                    classes.append(possible_class)
                    break
            else:
                response = "{}, `{}` is not an available class. Try `!{}`." \
                    .format(message.author.mention, req_class_name, LIST_COMMAND)
                await BOT_SPAM_CHANNEL.send(response)
                await message.delete()
                return
    
    return (classes, False)


async def get_classes(guild):
    # get all classes in the ALLOWED_CATEGORIES
    classes = []
    for category in get_categories(guild):
            for channel in category.channels:
                class_ = Class(channel.name, channel)
                classes.append(class_)

    return classes


def get_categories(guild):
    categories = []
    for category in guild.categories:
        if category.name.upper() in ALLOWED_CATEGORIES:
            categories.append(category)
    return categories

def load_bot_spam_channel_id():
    """Load the Discord API authentication token."""
    with open(BOT_SPAM_FILE, "r") as bot_spam_file:
        return bot_spam_file.read().strip()
