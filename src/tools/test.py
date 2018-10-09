import json, jsonpickle

a1 = """{ "score ":-0.9719291925430298, "answer ": "可以关注微信公众号‘’京东家电小秘书‘’点击页面底部菜单选项；一点无忧‘自助办理、或点击召唤小秘书联系家电专属京东客服进行人工咨询哦", "question ": "京东客服在哪里 ", "sourceList ":[ "cluster "], "optional ":{ "qwords ": "京东 客服 在 哪里 ", "awords ": "亲 可以 关注 微信 公众 号 ‘ ’ 京东 家电 小 秘书 ‘ ’ 点击 页面 底部 菜单 选项 ； 一点 无忧 ‘ 自助 办理 、 或 点击 召唤 小 秘书 联系 家电 专属 京东 客服 进行 人工 咨询 哦 ` , "}}"""
b1 = jsonpickle.decode(a1)
print(b1["answer "])

a2 = """{ "score ":-0.9719291925430298, "answer ": "可以关注微信公众号‘’京东家电小秘书‘’点击页面底部菜单选项；一点无忧‘自助办理、或点击召唤小秘书联系家电专属京东客服进行人工咨询哦", ", "question ": "京东客服在哪里 ", "sourceList ":[ "cluster "], "optional ":{ "qwords ": "京东 客服 在 哪里 ", "awords ": "亲 可以 关注 微信 公众 号 ‘ ’ 京东 家电 小 秘书 ‘ ’ 点击 页面 底部 菜单 选项 ； 一点 无忧 ‘ 自助 办理 、 或 点击 召唤 小 秘书 联系 家电 专属 京东 客服 进行 人工 咨询 哦 ` , "}}"""
b1 = jsonpickle.decode(a2)
a2 = json.dumps(a2)
b2 = jsonpickle.decode(a2)
print(b2["answer "])
