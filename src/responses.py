from revChatGPT.V1 import Chatbot
from dotenv import load_dotenv
import os

load_dotenv()
openAI_key = os.getenv("OPENAI_KEY")
openAI_status = os.getenv("OPENAI_STATUS")
chatbot = Chatbot(config={
    "access_token": openAI_key,
    "paid": openAI_status == "TRUE"
})

async def handle_response(message) -> str:
    for response in chatbot.ask(message):
        responseMessage = response["message"]

    return responseMessage