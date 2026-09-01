import pandas as pd
from datetime import datetime

def monitor_key_companies(df, key_companies):
    """监控重点企业公告"""
    key_announcements = df[df["公司名称"].isin(key_companies)]
    if not key_announcements.empty:
        return key_announcements.to_html(index=False, classes="table table-striped")
    else:
        return "<p>今日无重点企业公告</p>"

def generate_announcement_report(df, key_companies):
    """生成公告报告"""
    today = datetime.now().strftime("%Y年%m月%d日")
    total_announcements = len(df)
    
    # 统计各类型公告数量
    category_stats = df["公告类型"].value_counts().to_dict()
    
    # 监控重点企业
    key_announcements_html = monitor_key_companies(df, key_companies)
    
    # 生成HTML报告
    html_report = f"""
    <html>
    <head>
        <title>巨潮资讯每日速递 - {today}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #34495e; margin-top: 30px; }}
            .table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            .th, .td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            .th {{ background-color: #f2f2f2; font-weight: bold; }}
            .highlight {{ background-color: #ffffcc; }}
            .summary {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; }}
            .category-stats {{ margin-top: 15px; }}
            .category-item {{ margin: 5px 0; }}
        </style>
    </head>
    <body>
        <h1>📅 巨潮资讯每日速递 - {today}</h1>
        
        <div class="summary">
            <h3>📊 今日公告概览</h3>
            <p>今日共发布 <strong>{total_announcements}</strong> 份公告</p>
            
            <div class="category-stats">
                <h4>公告类型分布：</h4>
                {''.join([f'<div class="category-item"><strong>{category}</strong>: {count} 份</div>' for category, count in category_stats.items()])}
            </div>
        </div>
        
        <h2>⚠️ 重点企业监控</h2>
        {key_announcements_html}
        
        <h2>📋 今日公告详情</h2>
        {df.to_html(index=False, classes="table")}
        
        <p style="text-align: right; color: #888; margin-top: 30px;">数据来源：巨潮资讯网 | 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </body>
    </html>
    """
    
    return html_report
