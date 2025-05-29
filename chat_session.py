# chat_session.py
import json
import requests
from config import API_KEY, API_URL, MODEL_NAME, SYSTEM_PROMPT


class ChatSession:
    def __init__(self, system_prompt=SYSTEM_PROMPT):
        self.history = []
        self.total_tokens = 0
        if system_prompt:
            self._add_message("system", system_prompt)

    def generate_prompt(self, user_input):
        return f"""
        {SYSTEM_PROMPT}
        当前对话上下文：{self.history[-2:] if self.history else '无'}
        用户最新输入：{user_input}
        """

    def stream_response(self, user_input):
        """流式响应生成器"""
        full_prompt = self.generate_prompt(user_input)
        self._add_message("user", full_prompt)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }

        data = {
            "model": MODEL_NAME,
            "messages": self.history[-5:],
            "temperature": 0.7,
            "max_tokens": 1024,
            "top_p": 0.9,
            "stream": True
        }

        response = requests.post(API_URL, headers=headers, json=data, stream=True)
        response.raise_for_status()

        full_response = []
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith('data:'):
                    json_str = decoded_line[5:].strip()
                    if json_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(json_str)
                        content = chunk['choices'][0]['delta'].get('content', '')
                        if content:
                            full_response.append(content)
                            yield content
                    except:
                        continue

        self._add_message("assistant", "".join(full_response))

    def _add_message(self, role, content):
        self.history.append({"role": role, "content": content})