import os
import json
import csv
import random
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI

# Load API key từ file .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__, static_folder='UI_UX_Design')
CORS(app) # Cho phép index.html gọi API localhost

@app.route('/')
def serve_index():
    return send_from_directory('UI_UX_Design', 'index.html')

# --- Tích hợp Dữ liệu CSV ---
def load_inventory():
    inventory = []
    filepath = os.path.join(os.path.dirname(__file__), 'data', 'ingredients.csv')
    with open(filepath, encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            inventory.append({
                "id": row['ingredient_id'],
                "name": row['ingredient_name'],
                "price": int(row['price_vnd']),
                "available": row['available'].lower() == 'yes',
                "unit": row['package_unit'],
                "qty": int(row['package_qty'])
            })
    return inventory

INVENTORY = load_inventory()

def get_inventory_context():
    lines = ["KHO HÀNG (INVENTORY):"]
    for item in INVENTORY:
        status = "Còn hàng" if item['available'] else "HẾT HÀNG"
        lines.append(f"- [{item['id']}] {item['name']} ({item['qty']} {item['unit']}): {item['price']}đ - {status}")
    return "\n".join(lines)

def get_recipes_context():
    recipes = {}
    with open(os.path.join(os.path.dirname(__file__), 'data', 'recipes.csv'), encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            recipes[row['recipe_id']] = {
                "name": row['recipe_name'],
                "servings": row['base_servings'],
                "time": row['estimated_time_min'],
                "tags": row['tags'],
                "ingredients": []
            }
            
    with open(os.path.join(os.path.dirname(__file__), 'data', 'recipe_ingredients.csv'), encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            rid = row['recipe_id']
            if rid in recipes:
                recipes[rid]['ingredients'].append({
                    "id": row['ingredient_id'],
                    "name": row['ingredient_name'],
                    "qty": row['quantity_for_base_servings'],
                    "unit": row['quantity_unit'],
                    "req": row['required_or_optional']
                })
                
    lines = ["CÁC CÔNG THỨC NẤU ĂN (RECIPES):"]
    for rid, r in recipes.items():
        lines.append(f"\n{rid} - {r['name']} ({r['servings']} người, {r['time']} phút). Đặc điểm: {r['tags']}")
        lines.append("  Nguyên liệu:")
        for ing in r['ingredients']:
            lines.append(f"  - {ing['name']} ({ing['id']}) - {ing['qty']} {ing['unit']} ({ing['req']})")
    
    return "\n".join(lines)

# 2. HỒ SƠ NGƯỜI DÙNG
PROFILES = {
    "lan": {"name": "Lan", "allergies": ["tôm", "cua", "hải sản"], "preferences": ["hành lá"]},
    "bach": {"name": "Bách", "allergies": ["hành lá"], "preferences": ["thịt bò"]}
}

# 3. ĐỊNH NGHĨA TOOL (FUNCTION CALLING)
def execute_checkout_cart(items):
    total = 0
    receipt = []
    
    for req_item in items:
        matched_item = next((i for i in INVENTORY if i['name'].lower() == req_item['name'].lower()), None)
        if matched_item:
            qty = int(req_item.get('quantity', 1))
            price = matched_item['price'] * qty
            total += price
            receipt.append({
                "name": matched_item['name'],
                "quantity": qty,
                "unit": f"gói ({matched_item['qty']} {matched_item['unit']})",
                "price": price,
                "unit_price": matched_item['price']
            })
            
    payment_code = f"MOMO-{random.randint(100000, 999999)}"
    return {
        "status": "success",
        "payment_code": payment_code,
        "order_status": "packing",
        "total_price": total,
        "items": receipt
    }

tools = [
    {
        "type": "function",
        "function": {
            "name": "checkout_cart",
            "description": "Hàm thanh toán. CHỈ GỌI KHI NGƯỜI DÙNG NÓI 'Đồng ý', 'Chốt', 'Thanh toán'. NẾU CHƯA XÁC NHẬN THÌ TUYỆT ĐỐI KHÔNG ĐƯỢC GỌI.",
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "description": "Danh sách các món hàng",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "quantity": {"type": "integer", "description": "Số lượng gói/phần"}
                            },
                            "required": ["name", "quantity"]
                        }
                    }
                },
                "required": ["items"]
            }
        }
    }
]

