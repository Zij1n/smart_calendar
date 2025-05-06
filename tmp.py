from google import genai

client = genai.Client(api_key="AIzaSyBhQBPGExmEWSosI_uCVHgTM-JTVINAoIY")


print("List of models that support generateContent:\n")
for m in client.models.list():
    for action in m.supported_actions:
        if action == "generateContent":
            print(m.name)
