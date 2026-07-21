<h1>
  <img src="resources/icon/icon.png" width="185" height="185" style="float: right;">
  PaperSlice — PDF Poster Splitter
</h1>

将大型 PDF 页面（A0/A1/A2/A3 等）智能切分为可打印的标准纸张（A4/Letter 等），支持交互式分割线、手动排序、批量导出。

A desktop tool for splitting large PDF pages into printable tiles with interactive split-line placement, manual tile ordering, and batch export.

---

## 功能特性

| 功能 | 说明 |
|------|------|
| 交互式切割线 | 垂直/水平/四等分预设 + 手动添加 + 鼠标拖拽微调 |
| 页面筛选 | 按页码范围/指定列表、页面尺寸、方向筛选，仅影响显示不改变勾选 |
| 页面选择 | 每页独立复选框 + 三态全选，仅勾选页参与导出 |
| 视图切换 | 全部页面 / 筛选结果一键切换，复选框状态完全保留 |
| 排序规则 | 可调先行后列/先列后行、行/列遍历方向，实时微型网格预览 |
| 一键排序 | "自动"按钮按规则瞬间排列图块，点击图块仍可微调 |
| 页面缓存 | 切换页面自动保存/恢复每页的分割线和排序状态 |
| 项目存档 | `.ppslc` 格式保存所有页面配置，关闭时提示保存 |
| 导出控制 | 导出已选择页 / 切分并导出全部页，未勾选页自动跳过 |
| 实时预览 | 可调 DPI (100/150/300/自定义) 渲染，支持缩放和拖拽 |
| 图片导入 | 支持 PNG/JPG/BMP/TIFF 作为单页文档导入 |
| 多纸张支持 | ISO216 (A0-A10, B0-B10) + ANSI + North American (Letter/Legal/Tabloid) |

---

## 操作流程

```
1. 打开或拖拽                     [打开 PDF / 图片] 按钮 或 [拖拽文件到预览框]
   │
2. 选择目标纸张             [类别] + [大小] 下拉框
   │
3. 勾选参与导出的页面       [全选] 复选框 / 逐个勾选
   ├─ 筛选: [筛选] 按钮 → 按页码/尺寸/方向过滤显示
   └─ 视图: [全部页面 / 筛选结果] 切换
   │
4. 放置分割线
   ├─ 预设:   垂直二分 / 水平二分 / 四等分
   ├─ 手动:   + 竖线 / + 横线
   ├─ 批量:   勾选"应用到已选择页"后操作
   ├─ 拖拽:   鼠标拖动切割线微调
   └─ 清除:   清除切割线
   │
5. 排序图块
   ├─ [规则]  自定义行列方向与优先轴 (预览网格)
   ├─ [自动]  一键按规则排列, 勾选"应用到已选择页"则批量
   ├─ 点击:   点击预览图块手动调整顺序
   └─ [重置]  恢复默认顺序
   │
6. 导出
   ├─ 导出已选择页  →  仅导出勾选的页面到单个 PDF
   └─ 切分并导出    →  导出所有已配置页面到单个 PDF
```

![界面示例](resources/images/sample.png)

---

## 技术架构

**Clean Architecture + MVVM + DDD** 分层设计：

```
┌──────────────────────────────────────────────────┐
│  Presentation (PySide6)                           │
│  MainWindow ←→ MainViewModel (Qt Signal 桥接)     │
│  PreviewWidget (QGraphicsView, 拖拽/点击交互)      │
├──────────────────────────────────────────────────┤
│  Application (无 Qt/PyMuPDF 依赖)                  │
│  UseCases / DTOs / Repository Interfaces          │
├──────────────────────────────────────────────────┤
│  Domain (无任何外部依赖)                             │
│  Geometry → Paper → Document → Layout → Export    │
├──────────────────────────────────────────────────┤
│  Infrastructure                                   │
│  MuPDFRepository / PdfSplitter / ConfigService    │
└──────────────────────────────────────────────────┘
```

调用链：`GUI → ViewModel → UseCase → Repository Interface → MuPDF Adapter → PyMuPDF`

---

## 编译与运行

### 环境要求

- Python >= 3.10
- Windows / macOS / Linux

### 安装

```bash
git clone https://github.com/Eason3Blue/PaperSlice.git
cd PaperSlice
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 运行

```bash
# 普通模式
python -m pdfsplitter.main

# 开发模式 (启用 DEBUG 日志)
# PowerShell:
$env:pdfsplitter_DEV = "1"
python -m pdfsplitter.main
# CMD:
set pdfsplitter_DEV=1 && python -m pdfsplitter.main
```

### 测试

```bash
pytest tests/ -v

# 按模块运行
pytest tests/domain/geometry/ -v
pytest tests/domain/layout/ -v

# 覆盖率
pytest tests/ --cov=pdfsplitter --cov-report=html
```

### 打包为 exe

```bash
pip install pyinstaller
python build.py              # 构建
python build.py --clean      # 清理后构建
```

产物位于 `dist/PaperSlice/PaperSlice.exe`。图标：`resources/icon/icon.ico`。

### 依赖

| 包 | 版本 | 用途 |
|----|------|------|
| PySide6 | >=6.5.0 | GUI 框架 |
| PyMuPDF | >=1.24.0 | PDF 渲染与操作 |
| pypdf | >=4.0.0 | PDF 元数据处理 |
| rich | >=13.0.0 | 终端日志美化 |
| pytest | >=8.0.0 | 单元测试 |

---

## 项目结构

```
PaperSlice/
├── pdfsplitter/
│   ├── domain/            # 领域层: geometry, paper, layout, document, export
│   ├── application/       # 应用层: DTOs, UseCases, Repository 接口
│   ├── infrastructure/    # 基础设施: MuPDF, fitz, config, logging
│   ├── presentation/      # 表示层: MainWindow, ViewModel, PreviewWidget
│   ├── bootstrap.py       # DI 组合根
│   └── main.py            # 入口点
├── tests/                 # 单元测试 (292 条)
├── resources/             # 图标 & 图片
├── AGENTS.md              # AI Agent 开发指引
├── build.py               # PyInstaller 打包脚本
└── requirements.txt
```

---

## 配置

`settings.json`（自动创建于运行目录）：

```json
{
  "version": 1,
  "recent_files": [],
  "last_paper": "A4",
  "last_paper_category": "ISO216",
  "last_margin_mm": 10.0,
  "last_overlap_mm": 5.0,
  "cut_lines_enabled": false,
  "page_numbers_enabled": false,
  "default_dpi": 150,
  "window_geometry": null,
  "language": "zh_CN"
}
```

---

## 路线图

| 功能 | 状态 |
|------|------|
| 交互式切割线 + 手动排序 + 批量导出 | ✅ |
| 图片支持 (PNG/JPG/BMP/TIFF) | ✅ |
| 页面筛选 (页码/尺寸/方向) | ✅ |
| 页面选择 (复选框 + 三态全选) | ✅ |
| 可调排序规则 (方向/优先轴) | ✅ |
| 预览缩放 + 渲染精度调整 | ✅ |
| 项目存档 (.ppslc) | ✅ |
| Overlap (重叠) 支持 | 🔜 |
| CLI 命令行模式 | 📋 |
| 插件系统 | 📋 |
| Crop / Merge / Booklet / N-Up | 📋 |

---

## 许可证

GPL v3.0 License
