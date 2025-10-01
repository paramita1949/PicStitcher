#!/usr/bin/env python3
"""
从 main.py 中提取版本号
"""
import re
import sys

def get_version():
    """从 main.py 中提取 __version__ 的值"""
    try:
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 匹配 __version__ = "x.x.x" 格式
        match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            version = match.group(1)
            print(version)
            return version
        else:
            print("ERROR: Could not find __version__ in main.py", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    get_version()

