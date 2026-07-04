import google.generativeai as genai

genai.configure(
    api_key="PASTE_YOUR_NEW_KEY_HERE"
)

try:
    model = genai.GenerativeModel("gemini-1.5-flash")

    response = model.generate_content(
        "Say hello"
    )

    print(response.text)

except Exception as e:
    print("ERROR:")
    print(e)