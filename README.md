# 3D照片生成器

## 功能
- 上传一张照片
- AI自动生成3D模型
- 浏览器中可旋转/缩放查看
- 一键下载保存到本地

## 技术栈
- 后端：Python + FastAPI + TripoSR
- 前端：HTML + Three.js
- 显卡：GTX 1650 Ti 4GB

## 目录结构
```
D:\3d-photo\
├── backend\          # FastAPI 后端
│   └── app.py
├── frontend\         # Three.js 前端
│   └── index.html
├── outputs\          # 生成的3D模型存储
├── setup.bat         # 一键安装脚本
└── start.bat         # 一键启动脚本
```
