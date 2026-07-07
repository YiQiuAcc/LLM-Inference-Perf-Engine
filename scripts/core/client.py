import json
import time
from urllib import request, error


def _parse_ollama_stream(resp, start_time):
    """逐行读取 Ollama SSE 流, 返回 (latency, response_time, token_count, status_code)"""
    latency = 0.0
    first_token_received = False
    token_count = 0
    eval_count = 0

    for raw_line in resp:
        line = raw_line.decode("utf-8", errors="ignore").strip()
        if not line.startswith("data: "):
            continue
        data_str = line[6:].strip()
        if data_str == "[DONE]":
            continue
        data = json.loads(data_str)
        if "response" in data:
            if not first_token_received:
                latency = time.time() - start_time
                first_token_received = True
            token_count += 1
        if data.get("done"):
            eval_count = data.get("eval_count", 0)

    final_tokens = eval_count if eval_count > 0 else token_count
    return latency, time.time() - start_time, final_tokens, resp.status


def _parse_vllm_stream(resp, start_time):
    """逐行读取 vLLM SSE 流, 返回 (latency, response_time, token_count, status_code)"""
    latency = 0.0
    first_token_received = False
    token_count = 0

    for raw_line in resp:
        line = raw_line.decode("utf-8", errors="ignore").strip()
        if not line.startswith("data: "):
            continue
        data_str = line[6:].strip()
        if data_str == "[DONE]":
            continue
        data = json.loads(data_str)
        choices = data.get("choices", [])
        if choices:
            delta = choices[0].get("delta", {})
            if "content" in delta:
                if not first_token_received:
                    latency = time.time() - start_time
                    first_token_received = True
                token_count += 1

    return latency, time.time() - start_time, token_count, resp.status


class _BaseClient:
    """客户端基类, 封装 HTTP 请求公共逻辑"""

    def __init__(self, base_url: str, model: str, prompt: str, timeout: int = 600):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.prompt = prompt
        self.timeout = timeout

    def _do_request(self, url: str, payload: bytes, headers: dict, stream: bool):
        """发送 HTTP POST 请求, 根据 stream 模式决定解析方式"""
        req = request.Request(url, data=payload, headers=headers, method="POST")
        try:
            start = time.time()
            with request.urlopen(req, timeout=self.timeout) as resp:
                if stream:
                    return self._parse_stream(resp, start)
                else:
                    return self._parse_nonstream(resp, start)
        except error.HTTPError as e:
            raise RuntimeError(f"HTTP {e.code}: {e.reason}")
        except error.URLError as e:
            raise RuntimeError(f"连接失败: {e.reason}")
        except Exception as e:
            raise RuntimeError(f"请求异常: {str(e)}")

    def _parse_nonstream(self, resp, start_time):
        raise NotImplementedError

    def _parse_stream(self, resp, start_time):
        raise NotImplementedError


class OllamaStressClient(_BaseClient):
    """Ollama API 压测客户端"""

    def _make_payload(self, stream: bool) -> bytes:
        return json.dumps(
            {
                "model": self.model,
                "prompt": self.prompt,
                "stream": stream,
                "options": {"temperature": 0.7, "num_predict": 2048},
            }
        ).encode("utf-8")

    def send_chat_request(self):
        payload = self._make_payload(False)
        headers = {"Content-Type": "application/json"}
        return self._do_request(
            f"{self.base_url}/api/generate", payload, headers, False
        )

    def send_stream_request(self):
        payload = self._make_payload(True)
        headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
        return self._do_request(f"{self.base_url}/api/generate", payload, headers, True)

    def _parse_nonstream(self, resp, start_time):
        raw = resp.read()
        end = time.time()
        result = json.loads(raw.decode("utf-8"))
        return 0.0, end - start_time, result.get("eval_count", 0), resp.status

    def _parse_stream(self, resp, start_time):
        return _parse_ollama_stream(resp, start_time)


class VLLMStressClient(_BaseClient):
    """vLLM API 压测客户端(OpenAI 兼容端点)"""

    def _make_payload(self, stream: bool) -> bytes:
        return json.dumps(
            {
                "model": self.model,
                "messages": [{"role": "user", "content": self.prompt}],
                "stream": stream,
                "max_tokens": 2048,
                "temperature": 0.7,
            }
        ).encode("utf-8")

    def send_chat_request(self):
        payload = self._make_payload(False)
        headers = {"Content-Type": "application/json"}
        return self._do_request(
            f"{self.base_url}/v1/chat/completions", payload, headers, False
        )

    def send_stream_request(self):
        payload = self._make_payload(True)
        headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
        return self._do_request(
            f"{self.base_url}/v1/chat/completions", payload, headers, True
        )

    def _parse_nonstream(self, resp, start_time):
        raw = resp.read()
        end = time.time()
        result = json.loads(raw.decode("utf-8"))
        usage = result.get("usage", {})
        return 0.0, end - start_time, usage.get("completion_tokens", 0), resp.status

    def _parse_stream(self, resp, start_time):
        return _parse_vllm_stream(resp, start_time)
