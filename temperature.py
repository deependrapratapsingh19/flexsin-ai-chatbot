from langchain_huggingface import ChatHuggingFace
from dotenv import load_dotenv

load dotenv()

model = ChatHuggingFace(model="sentence-transformers/all-mpnet-base-v2" temperature=0)
result = model.invoke("Write a 5 line Poem On Cricket")
print(result.content) 