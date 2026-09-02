import pandas as pd
from datetime import datetime, timedelta
import time
import random
from playwright.sync_api import sync_playwright
import json

class JuchaoCrawler:
    def __init__(self):
        self.base_url = "https://www.cninfo.com.cn/new/hisAnnouncement/query" 
        self.browser = None
        self.context = None
        self.page = None
    
    def _setup_browser(self):
        """启动浏览器并配置上下文"""
        playwright = sync_playwright().start()
        
        # 配置浏览器启动参数
        self.browser = playwright.chromium.launch(
            headless=True,  # GitHub Actions中必须设置为True
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--no-zygote",
                "--single-process",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor"
            ]
        )
        
        # 创建浏览器上下文
        self.context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
            timezone_id="Asia/Shanghai"
        )
        
        # 创建新页面
        self.page = self.context.new_page()
        
        # 添加请求拦截，监控网络请求
        self.page.route("**/query", lambda route: route.continue_())
        
        return playwright
    
    def _get_announcements_data(self, today):
        """通过浏览器网络请求获取公告数据"""
        # 先访问搜索页面初始化会话
        self.page.goto(
            "https://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search", 
            wait_until="networkidle",
            timeout=30000
        )
        
        # 等待页面加载完成
        self.page.wait_for_selector(".search-input", timeout=20000)
        
        # 构造请求参数
        request_data = {
            "url": self.base_url,
            "payload": {
                "pageNum": "1",
                "pageSize": "100",  # 每页最多100条
                "column": "szse",
                "tabName": "fulltext",
                "plate": "",
                "stock": "",
                "searchkey": "",
                "secid": "",
                "category": "",
                "trade": "",
                "seDate": f"{today}~{today}",
                "sortName": "",
                "sortType": "",
                "isHLtitle": "true"
            }
        }
        
        # 发送请求获取数据 - 修复了参数传递方式
        response = self.page.evaluate("""async (data) => {
            const response = await fetch(data.url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: new URLSearchParams(data.payload)
            });
            return await response.json();
        }""", request_data)
        
        return response
    
    def get_today_announcements(self):
        """获取今日发布的所有公告"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        playwright = None
        try:
            # 启动浏览器
            playwright = self._setup_browser()
            
            # 获取公告数据
            data = self._get_announcements_data(today)
            
            if data.get("totalAnnouncement", 0) == 0:
                return pd.DataFrame()
            
            announcements = data.get("announcements", [])
            if not announcements:
                return pd.DataFrame()
            
            # 解析公告数据
            parsed_data = self._parse_announcements(announcements)
            
            return pd.DataFrame(parsed_data)
            
        except Exception as e:
            print(f"爬取失败: {str(e)}")
            return pd.DataFrame()
        finally:
            # 关闭浏览器
            if self.browser:
                self.browser.close()
            if playwright:
                playwright.stop()
    
    def _parse_announcements(self, announcements):
        """解析公告数据"""
        parsed_data = []
        for item in announcements:
            parsed_data.append({
                "公司代码": item.get("secCode", ""),
                "公司名称": item.get("secName", ""),
                "公告标题": item.get("announcementTitle", ""),
                "公告时间": self._format_time(item.get("announcementTime", "")),
                "公告类型": self._classify_announcement(item.get("announcementTitle", "")),
                "公告链接": f"https://www.cninfo.com.cn{item.get('adjunctUrl',  '')}"
            })
        return parsed_data
    
    def _format_time(self, timestamp):
        """格式化时间戳"""
        try:
            return datetime.fromtimestamp(int(timestamp)/1000).strftime("%Y-%m-%d %H:%M:%S")
        except:
            return ""
    
    def _classify_announcement(self, title):
        """根据标题对公告进行分类"""
        classification_rules = [
            ("重大事项", ["重大事项", "重大合同", "重大资产重组", "对外投资", "重大诉讼", "重大仲裁"]),
            ("财务报告", ["年报", "半年报", "季报", "财务报告", "业绩预告", "业绩快报"]),
            ("股权变动", ["股权转让", "增持", "减持", "股权质押", "解除质押", "回购"]),
            ("监管信息", ["监管函", "行政处罚", "立案调查", "问询函", "回复函"]),
            ("股东大会", ["股东大会", "临时股东大会", "股东大会议决议"]),
            ("关联交易", ["关联交易", "关联方", "关联关系"]),
            ("对外担保", ["对外担保", "担保事项"]),
            ("其他", [])
        ]
        
        for category, keywords in classification_rules:
            if any(keyword in title for keyword in keywords):
                return category
        return "其他"
