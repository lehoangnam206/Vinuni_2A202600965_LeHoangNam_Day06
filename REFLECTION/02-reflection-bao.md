# Phản ánh cá nhân — Bảo

> **Họ tên:** Lê Trần Quốc Bảo 
> **MSV:** 2A202600596  
> **Vai trò:** Logic AI Integration / Backend Website  
> **Sản phẩm:** Grocery AI — Trợ lý đi chợ 1 chạm  
> **Ngày:** 04/06/2026 | AI Thực Chiến · Batch 02

---

## 1. Tôi đã làm gì hôm nay?

Tôi phụ trách phần "ruột" của sản phẩm — backend Flask và toàn bộ logic tích hợp AI vào hệ thống.

**Phần tôi trực tiếp phụ trách:**

- **Backend Flask (`app.py`):** Xây dựng toàn bộ server từ đầu — khởi tạo app, cấu hình CORS, đăng ký routes, xử lý request/response.
- **Tích hợp OpenAI API:** Kết nối `openai.chat.completions.create()` với model `gpt-3.5-turbo`, truyền system prompt từ Hùng + lịch sử chat từ frontend vào mỗi request.
- **Logic phát hiện chốt đơn (keyword detection):** Viết logic kiểm tra tin nhắn cuối của user có chứa từ khóa `đồng ý`, `chốt`, `mua`... để quyết định có gọi AI hay xử lý checkout ngay.
- **Parse giỏ hàng (deterministic):** Nhận output text từ AI, dùng `parse_cart_from_text()` để extract tên món, định lượng, giá tiền bằng regex — tuyệt đối không để AI tự tạo đơn.
- **API quản lý đơn hàng:** Xây dựng 5 endpoints: `GET /api/order/{id}`, `GET/POST /api/store/orders`, `GET/POST /api/driver/orders`.
- **Load dữ liệu CSV:** Viết `load_inventory()` và `get_recipes_context()` để đọc 3 file CSV và format thành context string truyền vào system prompt.

---

## 2. Điều tôi học được từ hôm nay

### Về tích hợp AI vào hệ thống thật

Điều lớn nhất tôi học được: **AI là một "service" không đáng tin tuyệt đối — phải design cho trường hợp AI trả lời sai**.

Khi tôi viết `parse_cart_from_text()`, tôi phải đối mặt với thực tế: AI đôi khi trả lời đúng nội dung nhưng sai format. Regex phải xử lý ít nhất 4 pattern khác nhau:
```
"1. Thịt bò - 1 khay - 85.000đ"
"+ Hành tây (1 củ): 15k"
"- Cà rốt — 12.000 VNĐ"
```

Điều này dạy tôi: **khi output của AI là input cho một hệ thống khác, bạn phải viết defensive code ở tầng nhận**.

### Về kiến trúc "AI tư vấn, Logic tạo đơn"

Ban đầu tôi định để AI tự tạo giỏ hàng dạng JSON. Nhưng sau khi thử nghiệm, AI đôi khi bịa giá hoặc thêm sản phẩm không có trong kho. 

Quyết định tách ra: AI chỉ trả lời text, Python parse và validate = **deterministic + auditable**. Đây là kiến trúc đúng cho prototype — có thể trace bug ngay trong code thay vì phải debug AI.

### Về Flask và REST API design

Hôm nay tôi viết API theo chuẩn RESTful lần đầu trong bối cảnh production-like: GET để lấy dữ liệu, POST để thay đổi trạng thái. Polling từ frontend mỗi 2 giây để update tracking — đơn giản nhưng hiệu quả cho demo.

---

## 3. Điều khó nhất hôm nay

**Đồng bộ format output giữa AI (Hùng viết prompt) và logic parse (tôi viết regex).**

Khi Hùng thay đổi format trong system prompt, regex của tôi bị lỗi. Ngược lại, khi tôi cần thêm một field mới trong giỏ hàng, Hùng phải cập nhật prompt để AI báo đúng thông tin đó.

Giải pháp chúng tôi đồng ý: **viết một "output contract" — tài liệu mô tả chính xác format AI phải trả về**, cả hai bên code theo đó. Đơn giản nhưng rất hiệu quả.

---

## 4. Điều tôi muốn làm khác đi

1. **Dùng JSON structured output ngay từ đầu** — `response_format={"type":"json_object"}` sẽ loại bỏ toàn bộ vấn đề regex parse. Tôi chọn text parsing vì nghĩ nhanh hơn, nhưng thực ra tốn nhiều giờ debug hơn.
2. **Thêm logging cho mỗi AI request** — lưu input/output vào file log để debug dễ hơn. Lần sau sẽ setup từ đầu.
3. **Unit test cho `parse_cart_from_text()`** — hàm này quan trọng nhất mà tôi viết xong không test đủ case. Nam phát hiện 2 lỗi khi test integration.

---

## 5. Suy nghĩ về AI trong sản phẩm thật

> Tích hợp AI không khó ở chỗ gọi API — khó ở chỗ xử lý những gì AI trả về.

Tôi có thể gọi `openai.chat.completions.create()` trong 5 dòng code. Nhưng để hệ thống không bị crash, không tạo đơn sai, không expose lỗi cho user khi AI hallucinate — đó mới là phần tốn thời gian thật sự.

Bản production sẽ cần: retry logic, rate limit handling, fallback khi API down, validate output trước khi đưa vào DB.

---

## 6. Một câu tóm tắt ngày hôm nay

> Hôm nay tôi học được rằng tích hợp AI tốt không phải là để AI làm nhiều — mà là biết chính xác AI nên làm gì và không nên làm gì.

---

*[Tên Bảo] · MSV [MSV] · Batch 02 · Day 06 · 04/06/2026*
