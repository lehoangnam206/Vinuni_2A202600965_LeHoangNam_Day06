# Phản ánh cá nhân — Thái

> **Họ tên:** [Họ tên đầy đủ của Thái]  
> **MSV:** [MSV của Thái]  
> **Vai trò:** Database Designer / Data Engineer  
> **Sản phẩm:** Grocery AI — Trợ lý đi chợ 1 chạm  
> **Ngày:** 04/06/2026 | AI Thực Chiến · Batch 02

---

## 1. Tôi đã làm gì hôm nay?

Tôi phụ trách "nguồn dữ liệu sự thật" — nếu data sai, AI sẽ tư vấn sai, dù prompt có hay đến đâu.

**Phần tôi trực tiếp phụ trách:**

- **Thiết kế schema CSV:** Xây dựng 3 file data với schema rõ ràng, nhất quán:
  - `ingredients.csv` — kho nguyên liệu: ingredient_id, ingredient_name, category, package_qty, package_unit, price_vnd, available
  - `recipes.csv` — danh mục món ăn: recipe_id, recipe_name, meal_type, difficulty, base_servings, estimated_time_min, tags
  - `recipe_ingredients.csv` — mapping many-to-many: recipe_id, ingredient_id, ingredient_name, quantity_for_base_servings, quantity_unit, required_or_optional

- **Điền dữ liệu thực tế:** Research giá nguyên liệu thị trường VN (2025–2026), nhập ~40 nguyên liệu + 50 công thức món ăn phổ biến (bữa trưa, bữa tối, chay, mặn, healthy...).

- **Phân loại danh mục:** Tách gia vị khỏi nguyên liệu thông thường — quan trọng vì Hùng cần biết item nào không được tính tiền. Category `gia vị` = không bán, chỉ nhắc người dùng tự chuẩn bị.

- **Đảm bảo data chính xác:** Kiểm tra không có ID trùng, không có giá 0, trạng thái `available` đúng thực tế, đơn vị tính nhất quán (g, ml, củ, khay...).

- **Thêm trường `required_or_optional`** trong recipe_ingredients — giúp AI biết nguyên liệu nào bắt buộc, nguyên liệu nào có thể bỏ qua nếu thiếu tiền/dị ứng.

---

## 2. Điều tôi học được từ hôm nay

### Về vai trò Data trong sản phẩm AI

Trước hôm nay tôi nghĩ data chỉ là "điền bảng cho xong". Sau hôm nay tôi hiểu: **data là context của AI — data tốt mới có AI tốt**.

Khi tôi điền đúng category `gia vị` cho muối, mắm, dầu ăn → Hùng viết prompt lọc ra → AI không tính tiền gia vị. Nếu tôi phân loại sai, toàn bộ chuỗi logic này vỡ.

Đây là **data contract giữa DB và AI** — tôi phải hiểu AI sẽ dùng data này như thế nào để thiết kế schema phù hợp.

### Về thiết kế schema cho AI consumption

Schema cho AI khác schema cho app thông thường:

| App thông thường | AI-consumed schema |
|---|---|
| Normalize tối đa, nhiều bảng | Denormalize một phần để giảm join |
| ID quan trọng nhất | Human-readable name quan trọng hơn |
| FK constraints chặt | AI cần text tự nhiên, không cần FK |
| Số lượng tối thiểu | Verbose hơn để AI có context |

Ví dụ: tôi giữ cột `ingredient_name` trong `recipe_ingredients` dù đã có `ingredient_id` — vì khi inject vào prompt, AI đọc tên, không đọc ID.

### Về data quality và AI hallucination

Tôi nhận ra một điều thú vị: **data chất lượng giảm hallucination**. Khi kho hàng có đầy đủ tên, đơn vị, giá rõ ràng → AI có thể trích dẫn chính xác thay vì đoán. Khi data thiếu hoặc mơ hồ → AI "tự sáng tác" để điền vào chỗ trống.

---

## 3. Điều khó nhất hôm nay

**Research giá thực tế và đảm bảo data nhất quán.**

Tôi phải đảm bảo:
- Giá tiền hợp lý với thị trường VN (không quá rẻ như 5k/khay thịt, không quá đắt)
- Package size thực tế (thịt bò khay 300g, rau muống bó 200g...)
- 50 công thức đa dạng đủ bữa sáng, trưa, tối, chay, mặn, healthy

Phần mất nhiều thời gian nhất: đảm bảo ingredient_id trong `recipe_ingredients` khớp đúng với `ingredients.csv`. Tôi lỡ viết `I001` ở chỗ này nhưng `ING001` ở chỗ kia — gây lỗi khi Bảo đọc data. Phải ngồi validate lại toàn bộ.

**Bài học:** Data validation là bước không thể bỏ qua, dù đang hack nhanh.

---

## 4. Điều tôi muốn làm khác đi

1. **Dùng database thật (SQLite hoặc MongoDB)** thay vì CSV — query linh hoạt hơn, không bị lỗi encoding, dễ update runtime.
2. **Thêm script validation** — script Python kiểm tra tự động: không có ID trùng, tất cả ingredient_id trong recipe_ingredients tồn tại trong ingredients, không có giá 0.
3. **Thêm trường dinh dưỡng** — calories, protein, carbs — để AI có thể gợi ý theo nhu cầu dinh dưỡng, không chỉ theo khẩu vị.
4. **Version data** — mỗi lần cập nhật kho hàng, lưu lại phiên bản cũ để rollback nếu AI behavior thay đổi bất ngờ.

---

## 5. Suy nghĩ về AI trong sản phẩm thật

> AI giỏi đến đâu cũng không compensate được data xấu — GIGO (Garbage In, Garbage Out) vẫn đúng trong thời đại AI.

Tôi bắt đầu nghĩ đến bước tiếp theo: thay vì CSV tĩnh, kho hàng nên là database thật kết nối với inventory system của siêu thị — real-time stock, real-time pricing. Khi đó AI sẽ không bao giờ gợi ý hàng đã hết, và giá luôn đúng.

---

## 6. Một câu tóm tắt ngày hôm nay

> Hôm nay tôi học được rằng người làm data không chỉ điền bảng — mà đang đặt nền móng cho toàn bộ hệ thống AI phía trên.

---

*[Tên Thái] · MSV [MSV] · Batch 02 · Day 06 · 04/06/2026*
