# Phản ánh cá nhân — Hùng

> **Họ tên:** Đỗ Văn  Hùng  
> **MSV:** 2A202600759  
> **Vai trò:** Prompt Engineer / System Prompt Designer  
> **Sản phẩm:** Grocery AI — Trợ lý đi chợ 1 chạm  
> **Ngày:** 04/06/2026 | AI Thực Chiến · Batch 02

---

## 1. Tôi đã làm gì hôm nay?

Tôi phụ trách phần "não" của sản phẩm — system prompt quyết định cách AI hiểu yêu cầu, tuân thủ ràng buộc, và trả lời đúng format.

**Phần tôi trực tiếp phụ trách:**

- **System prompt (`get_system_prompt()`):** Thiết kế và tối ưu toàn bộ system prompt ~80 dòng, gồm 4 phần chính: vai trò AI, kho hàng (inject từ CSV), công thức món ăn (inject từ CSV), và profile người dùng (dị ứng, sở thích).
- **Ràng buộc (Guardrails):** Viết 6 ràng buộc cứng để AI không hallucinate — không bán gia vị, không chia nhỏ gói hàng, không đề xuất nguyên liệu người dùng dị ứng, chỉ bán hàng trong kho.
- **Format output:** Định nghĩa chính xác format AI phải trả về để Bảo viết regex parse được. Thử nghiệm và điều chỉnh qua nhiều iteration cho đến khi parse success rate > 95%.
- **Profile injection:** Thiết kế cơ chế inject profile Lan/Bách vào prompt — dị ứng được viết in hoa và đặt ở vị trí nổi bật để AI không bỏ qua.
- **Quy trình 3 bước (Workflow):** Thiết kế workflow rõ ràng trong prompt — Bước 1 tiếp nhận, Bước 2 gợi ý (không được gọi checkout), Bước 3 xử lý feedback — để AI không bị confuse giữa các bước.

---

## 2. Điều tôi học được từ hôm nay

### Về Prompt Engineering thực chiến

Trước hackathon tôi nghĩ prompt engineering là viết câu lệnh hay cho AI. Sau hôm nay tôi hiểu đây là **một dạng lập trình — với ngôn ngữ là tiếng tự nhiên**.

Bài học cụ thể:

**1. Thứ tự thông tin trong prompt quan trọng hơn nội dung**

Tôi thử nghiệm 3 version:
- Version 1: Đặt dị ứng ở cuối prompt → AI đôi khi bỏ qua khi context dài
- Version 2: Đặt dị ứng ở đầu → tốt hơn nhưng AI vẫn fail với Lan và tôm
- Version 3: Viết dị ứng in hoa + nhắc lại 2 lần trong prompt → AI tuân thủ 100% trong các test

**2. Ví dụ cụ thể > Mô tả trừu tượng**

```
❌ "Liệt kê nguyên liệu theo format chuẩn"
✅ "Ví dụ: 1. Thịt bò (Khay 300g) - 1 khay - 85.000đ"
```

Với ví dụ cụ thể, AI tuân format đúng ngay từ lần đầu. Không có ví dụ, phải thử 5–6 lần.

**3. Ranh giới rõ ràng giữa các bước**

Khi tôi viết "Bước 2: TUYỆT ĐỐI KHÔNG GỌI hàm checkout", AI dừng đề xuất checkout ở giữa chừng. Trước khi có ràng buộc này, AI đôi khi tự chốt đơn trong câu gợi ý.

### Về context window và token budget

Khi inject toàn bộ kho hàng (~40 items) + công thức (~50 recipes) vào prompt, mỗi request tiêu thụ ~2000 token chỉ riêng system prompt. Tôi học được cần cân bằng giữa **thông tin đầy đủ cho AI** và **chi phí token**.

---

## 3. Điều khó nhất hôm nay

**Ép AI tuân đúng format mà không làm AI "cứng đờ" trong hội thoại.**

Nếu ràng buộc quá cứng, AI trả lời máy móc, không tự nhiên. Nếu quá lỏng, AI viết văn xuôi, regex của Bảo không parse được.

Giải pháp tôi tìm ra: **ràng buộc format chỉ áp dụng ở Bước 2 (gợi ý), không áp dụng ở Bước 1 (hỏi thêm) và Bước 3 (xác nhận)**. AI được phép linh hoạt trong hội thoại, nhưng khi đến phần liệt kê nguyên liệu thì phải đúng format.

---

## 4. Điều tôi muốn làm khác đi

1. **Dùng function calling thay vì prompt format** — `tools` parameter của OpenAI cho phép AI trả JSON có schema cố định, không cần ép format bằng text. Sẽ robust hơn nhiều.
2. **A/B test prompt** — tôi thay đổi prompt theo cảm tính. Bản production cần test có hệ thống: đo parse success rate, user satisfaction rate.
3. **Versioning prompt** — mỗi lần sửa prompt tôi ghi đè. Nên lưu lịch sử các version để rollback khi có regression.

---

## 5. Suy nghĩ về AI trong sản phẩm thật

> System prompt là hợp đồng giữa sản phẩm và AI — càng chi tiết, càng ít bất ngờ.

Nhưng hợp đồng không bao giờ bao quát hết mọi tình huống. Người dùng thật sẽ nhập những câu không ai nghĩ đến. Vì vậy guardrails tốt nhất là kết hợp: **prompt cứng ở tầng AI + validate logic ở tầng code + human review ở tầng sản phẩm**.

---

## 6. Một câu tóm tắt ngày hôm nay

> Hôm nay tôi học được rằng viết prompt tốt không phải là viết dài — mà là viết đúng chỗ, đúng thứ tự, và có ví dụ cụ thể.

---

*Đỗ Văn Hùng · MSV 2A202600759 · Batch 02 · Day 06 · 04/06/2026*
