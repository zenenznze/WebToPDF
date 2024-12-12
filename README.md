# WebToPDF 网页转PDF工具

A tool to capture screenshots of web pages and convert them to PDF using headless browser.
一个使用无头浏览器将网页截图并转换为PDF的工具。

## Features 功能特点

- Convert any web page to PDF 将任何网页转换为PDF
- Take full-page screenshots 支持全页面截图
- Headless browser automation 无头浏览器自动化
- Support custom viewport sizes 支持自定义视窗大小

## Prerequisites 环境要求

- Python 3.7+
- Node.js 14+
- Playwright or Puppeteer (will be specified in requirements.txt)

## Installation 安装

1. Clone the repository 克隆仓库
```bash
git clone https://github.com/yourusername/webtopdf.git
cd webtopdf
```

2. Install dependencies 安装依赖
```bash
pip install -r requirements.txt
```

## Usage 使用方法

```bash
python main.py --url https://example.com --output example.pdf
```

### Parameters 参数说明

- `--url`: Target webpage URL 目标网页URL
- `--output`: Output PDF file path 输出PDF文件路径
- `--width`: Viewport width (optional, default: 1920) 视窗宽度（可选，默认：1920）
- `--height`: Viewport height (optional, default: 1080) 视窗高度（可选，默认：1080）

## Example 示例

```bash
python main.py --url https://github.com --output github.pdf
```

## License 许可证

MIT License

## Contributing 贡献

Feel free to open issues and pull requests!
欢迎提出问题和贡献代码！
