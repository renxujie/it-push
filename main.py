import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import ssl
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

def generate_email_content(announcements, global_events, a股_events, announcement_summary, focus_company_news):
    """生成优化后的邮件内容"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    content = f"""
    <html>
    <head>
        <title>今日A股公告与全球大事件</title>
        <style>
            body {{ font-family: 'Microsoft YaHei', sans-serif; }}
            .header {{ background-color: #f5f5f5; padding: 10px; border-bottom: 1px solid #ddd; }}
            .section {{ margin: 20px 0; }}
            .highlight {{ background-color: #fff3cd; padding: 10px; border-radius: 5px; }}
            .announcement-table {{ width: 100%; border-collapse: collapse; }}
            .announcement-table th {{ background-color: #f0f0f0; padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
            .announcement-table td {{ padding: 8px; border-bottom: 1px solid #eee; }}
            .event-list {{ list-style-type: none; padding: 0; }}
            .event-item {{ margin: 10px 0; padding: 10px; background-color: #fafafa; border-radius: 5px; }}
            .event-source {{ color: #666; font-size: 12px; }}
            .event-time {{ color: #999; font-size: 12px; }}
            .impact-positive {{ color: #007bff; font-weight: bold; }}
            .impact-negative {{ color: #dc3545; font-weight: bold; }}
            .impact-neutral {{ color: #6c757d; font-weight: bold; }}
            .summary-card {{ background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .summary-stat {{ display: inline-block; margin-right: 20px; padding: 5px 10px; background-color: #bbdefb; border-radius: 3px; }}
            .news-list {{ list-style-type: none; padding: 0; }}
            .news-item {{ margin: 10px 0; padding: 10px; background-color: #e8f5e9; border-radius: 5px; }}
            .company-news {{ margin: 20px 0; padding: 10px; background-color: #e3f2fd; border-radius: 5px; }}
            .company-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #007bff; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>今日A股公告与全球大事件 ({today})</h1>
        </div>
        
        <!-- 公告汇总信息 -->
        <div class="section">
            <div class="summary-card">
                <h2>📊 今日公告汇总</h2>
                <div class="summary-stat">总公告数: {announcement_summary['total']}</div>
                <div class="summary-stat">重点公司公告: {announcement_summary['focus_count']}</div>
                <div class="summary-stat">重大事项: {announcement_summary['important_count']}</div>
                <div class="summary-stat">利好事件: {announcement_summary['positive_count']}</div>
                <div class="summary-stat">利空事件: {announcement_summary['negative_count']}</div>
            </div>
        </div>
        
        <!-- 重点关注公告提醒 -->
        <div class="section highlight">
            <h2>🚨 重点关注公告</h2>
            {generate_focus_announcements(announcements)}
        </div>
        
        <!-- 重点公司相关新闻汇总 -->
        <div class="section">
            <h2>📰 重点公司相关新闻汇总</h2>
            {generate_focus_company_news(focus_company_news)}
        </div>
        
        <!-- A股重要事件分析 -->
        <div class="section">
            <h2>📊 A股重要事件分析</h2>
            {generate_a股_events_list(a股_events)}
        </div>
        
        <!-- 今日A股公告 -->
        <div class="section">
            <h2>📋 今日A股公告</h2>
            {generate_announcement_table(announcements)}
        </div>
        
        <!-- 全球大事件 -->
        <div class="section">
            <h2>🌍 今日全球大事件</h2>
            {generate_global_events_list(global_events)}
        </div>
    </body>
    </html>
    """
    
    return content

def generate_focus_announcements(announcements):
    """生成重点关注公告列表"""
    # 检查announcements是否为空
    if announcements.empty:
        return "<p>今日无公告</p>"
    
    focus_announcements = announcements[announcements['公告类型'].str.contains("重点关注")]
    
    if focus_announcements.empty:
        return "<p>今日无重点关注公告</p>"
    
    list_html = "<ul>"
    for _, row in focus_announcements.iterrows():
        list_html += f"""
        <li>
            <h3><a href="{row['公告链接']}" target="_blank">{row['公告标题']}</a></h3>
            <p>时间: {row['公告时间']} | 类型: {row['公告类型']}</p>
        </li>
        """
    list_html += "</ul>"
    return list_html

def generate_focus_company_news(focus_company_news):
    """生成重点公司相关新闻列表"""
    if not focus_company_news:
        return "<p>今日无重点公司相关新闻</p>"
    
    news_html = ""
    for company, news_list in focus_company_news.items():
        if not news_list:
            continue
        
        news_html += f"""
        <div class="company-news">
            <div class="company-title">🔍 {company} 相关新闻</div>
            <ul>
        """
        for news in news_list:
            impact_class = "impact-neutral"
            if news["impact"] == "利好":
                impact_class = "impact-positive"
            elif news["impact"] == "利空":
                impact_class = "impact-negative"
            
            news_html += f"""
            <li>
                <h3><a href="{news['url']}" target="_blank">{news['title']}</a></h3>
                <p class='event-source'>来源: {news['source']}</p>
                <p class='event-time'>时间: {news['time']}</p>
                <p>影响: <span class="{impact_class}">{news['impact']}</span></p>
                <p>摘要: {news['summary']}</p>
            </li>
            """
        news_html += "</ul></div>"
    
    return news_html if news_html else "<p>今日无重点公司相关新闻</p>"

def generate_a股_events_list(a股_events):
    """生成A股重要事件列表"""
    if not a股_events:
        return "<p>今日无重大A股事件</p>"
    
    list_html = "<ul>"
    for event in a股_events:
        impact_class = "impact-neutral"
        if event["事件影响"] == "重大利好":
            impact_class = "impact-positive"
        elif event["事件影响"] == "重大利空":
            impact_class = "impact-negative"
        
        list_html += f"""
        <li>
            <h3>{event['公司名称']} - {event['事件类型']}</h3>
            <p>{event['事件标题']}</p>
            <p>时间: {event['事件时间']} | 影响: <span class="{impact_class}">{event['事件影响']}</span></p>
            <p><a href="{event['详情链接']}" target="_blank">查看详情</a></p>
        </li>
        """
    list_html += "</ul>"
    return list_html

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
    """优化后主函数"""
    print("开始抓取数据...")
    
    # 初始化爬虫
    crawler = JuchaoCrawler()
    
    # 获取今日公告
    print("正在抓取今日A股公告...")
    announcements = crawler.get_today_announcements()
    print(f"成功抓取{len(announcements)}条公告")
    
    # 生成公告汇总信息
    announcement_summary = crawler.generate_announcement_summary(announcements)
    print("生成公告汇总信息...")
    
    # 分析A股重要事件
    print("正在分析A股重要事件...")
    a股_events = crawler.analyze_a股_events(announcements)
    print(f"识别到{len(a股_events)}条重要事件")
    
    # 获取重点公司相关新闻
    print("正在抓取重点公司相关新闻...")
    focus_company_news = crawler.get_focus_company_news()
    print(f"成功抓取重点公司相关新闻")
    
    # 获取全球大事件
    print("正在抓取全球大事件...")
    global_events = crawler.get_global_events()
    print(f"成功抓取{len(global_events)}条全球大事件")
    
    # 生成邮件内容
    content = generate_email_content(announcements, global_events, a股_events, announcement_summary, focus_company_news)
    
    # 发送邮件
    subject = f"今日A股公告与全球大事件 ({datetime.now().strftime('%Y-%m-%d')})"
    send_email(subject, content)

if __name__ == "__main__":
    main()
