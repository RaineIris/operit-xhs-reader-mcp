# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "mcp",
#   "requests",
# ]
# ///

import subprocess
import sys

def ensure_dependencies():
    """启动时自动检测并安装缺失依赖"""
    required = {"mcp": "mcp", "requests": "requests"}
    missing = []
    for import_name, pip_name in required.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pip_name)
    if missing:
        try:
            # 先尝试标准安装
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--user"] + missing,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            # 失败后再尝试 break-system-packages
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "--break-system-packages"] + missing,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            except subprocess.CalledProcessError:
                pass  # 依赖安装失败，让后续导入时报错

ensure_dependencies()

import json
import re
import base64
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Xiaohongshu_Stealth_Reader")

HUNYUAN_BASE_URL = "https://api.hunyuan.cloud.tencent.com/v1"


def get_api_key():
    """每次调用时动态读取环境变量"""
    return os.environ.get("HUNYUAN_API_KEY", "")


def describe_image(image_url: str) -> str:
    """下载图片，调混元vision，返回图片内容描述"""
    api_key = get_api_key()
    if not api_key:
        return "[未配置HUNYUAN_API_KEY]"
    try:
        resp = requests.get(image_url, timeout=15)
        resp.raise_for_status()
        img_b64 = base64.b64encode(resp.content).decode("utf-8")
        content_type = resp.headers.get("Content-Type", "image/jpeg")
        if "webp" in content_type:
            media_type = "image/webp"
        elif "png" in content_type:
            media_type = "image/png"
        else:
            media_type = "image/jpeg"

        payload = {
            "model": "hunyuan-vision",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{media_type};base64,{img_b64}"}
                        },
                        {
                            "type": "text",
                            "text": "这是一篇小红书帖子中的图片。请直接提取并转录图片中的所有文字内容，保持原文顺序。如果有图表或配图，简要描述其内容（一句话即可）。不要添加分析、总结或额外解释。"
                        }
                    ]
                }
            ],
            "max_tokens": 1000
        }
        r = requests.post(
            f"{HUNYUAN_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=60
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[图片理解失败: {str(e)}]"


def describe_images_parallel(image_urls: list) -> dict:
    """并行处理所有图片，返回 {index: description}"""
    results = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_idx = {
            executor.submit(describe_image, url): i
            for i, url in enumerate(image_urls)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                results[idx] = f"[图片处理异常: {str(e)}]"
    return results


def get_xhs_data(url: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html = response.text
        match = re.search(r'window\.__INITIAL_STATE__=({.+?})</script>', html)
        if not match:
            title_match = re.search(r'<title>(.+?)</title>', html)
            title = title_match.group(1) if title_match else "无标题"
            return {"title": title, "desc": "反爬限制，未能抓取完整内容。", "images": []}
        state_str = match.group(1).replace('undefined', 'null')
        data = json.loads(state_str)
        note_data = data.get("note", {}).get("noteDetailMap", {})
        if not note_data:
            return {"title": "无标题", "desc": "未找到笔记内容", "images": []}
        first_key = list(note_data.keys())[0]
        note = note_data[first_key].get("note", {})
        title = note.get("title", "")
        desc = note.get("desc", "")
        images = []
        for img in note.get("imageList", []):
            url_default = img.get("urlDefault")
            if url_default:
                if not url_default.startswith("http"):
                    url_default = f"https://sns-webpic-qc.xhscdn.com/{url_default}"
                images.append(url_default)
        return {"title": title, "desc": desc, "images": images}
    except Exception as e:
        return {"title": "解析出错", "desc": str(e), "images": []}


@mcp.tool()
def read_xiaohongshu_full(url: str) -> list:
    """
    读取小红书图文帖子。返回标题、文案，并用混元vision理解每张图片内容。
    """
    data = get_xhs_data(url)
    images = data.get("images", [])

    img_descriptions = ""
    if images:
        results = describe_images_parallel(images)
        for i in range(len(images)):
            desc = results.get(i, "[未获取到描述]")
            img_descriptions += f"\n【第{i+1}张图片内容】\n{desc}\n"

    text_content = (
        f"【小红书帖子内容】\n\n"
        f"标题: {data['title']}\n\n"
        f"文案:\n{data['desc']}\n"
        f"{img_descriptions}"
    )
    return [text_content]


if __name__ == "__main__":
    mcp.run()
