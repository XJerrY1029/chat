# My ChatGPT-like Project

![界面截图](screenshot.png)

## 功能特性
- 类 ChatGPT 对话界面
- 支持 PDF/Word 文件分析
- 实时消息交互
- 流式响应支持

## 技术栈
| 前端                 | 后端             |
|----------------------|------------------|
| React + TypeScript   | FastAPI          |
| Vite                 | OpenAI API       |

## 本地运行
```bash
# 后端
cd backend && pip install -r requirements.txt
uvicorn main:app --reload

# 前端
cd frontend && npm install
npm run dev
