# SPEC Sản Phẩm — Grocery AI: Trợ lý đi chợ 1 chạm

> Track: **Food & Local Delivery**  
> App tham chiếu: Bách Hóa Xanh, ShopeeFood, GrabFood  
> Ngày: 04/06/2026 · Batch 02 · Day 06

---

## 1. Bằng chứng

### Trải nghiệm trực tiếp

Nhóm thử nghiệm app Bách Hóa Xanh và ghi nhận:

- Phải biết chính xác tên sản phẩm mới tìm được — "thịt bò" ra hàng trăm kết quả, lọc tay từng món.
- Không có tính năng gợi ý "mua theo bữa ăn" — phải tự nhớ và thêm từng nguyên liệu riêng.
- Không có bộ lọc dị ứng/kiêng cữ theo profile cá nhân — tự kiểm tra nhãn từng sản phẩm.
- Khó kiểm soát ngân sách khi chọn nhiều sản phẩm riêng lẻ.

### Nguồn bên ngoài

- **App Store reviews (Bách Hóa Xanh):** Nhiều đánh giá phản ánh "tìm mãi không ra sản phẩm", "không biết mua gì cho bữa cơm hôm nay".
- **Sản phẩm tham chiếu quốc tế:** Instacart (Mỹ) đã tích hợp "Ask Instacart" — nhập câu tự nhiên → tự thêm nguyên liệu vào giỏ. Chứng minh hướng này có nhu cầu thật và kỹ thuật khả thi.

---

## 2. Lát cắt để build

> Một người dùng (có profile dị ứng/sở thích) nhập nhu cầu nấu ăn bằng tiếng Việt tự nhiên → AI đọc kho hàng thật và công thức món ăn → trả về danh sách nguyên liệu cụ thể kèm giá → người dùng xác nhận → hệ thống giao cho nhân viên siêu thị và tài xế.

---

## 3. AI Product Canvas

### Value — Giá trị

| | |
|---|---|
| **Dành cho ai** | Người nội trợ, sinh viên, người bận rộn muốn nấu ăn tại nhà |
| **Điểm đau** | Search thủ công từng nguyên liệu, không kiểm soát dị ứng/ngân sách |
| **AI giải được gì** | Nhận câu tự nhiên → ánh xạ kho hàng thật → tính tiền → tạo giỏ 1 chạm |

### Trust — Niềm tin

| Tình huống | Cách xử lý |
|---|---|
| AI gợi ý sai | Người dùng xem danh sách trước khi chốt — chat lại để thay đổi |
| AI gợi ý món dị ứng | System prompt ràng buộc cứng: dị ứng inject thẳng vào prompt |
| Giỏ hàng sai giá | Giá lấy từ CSV (nguồn thật) — deterministic, không để AI tự tính |

### Feasibility — Tính khả thi

| Yếu tố | Đánh giá |
|---|---|
| Chi phí/lượt | ~0.001–0.004 USD với gpt-3.5-turbo |
| Độ trễ | 1–3 giây — chấp nhận được |
| Dữ liệu cần | CSV kho hàng + CSV công thức — đã có |
| Rủi ro lớn nhất | AI không tuân format → parse_cart fail → giỏ rỗng |

### Tín hiệu học

- User yêu cầu thay thế nguyên liệu → ghi nhận preference pattern
- Giỏ hàng rỗng sau checkout → signal parse thất bại, cần cải thiện format prompt
- User hỏi món ngoài kho → signal bổ sung inventory

---

## 4. Augment hay Automate?

**Lựa chọn: Augment (Tăng năng lực)**

- AI gợi ý → **người dùng quyết định** có chốt hay không (human-in-the-loop)
- Tạo đơn: **hoàn toàn deterministic** — Python regex parse, không để AI tự tạo đơn
- Vận hành (nhân viên nhặt, tài xế giao): con người thực hiện, hệ thống điều phối

**Lý do:** Tạo đơn sai giá = người dùng bị tính tiền nhầm = mất tin tưởng, rủi ro pháp lý.

---

## 5. Bốn đường đi trải nghiệm

| Đường đi | Tình huống | Cách xử lý |
|---|---|---|
| **Thuận** | AI gợi ý đúng, user bấm chốt | Giỏ hàng tạo, mã MOMO xuất hiện, tracking realtime |
| **AI không chắc** | User nhập thiếu số người hoặc tên món | AI hỏi lại: "Bạn muốn nấu cho mấy người?" |
| **AI sai** | User không đồng ý với gợi ý | User chat lại yêu cầu thay đổi — AI tính toán lại |
| **User sửa** | User xóa 1 món trong giỏ | UI cho phép xóa từng item — tổng tiền cập nhật |

---

## 6. Lỗi đáng lo nhất

### Lỗi 1 — AI không tuân format output
- **Khi nào:** AI trả lời văn xuôi thay vì danh sách có format
- **Hậu quả:** Giỏ hàng rỗng — user không biết đã đặt được chưa
- **Xử lý:** System prompt ép format nghiêm + regex parse với nhiều pattern fallback

### Lỗi 2 — AI đề xuất sản phẩm dị ứng
- **Khi nào:** AI bỏ qua profile khi context dài
- **Hậu quả:** Người dùng dị ứng (Lan) nhận gợi ý tôm/hải sản → nguy hiểm
- **Xử lý:** Dị ứng viết IN HOA, đặt ở đầu system prompt, nhắc lại 2 lần

### Lỗi 3 — AI bịa sản phẩm ngoài kho
- **Khi nào:** AI hallucinate tên hoặc giá không có trong CSV
- **Hậu quả:** Đơn hàng chứa sản phẩm không tồn tại
- **Xử lý:** Prompt nhấn mạnh "CHỈ BÁN CÁC NGUYÊN LIỆU TRONG KHO" + liệt kê toàn bộ kho

---

## 7. Kế hoạch kiểm thử

### Happy path
```
Persona: Lan
Input: "Tối nay nấu bò xào hành tây cho 2 người, ngân sách 150k"
Kỳ vọng: Gợi ý bò xào không hải sản, tổng ≤ 150k, chốt đơn thành công
```

### Edge case
```
Persona: Lan
Input: "Tôi muốn ăn tôm rang muối cho 2 người"
Kỳ vọng: AI từ chối tôm, gợi ý thay thế không hải sản

Persona: Bách
Input: "Nấu gì đó cho 3 người, 80k"
Kỳ vọng: Không có hành lá, tổng ≤ 80k
```

---

## 8. Phân công

| Thành viên | MSV | Phần phụ trách |
|---|---|---|
| **Đặng Ngọc Bách** | 2A202600661 | Thiết kế UI/UX, luồng hoạt động, thuyết trình, SPEC, slide |
| **Lê Trần Quốc Bảo** | 2A202600596 | Backend Flask, tích hợp OpenAI API, parse_cart logic, API routes |
| **Đỗ Văn Hùng** | 2A202600759 | System prompt, guardrails, format output contract |
| **Bùi Văn Thái** | 2A202600674 | Thiết kế schema CSV, điền dữ liệu nguyên liệu + công thức |
| **Lê Hoàng Nam** | 2A202600965 | Test cases, adversarial testing, demo script, câu lệnh demo |
