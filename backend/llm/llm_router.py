import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

load_dotenv()

# Initialize the Groq model
llm = ChatGroq(
    temperature=0,
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

def call_llm(prompt: str, model_type="groq"):
    try:
        if model_type == "groq":
            response = llm.invoke([HumanMessage(content=prompt)])
            return response.content
        return f"Mocked LLM Response for prompt: {prompt[:50]}..."
    except Exception as e:
        return f"Error calling LLM: {str(e)}"
