#!/usr/bin/env python3
"""为新文章加图到 GitHub 图床仓库，push 并生成 URL 列表。

用法:
  add.py <源目录> [slug]                    # 拷图 + push + 打印 URL 表
  add.py <源目录> [slug] --html <HTML路径>  # 顺便替换 HTML 里的图片路径
  add.py <源目录> [slug] --dry-run          # 只显示要做什么，不实际执行

参数:
  源目录        含 jpg/jpeg/png/webp 的目录
  slug          仓库里的子目录名（不给默认 = 源目录名）

示例:
  add.py ~/Desktop/新文章/配图 climate-2027
  add.py ~/Desktop/新文章/配图 climate-2027 --html ~/Desktop/新文章/文章.html
"""
import argparse, os, shutil, subprocess, sys
from urllib.parse import quote

REPO_ROOT = os.path.expanduser("~/Desktop/assets")
REPO_OWNER = "Chiwang3047"
REPO_NAME = "assets"
BRANCH = "main"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def jsdelivr(slug, fn):
    return f"https://cdn.jsdelivr.net/gh/{REPO_OWNER}/{REPO_NAME}@{BRANCH}/{slug}/{quote(fn)}"


def raw_gh(slug, fn):
    return f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{slug}/{quote(fn)}"


def run(cmd, cwd=None, check=True):
    print(f"  $ {' '.join(cmd)}")
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.stdout.strip():
        print("  " + r.stdout.strip().replace("\n", "\n  "))
    if r.returncode != 0:
        print(f"  ✗ stderr: {r.stderr.strip()}", file=sys.stderr)
        if check:
            sys.exit(r.returncode)
    return r


def main():
    p = argparse.ArgumentParser(description="新文章配图 → GitHub 图床")
    p.add_argument("source_dir", help="含图片的源目录")
    p.add_argument("slug", nargs="?", help="仓库子目录名（默认=源目录名）")
    p.add_argument("--html", help="要顺便替换路径的 HTML 文件")
    p.add_argument("--dry-run", action="store_true", help="只显示不执行")
    p.add_argument("--force", action="store_true", help="目标 slug 目录已存在时覆盖")
    args = p.parse_args()

    src = os.path.abspath(os.path.expanduser(args.source_dir))
    if not os.path.isdir(src):
        sys.exit(f"✗ 源目录不存在: {src}")

    slug = args.slug or os.path.basename(src.rstrip("/"))
    dst = os.path.join(REPO_ROOT, slug)

    imgs = sorted(f for f in os.listdir(src) if os.path.splitext(f)[1].lower() in IMAGE_EXTS)
    if not imgs:
        sys.exit(f"✗ 源目录里没有 jpg/png/webp 图片: {src}")

    print(f"源目录: {src}")
    print(f"slug:  {slug}  → 仓库: {dst}")
    print(f"图片:  {len(imgs)} 张")
    for fn in imgs:
        print(f"       {fn}")
    print()

    if os.path.exists(dst) and not args.force:
        sys.exit(f"✗ 目标已存在: {dst}\n  加 --force 覆盖，或换一个 slug")

    if args.dry_run:
        print("=== dry-run，以下为将执行的命令 ===")
        print(f"  mkdir -p {dst}")
        print(f"  cp {src}/*.{{jpg,png,webp,...}} {dst}/")
        print(f"  cd {REPO_ROOT} && git add {slug} && git commit -m 'add {slug} images ({len(imgs)})' && git push")
    else:
        print("=== 拷贝图片 ===")
        os.makedirs(dst, exist_ok=True)
        for fn in imgs:
            shutil.copy2(os.path.join(src, fn), os.path.join(dst, fn))
            print(f"  ✓ {fn}")

        print("\n=== git add / commit / push ===")
        run(["git", "add", slug], cwd=REPO_ROOT)
        run(["git", "commit", "-m", f"add {slug} images ({len(imgs)})"], cwd=REPO_ROOT)
        run(["git", "push"], cwd=REPO_ROOT)

    print("\n=== URL 列表（jsDelivr CDN，国内加速）===")
    print()
    print("| 文件 | jsDelivr URL |")
    print("|------|--------------|")
    for fn in imgs:
        print(f"| {fn} | {jsdelivr(slug, fn)} |")

    urls_md = os.path.join(src, "urls.md")
    with open(urls_md, "w", encoding="utf-8") as f:
        f.write(f"# {slug} · 图床 URL\n\n")
        f.write("## jsDelivr CDN（推荐，国内加速）\n\n")
        for fn in imgs:
            f.write(f"- **{fn}**\n  `{jsdelivr(slug, fn)}`\n\n")
        f.write("## GitHub Raw（备选）\n\n")
        for fn in imgs:
            f.write(f"- **{fn}**\n  `{raw_gh(slug, fn)}`\n\n")
    print(f"\nURL 列表已保存: {urls_md}")

    if args.html and not args.dry_run:
        if not os.path.isfile(args.html):
            print(f"⚠ HTML 不存在: {args.html}")
            return
        with open(args.html, encoding="utf-8") as f:
            html = f.read()
        n = 0
        for fn in imgs:
            for old in (f"./{slug}/{fn}", f"{slug}/{fn}"):
                if old in html:
                    html = html.replace(old, jsdelivr(slug, fn))
                    n += 1
                    break
        out = os.path.splitext(args.html)[0] + "_github.html"
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"\nHTML 已重写: {out}（替换 {n}/{len(imgs)} 张）")


if __name__ == "__main__":
    main()
