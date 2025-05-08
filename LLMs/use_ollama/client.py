""" 通用封装 """
import requests
import json

class OllamaClient:
    def __init__(self, model_name="llama2", host="http://localhost:11434"):
        self.model = model_name
        self.api_url = f"{host}/api/generate"

    def generate(self, prompt: str, stream: bool = False, **options) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
        }
        payload.update(options)

        response = requests.post(self.api_url, json=payload, stream=stream)
        if not response.ok:
            raise RuntimeError(f"Request failed: {response.status_code}: {response.text}")

        if stream:
            return self._parse_streaming(response)
        else:
            return response.json().get("response", "")

    def _parse_streaming(self, response) -> str:
        result = ""
        for line in response.iter_lines():
            if line:
                line_json = json.loads(line.decode("utf-8"))
                result += line_json.get("response", "")
        return result
