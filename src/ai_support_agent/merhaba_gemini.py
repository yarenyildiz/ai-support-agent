from google import genai

client = genai.Client()

cevap = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents="İnstagram kaç senesinde kuruldu",
)

print(cevap.text)
