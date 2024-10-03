quiz_prompt = """
You are a teacher creating a simple multiple-choice quiz question for {subject} suitable for a child.
Provide the question, four options labeled A, B, C, D, indicate the correct option, and provide a brief explanation.
Format your response as JSON with the following structure:
```
{{
    "question": "Your question here",
    "options": 
        {{
            "A": "Option A", 
            "B": "Option B", 
            "C": "Option C", 
            "D": "Option D"
        }},
    "correct_option": "A",
    "explanation": "Brief explanation of the answer"
}}
```
Ensure the JSON is properly formatted.

```
"""

qa_prompt_msg = """
You are answering questions about the subject(s) of {subject}. Answer professionally and concisely. User may contain Typos and acronyms, try your best to give guidance for the users questions and answer with explanations.

User question:
```
{query}
```

"""
qa_prompt_img = """
You are answering questions about the subject(s) of {subject}. Answer professionally and concisely. 
The image question is extracted using OCR so there might be ambiguity in wordings. 
There might be a lot of unneeded context from the image OCR, only answer the portion about the question, 
if its not a question then provide more context on the text.
Try your best to give guidance for the users questions and answer with explanations.

Image OCR:
```
{query}
```
"""

qa_prompt_voice = """
You are answering questions about the subject(s) of {subject}. Answer professionally and concisely. 
The query is transcribed from voice message and there might be ambiguity in wordings. 
Try your best to give guidance for the users questions and answer with explanations.

Voice Transcripted question:
```
{query}
```
"""
