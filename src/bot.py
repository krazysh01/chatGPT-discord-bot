import discord
import os
import openai
from random import randrange
from discord import app_commands
from src import responses
from src import log
from src import art
from src import personas


logger = log.setup_logger(__name__)

isPrivate = False
isReplyAll = False
listenChannel = None

class aclient(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.activity = discord.Activity(type=discord.ActivityType.listening, name="/chat | /help")

async def send_message(message, user_message):
    isReplyAll = os.getenv("REPLYING_ALL")
    if isReplyAll == "False":
        author = message.user.id
        await message.response.defer(ephemeral=isPrivate)
    else:
        author = message.author.id
    try:
        response = (f'> **{user_message}** - <@{str(author)}' + '> \n\n')
        chat_model = os.getenv("CHAT_MODEL")
        if chat_model == "OFFICIAL":
            response = f"{response}{await responses.official_handle_response(user_message)}"
        elif chat_model == "UNOFFICIAL":
            response = f"{response}{await responses.unofficial_handle_response(user_message)}"
        char_limit = 1900
        if len(response) > char_limit:
            # Split the response into smaller chunks of no more than 1900 characters each(Discord limit is 2000 per chunk)
            if "```" in response:
                # Split the response if the code block exists
                parts = response.split("```")

                for i in range(len(parts)):
                    if i%2 == 0: # indices that are even are not code blocks
                        if isReplyAll == "True":
                            await message.channel.send(parts[i])
                        else:
                            await message.followup.send(parts[i])

                    else: # Odd-numbered parts are code blocks
                        code_block = parts[i].split("\n")
                        formatted_code_block = ""
                        for line in code_block:
                            while len(line) > char_limit:
                                # Split the line at the 50th character
                                formatted_code_block += line[:char_limit] + "\n"
                                line = line[char_limit:]
                            formatted_code_block += line + "\n"  # Add the line and seperate with new line

                        # Send the code block in a separate message
                        if (len(formatted_code_block) > char_limit+100):
                            code_block_chunks = [formatted_code_block[i:i+char_limit]
                                                 for i in range(0, len(formatted_code_block), char_limit)]
                            for chunk in code_block_chunks:
                                if isReplyAll == "True":
                                    await message.channel.send(f"```{chunk}```")
                                else:
                                    await message.followup.send(f"```{chunk}```")
                        elif isReplyAll == "True":
                            await message.channel.send(f"```{formatted_code_block}```")
                        else:
                            await message.followup.send(f"```{formatted_code_block}```")

            else:
                response_chunks = [response[i:i+char_limit]
                                   for i in range(0, len(response), char_limit)]
                for chunk in response_chunks:
                    if isReplyAll == "True":
                        await message.channel.send(chunk)
                    else:
                        await message.followup.send(chunk)
        elif isReplyAll == "True":
            await message.channel.send(response)
        else:
            await message.followup.send(response)
    except Exception as e:
        if isReplyAll == "True":
            await message.channel.send("> **Error: Something went wrong, please try again later!**")
        else:
            await message.followup.send("> **Error: Something went wrong, please try again later!**")
        logger.exception(f"Error while sending message: {e}")


async def send_start_prompt(client):
    import os.path

    config_dir = os.path.abspath(__file__ + "/../../config/")
    prompt_name = 'starting-prompt.txt'
    prompt_path = os.path.join(config_dir, prompt_name)
    try:
        if os.path.isfile(prompt_path) and os.path.getsize(prompt_path) > 0:
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt = f.read()
                if (listenChannel):
                    logger.info(f"Send starting prompt with size {len(prompt)}")
                    chat_model = os.getenv("CHAT_MODEL")
                    response = ""
                    if chat_model == "OFFICIAL":
                        response = f"{response}{await responses.official_handle_response(prompt)}"
                    elif chat_model == "UNOFFICIAL":
                        response = f"{response}{await responses.unofficial_handle_response(prompt)}"
                    channel = client.get_channel(int(discord_channel_id))
                    await channel.send(response)
                    logger.info(f"Starting prompt response:{response}")
                else:
                    logger.info("No Channel selected. Skip sending starting prompt.")
        else:
            logger.info(f"No {prompt_name}. Skip sending starting prompt.")
    except Exception as e:
        logger.exception(f"Error while sending starting prompt: {e}")


def run_discord_bot():
    global listenChannel
    client = aclient()
    persona_choices = [
        app_commands.Choice(name="Random", value="random"),
    ]
    for persona in personas.PERSONAS.keys() :
        persona_choices.append(app_commands.Choice(name=persona, value=persona))

    personas.current_persona = os.getenv("DEFAULT_PERSONA")

    @client.event
    async def on_ready():
        await send_start_prompt(client)
        await client.tree.sync()
        logger.info(f'{client.user} is now running!')


    @client.tree.command(name="ask", description="Ask assistant a Question")
    async def ask(interaction: discord.Interaction, *, message: str):
        if interaction.user == client.user:
            return
        username = str(interaction.user)
        channel = str(interaction.channel)
        logger.info(
            f"\x1b[31m{username}\x1b[0m : /chat [{message}] in ({channel})")
        await send_message(interaction, message)

    @client.tree.context_menu(name="Answer Question")
    async def answer(interaction: discord.Interaction, message: discord.Message):
        if interaction.user == client.user:
            return
        username = str(interaction.user)
        channel = str(interaction.channel)
        logger.info(
            f"\x1b[31m{username}\x1b[0m : answered [{message}] in ({channel})")
        await send_message(interaction, message.content)

    @client.tree.command(name="help", description="Show help for the bot")
    async def help(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send(""":star:**BASIC COMMANDS** \n
        - `/ask [message]` Ask assistant a question
        - `""")

        logger.info(
            "\x1b[31mSomeone needs help!\x1b[0m")

    @client.tree.command(name="switchpersona", description="Switch between optional chatGPT jailbreaks")
    @app_commands.choices(persona=persona_choices)
    async def chat(interaction: discord.Interaction, persona: app_commands.Choice[str]):
        isReplyAll =  os.getenv("REPLYING_ALL")
        if isReplyAll == "True":
            await interaction.response.defer(ephemeral=False)
            await interaction.followup.send(
                "> **Warn: You already on replyAll mode. If you want to use slash command, switch to normal mode, use `/replyall` again**")
            logger.warning("\x1b[31mYou already on replyAll mode, can't use slash command!\x1b[0m")
            return
        if interaction.user == client.user:
            return

        await interaction.response.defer(thinking=True)
        username = str(interaction.user)
        channel = str(interaction.channel)
        logger.info(
            f"\x1b[31m{username}\x1b[0m : '/switchpersona [{persona.value}]' ({channel})")

        persona = persona.value

        if persona == personas.current_persona:
            await interaction.followup.send(f"> **Warn: Already set to `{persona}` persona**")

        elif persona == "standard":
            personas.current_persona = "standard"
            await interaction.followup.send(
                f"> **Info: Switched to `{persona}` persona**")

        elif persona == "random":
            choices = list(personas.PERSONAS.keys())
            choice = randrange(0, 6)
            chosen_persona = choices[choice]
            personas.current_persona = chosen_persona
            # await responses.switch_persona(chosen_persona)
            await interaction.followup.send(
                f"> **Info: Switched to `{chosen_persona}` persona**")

        elif persona in personas.PERSONAS:
            try:
                personas.current_persona = persona
                await interaction.followup.send(
                f"> **Info: Switched to `{persona}` persona**")
            except Exception as e:
                await interaction.followup.send(
                    "> **Error: Something went wrong, please try again later! 😿**")
                logger.exception(f"Error while switching persona: {e}")

        else:
            await interaction.followup.send(
                f"> **Error: No available persona: `{persona}` 😿**")
            logger.info(
                f'{username} requested an unavailable persona: `{persona}`')

    TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    listenChannel = os.getenv("DISCORD_CHANNEL_ID")

    client.run(TOKEN)
