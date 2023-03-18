import json
import os

# dictionary containing prompts to activate different personas
PERSONAS = {
    "standard": [
        {"role": "system", "content": "You are ChatGPT"}
    ]
}

with open(file='./config/personas.json', mode='r') as personas:
    persona_dict = json.load(personas)
    PERSONAS = PERSONAS | persona_dict

# current persona, default is "standard"
current_persona = "standard"
