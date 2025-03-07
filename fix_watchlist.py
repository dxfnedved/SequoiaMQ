import re

def fix_watchlist_paths():
    file_path = 'frontend-vue/src/api/watchlist.js'
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 修复两处API路径
    content = content.replace('return del(/watchlist/', 'return del(/api/watchlist/')
    content = content.replace('return put(/watchlist/', 'return put(/api/watchlist/')
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print('已修复 watchlist.js 中的API路径')

fix_watchlist_paths()
