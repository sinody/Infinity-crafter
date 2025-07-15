import json
import os.path
import time
from asyncio import WindowsSelectorEventLoopPolicy
import asyncio
from logging import log, debug, info, basicConfig, DEBUG, INFO, WARNING, CRITICAL, ERROR
import emoji
from g4f.client import Client
from g4f.client.stubs import ChatCompletion
from g4f.Provider import Chatai, Blackbox

client = Client(provider=Blackbox)

asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())  # Какая-то штука чтобы рантайма в консоли не было


def get_msg(msg, model="gpt-4", system_msg="", max_tokens=1024, temperature=0.7):
    started = time.time()

    response = client.chat.completions.create([
        {
            "role": "system",
            "content": system_msg
        },
        {
            "role": "user",
            "content": msg
        }
    ], model=model, web_search=False, max_tokens=max_tokens)
    print(f"Post elapsed time: {time.time() - started}")

    return response


def parse_msg(msg: ChatCompletion, model):
    message = msg.choices[-1].message.content
    return [message.strip()]


def reaction(terms: list, model):
    while True:
        started = time.time()

        msg = client.chat.completions.create([

            {
                "role": "user",
                "content": f"СКРЕСТИТЬ: {terms[0]} + {terms[1]}. Верни ТОЛЬКО результат скрещивания в формате: [Эмодзи(Несколько только в крайнем случае)][Название нового элемента]. НЕ СКЛАДЫВАЙ ЭМОДЗИ, А СКРЕЩИВАЙ. Никаких пояснений, описаний или дополнительного текста, не должно содержать + или =. Название может быть любым сочетанием слов, но должно логически следовать из скрещивания и быть креативным."
            }
        ], model=model, web_search=False, max_tokens=64)
        print(f"Post elapsed time: {time.time() - started}")
        msg = parse_msg(msg, model)

        if "+" in msg[-1] or "=" in msg[-1]:
            continue
        msg[-1].replace("Ответ:", "")
        return msg[-1].strip()
        # print("think:", message[0].strip())


basicConfig(level=ERROR)

all_elements = {"💧Вода", "🔥Огонь", "💨Ветер", "⛰Земля"}
selected = []
generated_reactions = {}
inp = ''

if os.path.exists("save.json"):
    with open("save.json", 'r') as f:
        raw_data: dict = json.load(f)
        for key, i in raw_data["generated_reactions"].items():
            generated_reactions[tuple(key.split())] = i
        all_elements = raw_data["all_elements"]


while True:
    if inp in ['ex', 'exit', "вых", "выход"]:
        exit(0)
    elif inp in ["s", 'save', 'sav', "с", "сохран", "сохранить"]:
        with open("save.json", 'w') as f:
            _generated_reactions = {}
            for key, i in generated_reactions.items():
                _generated_reactions[" ".join(key)] = i
            json.dump({
                "generated_reactions": _generated_reactions,
                "all_elements": list(all_elements)
            }, f, indent=4)
    if inp.isnumeric():
        num = int(inp)
        if num < len(all_elements):
            selected.append(list(all_elements)[num])
    elif inp in ["<", "redo", "prev"]:
        selected.pop(-1)

    for num, i in enumerate(all_elements):
        print(num, i)

    if selected:
        print("Выбрано: " + ", ".join(selected) + '.')
        if len(selected) > 1:
            print("Рассчитываем реакцию...")
            if tuple(selected) not in list(generated_reactions.keys()):
                reaction_result = reaction(selected, model="gpt-4o-mini")
            else:
                reaction_result = generated_reactions[tuple(selected)]

            # Проверка есть ли уже похожий элемент
            all_elements_w_emoji = list(map(lambda x: emoji.replace_emoji(x, ""), list(all_elements)))
            if emoji.replace_emoji(reaction_result, "") in list(map(lambda x: emoji.replace_emoji(x, ""), all_elements)):
                reaction_result = list(all_elements)[all_elements_w_emoji.index(emoji.replace_emoji(reaction_result, ""))]

            all_elements.add(reaction_result)
            generated_reactions[tuple(selected)] = reaction_result
            print("Итог: " + reaction_result)
            selected.clear()
            inp = ""
            continue

    inp = input(">").strip()
