import requests
import re

class Generator:
    def __init__(self, model_url="http://localhost:1234/v1"):
        self.model_url = model_url
        self.headers = {"Content-Type": "application/json"}
        self.prompt_template = """
        Answer the question based only on the following context:
        {context}
        
        Question: {question}
        
        Answer in clear, concise English. If you don't know the answer, say 'I don't know'. Answer must be from only the context and not even from your own understanding of the question."""
    
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
        payload = {
            "prompt": full_prompt,
            "temperature": 0.7,
            "max_tokens": 500
        }   
        try:
            response = requests.post(
                f"{self.model_url}/completions",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            raw = response.json()["choices"][0]["text"].strip()
            return self._extract_answer(raw)
        
        except Exception as e:
            print(f"Generation error: {str(e)}")
            return "Sorry, I encountered an error generating the response."
        

      
# generator = Generator()
# print(generator._extract_answer("So, don't provide any additional information beyond what is in the context.\n</think>\n\nI am currently working at Space in Africa."))
# response = generator.generate("What is AI?", ["AI stands for Artificial Intelligence..."])
# print(response)