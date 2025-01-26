from groq import Groq

def ask_groq(question, content):
    """
    Use Groq's LLM API to get a response based on the uploaded content and the user's question.
    """
    # Initialize Groq client
    client = Groq()

    # Create a conversation with messages (context + question)
    messages = [
        {"role": "system", "content": content},  # You can add your PDF content as context
        {"role": "user", "content": question}   # The user's question
    ]

    # Make the API call for a chat completion
    completion = client.chat.completions.create(
        model="llama3-8b-8192",  # The model you want to use
        messages=messages,
        temperature=1,  # Adjust the creativity of the responses
        max_completion_tokens=1024,  # The max number of tokens in the response
        top_p=1,
        stream=True,
        stop=None
    )

    # Capture the response (groq streams the response)
    response_content = ""
    for chunk in completion:
        response_content += chunk.choices[0].delta.content or ""

    return {"answer": response_content.strip()}
