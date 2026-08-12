# -*- coding: utf-8 -*-
"""3d 等待搜索结果就绪（轮询岗位容器出现，非固定延时）。用法：browser-use <<'PY' ... PY 中调用。"""

import time


def wait_jobs(js, wait_for_load, timeout=10):
    """轮询岗位容器出现（最多 timeout 秒，每次 sleep 1s），出现即完成并 wait_for_load。返回 bool。"""
    for _ in range(timeout):
        n = js("document.querySelectorAll('[class*=job-title],[class*=JobTitle],[class*=position],[class*=job-item],[class*=post]').length")
        if n and int(n) > 0:
            wait_for_load()
            return True
        time.sleep(1)
    wait_for_load()
    return False
