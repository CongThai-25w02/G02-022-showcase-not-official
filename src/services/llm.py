"""LLM factory — chọn provider qua settings.llm_provider.

  • "gemini" (mặc định): ChatGoogleGenerativeAI (cloud, cần GEMINI_API_KEY).
  • "ollama" (local): ChatOllama, trỏ tới Ollama trên máy (mặc định
    http://localhost:11434). Dùng để chạy agent TẠM THỜI bằng model local —
    không tốn quota cloud. Cần model hỗ trợ function-calling (qwen2.5, llama3.1)
    vì act_node dùng `bind_tools`.

Cả hai nhánh trả về một chat model tương thích LangChain (hỗ trợ `.ainvoke`
và `.bind_tools`), nên phần còn lại của agent không cần biết provider nào.
"""
from __future__ import annotations

from src.config import get_settings


def get_llm():
    """Trả về chat model theo provider đã cấu hình (gemini | ollama)."""
    settings = get_settings()

    if settings.llm_provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError as exc:  # pragma: no cover - lỗi môi trường
            raise ImportError(
                "LLM_PROVIDER=ollama nhưng chưa cài 'langchain-ollama'. "
                "Cài: pip install langchain-ollama  — và chạy Ollama: "
                f"`ollama pull {settings.ollama_model}` rồi `ollama serve`."
            ) from exc
        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=settings.llm_temperature,
        )

    # Mặc định: Gemini (cloud)
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=settings.model_name,
        google_api_key=settings.gemini_api_key,
        temperature=settings.llm_temperature,
    )
