import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import ssl  # 确保导入ssl模块
import os
from crawler import JuchaoCrawler

def send_email(subject, content):
    # 从环境变量读取邮箱配置
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
        print(f"错误类型: {type(e).__name__}")

def generate_email_content(announcements, global_events):
    """生成邮件内容"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    content = f"""
    <html>
    <head>
        <title>今日A股公告与全球大事件</title>
        <style>
            body {{ font-family: 'Microsoft YaHei', sans-serif; }}
            .header {{ background-color: #f5f5f5; padding: 10px; border-bottom: 1px solid #ddd; }}
            .section {{ margin: 20px 0; }}
            .announcement-table {{ width: 100%; border-collapse: collapse; }}
            .announcement-table th {{ background-color: #f0f0f0; padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
            .announcement-table td {{ padding: 8px; border-bottom: 1px solid #eee; }}
            .event-list {{ list-style-type: none; padding: 0; }}
            .event-item {{ margin: 10px 0; padding: 10px; background-color: #fafafa; border-radius: 5px; }}
            .event-source {{ color: #666; font-size: 12px; }}
            .event-time {{ color: #999; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>今日A股公告与全球大事件 ({today})</h1>
        </div>
        
        <div class="section">
            <h2>今日A股公告</h2>
            {generate_announcement_table(announcements)}
        </div>
        
        <div class="section">
            <h2>今日全球大事件</h2>
            {generate_global_events_list(global_events)}
        </div>
    </body>
    </html>
    """
    
    return content

def generate_announcement_table(announcements):
    """生成公告表格"""
    if announcements.empty:
        return "<p>今日暂无公告</p>"
    
    table_html = """
    <table class="announcement-table">
        <tr>
            <th>公司代码</th>
            <th>公司名称</th>
            <th>公告标题</th>
            <th>公告时间</th>
            <th>公告类型</th>
            <th>操作</th>
        </tr>
    """
    
    for _, row in announcements.iterrows():
        table_html += f"""
        <tr>
            <td>{row['公司代码']}</td>
            <td>{row['公司名称']}</td>
            <td>{row['公告标题']}</td>
            <td>{row['公告时间']}</td>
            <td>{row['公告类型']}</td>
            <td>
                <a href="{row['公告链接']}" target="_blank">查看详情</a> | 
                <a href="{row['PDF下载链接']}" target="_blank">下载PDF</a>
            </td>
        </tr>
        """
    
    table_html += "</table>"
    return table_html

def generate_global_events_list(global_events):
    """生成全球大事件列表"""
    if not global_events:
        return "<p>今日暂无全球大事件</p>"
    
    list_html = "<ul class='event-list'>"
    
    for event in global_events:
        list_html += f"""
        <li class='event-item'>
            <h3><a href="{event['url']}" target="_blank">{event['title']}</a></h3>
            <p class='event-source'>来源: {event['source']}</p>
            <p class='event-time'>时间: {event['time']}</p>
            <p>分类: {event['category']}</p>
        </li>
        """
    
    list_html += "</ul>"
    return list_html

def main():
    """主函数"""
    print("开始抓取数据...")
    
    # 初始化爬虫
    crawler = JuchaoCrawler()
    
    # 获取今日公告
    print("正在抓取今日A股公告...")
    announcements = crawler.get_today_announcements()
    print(f"成功抓取{len(announcements)}条公告")
    
    # 获取全球大事件
    print("正在抓取全球大事件...")
    global_events = crawler.get_global_events()
    print(f"成功抓取{len(global_events)}条全球大事件")
    
    # 生成邮件内容
    content = generate_email_content(announcements, global_events)
    
    # 发送邮件
    subject = f"今日A股公告与全球大事件 ({datetime.now().strftime('%Y-%m-%d')})"
    send_email(subject, content)

if __name__ == "__main__":
    main()
