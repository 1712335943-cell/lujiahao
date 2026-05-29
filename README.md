# Desktop Pet MVP

这是一个兼容 `Windows + macOS` 的桌宠原型，使用 `PySide6 Essentials` 开发。

当前能力：

- 透明悬浮桌宠
- 沿屏幕四边自动巡逻
- 到达角落自动转边
- 点击互动
- 拖拽后自动吸附边缘
- 托盘菜单
- 设置窗口
- 本地保存配置

## 安装

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

## 启动

```bash
./.venv/bin/python main.py
```

## 交互

- 左键拖动：移动桌宠，松手后自动贴边
- 双击：打开设置
- 右键：打开菜单
- 托盘图标：单击显示/隐藏，右键更多菜单

## 后续替换如鸢风资源

现在桌宠形象是代码绘制的原创占位图，方便先把逻辑跑通。后续你只需要把渲染逻辑换成：

- PNG 序列帧
- 精灵图
- Spine 资源

替换入口主要在：

- `desktop_pet/art.py`
- `desktop_pet/pet_window.py`

## 打包建议

### Windows 安装包

Windows 安装包需要在 Windows 机器上构建，不能在 macOS 上直接交叉打出可用的 `.exe` 安装包。

准备：

- 安装 Python 3.10+，安装时勾选 `Add python.exe to PATH`
- 安装 Inno Setup 6: https://jrsoftware.org/isinfo.php

在 Windows PowerShell 里进入项目目录后执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1
```

输出：

- 免安装程序目录：`dist\DesktopPet\DesktopPet.exe`
- 安装包：`release\DesktopPetSetup.exe`

如果没有安装 Inno Setup，脚本会只生成 `dist\DesktopPet\DesktopPet.exe`，不会生成安装包。

也可以把项目推到 GitHub，然后在 Actions 里手动运行 `Build Windows Installer`。构建完成后，页面底部的 `Artifacts` 会提供 `DesktopPetSetup.exe` 下载。

### macOS

```bash
pyinstaller --windowed --name DesktopPet main.py
```

如果要正式分发，macOS 还需要补签名和 notarization。
