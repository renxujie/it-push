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
        
        # 重点关注公司列表
        self.focus_companies = ['麒信安', '宇信科技', '拓维信息', '卧龙电驱', '三花智控']
        
        # 全球大事件数据源配置，更换为更稳定的网站
        self.global_news_sources = [
            {
                "name": "新浪财经",
                "url": "https://finance.sina.com.cn/world.html", 
                "selector": ".list-item",
                "title_selector": "h2",
                "time_selector": ".time"
            },
            {
                "name": "凤凰财经",
                "url": "https://finance.ifeng.com/list/145,0,0,0,1,0.html", 
                "selector": ".news-item",
                "title_selector": "h3",
                "time_selector": ".time"
            },
            {
                "name": "中国经济网",
                "url": "https://world.ce.cn/", 
                "selector": ".news-item",
                "title_selector": "h3",
                "time_selector": ".time"
            },
            {
                "name": "环球财经网",
                "url": "https://www.hqcj.com/", 
                "selector": ".news-item",
                "title_selector": "h3",
                "time_selector": ".time"
            }
        ]
        
        # 重点公司相关新闻数据源
        self.focus_news_sources = [
            {
                "name": "新浪财经",
                "url": "https://finance.sina.com.cn/stock/", 
                "search_url": "https://search.sina.com.cn/?q={}&c=news&range=all", 
                "selector": ".news-item",
                "title_selector": "h2",
                "time_selector": ".time"
            },
            {
                "name": "东方财富网",
                "url": "https://www.eastmoney.com/", 
                "search_url": "https://so.eastmoney.com/news/s?keyword={}", 
                "selector": ".news-item",
                "title_selector": "h3",
                "time_selector": ".time"
            },
            {
                "name": "同花顺财经",
                "url": "http://www.10jqka.com.cn/", 
                "search_url": "http://so.10jqka.com.cn/s?wd={}",
                "selector": ".news-item",
                "title_selector": "h3",
                "time_selector": ".time"
            },
            {
                "name": "雪球",
                "url": "https://xueqiu.com/", 
                "search_url": "https://xueqiu.com/search?q={}&type=all", 
                "selector": ".item",
                "title_selector": "h3",
                "time_selector": ".time"
            }
        ]
    
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
        
        # 发送请求获取数据
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
            
            # 按公告类型排序
            df = pd.DataFrame(parsed_data)
            df = df.sort_values(by=["公告类型", "公告时间"], ascending=[True, False])
            
            return df
            
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
                "公告链接": self._build_announcement_url(item),
                "PDF下载链接": self._build_pdf_download_url(item)
            })
        return parsed_data
    
    def _build_announcement_url(self, item):
        """构建完整的公告页面链接"""
        sec_code = item.get("secCode", "")
        announcement_id = item.get("announcementId", "")
        
        # 构建标准公告链接
        base_url = "https://www.cninfo.com.cn/new/disclosure/detail?plate=szse&orgId=" 
        org_id = sec_code if len(sec_code) == 9 else f"gsh{sec_code}"
        url = f"{base_url}{org_id}&stockCode={sec_code}&announcementId={announcement_id}"
        
        return url
    
    def _build_pdf_download_url(self, item):
        """构建直接下载PDF的链接"""
        adjunct_id = item.get("adjunctId", "")
        if not adjunct_id:
            return ""
        
        # 构建PDF下载链接
        pdf_url = f"https://static.cninfo.com.cn/finalpage/{datetime.now().year}/{datetime.now().month}/{datetime.now().day}/{adjunct_id}.PDF" 
        return pdf_url
    
    def _format_time(self, timestamp):
        """格式化时间戳"""
        try:
            return datetime.fromtimestamp(int(timestamp)/1000).strftime("%Y-%m-%d %H:%M:%S")
        except:
            return ""
    
    def _classify_announcement(self, title):
        """优化公告分类逻辑，增加重点公司识别"""
        # 检查是否为重点公司公告
        for company in self.focus_companies:
            if company in title:
                return f"重点关注 | {company}公告"
        
        # 优化分类规则
        classification_rules = [
            ("重大事项", ["重大事项", "重大合同", "重大资产重组", "对外投资", "重大诉讼", "重大仲裁"]),
            ("财务报告", ["年报", "半年报", "季报", "财务报告", "业绩预告", "业绩快报"]),
            ("股权变动", ["股权转让", "增持", "减持", "股权质押", "解除质押", "回购"]),
            ("监管信息", ["监管函", "行政处罚", "立案调查", "问询函", "回复函"]),
            ("股东大会", ["股东大会", "临时股东大会", "股东大会议决议"]),
            ("关联交易", ["关联交易", "关联方", "关联关系"]),
            ("对外担保", ["对外担保", "担保事项"]),
            ("行业动态", ["行业政策", "行业标准", "行业研究"]),
            ("其他", [])
        ]
        
        for category, keywords in classification_rules:
            if any(keyword in title for keyword in keywords):
                return category
        return "其他"
    
    def generate_announcement_summary(self, announcements):
        """生成公告汇总信息"""
        if announcements.empty:
            return {
                'total': 0,
                'focus_count': 0,
                'important_count': 0,
                'positive_count': 0,
                'negative_count': 0
            }
        
        # 统计重点公司公告
        focus_count = len(announcements[announcements['公告类型'].str.contains("重点关注")])
        
        # 统计重大事项
        important_count = len(announcements[announcements['公告类型'].str.contains("重大事项")])
        
        # 统计利好和利空事件
        positive_count = 0
        negative_count = 0
        
        for _, row in announcements.iterrows():
            impact = self._assess_event_impact(row)
            if impact == "重大利好":
                positive_count += 1
            elif impact == "重大利空":
                negative_count += 1
        
        return {
            'total': len(announcements),
            'focus_count': focus_count,
            'important_count': important_count,
            'positive_count': positive_count,
            'negative_count': negative_count
        }
    
    def analyze_a股_events(self, announcements):
        """分析A股公告中的重要事件"""
        important_events = []
        
        # 检查announcements是否为空
        if announcements.empty:
            return important_events
        
        # 筛选需要关注的公告类型
        important_announcements = announcements[
            announcements['公告类型'].str.contains("重点关注|重大事项|股权变动|监管信息")
        ]
        
        for _, row in important_announcements.iterrows():
            event_impact = self._assess_event_impact(row)
            
            # 只有重大影响的事件才纳入重要事件
            if event_impact in ["重大利好", "重大利空"]:
                event = {
                    "公司名称": row['公司名称'],
                    "事件类型": row['公告类型'],
                    "事件标题": row['公告标题'],
                    "事件时间": row['公告时间'],
                    "事件影响": event_impact,
                    "详情链接": row['公告链接']
                }
                important_events.append(event)
        
        return important_events
    
    def _assess_event_impact(self, row):
        """评估事件对A股的影响"""
        title = row['公告标题']
        
        # 利好关键词
        positive_keywords = [
            "重大合同", "资产重组", "对外投资", "业绩预增", "高送转", 
            "分红", "回购", "增持", "战略合作", "专利获得"
        ]
        
        # 利空关键词
        negative_keywords = [
            "监管函", "行政处罚", "重大诉讼", "业绩预亏", "停牌", 
            "退市", "减持", "股权质押", "终止上市", "重大损失"
        ]
        
        # 检查是否包含利好关键词
        if any(keyword in title for keyword in positive_keywords):
            return "重大利好"
        
        # 检查是否包含利空关键词
        if any(keyword in title for keyword in negative_keywords):
            return "重大利空"
        
        return "中性"
    
    def get_focus_company_news(self):
        """获取重点公司相关新闻"""
        focus_company_news = {}
        
        try:
            for company in self.focus_companies:
                company_news = []
                print(f"正在抓取{company}的相关新闻...")
                
                for source in self.focus_news_sources:
                    try:
                        # 构造搜索URL
                        search_url = source["search_url"].format(urllib.parse.quote(company))
                        
                        # 添加随机等待时间
                        time.sleep(random.uniform(1, 3))
                        
                        # 构造请求头
                        headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                            "Accept-Language": "zh-CN,zh;q=0.9",
                            "Referer": source["url"],
                            "Upgrade-Insecure-Requests": "1"
                        }
                        
                        # 访问目标网站
                        response = requests.get(search_url, headers=headers, timeout=15)
                        response.raise_for_status()
                        
                        # 解析HTML
                        soup = BeautifulSoup(response.text, "html.parser")
                        items = soup.select(source["selector"])
                        
                        for item in items:
                            news = self._parse_html_item(item, source)
                            if news:
                                # 判断是否与公司相关
                                if company in news["title"]:
                                    # 评估对公司的影响
                                    impact, impact_class = self._assess_news_impact(news["title"], company)
                                    news["impact"] = impact
                                    news["impact_class"] = impact_class
                                    
                                    # 生成摘要
                                    news["summary"] = self._generate_news_summary(news["title"])
                                    
                                    company_news.append(news)
                        
                        print(f"成功抓取{source['name']}的{company}相关新闻")
                        
                    except Exception as e:
                        print(f"抓取{source['name']}的{company}相关新闻失败: {str(e)}")
                        continue
                
                # 去重和排序
                unique_news = self._deduplicate_news(company_news)
                sorted_news = sorted(unique_news, key=lambda x: x["time"], reverse=True)
                
                focus_company_news[company] = sorted_news[:10]  # 返回最新10条新闻
                
                print(f"成功抓取{len(sorted_news)}条{company}相关新闻")
            
            return focus_company_news
            
        except Exception as e:
            print(f"重点公司相关新闻抓取失败: {str(e)}")
            return {}
    
    def _is_company_related(self, title, company):
        """判断新闻是否与公司相关"""
        return company in title
    
    def _assess_news_impact(self, title, company):
        """评估新闻对公司的影响"""
        # 利好关键词
        positive_keywords = [
            "重大合同", "合作", "战略合作", "获奖", "专利", 
            "业绩预增", "高送转", "分红", "回购", "增持", 
            "利好", "上涨", "增长", "扩大", "扶持", "激励"
        ]
        
        # 利空关键词
        negative_keywords = [
            "监管", "处罚", "调查", "诉讼", "退市", 
            "业绩预亏", "下降", "下跌", "亏损", "减持", 
            "利空", "利空消息", "负面消息"
        ]
        
        # 检查是否包含利好关键词
        if any(keyword in title for keyword in positive_keywords):
            return ("利好", "impact-positive")
        
        # 检查是否包含利空关键词
        if any(keyword in title for keyword in negative_keywords):
            return ("利空", "impact-negative")
        
        return ("中性", "impact-neutral")
    
    def _generate_news_summary(self, title):
        """生成新闻摘要"""
        # 这里可以使用AI模型生成摘要，为了简化，我们直接返回标题
        return title
    
    def _parse_html_item(self, item, source):
        """更新HTML解析逻辑，适配新的数据源"""
        try:
            # 获取标题
            title_elem = item.select_one(source["title_selector"])
            if not title_elem:
                return None
            title = title_elem.get_text(strip=True)
            
            # 获取时间
            time_elem = item.select_one(source["time_selector"])
            if not time_elem:
                time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                time_str = time_elem.get_text(strip=True)
            
            # 获取链接
            link_elem = item.select_one("a")
            if not link_elem or not link_elem.has_attr("href"):
                return None
            url = link_elem["href"]
            
            # 处理相对链接
            if not url.startswith("http"):
                url = urllib.parse.urljoin(source["url"], url)
            
            return {
                "source": source["name"],
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
            elif len(time_str) == 10:  # 格式如"2026-06-26"
                return time_str + " 00:00:00"
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
    
    def _deduplicate_news(self, news_list):
        """去重相同新闻"""
        seen = set()
        unique_news = []
        
        for news in news_list:
            key = (news["title"], news["time"])
            if key not in seen:
                seen.add(key)
                unique_news.append(news)
        
        return unique_news
    
    def get_global_events(self):
        """优化全球大事件抓取，更换更稳定的数据源"""
        global_events = []
        
        # 使用requests+BeautifulSoup抓取数据
        try:
            for source in self.global_news_sources:
                try:
                    print(f"正在抓取{source['name']}...")
                    
                    # 添加随机等待时间
                    time.sleep(random.uniform(1, 3))
                    
                    # 构造请求头
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                        "Accept-Language": "zh-CN,zh;q=0.9",
                        "Referer": "https://www.baidu.com/", 
                        "Upgrade-Insecure-Requests": "1"
                    }
                    
                    # 访问目标网站
                    response = requests.get(source["url"], headers=headers, timeout=15)
                    response.raise_for_status()
                    
                    # 解析HTML
                    soup = BeautifulSoup(response.text, "html.parser")
                    items = soup.select(source["selector"])
                    
                    events = []
                    for item in items:
                        event = self._parse_html_item(item, source)
                        if event:
                            events.append(event)
                    
                    global_events.extend(events)
                    print(f"成功抓取{source['name']}，获取{len(events)}条事件")
                    
                except Exception as e:
                    print(f"抓取{source['name']}失败: {str(e)}")
                    continue
            
            # 去重和排序
            unique_events = self._deduplicate_events(global_events)
            sorted_events = sorted(unique_events, key=lambda x: x["time"], reverse=True)
            
            return sorted_events[:20]  # 返回最新20条事件
            
        except Exception as e:
            print(f"全局大事件抓取失败: {str(e)}")
            return []
    
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
