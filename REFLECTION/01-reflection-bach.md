# Phản ánh cá nhân — Đặng Ngọc Bách

> **Họ tên:** Đặng Ngọc Bách  
> **MSV:** 2A202600661  
> **Vai trò:** Thuyết trình / Thiết kế giao diện & Luồng hoạt động  
> **Sản phẩm:** Grocery AI — Trợ lý đi chợ 1 chạm  
> **Ngày:** 04/06/2026 | AI Thực Chiến · Batch 02

---

## 1. Tôi đã làm gì hôm nay?

Hôm nay là ngày hackathon — ngày tôi không viết nhiều code nhất, nhưng lại là ngày phải đưa ra nhiều quyết định nhất.

**Phần tôi trực tiếp phụ trách:**

- **Thiết kế giao diện (UI/UX):** Phác thảo 3 màn hình từ đầu — Customer chat UI (`index.html`), Store Picker (`store.html`), Driver (`driver.html`). Đảm bảo UX mobile-first, người dùng không cần hướng dẫn vẫn dùng được.
- **Thiết kế luồng hoạt động (Flow):** Vẽ toàn bộ user journey từ "nhập nhu cầu nấu ăn" → "giỏ hàng" → "nhặt đồ" → "giao hàng" → "xác nhận". Quyết định tách 3 giao diện thay vì nhét chung 1 app.
- **Kịch bản demo & slide:** Viết script demo 5 phút, phân chia ai nói phần nào, chuẩn bị sẵn câu trả lời Q&A cho nhóm.
- **Thuyết trình:** Dẫn dắt toàn bộ 10 phút demo — 5 phút trình bày + điều phối 5 phút Q&A cho cả nhóm.
- **Phối hợp nhóm:** Kết nối output của Hùng (system prompt) với output của Bảo (backend logic) để đảm bảo AI trả đúng format mà giao diện tôi thiết kế có thể hiển thị.

---

## 2. Điều tôi học được từ hôm nay

### Về thiết kế sản phẩm AI

Khi thiết kế giao diện cho sản phẩm AI, tôi nhận ra **UX của sản phẩm AI khác hoàn toàn với app thông thường**.

Với app thông thường: người dùng click → hệ thống làm → xong.  
Với app AI: người dùng nói → AI *cố gắng* hiểu → người dùng *chưa chắc* tin → người dùng quyết định.

Vì vậy tôi thiết kế thêm:
- Nút **"Đồng ý chốt đơn"** — không để AI tự chốt, người dùng phải bấm xác nhận. Đây là human-in-the-loop trong UI.
- Hiển thị danh sách nguyên liệu rõ ràng trước khi chốt — để người dùng *nhìn thấy và tin* trước khi hành động.
- Tracking realtime — để sau khi chốt, người dùng không bị "mất kiểm soát".

### Về vai trò thuyết trình trong nhóm tech

Tôi học được rằng **người thuyết trình phải hiểu sản phẩm sâu hơn bất kỳ ai** — không phải để code, mà để trả lời câu hỏi của bất kỳ ai trong phòng. Tôi phải hỏi Bảo về logic backend, hỏi Hùng về tại sao prompt viết thế này, hỏi Nam về những lỗi đã thấy khi test.

Kết quả: khi Q&A, tôi trả lời được *"Tại sao không để AI tạo đơn luôn?"* mà không cần hỏi lại nhóm.

### Về thiết kế luồng trước khi code

Nhóm tôi quyết định vẽ flow trước, code sau — và đây là quyết định đúng. Khi Bảo code backend, anh ấy biết chính xác cần API nào, trả về format gì. Khi Hùng viết prompt, anh ấy biết AI cần output gì để giao diện hiển thị đúng.

**Flow rõ = ít phải sửa code sau.**

---

## 3. Điều khó nhất hôm nay

Khó nhất không phải phần kỹ thuật — mà là **giữ nhịp cho cả nhóm trong hackathon**.

Lúc 11:00 (Checkpoint 1), Bảo vẫn đang debug Flask, Thái chưa xong data CSV, giao diện của tôi chạy nhưng backend chưa kết nối. Lúc đó phải quyết định: tiếp tục debug hay mock data để demo checkpoint trước?

Tôi chọn mock data tạm cho checkpoint, nhóm tiếp tục fix song song. Đây là quyết định đúng — giữ được tiến độ mà không panic.

---

## 4. Điều tôi muốn làm khác đi

1. **Wireframe rõ hơn từ đầu** — tôi phác thảo trên giấy nhưng không share sớm với cả nhóm. Bảo phải hỏi lại tôi 2 lần về format response API.
2. **Test UX trên mobile thật** — tôi thiết kế mobile-first nhưng chỉ test trên Chrome DevTools. Hôm demo trên điện thoại thật font hơi nhỏ.
3. **Chuẩn bị backup** — nếu demo live bị lỗi network, nên có video backup 30 giây.

---

## 5. Suy nghĩ về AI trong sản phẩm thật

> Người dùng không tin AI ngay từ đầu — họ cần thấy AI *làm đúng* trước khi giao quyền quyết định cho AI.

Tôi thiết kế luồng sao cho người dùng luôn nhìn thấy và kiểm soát được kết quả AI trước khi hành động. Đây là **progressive trust** — xây dựng niềm tin từng bước.

Bản production tiếp theo, tôi muốn thêm tính năng: "AI giải thích lý do chọn nguyên liệu này" — để người dùng hiểu AI đang nghĩ gì, thay vì chỉ nhìn kết quả cuối.

---

## 6. Một câu tóm tắt ngày hôm nay

> Hôm nay tôi hiểu rằng sản phẩm AI tốt không phải là AI làm nhiều nhất — mà là UI giúp người dùng tin tưởng đủ để hành động.

---

*Đặng Ngọc Bách · MSV 2A202600661 · Batch 02 · Day 06 · 04/06/2026*
