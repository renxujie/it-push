from crawler import JuchaoCrawler
from monitor import generate_announcement_report
from email_sender import EmailSender
from datetime import datetime
import os

def main():
    # 配置信息
    KEY_COMPANIES = ["麒麟信安", "宇信科技", "宏明电子"]    
    # 初始化组件
    crawler = JuchaoCrawler()
    email_sender = EmailSender()
    
    print(f"开始爬取 {datetime.now().strftime('%Y-%m-%d')} 公告...")
    today_announcements = crawler.get_today_announcements()
    
    if not today_announcements.empty:
        print(f"成功爬取 {len(today_announcements)} 条公告")
        
        # 生成报告
        print("生成公告报告...")
        html_report = generate_announcement_report(today_announcements, KEY_COMPANIES)
        
        # 发送邮件
        print("发送邮件报告...")
        email_sender.send_html_email(
            subject=f"{datetime.now().strftime('%Y%m%d')}巨潮资讯每日速递",
            html_content=html_report
        )
    else:
        print("今日无公告")

if __name__ == "__main__":
    main()
