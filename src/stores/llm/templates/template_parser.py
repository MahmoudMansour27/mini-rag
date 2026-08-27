import os

class TemplateParser:
    def __init__(self, language: str= None, default_language: str= "en"):
        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.default_language = default_language
        self.language = None

        self.set_language(language)

    def set_language(self, language: str):
        if not language:
            self.language = self.default_language

        language_path = os.path.join(self.current_path, "locales", language)
        if os.path.exists(language_path):
            self.language = language
        else:
            self.language = self.default_language

    # get function
    def get(self, group: str, key: str, var: dict = {}):
        if not group or not key:
            print("Group and key are required")
            return None

        group_path = os.path.join(self.current_path, "locales", self.language, f"{group}.py")
        targeted_language = self.language
        if not os.path.exists(group_path):
            print(f"Group '{group}' not found for language '{self.language}', falling back to default language '{self.default_language}'")
            group_path = os.path.join(self.current_path, "locales", self.default_language, f"{group}.py")
            targeted_language = self.default_language

        if not os.path.exists(group_path):
            print(f"Group '{group}' not found for default language '{self.default_language}'")
            return None

        # import the group file dynamically
        module = __import__(f"stores.llm.templates.locales.{targeted_language}.{group}", fromlist=[group])

        if not module:
            print(f"Group '{group}' not found for language '{self.language}'")
            return None

        key_attribute = getattr(module, key)
        return key_attribute.substitute(vars)
        


