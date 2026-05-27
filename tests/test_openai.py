from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-4.1-mini",
    input="Dime hola en español"
)

print(response.output[0].content[0].text)


