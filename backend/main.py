# backend/main.py
import os
import io
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from PyPDF2 import PdfReader, errors as pdf_errors
from docx import Document
from openai import OpenAI

# 加载环境变量（必须放在最前面）
load_dotenv()

# --------------------------
# FastAPI 初始化
# --------------------------
app = FastAPI(title="ChatGPT-like API")

# 配置跨域（生产环境需限制 origins）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 OpenAI 客户端
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# --------------------------
# 数据模型
# --------------------------
class ChatRequest(BaseModel):
    messages: List[dict]
    model: Optional[str] = "gpt-3.5-turbo"
    max_tokens: Optional[int] = 1000


class FileAnalysisResponse(BaseModel):
    filename: str
    summary: str
    content_preview: str


# --------------------------
# 核心逻辑
# --------------------------
@app.post("/api/chat", response_model=dict)
async def chat_handler(request: ChatRequest):
    """处理聊天请求"""
    try:
        # 输入验证
        if not request.messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Messages cannot be empty"
            )

        # 调用 OpenAI API
        response = client.chat.completions.create(
            model=request.model,
            messages=request.messages,
            temperature=0.7,
            max_tokens=request.max_tokens
        )

        return {
            "content": response.choices[0].message.content,
            "role": "assistant",
            "model": request.model
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OpenAI API 请求失败: {str(e)}"
        )


@app.post("/api/analyze", response_model=FileAnalysisResponse)
async def analyze_file(file: UploadFile = File(...)):
    """文件内容分析接口"""
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_MIME_TYPES = {
        "pdf": "application/pdf",
        "txt": "text/plain",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    }

    try:
        # 基础验证
        if file.content_type not in ALLOWED_MIME_TYPES.values():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型，仅支持 {list(ALLOWED_MIME_TYPES.keys())}"
            )

        # 读取文件内容
        content = await file.read()

        # 文件大小验证
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件大小超过 {MAX_FILE_SIZE // 1024 // 1024}MB 限制"
            )

        # 文件解析
        text = ""
        if file.content_type == ALLOWED_MIME_TYPES["pdf"]:
            try:
                reader = PdfReader(io.BytesIO(content))
                text = "\n".join([page.extract_text() or "" for page in reader.pages])
            except pdf_errors.PdfReadError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="PDF 文件解析失败，请确认文件完整性"
                )
        elif file.content_type == ALLOWED_MIME_TYPES["docx"]:
            try:
                doc = Document(io.BytesIO(content))
                text = "\n".join([para.text for para in doc.paragraphs if para.text])
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Word 文档解析失败"
                )
        else:
            text = content.decode("utf-8", errors="ignore")

        # 内容截断（防止过长请求）
        processed_text = text[:5000].strip()  # 最多处理前5000个字符
        if not processed_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件内容为空或无法解析出文本"
            )

        # 调用 OpenAI 分析
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{
                "role": "user",
                "content": f"请用中文总结以下内容（200字内）：\n{processed_text}"
            }],
            temperature=0.3  # 降低随机性保证摘要准确性
        )

        return {
            "filename": file.filename,
            "summary": response.choices[0].message.content,
            "content_preview": processed_text[:300] + "..."  # 返回部分预览
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件处理失败: {str(e)}"
        )


# --------------------------
# 健康检查端点
# --------------------------
@app.get("/", include_in_schema=False)
async def health_check():
    return {
        "status": "active",
        "api_version": "1.0.0",
        "endpoints": {
            "chat": "/api/chat",
            "file_analysis": "/api/analyze"
        }
    }


# --------------------------
# 错误处理
# --------------------------
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "success": False
        }
    )