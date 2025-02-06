import re
import ollama

class Generator:
    def __init__(self, model="deepseek-1.5"):
        self.model = model
        self.headers = {"Content-Type": "application/json"}
        self.prompt_template = """ If the user input is a greeting (e.g., ‘Hi’, ‘Hello’, ‘How are you?’, ‘What’s up?’, ‘Bawo ni?’) take it as a direct greeting, 
        respond with a natural and friendly greeting. Otherwise, answer the question based only on the following context:
        {context}
        
        Question: {question}
        
        Answer in clear, concise English. If you don't know the answer, say 'I don't know'. 
        
        Given the context information above I want you to think step by step to answer the query in a crisp manner, incase case you don't know the answer say 'I don't know!'
        """
    
    def _format_prompt(self, context, question):
        joined_context = "\n\n".join(context)
        return self.prompt_template.format(
            context=joined_context,
            question=question
        )
    
    def _extract_answer(self, raw_text):
        cleaned = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL)
        cleaned = re.sub(r'.*?</think>', '', raw_text, flags=re.DOTALL)
        cleaned = re.sub(r'</?think>', '', cleaned, flags=re.IGNORECASE)
        if '<answer>' in cleaned:
            answer_match = re.search(r'<answer>(.*?)</answer>', cleaned, re.DOTALL)
            if answer_match:
                cleaned = answer_match.group(1).strip()
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)  
        cleaned = cleaned.strip()
        return cleaned

    def generate(self, query, context):
        full_prompt = self._format_prompt(context, query)     
        try:
            response = ollama.chat(model=self.model, messages=[{"role": "user", "content": full_prompt}])
            raw = response["message"]["content"].strip()
            print(raw)
            return self._extract_answer(raw)

        except Exception as e:
            print(f"Generation error: {str(e)}")
            return "Sorry, I encountered an error generating the response."
        

      
# generator = Generator()
# print(generator._extract_answer("So, don't provide any additional information beyond what is in the context.\n</think>\n\nI am currently working at Space in Africa."))
# response = generator.generate("What is AI?", ["AI stands for Artificial Intelligence..."])
# print(response)