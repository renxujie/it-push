import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import random
from fake_useragent import UserAgent

class JuchaoCrawler:
    def __init__(self):
        self.base_url = "https://www.cninfo.com.cn/new/hisAnnouncement/query" 
        self.ua = UserAgent()
        self.headers = self._generate_headers()
        self.session = requests.Session()
    
    def _generate_headers(self):
        """生成随机请求头，避免被识别为爬虫"""
        return {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Host": "www.cninfo.com.cn",
            "Origin": "https://www.cninfo.com.cn", 
            "Referer": "https://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search", 
            "User-Agent": self.ua.random,
            "X-Requested-With": "XMLHttpRequest"
        }
    
    def _get_cookies(self):
        """获取网站Cookies，模拟真实浏览器访问"""
        try:
            self.session.get("https://www.cninfo.com.cn/new/index",  headers=self.headers)
            return self.session.cookies
        except Exception as e:
            print(f"获取Cookies失败: {str(e)}")
            return None
    
    def get_today_announcements(self):
        """获取今日发布的所有公告"""
        today = datetime.now().strftime("%Y-%m-%d")
        start_date = today
        end_date = today
        
        all_announcements = []
        page_num = 1
        page_size = 30
        
        # 先获取Cookies
        self._get_cookies()
        
        while True:
            # 每次请求更新User-Agent
            self.headers["User-Agent"] = self.ua.random
            
            payload = {
                "pageNum": str(page_num),
                "pageSize": str(page_size),
                "column": "szse",
                "tabName": "fulltext",
                "plate": "",
                "stock": "",
                "searchkey": "",
                "secid": "",
                "category": "",
                "trade": "",
                "seDate": f"{start_date}~{end_date}",
                "sortName": "",
                "sortType": "",
                "isHLtitle": "true"
            }
            
            try:
                # 使用session保持连接
                response = self.session.post(
                    self.base_url, 
                    data=payload, 
                    headers=self.headers,
                    timeout=15
                )
                response.raise_for_status()
                
                # 尝试解析JSON
                try:
                    data = response.json()
                except Exception as e:
                    print(f"解析JSON失败，可能被反爬机制拦截: {str(e)}")
                    print(f"响应内容: {response.text[:200]}...")
                    
                    # 尝试重新获取Cookies并重试
                    self._get_cookies()
                    time.sleep(random.uniform(5, 10))
                    continue
                
                if data["totalAnnouncement"] == 0:
                    break
                
                announcements = data["announcements"]
                if not announcements:
                    break
                
                all_announcements.extend(self._parse_announcements(announcements))
                
                # 检查是否还有下一页
                if page_num * page_size >= data["totalAnnouncement"]:
                    break
                
                page_num += 1
                time.sleep(random.uniform(2, 5))  # 延长随机延迟时间
            
            except Exception as e:
                print(f"爬取第{page_num}页失败: {str(e)}")
                # 遇到错误时等待更长时间并重试
                time.sleep(random.uniform(10, 20))
                continue
        
        return pd.DataFrame(all_announcements)
    
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
