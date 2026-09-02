import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from crawler import JuchaoCrawler
import pandas as pd
import os  # 新增：用于读取环境变量

def send_email(subject, content):
    # 从环境变量读取邮箱配置，确保与GitHub Secrets一致
    sender_email = os.environ.get('SENDER_EMAIL')
    sender_password = os.environ.get('SENDER_PASSWORD')
    receiver_email = os.environ.get('RECEIVER_EMAIL')
    
    # 验证环境变量是否正确加载
    if not all([sender_email, sender_password, receiver_email]):
        print("错误：邮箱环境变量未正确配置")
        return
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(content, 'html', 'utf-8'))
    
    try:
        # 使用SSL加密连接
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.163.com', 465, context=context) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, [receiver_email], msg.as_string())
        print("邮件发送成功")
    except smtplib.SMTPAuthenticationError:
        print("认证失败: 请检查授权码是否正确，以及是否开启了SMTP服务")
        print(f"发送邮箱: {sender_email}")
    except Exception as e:
        print(f"邮件发送失败: {str(e)}")

def generate_html_report(announcements, global_events):
    """生成HTML格式的报告"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    html = f"""
    <html>
    <head>
        <title>每日资讯简报 - {today}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #3498db; margin-top: 30px; }}
            .announcement-item {{ margin-bottom: 15px; padding: 10px; border: 1px solid #eee; border-radius: 5px; }}
            .event-item {{ margin-bottom: 10px; padding: 8px; border-left: 3px solid #3498db; }}
            .company-name {{ font-weight: bold; color: #2c3e50; }}
            .announcement-type {{ color: #e74c3c; font-size: 0.9em; }}
            .event-source {{ color: #7f8c8d; font-size: 0.8em; }}
            .time {{ color: #95a5a6; font-size: 0.8em; }}
        </style>
    </head>
    <body>
        <h1>每日资讯简报 - {today}</h1>
    """
    
    # 添加A股公告部分
    if not announcements.empty:
        html += """
        <h2>📢 A股上市公司公告</h2>
        """
        
        # 按分类分组显示
        grouped = announcements.groupby("公告类型")
        for category, group in grouped:
            html += f"""
            <h3>{category} ({len(group)}条)</h3>
            """
            for _, row in group.iterrows():
                html += f"""
                <div class="announcement-item">
                    <div class="company-name">{row['公司名称']}({row['公司代码']})</div>
                    <div><a href="{row['公告链接']}" target="_blank">{row['公告标题']}</a></div>
                    <div class="time">{row['公告时间']}</div>
                    <div><a href="{row['PDF下载链接']}" target="_blank">📥 下载PDF</a></div>
                </div>
                """
    
    # 添加全球大事件部分
    if global_events:
        html += """
        <h2>🌍 全球大事件</h2>
        """
        
        # 按分类分组显示
        events_by_category = {}
        for event in global_events:
            category = event["category"]
            if category not in events_by_category:
                events_by_category[category] = []
            events_by_category[category].append(event)
        
        for category, events in events_by_category.items():
            html += f"""
            <h3>{category} ({len(events)}条)</h3>
            """
            for event in events:
                html += f"""
                <div class="event-item">
                    <div><a href="{event['url']}" target="_blank">{event['title']}</a></div>
                    <div class="event-source">{event['source']} · {event['time']}</div>
                </div>
                """
    
    html += """
    </body>
    </html>
    """
    
    return html

def main():
    crawler = JuchaoCrawler()
    
    # 获取A股公告
    announcements = crawler.get_today_announcements()
    
    # 获取全球大事件
    global_events = crawler.get_global_events()
    
    # 生成HTML报告
    html_content = generate_html_report(announcements, global_events)
    
    # 发送邮件
    today = datetime.now().strftime("%Y-%m-%d")
    subject = f"每日资讯简报 - {today}"
    send_email(subject, html_content)

if __name__ == "__main__":
    main()
