# Codebase — Grocery AI

Toàn bộ code prototype của nhóm.

---

## Cách chạy prototype

### 1. Cài dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Tạo file `.env`

```bash
cp .env.example .env
# Mở .env và điền OPENAI_API_KEY + mongo_url
```

Nội dung `.env` cần có:

```
OPENAI_API_KEY=sk-your-key-here
mongo_url=mongodb://localhost:27017
```

### 3. Chạy server (Flask)

```bash
python app.py
```

Server chạy tại: `http://127.0.0.1:5001`

### 4. Mở các giao diện

| Giao diện | URL |
|---|---|
| Customer (Chat AI) | http://127.0.0.1:5001/ |
| Store Picker | http://127.0.0.1:5001/store |
| Driver | http://127.0.0.1:5001/driver |

> Nếu muốn chạy FastAPI version thay thế:
> ```bash
> python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
> ```
> Mở: http://127.0.0.1:8000/chat

---

## Tools & API đã dùng

| Công nghệ | Mục đích |
|---|---|
| **OpenAI GPT-3.5-turbo** | AI tư vấn nguyên liệu, hiểu tiếng Việt tự nhiên |
| **Python Flask 3.0** | Web backend chính + API routes |
| **FastAPI + uvicorn** | Alternative backend với MongoDB support |
| **HTML / CSS / Vanilla JS** | 3 giao diện: Customer, Store, Driver |
| **CSV files** | Kho nguyên liệu (~40 items) + 50 công thức món ăn |
| **MongoDB (PyMongo)** | Database cho FastAPI version |
| **python-dotenv** | Quản lý biến môi trường |

---

## Cấu trúc file

```
codebase/
├── app.py               ← Flask backend (main prototype)
├── grocery_agent.py     ← AI agent standalone
├── requirements.txt     ← Python dependencies
├── .env.example         ← Template biến môi trường
├── app/                 ← FastAPI module (alternative)
│   ├── main.py
│   ├── chatbot.py
│   ├── auth.py
│   ├── db.py
│   └── ...
├── UI_UX_Design/        ← Frontend HTML
│   ├── index.html       ← Customer chat
│   ├── store.html       ← Store Picker
│   └── driver.html      ← Driver
└── data/                ← Dữ liệu
    ├── ingredients.csv
    ├── recipes.csv
    └── recipe_ingredients.csv
```

---

## Phân công

| File / Phần | Người phụ trách |
|---|---|
| `app.py` — Backend Flask, AI integration, parse cart | Lê Trần Quốc Bảo (2A202600596) |
| `app/` — FastAPI module, MongoDB, auth | Lê Trần Quốc Bảo (2A202600596) |
| `UI_UX_Design/index.html` — Customer chat UI | Đặng Ngọc Bách (2A202600661) |
| `UI_UX_Design/store.html` + `driver.html` — Store & Driver UI | Đặng Ngọc Bách (2A202600661) |
| System prompt trong `app.py` → `get_system_prompt()` | Đỗ Văn Hùng (2A202600759) |
| `data/*.csv` — Kho nguyên liệu + công thức + mapping | Bùi Văn Thái (2A202600674) |
| Test cases, demo script, câu lệnh demo | Lê Hoàng Nam (2A202600965) |
| SPEC, slide, thuyết trình | Đặng Ngọc Bách (2A202600661) |

> ⚠️ Không commit file `.env` hoặc API key thật. Dùng `.env.example` thay thế.
