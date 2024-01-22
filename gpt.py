"""oepnAI 사용 예제"""
from openai import OpenAI

client = OpenAI()


async def gpt3_turbo(question):
    """GPT3.5 turbo에게 물어보기"""
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "Answer questions as if you were talking to a close friend.",
            },
            {
                "role": "system",
                "content": "Just answer the questions asked and don't use flowery language.",
            },
            {
                "role": "user",
                "content": question,
            },
        ],
    )
    print(completion.choices[0].message)
    return completion.choices[0].message.content
