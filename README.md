# 佛学工作室后端 (V4 架构实现·第一阶段)

FastAPI + SQLite + 可插拔 Provider 架构。当前无需任何付费 API Key 即可完整运行。

## 已真实实现并测试通过
- 通用文件摄取引擎：TXT / Markdown / DOCX / PDF（文字版）上传、解析、SHA256去重、软删除/恢复
- 统一检索（本地关键词，未来可换 pgvector / OpenAI Embedding）
- Practice Engine：木鱼/念珠/引磬等修行记录真实落库，刷新不丢失
- Notes：笔记真实落库，可关联资源
- AI 对话接口：未配置 Key 时如实返回"未配置"，不伪造回答
- 启动健康检查：如实报告每个依赖的连接状态
- 独立端口/独立数据库/独立日志/独立存储目录

## 尚未实现（依赖你后续决定）
- OCR（扫描版PDF）—— 需要额外安装 OCR 引擎
- 音频/视频处理（FFmpeg + STT/TTS）—— 需要安装 FFmpeg，且 STT/TTS 依赖 OpenAI Key
- 真实 AI 摘要/问答/向量语义检索 —— 需要你提供 OpenAI API Key
- n8n 双向自动化 —— 需要你已有 n8n 实例
- 前端尚未接入此后端（目前前端仍用 mock 数据，需要下一步对接）

## 本地运行
\`\`\`
python -m venv venv
venv\\Scripts\\activate   (Windows)  或  source venv/bin/activate (Mac/Linux)
pip install -r requirements.txt
python scripts/check_port.py
uvicorn app.main:app --reload
\`\`\`
启动后访问 http://localhost:5891/docs 查看/测试全部接口。

## 接入 OpenAI（可选，产生费用）
编辑 .env：
\`\`\`
AI_PROVIDER=openai
OPENAI_API_KEY=sk-xxx
\`\`\`
重启后 /api/health 会显示 ai_provider: connected。
