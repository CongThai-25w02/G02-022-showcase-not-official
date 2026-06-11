# Architecture Diagram — AI20K‑162 Task‑Planner Agent

## System Overview

```mermaid
graph TB
    User([Vận hành viên]) -->|mục tiêu tiếng Việt| FE[Frontend<br/>canvas 2D + trace]
    FE <-->|REST + WebSocket| API[FastAPI]
    API --> AGENT[LangGraph Agent]
    AGENT -->|function-calling| GEM[Gemini]
    AGENT -->|tools| WORLD[World sim Python<br/>grid · robot · objects · people]
    WORLD --> FE
    AGENT --> LS[(LangSmith)]
```

## Agent Flow (vòng lập kế hoạch)

```mermaid
graph LR
    START((Mục tiêu NL)) --> PARSE[parse_goal]
    PARSE --> PERCEIVE[perceive world]
    PERCEIVE --> PLAN[plan: LLM sinh các bước]
    PLAN --> ACT[act: gọi 1 tool]
    ACT --> OBS{observe: kết quả?}
    OBS -->|ok, chưa xong| ACT
    OBS -->|bị chặn / vật cản| REPLAN[replan]
    REPLAN --> PLAN
    OBS -->|có người ở lối| ASK[safety: dừng + ask_human]
    ASK --> PLAN
    OBS -->|đạt mục tiêu| SUM[summarize + trace]
    SUM --> END((Done))
```

## Component Details

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Frontend | Canvas 2D (JS) | Nhập mục tiêu, render sim + robot + người, hiển thị kế hoạch/trace |
| Backend | FastAPI | API + WebSocket stream |
| Agent | LangGraph + LangChain | Plan‑and‑execute + ReAct, vòng replan |
| LLM | Gemini (function‑calling) | Sinh kế hoạch + chọn tool |
| Sim World | Python `World` (grid, A*) | Môi trường có thẩm quyền; tool đọc/đổi trạng thái |
| Tools | perceive/locate/check_path/move/pick/drop/wait/ask/done | Primitives tri giác + hành động |
| Logging | LangSmith | Log prompt + tool calls (AI logs) |
| Tests | pytest | Tools, world, graph, eval |

## Tool layer (primitives của agent)

```mermaid
graph TB
    subgraph Perception["Tri giác (đọc world)"]
        P1[perceive]
        P2[locate_object]
        P3[check_path]
    end
    subgraph Action["Hành động (đổi world)"]
        A1[move_to]
        A2[pick]
        A3[drop]
    end
    subgraph Meta["Meta / an toàn"]
        M1[wait]
        M2[ask_human]
        M3[done]
    end
    AGENT[LangGraph Agent] --> Perception & Action & Meta --> WORLD[(World sim)]
```

> Ghi chú trung thực: thế giới là **mô phỏng 2D** (không phải robot thật); **agent là thật** — LLM lập kế hoạch + gọi tool + đọc observation thật từ sim (không tự "tưởng tượng" kết quả). Đây là planner mức nhiệm vụ, chưa thay lớp điều khiển/an toàn cứng của robot thật.
