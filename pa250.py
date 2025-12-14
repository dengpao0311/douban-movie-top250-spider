# 豆瓣电影爬虫 - 我自己写的第一个能用的爬虫
# 2024年12月刚学完爬虫基础时做的

import requests
from bs4 import BeautifulSoup
import csv
import time
import random


# 豆瓣电影TOP250的页面
# 我研究了好久才发现分页规律：?start=0, 25, 50...
# 每页25部电影，一共10页

def get_one_page(page_num):
    """抓取一页的数据，page_num从0到9"""

    # 设置请求头，不然豆瓣会拒绝访问
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    # 计算start参数
    start = page_num * 25
    url = f'https://movie.douban.com/top250?start={start}'

    print(f'正在抓取第 {page_num + 1} 页...')

    try:
        # 发送请求
        response = requests.get(url, headers=headers, timeout=10)

        # 检查状态码
        if response.status_code != 200:
            print(f'第 {page_num + 1} 页请求失败，状态码：{response.status_code}')
            return None

        # 设置编码，不然中文会乱码
        response.encoding = 'utf-8'

        return response.text

    except Exception as e:
        print(f'第 {page_num + 1} 页出错：{e}')
        return None


def parse_html(html):
    """解析HTML，提取电影信息"""

    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')

    # 豆瓣的每部电影都在class="item"的div里
    movie_items = soup.find_all('div', class_='item')

    movies = []

    for item in movie_items:
        # 电影标题
        title_tag = item.find('span', class_='title')
        title = title_tag.text if title_tag else '未知'

        # 评分
        rating_tag = item.find('span', class_='rating_num')
        rating = rating_tag.text if rating_tag else '0.0'

        # 评价人数 - 这个找了好久才找到正确的位置
        star_div = item.find('div', class_='star')
        if star_div:
            # star里面的最后一个span是评价人数
            all_spans = star_div.find_all('span')
            if len(all_spans) >= 4:
                comment_text = all_spans[3].text  # 比如 "(1234567人评价)"
                # 去掉括号和"人评价"
                comment_num = comment_text.replace('(', '').replace(')', '').replace('人评价', '')
            else:
                comment_num = '0'
        else:
            comment_num = '0'

        # 短评 - 有时候没有
        quote_tag = item.find('span', class_='inq')
        quote = quote_tag.text if quote_tag else '无'

        # 导演和演员信息 - 后来加的，开始没注意到
        info_div = item.find('div', class_='bd')
        if info_div:
            # 第二个p标签里是导演演员信息
            p_tags = info_div.find_all('p')
            if len(p_tags) > 1:
                info_text = p_tags[1].text.strip()
                # 去掉多余的空格和换行
                info_text = ' '.join(info_text.split())
            else:
                info_text = '未知'
        else:
            info_text = '未知'

        movies.append({
            '排名': len(movies) + 1,
            '电影名': title,
            '评分': rating,
            '评价人数': comment_num,
            '短评': quote,
            '信息': info_text[:50] + '...' if len(info_text) > 50 else info_text  # 截取前50字符
        })

    print(f'本页解析到 {len(movies)} 部电影')
    return movies


def save_to_csv(movies, filename='douban_movies.csv'):
    """保存数据到CSV文件"""

    if not movies:
        print('没有数据可保存')
        return

    # 最开始用utf-8，发现Excel打开乱码
    # 查了下要用utf-8-sig，Excel才能正确显示中文
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        # 定义CSV的列
        fieldnames = ['排名', '电影名', '评分', '评价人数', '短评', '信息']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        # 写表头
        writer.writeheader()

        # 写入数据
        writer.writerows(movies)

    print(f'数据已保存到 {filename}，共 {len(movies)} 条记录')


def main():
    """主函数"""

    print('=' * 50)
    print('豆瓣电影TOP250爬虫 - 开始运行')
    print('=' * 50)

    all_movies = []

    # 抓取10页数据
    for page in range(10):
        # 抓取一页
        html = get_one_page(page)

        if html:
            # 解析数据
            movies = parse_html(html)
            all_movies.extend(movies)

            # 显示本页第一条电影
            if movies:
                first_movie = movies[0]
                real_rank = page * 25 + 1
                print(f'  第{real_rank}名：{first_movie["电影名"]} - {first_movie["评分"]}分')

        # 随机等待1-3秒，避免被封IP
        # 一开始没加这个，抓了几页就被限制了
        wait_time = random.uniform(1, 3)
        time.sleep(wait_time)

        print()  # 空行

    # 显示统计信息
    print('=' * 50)
    print(f'抓取完成！总共获取 {len(all_movies)} 部电影')

    # 显示前5名
    print('\n豆瓣电影TOP5：')
    for i in range(min(5, len(all_movies))):
        movie = all_movies[i]
        print(f'{i + 1}. {movie["电影名"]} - {movie["评分"]}分（{movie["评价人数"]}人评价）')
        print(f'   短评：{movie["短评"]}')

    # 保存数据
    save_to_csv(all_movies)

    print('\n程序运行结束！')
    print('可以打开 douban_movies.csv 查看完整数据')


# 测试用的函数 - 最开始写的时候用来调试的
def test_one_page():
    """测试只抓取第一页"""
    print('测试模式：只抓取第一页')
    html = get_one_page(0)
    if html:
        movies = parse_html(html)
        print(f'第一页有 {len(movies)} 部电影：')
        for movie in movies[:3]:  # 只显示前3部
            print(f'  {movie["电影名"]} - {movie["评分"]}分')


if __name__ == '__main__':

    main()