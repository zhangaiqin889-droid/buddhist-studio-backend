#!/usr/bin/env python3
"""
硬性规则4：后端也要独立端口检测，不抢占已有项目/服务。
在你本机运行 `python scripts/check_port.py` 会真实探测端口占用，
自动跳过已占用端口（包括前端5793、n8n 5678、AI Video Studio 8765/8788），
把可用端口写回 .env 的 APP_PORT。
"""
import json
import socket
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT_CONFIG_PATH = os.path.join(os.path.dirname(ROOT), "buddhist-studio", "port.config.json")
ENV_PATH = os.path.join(ROOT, ".env")


def is_port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def find_free_port(start: int, avoid: set[int]) -> int:
    port = start
    for _ in range(200):
        if port not in avoid and is_port_free(port):
            return port
        port += 1
    raise RuntimeError(f"未能在 {start}-{start + 200} 范围内找到空闲端口")


def main():
    avoid = {5678, 8765, 8788, 5173, 3000, 8000, 8080, 5793}
    if os.path.exists(PORT_CONFIG_PATH):
        try:
            with open(PORT_CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                avoid.add(cfg["frontend"]["port"])
        except Exception:
            pass

    port = find_free_port(5891, avoid)

    lines = []
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            lines = [ln for ln in f.read().splitlines() if not ln.startswith("APP_PORT=")]
    lines.insert(0, f"APP_PORT={port}")
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"✅ 后端端口检测完成: {port}（已写入 .env 的 APP_PORT，不与前端/n8n/AI Video Studio 冲突）")


if __name__ == "__main__":
    main()
