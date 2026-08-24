from ..LLMAbstractInterface import LLMAbstractInterface
from ..LLMEnums import OpenAIEnums
from openai import OpenAI

class OpenAIProvider(LLMAbstractInterface):

    def __init__(self, api_key: str, api_url: str = None, 
                 default_input_max_characters: int=1000,
                 default_generation_max_output_tokens: int=1000,
                 default_generation_temperature: float=0.1):
        
        self.api_key = api_key
        self.api_url = api_url

        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens    
        self.default_generation_temperature = default_generation_temperature

        self.generaion_model = None

        self.embedding_model = None
        self.embedding_size = None

        self.client = OpenAI(
            api_key= self.api_key,
            api_url= self.api_url
        )
    
    def set_generation_model(self, model_id):
        self.generaion_model = model_id

    def set_embedding_model(self, model_id, embedding_size):
        self.embedding_model = model_id
        self.embedding_size = embedding_size

    def process_text(self, text: str):
        return text[:self.default_input_max_characters].strip()
    
    def generate_text(self, prompt: str,
                      chat_history: list=[], 
                      max_output_tokens: int=None, 
                      temperature: float=None):
        if not self.client:
            print("OpenAI client not initialized. Please check your API key.")
            return None
        
        if not self.generaion_model:
            print("Generation model not set. Please set a generation model before generating text.")
            return None
        
        max_output_tokens = max_output_tokens if max_output_tokens else self.default_generation_max_output_tokens
        temperature = temperature if temperature else self.default_generation_temperature

        chat_history.append(
            self.construct_prompt(
                prompt= prompt,
                role= OpenAIEnums.USER.value
            )
        )

        response = self.client.chat.completions.create(
            model= self.generaion_model,
            messages= chat_history,
            temperature= temperature,
            max_tokens= max_output_tokens
        )

        if not response or not response.choices or len(response.choices) == 0 or not response.choices[0].message:
            print("No response received from OpenAI API.")
            return None
        
        print(f"OpenAI API response:\n {response.choices[0].message}")
        return response.choices[0].message['content']
    
    def embed_text(self, text, document_type = None):
        if not self.client:
            print("Cohere client not initialized. Please check your API key.")
            return None
        
        if not self.embedding_model:
            print("Embedding model not set. Please set an embedding model before generating embeddings.")
            return None

        response = self.client.embeddings.create(
            model= self.embedding_model,
            texts = text,
        )

        if not response or not response.data or len(response.data) == 0 or not response.data[0].embedding:
            print("No embeddings received from OpenAI API.")
            return None
        
        print(f"OpenAI API embeddings response:\n {response.data[0].embedding}")
        return response.data[0].embedding
    
    def construct_prompt(self, prompt, role):
        return {
            "role": role,
            "content": self.process_text(prompt)
        }

    