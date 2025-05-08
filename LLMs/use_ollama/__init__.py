"""
    使用Ollama的弊端：
        1. 无法便捷操作如max_token等参数（是懒得实现）
        2. 本地模型通过Ollama加载后，项目是通过Ollama的本地HTTP协议在进行交互
        3. prompt工程比较固化
"""