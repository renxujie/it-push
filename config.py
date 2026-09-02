# 邮箱配置
EMAIL_CONFIG = {
    "sender": "your-email@163.com",
    "password": "your-password",
    "receiver": "recipient@163.com"
}

# 全球大事件数据源配置
GLOBAL_NEWSOURCES = [
    {
        "name": "华尔街见闻",
        "url": "https://wallstreetcn.com/live/global", 
        "type": "html",
        "selector": ".live-item"
    },
    # 可以添加更多数据源
]
