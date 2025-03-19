import json
import openai

with open("config.json", "r") as file:
    config = json.load(file)
embedding_url = config.get("gpt40_mini_url")
embedding_key = config.get("gpt40_mini_key")

openai_client = openai.AzureOpenAI(
    api_key=embedding_key,
    api_version="2024-10-21",
    azure_endpoint=embedding_url)


def calculate_llm_answer(system_prompt, user_prompt, temp=0.1, max_tokens=100):
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temp,
        max_tokens=max_tokens
    )

    return response.choices[0].message.content