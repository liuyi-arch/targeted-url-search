# -*- coding: utf-8 -*-
"""3a 收尾：保活关闭站点 tab——关闭前若它是最后一个 page tab，先建 about:blank 占位，
防窗口消失（Chrome 关唯一 tab 后窗口关闭，下次开新站需重建），配合方案 A 使用。"""


def close_tab_keepalive(cdp, tid):
    """关闭站点 tab（tid）；若它是最后一个 page tab 则先创建 about:blank 占位。"""
    targets = cdp("Target.getTargets")["targetInfos"]
    others = [t for t in targets if t.get("type") == "page" and t.get("targetId") != tid]
    if len(others) == 0:
        cdp("Target.createTarget", url="about:blank")
        print("[保活] 已创建 about:blank 占位，窗口不会关闭")
    cdp("Target.closeTarget", targetId=tid)
