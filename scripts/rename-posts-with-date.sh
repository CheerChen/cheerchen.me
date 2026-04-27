#!/bin/bash

# 批量修改 posts 文件夹名，添加日期前缀
# 同时在所有 markdown 文件的 front matter 中添加 slug 字段以保持 URL 不变

set -e  # 遇到错误立即退出

POSTS_DIR="content/posts"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 检查 posts 目录是否存在
if [ ! -d "$POSTS_DIR" ]; then
    echo "错误: $POSTS_DIR 目录不存在"
    exit 1
fi

echo "开始处理 $POSTS_DIR 目录下的文件夹..."
echo "----------------------------------------"

# 遍历 posts 目录下的所有子文件夹
for dir in "$POSTS_DIR"/*/ ; do
    # 跳过不存在的目录
    [ -d "$dir" ] || continue
    
    # 获取文件夹名（不含路径和尾部斜杠）
    folder_name=$(basename "$dir")
    
    # 跳过 .DS_Store 等隐藏文件
    if [[ "$folder_name" == .* ]]; then
        continue
    fi
    
    echo ""
    echo "处理文件夹: $folder_name"
    
    # 查找 index.zh.md 文件来提取日期
    zh_file="$dir/index.zh.md"
    
    if [ ! -f "$zh_file" ]; then
        echo "  ⚠️  警告: 未找到 $zh_file，跳过此文件夹"
        continue
    fi
    
    # 从 index.zh.md 提取日期 (格式: date = '2025-07-29T15:25:26+09:00')
    date_line=$(grep -E "^date = '[0-9]{4}-[0-9]{2}-[0-9]{2}T" "$zh_file" | head -n 1)
    
    if [ -z "$date_line" ]; then
        echo "  ⚠️  警告: 未找到有效的日期字段，跳过此文件夹"
        continue
    fi
    
    # 提取日期部分 (YYYY-MM-DD)
    date=$(echo "$date_line" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -n 1)
    
    if [ -z "$date" ]; then
        echo "  ⚠️  警告: 无法解析日期，跳过此文件夹"
        continue
    fi
    
    echo "  📅 提取到日期: $date"
    
    # 检查文件夹名是否已经包含日期前缀
    if [[ "$folder_name" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}- ]]; then
        echo "  ℹ️  文件夹名已包含日期前缀，跳过重命名"
        # 但仍然需要检查并添加 slug 字段
        original_slug=$(echo "$folder_name" | sed -E 's/^[0-9]{4}-[0-9]{2}-[0-9]{2}-//')
    else
        original_slug="$folder_name"
    fi
    
    echo "  🔖 原始 slug: $original_slug"
    
    # 新文件夹名
    new_folder_name="${date}-${original_slug}"
    new_dir="${POSTS_DIR}/${new_folder_name}"
    
    # 查找所有 .md 文件
    md_files=("$dir"*.md)
    
    if [ ${#md_files[@]} -eq 0 ]; then
        echo "  ⚠️  警告: 未找到 markdown 文件，跳过此文件夹"
        continue
    fi
    
    echo "  📝 找到 ${#md_files[@]} 个 markdown 文件"
    
    # 为所有 markdown 文件添加 slug 字段
    for md_file in "${md_files[@]}"; do
        [ -f "$md_file" ] || continue
        
        md_filename=$(basename "$md_file")
        echo "    处理: $md_filename"
        
        # 检查是否已存在 slug 字段
        if grep -q "^slug = " "$md_file"; then
            echo "      ℹ️  已存在 slug 字段，跳过"
            continue
        fi
        
        # 在 front matter 中的 date 行后添加 slug 字段
        # 使用 sed 在包含 date = 的行后插入 slug 行
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS 使用 BSD sed
            sed -i '' "/^date = /a\\
slug = '$original_slug'
" "$md_file"
        else
            # Linux 使用 GNU sed
            sed -i "/^date = /a slug = '$original_slug'" "$md_file"
        fi
        
        echo "      ✅ 已添加 slug = '$original_slug'"
    done
    
    # 重命名文件夹（如果需要）
    if [ "$folder_name" != "$new_folder_name" ]; then
        if [ -d "$new_dir" ]; then
            echo "  ⚠️  警告: 目标文件夹 $new_folder_name 已存在，跳过重命名"
        else
            mv "$dir" "$new_dir"
            echo "  ✅ 文件夹已重命名: $folder_name -> $new_folder_name"
        fi
    else
        echo "  ℹ️  文件夹名无需更改"
    fi
    
    echo "  ✅ 完成处理"
done

echo ""
echo "----------------------------------------"
echo "✅ 所有文件夹处理完成！"
echo ""
echo "建议操作："
echo "1. 运行 'hugo server' 检查网站是否正常"
echo "2. 访问几篇博文，确认 URL 没有改变"
echo "3. 如果一切正常，提交改动到 git"
