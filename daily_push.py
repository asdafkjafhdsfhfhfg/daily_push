import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
import datetime
import os  # 用于读取 GitHub Secrets
import sys

# --- 环境变量配置 (从 GitHub Secrets 读取) ---
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

def fetch_github_trending():
    print("正在抓取 GitHub Trending 数据...")
    url = "https://github.com/trending"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        repos = soup.select('article.Box-row')
        trending_list = []
        for repo in repos[:5]:
            title_tag = repo.select_one('h2 a')
            name = title_tag.text.strip().replace('\n', '').replace(' ', '')
            link = "https://github.com" + title_tag['href']
            
            desc_tag = repo.select_one('p.col-9')
            description = desc_tag.text.strip() if desc_tag else "暂无描述"
            
            stars_tag = repo.select_one('span.d-inline-block.float-sm-right')
            stars = stars_tag.text.strip() if stars_tag else "N/A"
            
            trending_list.append({"name": name, "link": link, "desc": description, "stars": stars})
        
        print(f"成功获取 {len(trending_list)} 条数据")
        return trending_list
    except Exception as e:
        print(f"抓取失败: {e}")
        return []

def format_html_email(projects):
    if not projects:
        return None
    
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    # 保持你喜欢的列表样式 + 裸链接
    html_content = f"""
    <html>
    <body style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
        <div style="padding: 20px 0; border-bottom: 2px solid #eaecef; margin-bottom: 20px;">
            <h2 style="margin: 0; color: #24292e;">🚀 GitHub 每日 start 榜单 top 5</h2>
            <p style="margin: 5px 0 0; color: #586069; font-size: 14px;">{date_str} | Daily Report</p>
        </div>
    """
    
    for idx, p in enumerate(projects, 1):
        html_content += f"""
        <div style="margin-bottom: 25px; padding-bottom: 15px; border-bottom: 1px dashed #e1e4e8;">
            <div style="font-size: 18px; margin-bottom: 4px;">
                <span style="background-color: #24292e; color: #fff; padding: 2px 8px; border-radius: 10px; font-size: 12px; vertical-align: middle; margin-right: 8px;">#{idx}</span>
                <span style="font-weight: bold; color: #333; vertical-align: middle;">{p['name']}</span>
            </div>
            <div style="font-size: 12px; font-family: Consolas, Monaco, monospace; color: #0366d6; margin-bottom: 10px; word-break: break-all; background-color: #f6f8fa; padding: 4px 8px; border-radius: 4px;">
                {p['link']}
            </div>
            <div style="color: #586069; font-size: 14px; margin-bottom: 8px;">
                {p['desc']}
            </div>
            <div style="font-size: 13px; color: #d73a49; font-weight: 600;">
                🔥 今日新增 Star: {p['stars']}
            </div>
        </div>
        """
        
    html_content += "</body></html>"
    return html_content

def send_email(content):
    if not content:
        return

    # 检查环境变量是否存在
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("❌ 错误: 未找到环境变量 SENDER_EMAIL 或 SENDER_PASSWORD")
        return

    print("正在连接邮件服务器...")
    message = MIMEText(content, 'html', 'utf-8')
    message['From'] = formataddr(["GitHub Bot", SENDER_EMAIL])
    message['To'] = formataddr(["User", RECEIVER_EMAIL])
    message['Subject'] = Header(f"GitHub Trending - {datetime.datetime.now().strftime('%H:%M')}", 'utf-8')

    try:
        smtp_obj = smtplib.SMTP_SSL('smtp.qq.com', 465)
        smtp_obj.login(SENDER_EMAIL, SENDER_PASSWORD)
        smtp_obj.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], message.as_string())
        smtp_obj.quit()
        print(f"✅ 发送成功")
    except smtplib.SMTPException as e:
        print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    # 直接运行一次逻辑
    projects = fetch_github_trending()
    if projects:
        email_content = format_html_email(projects)
        send_email(email_content)
    else:
        print("未获取到数据，跳过发送")
