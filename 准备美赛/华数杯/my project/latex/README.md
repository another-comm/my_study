# 华数杯数学建模竞赛 LaTeX 项目

## 项目说明

本项目用于华数杯数学建模竞赛的论文编写。

## 文件结构

- `main.tex` - 主文档文件
- `README.md` - 项目说明文件

## 编译方法

使用 XeLaTeX 编译（推荐，支持中文）：

```bash
xelatex main.tex
xelatex main.tex  # 第二次编译以生成目录
```

或使用 pdfLaTeX：

```bash
pdflatex main.tex
pdflatex main.tex
```

## 注意事项

1. 确保已安装 CTeX 宏包或 TeX Live 完整版
2. 编译时需要支持中文的 LaTeX 发行版
3. 建议使用 XeLaTeX 引擎编译以获得更好的中文支持
