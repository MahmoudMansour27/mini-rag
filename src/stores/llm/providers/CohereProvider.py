from ..LLMAbstractInterface import LLMAbstractInterface
from ..LLMEnums import CohereEnums, DocumentTypeEnum
import cohere

class CohereProvider(LLMAbstractInterface):

    def __init__(self, api_key: str,
                 default_input_max_characters: int=1000,
                 default_generation_max_output_tokens: int=1000,
                 default_generation_temperature: float=0.1):
        
        self.api_key = api_key
        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens    
        self.default_generation_temperature = default_generation_temperature

        self.generaion_model = None

        self.embedding_model = None
        self.embedding_size = None

        self.client = cohere.ClientV2(api_key= self.api_key)
        self.enums = CohereEnums

    
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
            print("Cohere client not initialized. Please check your API key.")
            return None
        
        if not self.generaion_model:
            print("Generation model not set. Please set a generation model before generating text.")
            return None
        
        max_output_tokens = max_output_tokens if max_output_tokens else self.default_generation_max_output_tokens
        temperature = temperature if temperature else self.default_generation_temperature
        messages= [
            chat_history,
            { 
                "role": "user",
                "content": self.process_text(prompt)
            }
        ]

        print(prompt)

        response = self.client.chat(
            model= self.generaion_model,
            messages= messages,
            temperature= temperature,
            max_tokens= max_output_tokens
        )

        if not response or not response.message:
            print("No response received from Cohere API.")
            return None
        
        print(f"Cohere API response:\n {response}")

        response_dict = response.message.content[0].model_dump()
        print(f"Answer dict:\n {response_dict}")

        final_answer = ""
        if response_dict.get("type") == "thinking":
            print("Thinking:", response_dict.get("thinking"))
            final_answer = response_dict.get("thinking")
        elif response_dict.get("type") == "text":
            print("Response:", response_dict.get("text"))
            final_answer = response_dict.get("text")

        return final_answer
    
    def embed_text(self, text, document_type = None):
        if not self.client:
            print("Cohere client not initialized. Please check your API key.")
            return None
        
        if not self.embedding_model:
            print("Embedding model not set. Please set an embedding model before generating embeddings.")
            return None
        
        input_type = CohereEnums.DOCUMENT.value
        if document_type == DocumentTypeEnum.QUERY.value:
            input_type = CohereEnums.QUERY.value

        response = self.client.embed(
            model= self.embedding_model,
            texts = [self.process_text(text)],
            input_type= input_type,
            embedding_types=['float'],
            output_dimension = self.embedding_size
        )

        if not response or not response.embeddings or not response.embeddings.float:
            print("No embeddings received from Cohere API.")
            return None
        
        print(f"Cohere API embeddings response:\n {response.embeddings.float[0]}")
        return response.embeddings.float[0]

    def construct_prompt(self, prompt, role):
        return {
            "role": role,
            "content": self.process_text(prompt)
        }
