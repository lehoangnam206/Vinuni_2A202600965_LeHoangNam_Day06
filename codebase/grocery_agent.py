import os
import json
import random
from dotenv import load_dotenv
from openai import OpenAI

# Load API key từ file .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 1. KHO HÀNG GIẢ LẬP
INVENTORY = [
    {"name": "Thịt bò thăn", "price": 145000, "weight": "500g", "tag": "Chuẩn VietGAP"},
    {"name": "Thịt heo băm", "price": 60000, "weight": "400g", "tag": "Chuẩn VietGAP"},
    {"name": "Cà chua Đà Lạt", "price": 18000, "weight": "300g", "tag": "Organic"},
    {"name": "Hành lá, ngò rí", "price": 5000, "weight": "100g", "tag": "Rau gia vị"},
    {"name": "Tôm sú tươi", "price": 150000, "weight": "500g", "tag": "Hải sản"},
    {"name": "Mực ống tươi", "price": 120000, "weight": "500g", "tag": "Hải sản"},
    {"name": "Đậu hũ hộp", "price": 12000, "weight": "1 hộp", "tag": "Ăn chay"}
]

# 2. HỒ SƠ NGƯỜI DÙNG
USER_PROFILES = {
    "1": {"name": "Lan", "habit": "DỊ ỨNG TÔM CUA HẢI SẢN (TUYỆT ĐỐI KHÔNG CHỌN TÔM MỰC). Rất thích ăn hành lá."},
    "2": {"name": "Bách", "habit": "CỰC KỲ GHÉT HÀNH LÁ (TUYỆT ĐỐI KHÔNG CHỌN HÀNH LÁ). Thích ăn thịt bò."}
}

# 3. ĐỊNH NGHĨA TOOL (FUNCTION CALLING)
# Dạy cho AI biết cách "nhấn nút thanh toán" thông qua việc gọi hàm này
def checkout_cart(items):
    print("\n" + "="*50)
    print("🛒 [HỆ THỐNG] ĐÃ NHẬN LỆNH CHỐT GIỎ HÀNG TỪ AI:")
    total = 0
    for item in items:
        print(f"   - {item['name']} ({item['weight']}): {item['price']:,}đ")
        total += item['price']
    print(f"\n💰 TỔNG CỘNG: {total:,}đ")
    
    if total > 100000:
        print("❌ CẢNH BÁO: Đơn hàng vượt ngân sách 100k! Cần sửa lại giỏ hàng.")
        print("="*50 + "\n")
        return json.dumps({"status": "failed", "reason": "over_budget"})
    else:
        payment_code = f"MOMO-{random.randint(100000, 999999)}"
        print("\n✅ Ngân sách hợp lệ.")
        print("💳 THÔNG TIN THANH TOÁN:")
        print(f"   - Mã thanh toán (Giả lập): {payment_code}")
        print("   - Trạng thái đơn hàng: ĐANG NHẶT ĐỒ 📦 (Chuyển cho nhân viên Bách Hóa Xanh)")
        print("="*50 + "\n")
        return json.dumps({"status": "success", "payment_code": payment_code, "order_status": "packing"})

tools = [
    {
        "type": "function",
        "function": {
            "name": "checkout_cart",
            "description": "Gọi hàm này khi bạn đã chọn xong danh sách nguyên liệu và muốn chốt đơn / thanh toán.",
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "description": "Danh sách các món hàng đã chọn",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Tên món hàng"},
                                "weight": {"type": "string", "description": "Khối lượng"},
                                "price": {"type": "integer", "description": "Giá tiền"}
                            },
                            "required": ["name", "weight", "price"]
                        }
                    }
                },
                "required": ["items"]
            }
        }
    }
]

def main():
    print("🤖 CHÀO MỪNG ĐẾN VỚI CORE AI TRỢ LÝ ĐI CHỢ (AGENT CLI)")
    print("-----------------------------------------------------")
    print("Bạn muốn thử nghiệm kịch bản cho User nào?")
    print("1. Chị Lan (Dị ứng Hải sản, Thích ăn hành)")
    print("2. Anh Bách (Ghét hành, Thích thịt bò)")
    
    user_choice = input("👉 Lựa chọn của bạn (1/2): ")
    profile = USER_PROFILES.get(user_choice, USER_PROFILES["1"])
    
    print(f"\n✅ Đã load Profile: {profile['name']}")
    print(f"⚠️ Memory: {profile['habit']}\n")
    
    inventory_str = "\n".join([f"- {i['name']} ({i['weight']}): {i['price']}đ [{i['tag']}]" for i in INVENTORY])
    
    system_prompt = f"""
Bạn là Grocery AI Assistant, một trợ lý mua sắm thực phẩm thông minh của siêu thị Bách Hóa Xanh.

KHO HÀNG HIỆN TẠI (INVENTORY DATABASE):
{inventory_str}

THÔNG TIN KHÁCH HÀNG:
Tên: {profile['name']}
Thói quen: {profile['habit']}

CORE RESPONSIBILITIES & STRICT CONSTRAINTS:
1. Bạn CHỈ được phép tư vấn và chọn các sản phẩm ĐANG CÓ SẴN trong KHO HÀNG HIỆN TẠI ở trên.
2. TUYỆT ĐỐI KHÔNG tự tạo sản phẩm mới. KHÔNG tự đoán giá. Không giả định là khách có sẵn ở nhà.
3. Nếu khách hàng yêu cầu món KHÔNG CÓ TRONG KHO (ví dụ: cua, khế, rau đay...), bạn BẮT BUỘC phải từ chối khéo léo, thông báo siêu thị không bán món đó và đề xuất nguyên liệu thay thế CÓ SẴN.
4. Luôn tuân thủ tuyệt đối Thói quen mua sắm (dị ứng, sở thích) của khách hàng.
5. Ưu tiên các sản phẩm chuẩn VietGAP hoặc Organic nếu có thể.
6. Theo dõi sát ngân sách. Nếu vượt ngân sách, hãy cảnh báo và đưa ra phương án thay thế.
7. Giao tiếp ngắn gọn, thân thiện. Khi khách hàng đã CHỐT danh sách nguyên liệu, BẮT BUỘC phải gọi hàm `checkout_cart` để tính tiền.
"""

    messages = [{"role": "system", "content": system_prompt}]
    
    while True:
        user_input = input("👤 User (Gõ 'exit' để thoát): ")
        if user_input.lower() == 'exit':
            break
            
        messages.append({"role": "user", "content": user_input})
        
        print("⏳ AI đang xử lý...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        
        # Nếu AI quyết định gọi Tool (hàm checkout_cart)
        if response_message.tool_calls:
            tool_call = response_message.tool_calls[0]
            if tool_call.function.name == "checkout_cart":
                args = json.loads(tool_call.function.arguments)
                checkout_cart(args['items'])
                
                # Ghi nhận lại lịch sử là tool đã chạy thành công
                messages.append(response_message)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": "Checkout successful"
                })
                
                # Lấy thêm câu chào tạm biệt từ AI sau khi chốt đơn
                final_response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages
                )
                print(f"🤖 AI: {final_response.choices[0].message.content}\n")
                messages.append(final_response.choices[0].message)

        # Nếu AI chỉ trả lời bằng chữ thông thường (chưa chốt đơn)
        elif response_message.content:
            print(f"🤖 AI: {response_message.content}\n")
            messages.append({"role": "assistant", "content": response_message.content})

if __name__ == "__main__":
    main()
