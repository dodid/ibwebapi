"""
apigen.py

This module provides functionality to generate Python SDK code from OpenAPI specifications.
It utilizes the llmdriver (https://github.com/dodid/llmdriver.git) library to automate the prompt generation process for ChatGPT.

Classes:
    OpenAPIClientPromptGenerator: A class to generate prompts for generating SDK code from OpenAPI specification.

Usage:
    Initialize the OpenAPIClientPromptGenerator with the path to the OpenAPI specification JSON file.
    Use the generator to iterate over API paths and generate SDK code.
    The OpenAPI spec file can be downloaded from the IB Web API website https://api.ibkr.com/gw/api/v3/api-docs
"""

import json
from pathlib import Path

from llmdriver import ChatGPTAutomator, PromptGenerator


class OpenAPIClientPromptGenerator(PromptGenerator):
    """
    A class to generate prompts for generating SDK code from OpenAPI specification.
    Inherits from PromptGenerator and formats the prompts based on the OpenAPI path and method information.
    """

    prompt_template = """
    You are an AI tasked with generating Python SDK code for OpenAPI specifications.
    The following information describes the API path and HTTP method for which SDK code is required.

    Please generate Python client SDK code for the specified API endpoint and methods, following these guidelines:
    - Use best practices in Python SDK development.
    - Include appropriate documentation for input parameters, capture relevant information from the spec.
    - Include appropriate document for return values, including example return values.
    - Ensure that the generated code is clean and maintainable.
    - Only output the generated code. Do not include any other information. Do not repeat existing code.
    - The generated method should fit seamlessly into the following class:

    class IBClient:

        def __init__(self, host: str = "localhost", port: int = 5000, ssl: bool = False) -> None:
            self.url = f"http://{{host}}:{{port}}/v1/api/"
            self.ssl = ssl
            self._account_id = self.get_accounts()[0]["accountId"]

        @property
        def account_id(self) -> str:
            if self._account_id is None:
                raise ValueError("The account_id has not been set.")
            return self._account_id

        def _request(self, method: str, endpoint: str, **kwargs) -> dict:
            url = f"{{self.url}}{{endpoint}}"
            response = requests.request(method, url, verify=self.ssl, **kwargs)
            response.raise_for_status()
            return response.json()

        def get_accounts(self) -> list:
            return self._request("GET", "portfolio/accounts")

    Endpoint:
    {path}

    Methods:
    {method}
    """

    def __init__(self, openapi_spec_file: Path):
        """
        Initializes the prompt generator with the OpenAPI specification file path.

        :param openapi_spec_file: (Path) Path to the OpenAPI specification JSON file.
        """
        self.source = openapi_spec_file
        self.dest = openapi_spec_file.name.replace('.json', '_sdk.py')  # Adjust output file name
        with open(self.source, 'r') as f:
            self.data = json.load(f)  # Load the OpenAPI spec

    def __len__(self):
        """
        Return the number of API paths in the OpenAPI specification.
        """
        return len(self.data.get('paths', {}))

    def __iter__(self):
        """
        Yield formatted prompts for each path-method pair in the OpenAPI specification.
        """
        for path, methods in self.data.get('paths', {}).items():
            yield self.prompt_template.format(path=path, method=json.dumps(methods))

    def handle_response(self, response):
        """
        Handle the response from the model by appending the generated SDK code to the output file.

        :param response: (str) The generated SDK code.
        :param path: (str) The API path for which the code was generated.
        :param method: (str) The HTTP method for which the code was generated.
        """
        with open(self.dest, 'a') as f:
            f.write(response + "\n\n")



if __name__ == "__main__":
    openapi_file = Path('api-docs.json')  # Path to the OpenAPI spec file
    sdk_generator = OpenAPIClientPromptGenerator(openapi_file)

    # Automate SDK generation using ChatGPT
    automator = ChatGPTAutomator(silent=True)
    automator.run(sdk_generator)
