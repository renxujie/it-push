import pandas as pd
from datetime import datetime, timedelta
import time
import random
from playwright.sync_api import sync_playwright
import json
import urllib.parse
import requests
from bs4 import BeautifulSoup

class JuchaoCrawler:
    def __init__(self):
        self.base_url = "https://www.cninfo.com.cn/new/hisAnnouncement/query" 
        self.browser = None
        self.context = None
        self.page = None
        
        # 全球大事件数据源配置
        self.global_news_sources = [
            {
                "name": "华尔街见闻",
                "url": "https://wallstreetcn.com/live/global", 
                "type": "html",
                "selector": ".live-item"
            },
            {
                "name": "路透中文网",
                "url": "https://cn.reuters.com/", 
                "type": "html",
                "selector": ".news-headline-list li"
            },
            {
                "name": "BBC中文网",
                "url": "https://www.bbc.com/zhongwen/simp", 
                "type": "html",
                "selector": ".media-list__item"
            }
        ]
    
    # ... 保留原有巨潮资讯网爬取代码 ...
    
    def get_global_events(self):
        """获取每日全球大事件"""
        global_events = []
        
        for source in self.global_news_sources:
            try:
                if source["type"] == "html":
                    events = self._scrape_html_news(source)
                    global_events.extend(events)
                    
            except Exception as e:
                print(f"抓取{source['name']}失败: {str(e)}")
                continue
        
        # 去重和排序
        unique_events = self._deduplicate_events(global_events)
        sorted_events = sorted(unique_events, key=lambda x: x["time"], reverse=True)
        
        return sorted_events[:20]  # 返回最新20条事件
    
    def _scrape_html_news(self, source):
        """抓取HTML格式的新闻网站"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }
        
        response = requests.get(source["url"], headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.select(source["selector"])
        
        events = []
        for item in items:
            event = self._parse_html_item(item, source)
            if event:
                events.append(event)
        
        return events
    
    def _parse_html_item(self, item, source):
        """解析HTML新闻条目"""
        try:
            if source["name"] == "华尔街见闻":
                title = item.select_one(".live-item__title").get_text(strip=True)
                time_str = item.select_one(".live-item__time").get_text(strip=True)
                url = "https://wallstreetcn.com"  + item.select_one("a")["href"]
                
                return {
                    "source": "华尔街见闻",
                    "title": title,
                    "time": self._parse_time(time_str),
                    "url": url,
                    "category": self._classify_global_event(title)
                }
                
            elif source["name"] == "路透中文网":
                title = item.select_one("a").get_text(strip=True)
                time_str = item.select_one(".timestamp").get_text(strip=True)
                url = "https://cn.reuters.com"  + item.select_one("a")["href"]
                
                return {
                    "source": "路透中文网",
                    "title": title,
                    "time": self._parse_time(time_str),
                    "url": url,
                    "category": self._classify_global_event(title)
                }
                
            elif source["name"] == "BBC中文网":
                title = item.select_one("h3").get_text(strip=True)
                time_str = item.select_one(".media-list__date").get_text(strip=True)
                url = "https://www.bbc.com"  + item.select_one("a")["href"]
                
                return {
                    "source": "BBC中文网",
                    "title": title,
                    "time": self._parse_time(time_str),
                    "url": url,
                    "category": self._classify_global_event(title)
                }
                
        except Exception as e:
            print(f"解析{source['name']}新闻失败: {str(e)}")
            return None
    
    def _parse_time(self, time_str):
        """统一解析时间格式"""
        try:
            # 处理不同格式的时间
            if "分钟前" in time_str or "小时前" in time_str:
                return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            elif "今天" in time_str:
                return datetime.now().strftime("%Y-%m-%d") + " " + time_str.replace("今天", "")
            else:
                return datetime.strptime(time_str, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M:%S")
        except:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _classify_global_event(self, title):
        """对全球大事件进行分类"""
        classification_rules = [
            ("国际冲突", ["冲突", "战争", "袭击", "导弹", "军事", "军演"]),
            ("财经市场", ["股市", "油价", "汇率", "美联储", "加息", "降息", "GDP", "通胀"]),
            ("科技动态", ["AI", "人工智能", "芯片", "科技", "互联网", "特斯拉", "苹果", "微软"]),
            ("政策法规", ["政策", "法案", "监管", "法律", "改革", "发布"]),
            ("社会热点", ["疫情", "灾难", "事故", "社会", "民生", "健康"]),
            ("企业动态", ["企业", "公司", "财报", "并购", "合作", "业绩"])
        ]
        
        for category, keywords in classification_rules:
            if any(keyword in title for keyword in keywords):
                return category
        return "其他"
    
    def _deduplicate_events(self, events):
        """去重相同事件"""
        seen = set()
        unique_events = []
        
        for event in events:
            key = (event["title"], event["time"])
            if key not in seen:
                seen.add(key)
                unique_events.append(event)
        
        return unique_events
