import inspect
import json
import time

import openai
from src.conf.config import settings
# Ваші функції з імпортуємого файлу
from src.repository import users, contacts
from src.routes import auth as routes_auth, contacts as routes_contacts, users as routes_users
from src.services import auth, email

openai.api_key = settings.openai_api_key


def generate_documentation(func, example_func, example_docstring):
    prompt = f'You are documentation module for Python witch read a function and returns string like in response example\nIndent:0 spaces\n\nCreate documentation for function: {func}\n\nExample func:{example_func}\n\nResponse example: {example_docstring}'
    time.sleep(34)  # Якщо використовуємо безкоштовну підписку
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        temperature=0.2,
        max_tokens=300
    )

    doc_func = response.choices[0].text.strip()
    # response = openai.ChatCompletion.create(
    #     model="gpt-3.5-turbo",
    #     messages=[
    #         {"role": "system", "content": "You are documentation module for Python witch read a function and returns string like in response example"},
    #         {"role": "user", "content": f'Indent:0 spaces\n\nCreate documentation for function: {func}\n\nExample func:{example_func}\n\nResponse example: {example_docstring}'}
    #     ]
    # )
    #
    # doc_func = response.choices[0].message.get('content')
    print(doc_func)
    return doc_func


def correct_prompt(func):
    with open('example.json', 'r') as json_file:
        file = json.load(json_file)
    from src.repository.users import confirmed_email as example_func
    docstring = file['confirmed_email']
    documentation = generate_documentation(func, example_func, docstring)
    return documentation


def check_documentation(func):
    docstring = correct_prompt(func)
    if not docstring.startswith('"""') and not docstring.endswith('"""'):
        print('trying new prompt')
        return check_documentation(func)
    return docstring



def write_docstring(module):
    generated_documentation = {}
    for function_name in dir(module):
        function = getattr(module, function_name)
        if callable(function) and not isinstance(function, type):
            documentation = check_documentation(function)
            generated_documentation[function_name] = documentation

    module_full_name = module.__name__
    module_documentation = {module_full_name: generated_documentation}
    with open('docs.json', 'a') as json_file:
        json.dump(module_documentation, json_file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    lst_modules = [auth, email]
    for module in lst_modules:
        write_docstring(module)
