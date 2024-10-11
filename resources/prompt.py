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


qa_prompt_msg2 = """
Here are some sources that may be relevant to the question below, quote these sources if necessary, if no sources provide then use your own knowledge. 
Sources:
```
{sources}
```
You are answering questions about the subject(s) of {subject}. Answer professionally and concisely. User may contain Typos and acronyms, try your best to give guidance for the users questions and answer with explanations.
answer with MARKDOWNs, and ALWAYS provide associate link from the sources, never provide tables and code blocks.

```Example:
User question:
What is the PM life cycle?
Answer:

Project management life cycles can vary across industries and project types, and variations such as iterative or agile approaches might be utilized depending on project needs.

The life cycle serves as a framework that guides project teams to systematically achieve project deliverables.

For further detailed insight, you can refer to the [PMBOK Guide](http://23.98.93.88:8081/view-pdf/datasources/Project%20Management/A_Guide_to_the_Project_Management_Body_of_Knowledge_PMBOK_Project_Management_Institute_7_2021_Project_Management_Institute.pdf#page=318), which provides an extensive overview of project management practices.
```

User question:
```
{query}
```
"""