def get_system_prompt(profile_key):
    profile = PROFILES.get(profile_key, PROFILES['lan'])
    inventory_str = get_inventory_context()
    recipes_str = get_recipes_context()
    
    system_prompt = f"""
Vai trò (Role):
Bạn là một trợ lý AI thông minh chuyên hỗ trợ đặt mua nguyên liệu nấu ăn của siêu thị Bách Hóa Xanh. Mục tiêu của bạn là gợi ý chính xác các nguyên liệu cần thiết dựa trên yêu cầu của người dùng, giới hạn ngân sách và số lượng người ăn.

{inventory_str}

{recipes_str}

HỒ SƠ KHÁCH HÀNG (USER PROFILE):
- Dị ứng/Không thích: {', '.join(profile['allergies'])}
- Sở thích: {', '.join(profile['preferences'])}

GIỚI HẠN DỮ LIỆU (Constraints - Rất quan trọng):
1. CHỈ ĐƯỢC PHÉP gợi ý các mặt hàng/nguyên liệu có sẵn trong KHO HÀNG ở trên.
2. Tuyệt đối KHÔNG tự bịa ra nguyên liệu, không tự đoán giá hoặc gợi ý các mặt hàng đã hết/không có sẵn.
3. Luôn tuân thủ tuyệt đối Dị ứng và Sở thích của khách hàng.
4. Hiểu các từ lóng tiền tệ: "1 củ" = 1,000,000đ, "1 lít" = 100,000đ.
5. Chỉ trả lời gọn gàng trong 1 tin nhắn duy nhất cho mỗi lần gợi ý.
6. [QUAN TRỌNG]: Ở Bước 2 (Khi đang gợi ý), TUYỆT ĐỐI KHÔNG ĐƯỢC GỌI HÀM `checkout_cart`. Bạn phải CHỜ người dùng phản hồi xác nhận "Đồng ý" hoặc "Chốt" thì mới được gọi hàm này.

QUY TRÌNH HOẠT ĐỘNG (Workflow):
Bước 1: Tiếp nhận yêu cầu (Input)
- Chờ người dùng cung cấp đủ 3 thông tin: [Số tiền/Ngân sách], [Tên món ăn hoặc Yêu cầu món], và [Số người ăn].
- Nếu thiếu bất kỳ thông tin nào, hãy lịch sự hỏi lại để người dùng bổ sung trước khi gợi ý.

Bước 2: Phân tích và Gợi ý (Suggest)
- Dựa trên KHO HÀNG có sẵn và CÁC CÔNG THỨC, đối chiếu với 3 thông tin ở Bước 1 để lên danh sách nguyên liệu phù hợp (đảm bảo không vượt ngân sách).
- Xuất ra 1 câu trả lời duy nhất chứa: Danh sách nguyên liệu (Bắt buộc ghi kèm đơn giá của từng nguyên liệu), Số lượng, Tổng tiền dự kiến. (Khi bạn nhắc đến giá tiền, Frontend sẽ tự động kích hoạt hiển thị nút [Đồng ý chốt đơn] trên UI).

Bước 3: Xử lý phản hồi của người dùng (Feedback/Action)
- Trường hợp 3.1 - Người dùng nói ĐỒNG Ý / CHỐT ĐƠN: Lập tức gọi hàm `checkout_cart` để chuyển hướng người dùng sang Giao diện Thanh toán.
- Trường hợp 3.2 - Người dùng không đồng ý mà tiếp tục yêu cầu đổi nguyên liệu, thêm/bớt đồ...: Tiếp nhận yêu cầu mới, tính toán lại dựa trên kho hàng có sẵn. Đưa ra danh sách gợi ý mới (quay lại Bước 2) cho đến khi người dùng hoàn toàn ưng ý và chốt đơn.
"""
    return system_prompt

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    profile_key = data.get('profile', 'lan')
    history = data.get('history', [])
    
    # Chuẩn bị messages cho OpenAI
    messages = [{"role": "system", "content": get_system_prompt(profile_key)}]
    
    # Lọc bỏ các tool_call messages cũ từ Frontend gửi lên để tránh lỗi cấu trúc, chỉ lấy text
    clean_history = []
    for msg in history:
        if msg.get('role') in ['user', 'assistant'] and msg.get('content'):
            clean_history.append({"role": msg['role'], "content": msg['content']})
            
    messages.extend(clean_history)
    
    try:
        # Kiểm tra tin nhắn cuối cùng của User xem có từ khóa chốt đơn không
        last_user_msg = next((msg['content'].lower() for msg in reversed(clean_history) if msg.get('role') == 'user'), "")
        checkout_keywords = ["đồng ý", "chốt", "thanh toán", "ok", "mua", "duyệt", "tiến hành"]
        is_checkout = any(kw in last_user_msg for kw in checkout_keywords)
        
        # Nếu user chưa có ý định chốt đơn -> KHÔNG cung cấp tool cho AI để tránh lỗi AI tự chốt
        if is_checkout:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
        else:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            
        response_message = response.choices[0].message
        
        # Kiểm tra xem AI có gọi hàm checkout không
        if response_message.tool_calls:
            # Gửi kết quả tool về cho AI để nó sinh câu chào tạm biệt
            messages.append(response_message)
            checkout_result = None
            
            for tool_call in response_message.tool_calls:
                if tool_call.function.name == "checkout_cart":
                    args = json.loads(tool_call.function.arguments)
                    checkout_result = execute_checkout_cart(args['items'])
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": json.dumps(checkout_result, ensure_ascii=False)
                    })
                else:
                    # Dummy response for unknown tools to prevent 400 errors
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": "{}"
                    })
                
            final_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            
            # Trả về cả tin nhắn text và dữ liệu giỏ hàng để Frontend vẽ màn hình 2
            return jsonify({
                "reply": final_response.choices[0].message.content,
                "cart": checkout_result
            })
                
        # Nếu chỉ chat bình thường
        return jsonify({
            "reply": response_message.content,
            "cart": None
        })
        
    except Exception as e:
        print("API Error:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5051, debug=True)
