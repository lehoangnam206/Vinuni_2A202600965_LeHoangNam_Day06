CHAT_HTML = """
<!doctype html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Grocery AI</title>
  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      background: #e9ecef;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    .mobile-frame {
      width: 375px;
      height: 812px;
      background: #f8f9fa;
      border-radius: 40px;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
      border: 12px solid #212529;
      position: relative;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }

    .header {
      background: #00a046;
      color: white;
      padding: 40px 20px 20px;
      text-align: center;
      font-weight: 700;
      font-size: 18px;
    }

    .screen {
      display: none;
      flex: 1;
      flex-direction: column;
      overflow-y: auto;
      min-height: 0;
    }

    .screen.active {
      display: flex;
    }

    .profile-strip {
      padding: 10px 15px;
      background: #e8f5e9;
      font-size: 14px;
      border-bottom: 1px solid #c8e6c9;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }

    .profile-strip b {
      color: #212529;
      white-space: nowrap;
    }

    .profile-pill {
      min-width: 0;
      padding: 5px 9px;
      border-radius: 5px;
      outline: none;
      border: 1px solid #00a046;
      background: white;
      color: #212529;
      font-size: 13px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .chat-container {
      flex: 1;
      padding: 15px;
      display: flex;
      flex-direction: column;
      gap: 15px;
      overflow-y: auto;
    }

    .msg {
      padding: 12px 16px;
      border-radius: 20px;
      max-width: 82%;
      line-height: 1.4;
      font-size: 15px;
      overflow-wrap: anywhere;
    }

    .msg.bot {
      background: white;
      align-self: flex-start;
      border-bottom-left-radius: 4px;
      border: 1px solid #e9ecef;
    }

    .msg.user {
      background: #00a046;
      color: white;
      align-self: flex-end;
      border-bottom-right-radius: 4px;
    }

    .msg.with-list {
      max-width: 88%;
    }

    .inline-cart {
      margin-top: 14px;
      padding-top: 12px;
      border-top: 1px solid #e9ecef;
    }

    .inline-cart.loading {
      opacity: 0.72;
      pointer-events: none;
    }

    .inline-cart-title {
      font-size: 14px;
      color: #212529;
      font-weight: 700;
      margin-bottom: 10px;
    }

    .inline-cart-item {
      display: grid;
      grid-template-columns: 24px 1fr auto;
      gap: 9px;
      align-items: center;
      padding: 10px 0;
      border-bottom: 1px solid #f1f3f5;
    }

    .inline-cart-item:last-of-type {
      border-bottom: 0;
    }

    .inline-cart-item input {
      width: 18px;
      height: 18px;
      accent-color: #00a046;
    }

    .inline-item-main {
      min-width: 0;
    }

    .inline-item-main h4 {
      font-size: 14px;
      color: #212529;
      line-height: 1.3;
      margin-bottom: 3px;
    }

    .inline-item-main p {
      font-size: 13px;
      color: #6c757d;
      line-height: 1.35;
    }

    .inline-item-actions {
      display: grid;
      grid-template-columns: repeat(3, 28px);
      gap: 5px;
    }

    .inline-item-actions.seasoning-actions {
      grid-template-columns: 58px 28px;
    }

    .inline-item-actions button,
    .inline-finalize {
      border: 0;
      cursor: pointer;
      font: inherit;
    }

    .inline-item-actions button {
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background: #e8f5e9;
      color: #1b5e20;
      font-weight: 700;
      line-height: 1;
    }

    .inline-item-actions .buy-seasoning {
      width: auto;
      min-width: 58px;
      border-radius: 14px;
      padding: 0 9px;
      background: #00a046;
      color: white;
      font-size: 12px;
    }

    .inline-item-actions .buy-seasoning.selected {
      background: #2e7d32;
    }

    .inline-item-actions .remove-inline {
      background: #f8d7da;
      color: #721c24;
    }

    .inline-total {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid #e9ecef;
      font-weight: 700;
      color: #212529;
    }

    .inline-finalize {
      width: 100%;
      min-height: 38px;
      margin-top: 12px;
      border-radius: 20px;
      background: #00a046;
      color: white;
      font-size: 14px;
      font-weight: 700;
    }

    .quick-prompts {
      display: flex;
      gap: 8px;
      overflow-x: auto;
      padding: 0 15px 12px;
      background: #f8f9fa;
    }

    .quick-prompts button {
      flex: 0 0 auto;
      border: 1px solid #c8e6c9;
      background: #e8f5e9;
      color: #1b5e20;
      border-radius: 18px;
      padding: 8px 12px;
      font-size: 13px;
      cursor: pointer;
      white-space: nowrap;
    }

    .typing {
      display: none;
      color: #6c757d;
      font-size: 13px;
      font-style: italic;
      margin-left: 15px;
      margin-bottom: 10px;
    }

    .chat-input-area {
      padding: 15px;
      background: white;
      border-top: 1px solid #dee2e6;
      display: flex;
      gap: 10px;
    }

    .chat-input-area input {
      flex: 1;
      min-width: 0;
      border: 1px solid #ced4da;
      border-radius: 20px;
      padding: 10px 15px;
      outline: none;
      font-size: 15px;
    }

    .chat-input-area input:focus {
      border-color: #00a046;
      box-shadow: 0 0 0 3px rgba(0, 160, 70, 0.15);
    }

    .chat-input-area button {
      background: #00a046;
      color: white;
      border: none;
      border-radius: 50%;
      width: 40px;
      height: 40px;
      cursor: pointer;
      display: flex;
      justify-content: center;
      align-items: center;
      font-size: 18px;
      line-height: 1;
      flex: 0 0 40px;
    }

    .chat-input-area button:disabled {
      opacity: 0.65;
      cursor: wait;
    }

    .cart-container {
      padding: 15px;
      flex: 1;
      overflow-y: auto;
    }

    .alert-banner {
      padding: 12px;
      border-radius: 8px;
      margin-bottom: 15px;
      font-size: 14px;
      border: 1px solid transparent;
      line-height: 1.45;
    }

    .alert-banner.success {
      background: #e8f5e9;
      color: #1b5e20;
      border-color: #c8e6c9;
    }

	    .alert-banner.empty {
	      background: #fff3cd;
	      color: #664d03;
	      border-color: #ffecb5;
	    }

	    .order-status {
	      display: inline-flex;
	      align-items: center;
	      width: fit-content;
	      padding: 5px 9px;
	      border-radius: 999px;
	      background: #fff3cd;
	      color: #664d03;
	      font-size: 12px;
	      font-weight: 700;
	      margin-top: 8px;
	    }

	    .order-status.paid {
	      background: #e8f5e9;
	      color: #1b5e20;
	    }

    .cart-item {
      background: white;
      padding: 15px;
      border-radius: 12px;
      margin-bottom: 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 14px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }

    .item-info {
      min-width: 0;
    }

    .item-info h4 {
      font-size: 15px;
      margin-bottom: 4px;
      color: #212529;
      line-height: 1.3;
    }

    .item-info p {
      font-size: 13px;
      color: #6c757d;
      margin-bottom: 4px;
    }

    .item-tag {
      display: inline-block;
      background: #e8f5e9;
      color: #2e7d32;
      font-size: 11px;
      padding: 2px 6px;
      border-radius: 4px;
      margin-top: 4px;
      font-weight: 700;
    }

    .item-tag.optional {
      background: #fff3cd;
      color: #664d03;
    }

    .item-price {
      font-weight: 700;
      color: #00a046;
      white-space: nowrap;
      font-size: 14px;
    }

    .cart-footer {
      padding: 20px;
      background: white;
      border-top: 1px solid #dee2e6;
    }

    .total-row {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 15px;
      font-size: 18px;
      font-weight: 700;
    }

    .checkout-btn,
    .secondary-btn {
      width: 100%;
      border: none;
      padding: 15px;
      border-radius: 12px;
      font-size: 16px;
      font-weight: 700;
      cursor: pointer;
    }

	    .checkout-btn {
	      background: #00a046;
	      color: white;
	      margin-bottom: 10px;
	    }

	    .checkout-btn:disabled {
	      opacity: 0.55;
	      cursor: not-allowed;
	    }

    .secondary-btn {
      background: #e9ecef;
      color: #212529;
    }

    .success-container {
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      padding: 30px;
      text-align: center;
      background: white;
    }

	    .success-icon {
	      width: 80px;
	      height: 80px;
	      background: #00a046;
	      color: white;
      border-radius: 50%;
      display: flex;
      justify-content: center;
      align-items: center;
	      font-size: 40px;
	      margin-bottom: 20px;
	    }

	    .success-container h2 {
	      font-size: 22px;
	      margin-bottom: 10px;
	      color: #212529;
	    }

	    .success-container p {
	      color: #6c757d;
	      font-size: 15px;
	      line-height: 1.45;
	      margin-bottom: 24px;
	    }

	    .paid-order {
	      width: 100%;
	      max-height: 240px;
	      overflow-y: auto;
	      margin: 0 0 20px;
	      text-align: left;
	    }

	    .paid-order-item {
	      display: flex;
	      justify-content: space-between;
	      gap: 12px;
	      padding: 10px 0;
	      border-bottom: 1px solid #e9ecef;
	      font-size: 14px;
	    }

	    .paid-order-item b {
	      color: #212529;
	    }

	    .paid-order-item span {
	      color: #00a046;
	      font-weight: 700;
	      white-space: nowrap;
	    }

	    .auth-container {
	      flex: 1;
	      display: flex;
	      flex-direction: column;
	      justify-content: center;
	      gap: 14px;
	      padding: 24px;
	      background: white;
	    }

	    .auth-container h2 {
	      font-size: 24px;
	      color: #212529;
	      line-height: 1.2;
	    }

	    .auth-container p {
	      color: #6c757d;
	      font-size: 14px;
	      line-height: 1.45;
	    }

	    .auth-form {
	      display: grid;
	      gap: 10px;
	      margin-top: 8px;
	    }

	    .auth-form input {
	      width: 100%;
	      border: 1px solid #dee2e6;
	      border-radius: 10px;
	      padding: 13px 14px;
	      font: inherit;
	      outline: none;
	    }

	    .auth-form input:focus {
	      border-color: #00a046;
	    }

	    .auth-actions {
	      display: grid;
	      grid-template-columns: 1fr 1fr;
	      gap: 10px;
	      margin-top: 4px;
	    }

	    .auth-primary,
	    .auth-secondary {
	      border: 0;
	      border-radius: 12px;
	      padding: 13px 10px;
	      cursor: pointer;
	      font: inherit;
	      font-weight: 700;
	    }

	    .auth-primary {
	      background: #00a046;
	      color: white;
	    }

	    .auth-secondary {
	      background: #e9ecef;
	      color: #212529;
	    }

	    .auth-error {
	      min-height: 20px;
	      color: #b42318;
	      font-size: 13px;
	    }

	    .auth-hidden {
	      display: none;
	    }

	    .profile-user {
	      min-width: 0;
	      display: flex;
	      align-items: center;
	      gap: 6px;
	    }

	    .logout-btn {
	      border: 0;
	      border-radius: 10px;
	      background: #dff3e4;
	      color: #1b5e20;
	      padding: 6px 8px;
	      cursor: pointer;
	      font-size: 12px;
	      font-weight: 700;
	      white-space: nowrap;
	    }

    @media (max-width: 430px) {
      body {
        align-items: stretch;
        background: #f8f9fa;
      }

      .mobile-frame {
        width: 100vw;
        height: 100vh;
        border: 0;
        border-radius: 0;
        box-shadow: none;
      }

      .header {
        padding-top: 26px;
      }
    }

	    .modal-overlay {
	      position: fixed;
	      top: 0; left: 0; width: 100vw; height: 100vh;
	      background: rgba(0, 0, 0, 0.5);
	      display: flex;
	      align-items: center;
	      justify-content: center;
	      z-index: 1000;
          backdrop-filter: blur(4px);
	    }
	    .modal-content {
	      background: #fff;
	      border-radius: 16px;
	      padding: 24px;
	      width: 90%;
	      max-width: 320px;
	      text-align: center;
	      box-shadow: 0 10px 25px rgba(0,0,0,0.2);
          animation: modalPop 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
	    }
        @keyframes modalPop {
          0% { transform: scale(0.8); opacity: 0; }
          100% { transform: scale(1); opacity: 1; }
        }
	    .modal-content h3 {
	      margin: 0 0 12px 0;
	      font-size: 18px;
	      color: #111827;
	    }
	    .modal-content p {
	      margin: 0 0 20px 0;
	      color: #4b5563;
	      font-size: 14px;
          line-height: 1.5;
	    }
	    .modal-close {
	      background: #00a046;
	      color: white;
	      border: none;
	      border-radius: 10px;
	      padding: 10px 24px;
	      font-weight: 600;
	      cursor: pointer;
          width: 100%;
	    }
	    .modal-delete {
	      background: #ef4444;
	      color: white;
	      border: none;
	      border-radius: 10px;
	      padding: 10px 24px;
	      font-weight: 600;
	      cursor: pointer;
          margin-right: 8px;
	      transition: background 0.2s;
	    }
	    .modal-delete:hover {
	      background: #dc2626;
	    }

  </style>
</head>
<body>
	  <!-- Allergy Modal -->
	  <div class="modal-overlay" id="allergyModal" style="display: none;">
	    <div class="modal-content">
	      <h3>Chi tiết ghi nhớ</h3>
	      <p id="allergyModalText"></p>
          <div style="display: flex; justify-content: center;">
            <button id="clearAllergiesBtn" class="modal-delete" style="display: none;">Xóa ghi nhớ</button>
	        <button class="modal-close" onclick="document.getElementById('allergyModal').style.display='none'">Đóng</button>
          </div>
	    </div>
	  </div>

	  <div class="mobile-frame">
	    <div class="header">Grocery AI</div>

	    <div id="screen-auth" class="screen active">
	      <div class="auth-container">
	        <h2 id="authTitle">Đăng nhập</h2>
	        <p id="authDescription">Mỗi tài khoản có ghi nhớ dị ứng và lịch sử chat riêng để AI không đề xuất nguyên liệu bạn cần tránh.</p>
	        <div class="auth-form">
	          <input id="authUsername" type="text" placeholder="Tên đăng nhập" autocomplete="username">
	          <input id="authPassword" type="password" placeholder="Mật khẩu" autocomplete="current-password">
	          <input id="authPasswordConfirm" class="auth-hidden" type="password" placeholder="Nhập lại mật khẩu" autocomplete="new-password">
	          <div class="auth-error" id="authError"></div>
	          <div class="auth-actions">
	            <button id="loginButton" class="auth-primary" type="button">Đăng nhập</button>
	            <button id="registerButton" class="auth-secondary" type="button">Đăng ký</button>
	          </div>
	        </div>
	      </div>
	    </div>

		    <div id="screen-chat" class="screen">
		      <div class="profile-strip">
		        <div class="profile-user">
		          <b id="currentUsername">Tài khoản</b>
		          <button id="logoutButton" class="logout-btn" type="button">Thoát</button>
		        </div>
		        <span class="profile-pill" id="userNote">Chưa ghi nhớ dị ứng</span>
	      </div>

      <div class="chat-container" id="chatHistory">
        <div class="msg bot">Chào bạn! Bạn muốn nấu món gì tối nay?</div>
      </div>

      <div class="quick-prompts">
        <button type="button">Tôi muốn ăn đậu phụ sốt cà chua</button>
        <button type="button">Cho tôi nguyên liệu canh chua cá</button>
        <button type="button">Tôi muốn nấu trứng sốt cà chua</button>
      </div>

      <div class="typing" id="typingIndicator">AI đang tư vấn và kiểm tra nguyên liệu...</div>

      <div class="chat-input-area">
        <input type="text" placeholder="Nhập món bạn muốn ăn" id="chatInput">
	        <button id="sendButton" type="button" aria-label="Gửi">›</button>
	      </div>
	    </div>

	    <div id="screen-cart" class="screen">
	      <div class="cart-container" id="cartContainer"></div>
	      <div class="cart-footer">
	        <div class="total-row">
	          <span>Tổng thanh toán</span>
	          <span id="checkoutTotal">0đ</span>
	        </div>
	        <button id="checkoutButton" class="checkout-btn" type="button">Thanh toán</button>
	        <button id="backToChatButton" class="secondary-btn" type="button">Quay lại chat</button>
	      </div>
	    </div>

		    <div id="screen-success" class="screen">
		      <div class="success-container">
		        <div class="success-icon">✓</div>
		        <h2>Đã thanh toán thành công</h2>
		        <p id="paymentSummary">Đơn hàng của bạn đã được ghi nhận.</p>
		        <div id="paidOrderContainer" class="paid-order"></div>
		        <button id="newOrderButton" class="secondary-btn" type="button">Quay lại chat</button>
		      </div>
		    </div>

	  </div>

  <script>
	    const chatHistory = document.getElementById("chatHistory");
	    const authTitle = document.getElementById("authTitle");
	    const authDescription = document.getElementById("authDescription");
	    const authUsername = document.getElementById("authUsername");
	    const authPassword = document.getElementById("authPassword");
	    const authPasswordConfirm = document.getElementById("authPasswordConfirm");
	    const authError = document.getElementById("authError");
	    const loginButton = document.getElementById("loginButton");
	    const registerButton = document.getElementById("registerButton");
		    const chatInput = document.getElementById("chatInput");
		    const sendButton = document.getElementById("sendButton");
		    const typingIndicator = document.getElementById("typingIndicator");
		    const userNote = document.getElementById("userNote");
		    const currentUsername = document.getElementById("currentUsername");
		    const logoutButton = document.getElementById("logoutButton");
		    const screens = document.querySelectorAll(".screen");
	    const cartContainer = document.getElementById("cartContainer");
	    const checkoutTotal = document.getElementById("checkoutTotal");
	    const checkoutButton = document.getElementById("checkoutButton");
		    const backToChatButton = document.getElementById("backToChatButton");
			    const newOrderButton = document.getElementById("newOrderButton");
			    const paymentSummary = document.getElementById("paymentSummary");
			    const paidOrderContainer = document.getElementById("paidOrderContainer");
			    let currentUser = JSON.parse(localStorage.getItem("grocery_ai_user") || "null");
		    let currentCheckoutData = null;
		    let authMode = "login";

	    function updateUserNote(memory) {
	      const allergies = (memory && memory.allergies) || [];
          
          userNote.onclick = function() {
              let text = "";
              let hasAllergies = false;
              if (memory && memory.allergySourceNote) {
                  text = "Hệ thống đã tự động ghi nhận từ câu nói:\\n\\n'" + memory.allergySourceNote + "'";
                  hasAllergies = true;
              } else if (allergies.length) {
                  text = "Hệ thống đã ghi nhớ các dị ứng:\\n" + allergies.map(a => a.label).join(", ");
                  hasAllergies = true;
              } else {
                  text = "Hệ thống chưa ghi nhớ dị ứng nào của bạn.";
              }
              document.getElementById("allergyModalText").innerText = text;
              document.getElementById("clearAllergiesBtn").style.display = hasAllergies ? "block" : "none";
              document.getElementById("allergyModal").style.display = "flex";
          };

          document.getElementById("clearAllergiesBtn").onclick = async function() {
              if (confirm("Bạn có chắc muốn xóa toàn bộ ghi nhớ dị ứng?")) {
                  try {
                      await fetch("/api/user/allergies?user_id=" + encodeURIComponent(currentUserId()), { method: "DELETE" });
                      document.getElementById('allergyModal').style.display = 'none';
                      addMessage("Hệ thống đã xóa toàn bộ ghi nhớ dị ứng. AI sẽ không còn tránh các nguyên liệu này nữa.", false);
                      userNote.innerHTML = '<span class="note-icon">📝</span> Dị ứng: không có';
                      userNote.classList.remove("has-note");
                      memory.allergySourceNote = "";
                      memory.allergies = [];
                  } catch (e) {
                      console.error(e);
                  }
              }
          };
          userNote.style.cursor = "pointer";
          
	      if (memory && memory.allergyNote) {
	        userNote.textContent = memory.allergyNote;
	        return;
	      }
	      if (!allergies.length) {
	        userNote.textContent = "Chưa ghi nhớ dị ứng";
	        return;
	      }
	      userNote.textContent = `Dị ứng: ${allergies.map((item) => item.label).join(", ")}`;
	    }

	    function currentUserId() {
	      return currentUser && currentUser.userId;
	    }

	    function setAuthMode(mode) {
	      authMode = mode;
	      authError.textContent = "";
	      authPassword.value = "";
	      authPasswordConfirm.value = "";
	      if (mode === "register") {
	        authTitle.textContent = "Tạo tài khoản";
	        authDescription.textContent = "Đăng ký để lưu note dị ứng, lịch sử chat và giỏ hàng riêng cho bạn.";
	        authPassword.autocomplete = "new-password";
	        authPasswordConfirm.classList.remove("auth-hidden");
	        loginButton.textContent = "Tạo tài khoản";
	        registerButton.textContent = "Quay lại đăng nhập";
	      } else {
	        authTitle.textContent = "Đăng nhập";
	        authDescription.textContent = "Mỗi tài khoản có ghi nhớ dị ứng và lịch sử chat riêng để AI không đề xuất nguyên liệu bạn cần tránh.";
	        authPassword.autocomplete = "current-password";
	        authPasswordConfirm.classList.add("auth-hidden");
	        loginButton.textContent = "Đăng nhập";
	        registerButton.textContent = "Đăng ký";
	      }
	      authUsername.focus();
	    }

	    function setCurrentUser(user, memory) {
	      currentUser = user;
	      localStorage.setItem("grocery_ai_user", JSON.stringify(user));
	      currentUsername.textContent = user.username;
	      updateUserNote(memory);
	      showScreen("screen-chat");
	      chatInput.focus();
	    }

	    async function submitAuth(mode = authMode) {
	      const username = authUsername.value.trim();
	      const password = authPassword.value.trim();
	      authError.textContent = "";
	      if (username.length < 3 || password.length < 6) {
	        authError.textContent = "Tên đăng nhập ít nhất 3 ký tự, mật khẩu ít nhất 6 ký tự.";
	        return;
	      }
	      if (mode === "register" && password !== authPasswordConfirm.value.trim()) {
	        authError.textContent = "Mật khẩu nhập lại chưa khớp.";
	        return;
	      }

	      loginButton.disabled = true;
	      registerButton.disabled = true;
	      try {
	        const response = await fetch(`/api/auth/${mode}`, {
	          method: "POST",
	          headers: { "Content-Type": "application/json" },
	          body: JSON.stringify({ username, password }),
	        });
	        const data = await response.json();
	        if (!response.ok) {
	          authError.textContent = data.detail || "Không xử lý được tài khoản.";
	          return;
	        }
	        setCurrentUser(data.user, data.memory);
	      } catch (error) {
	        authError.textContent = "Server chưa sẵn sàng.";
	      } finally {
	        loginButton.disabled = false;
	        registerButton.disabled = false;
	      }
	    }

	    async function loadUserMemory() {
	      if (!currentUserId()) {
	        showScreen("screen-auth");
	        authUsername.focus();
	        return;
	      }
	      currentUsername.textContent = currentUser.username;
	      try {
            await fetch(`/api/user/chat_history?user_id=${encodeURIComponent(currentUserId())}`, { method: "DELETE" });
	        const response = await fetch(`/api/memory?user_id=${encodeURIComponent(currentUserId())}`);
	        updateUserNote(await response.json());
	        showScreen("screen-chat");
	      } catch (error) {
	        userNote.textContent = "Chưa tải được ghi nhớ";
	      }
	    }

    function formatMoney(value) {
      return `${Number(value || 0).toLocaleString("vi-VN")}đ`;
    }

    function formatQuantity(value, unit) {
      const number = Number(value || 0);
      const text = Number.isInteger(number)
        ? `${number}`
        : `${number.toFixed(2).replace(/0+$/, "").replace(/\\.$/, "")}`;
      return `${text}${unit ? " " + unit : ""}`;
    }

	    function isSeasoning(item) {
	      return item.displayMode === "seasoning" || item.danhMuc === "Gia vị";
	    }

	    function servingsLabel(recipe) {
	      const servings = Number(recipe && recipe.requestedServings);
	      return servings ? ` - ${servings} người` : "";
	    }

    function addMessage(role, text) {
      const bubble = document.createElement("div");
      bubble.className = `msg ${role}`;
      bubble.textContent = text;
      chatHistory.appendChild(bubble);
      chatHistory.scrollTop = chatHistory.scrollHeight;
      return bubble;
    }

	    function makeText(tag, text, className) {
	      const node = document.createElement(tag);
	      if (className) node.className = className;
	      node.textContent = text;
	      return node;
	    }

	    function showScreen(screenId) {
	      screens.forEach((screen) => screen.classList.remove("active"));
	      document.getElementById(screenId).classList.add("active");
	    }

	    function cartActionMessage(action, itemName) {
	      if (action === "increase") return `tăng số lượng ${itemName}`;
	      if (action === "decrease") return `giảm số lượng ${itemName}`;
	      return `bỏ ${itemName} ra khỏi danh sách`;
    }

	    function cloneCartData(data) {
	      return JSON.parse(JSON.stringify(data || {}));
	    }

	    function lineCost(item) {
	      if (isSeasoning(item)) {
	        return item.purchaseSelected ? Number(item.seasoningLineCostVnd || 0) : 0;
	      }
	      return Number(item.chiPhiUocTinhVnd || item.giaVnd || 0);
	    }

	    function checkoutItems(data) {
	      return ((data && data.ingredients) || []).filter((item) => !isSeasoning(item) || item.purchaseSelected);
	    }

	    function recalculateCartData(data) {
	      const ingredients = data.ingredients || [];
	      data.totalEstimatedCostVnd = ingredients.reduce((total, item) => total + lineCost(item), 0);
	      return data;
	    }

    function findCartItem(data, itemName) {
      const normalizedName = itemName.trim().toLocaleLowerCase("vi-VN");
      return (data.ingredients || []).find((item) => item.tenNguyenLieu.toLocaleLowerCase("vi-VN") === normalizedName);
    }

    function mergeSeasoningSelections(data, previousData) {
      const selectedByName = new Map(
        ((previousData && previousData.ingredients) || [])
          .filter((item) => isSeasoning(item) && item.purchaseSelected)
          .map((item) => [item.tenNguyenLieu, true])
      );
      (data.ingredients || []).forEach((item) => {
        if (isSeasoning(item) && selectedByName.has(item.tenNguyenLieu)) {
          item.purchaseSelected = true;
        }
      });
      return recalculateCartData(data);
    }

    function setBubbleAdvice(cart, text) {
      const bubble = cart.closest(".msg");
      if (!bubble || !text) return;
      if (bubble.firstChild && bubble.firstChild.nodeType === Node.TEXT_NODE) {
        bubble.firstChild.textContent = text;
      }
    }

    function applyLocalCartAction(cart, action, itemName) {
      const data = cloneCartData(cart._cartData);
      data.ingredients = data.ingredients || [];

      if (action === "remove") {
        data.ingredients = data.ingredients.filter((item) => item.tenNguyenLieu !== itemName);
        data.reply = `Đã bỏ ${itemName} khỏi danh sách.`;
        return recalculateCartData(data);
      }

      const item = findCartItem(data, itemName);
      if (!item) return data;

      let multiplier = Number(item.quantityMultiplier || 1);
      if (action === "increase") {
        multiplier += 1;
      } else if (multiplier <= 1) {
        multiplier = Math.max(0.5, multiplier - 0.5);
      } else {
        multiplier = Math.max(0.5, multiplier - 1);
      }

      const baseQuantity = Number(item.baseQuantityStep || item.soLuongChoKhauPhanCoBan || 1);
      const baseCost = Number(item.baseLineCostVnd || item.chiPhiUocTinhVnd || item.giaVnd || 0);
      item.quantityMultiplier = multiplier;
      item.baseQuantityStep = baseQuantity;
      item.baseLineCostVnd = baseCost;
      item.soLuongChoKhauPhanCoBan = baseQuantity * multiplier;
      item.chiPhiUocTinhVnd = isSeasoning(item) ? 0 : Math.round(baseCost * multiplier);
      data.reply = action === "increase"
        ? `Đã tăng số lượng ${itemName}.`
        : `Đã giảm số lượng ${itemName}.`;
      return recalculateCartData(data);
    }

	    function toggleSeasoningPurchase(cart, itemName) {
	      const data = cloneCartData(cart._cartData);
	      const item = findCartItem(data, itemName);
	      if (!item || !isSeasoning(item)) return;

      item.purchaseSelected = !item.purchaseSelected;
      data.reply = item.purchaseSelected
        ? `Đã thêm ${itemName} vào tổng tiền.`
        : `Đã bỏ ${itemName} khỏi tổng tiền.`;
	      renderInlineCart(cart, recalculateCartData(data));
	    }

	    function renderCheckoutCart(data) {
	      const checkoutData = recalculateCartData(cloneCartData(data));
	      const items = checkoutItems(checkoutData);
	      currentCheckoutData = checkoutData;
	      cartContainer.innerHTML = "";

	      if (!items.length) {
	        cartContainer.appendChild(makeText("div", "Danh sách hiện đang trống.", "alert-banner empty"));
	        checkoutTotal.textContent = formatMoney(0);
	        checkoutButton.disabled = true;
	        showScreen("screen-cart");
	        return;
	      }

	      const recipe = checkoutData.matchedRecipe;
	      const title = recipe
	        ? `Đã chốt danh sách cho món ${recipe.tenMonAn}${servingsLabel(recipe)}.`
	        : "Đã chốt danh sách nguyên liệu.";
	      const banner = makeText("div", title, "alert-banner success");
	      banner.appendChild(makeText("div", "Chưa thanh toán", "order-status"));
	      cartContainer.appendChild(banner);

	      items.forEach((item) => {
	        const row = document.createElement("div");
	        row.className = "cart-item";

	        const info = document.createElement("div");
	        info.className = "item-info";

	        const name = makeText("h4", item.tenNguyenLieu, "");
	        const detailText = isSeasoning(item)
	          ? "Gia vị đã chọn mua"
	          : formatQuantity(item.soLuongChoKhauPhanCoBan, item.donViSoLuong);
	        const detail = makeText("p", detailText, "");
	        const tag = makeText("span", item.danhMuc || "Nguyên liệu", `item-tag${item.batBuoc === false ? " optional" : ""}`);
	        info.append(name, detail, tag);

	        const price = makeText("div", formatMoney(lineCost(item)), "item-price");
	        row.append(info, price);
	        cartContainer.appendChild(row);
	      });

	      checkoutTotal.textContent = formatMoney(checkoutData.totalEstimatedCostVnd || 0);
	      checkoutButton.disabled = false;
	      showScreen("screen-cart");
	    }

	    function renderPaidOrder(data) {
	      const checkoutData = recalculateCartData(cloneCartData(data));
	      const items = checkoutItems(checkoutData);
	      paidOrderContainer.innerHTML = "";
	      paidOrderContainer.appendChild(makeText("div", "Đã thanh toán", "order-status paid"));

	      items.forEach((item) => {
	        const row = document.createElement("div");
	        row.className = "paid-order-item";
	        const name = makeText("b", item.tenNguyenLieu, "");
	        const price = makeText("span", formatMoney(lineCost(item)), "");
	        row.append(name, price);
	        paidOrderContainer.appendChild(row);
	      });
	    }

	    async function syncInlineCart(cart, action, itemName) {
	      const optimisticData = applyLocalCartAction(cart, action, itemName);
	      renderInlineCart(cart, optimisticData);
      cart.classList.add("loading");
	      try {
	        const response = await fetch("/api/chat", {
	          method: "POST",
	          headers: { "Content-Type": "application/json" },
	          body: JSON.stringify({ message: cartActionMessage(action, itemName), user_id: currentUserId() }),
	        });
        const data = await response.json();
        updateUserNote(data.memory);
        renderInlineCart(cart, mergeSeasoningSelections(data, optimisticData));
      } catch (error) {
        addMessage("bot", "Mình chưa cập nhật được danh sách. Hãy thử lại nhé.");
      } finally {
        cart.classList.remove("loading");
      }
    }

    function renderInlineCart(cart, data) {
      cart._cartData = cloneCartData(data);
      const recipe = data.matchedRecipe;
      const ingredients = data.ingredients || [];

      cart.innerHTML = "";
      setBubbleAdvice(cart, data.reply);
      if (!ingredients.length) {
        cart.appendChild(makeText("div", "Danh sách nguyên liệu", "inline-cart-title"));
        cart.appendChild(makeText("p", data.reply || "Danh sách hiện đang trống.", ""));
        return;
      }

	      const title = recipe
	        ? `Danh sách nguyên liệu - ${recipe.tenMonAn}${servingsLabel(recipe)}`
	        : "Danh sách nguyên liệu";
      cart.appendChild(makeText("div", title, "inline-cart-title"));

      ingredients.forEach((item) => {
        const row = document.createElement("div");
        row.className = "inline-cart-item";
        if (isSeasoning(item)) row.classList.add("seasoning");

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.checked = true;
        checkbox.title = `Bỏ ${item.tenNguyenLieu}`;
        checkbox.addEventListener("change", () => {
          if (!checkbox.checked) syncInlineCart(cart, "remove", item.tenNguyenLieu);
        });

        const info = document.createElement("div");
        info.className = "inline-item-main";

        const name = document.createElement("h4");
        name.textContent = item.tenNguyenLieu;

        const quantity = document.createElement("p");
        quantity.textContent = `${formatQuantity(item.soLuongChoKhauPhanCoBan, item.donViSoLuong)} • ${formatMoney(item.chiPhiUocTinhVnd || item.giaVnd)}`;

        const actions = document.createElement("div");
        actions.className = "inline-item-actions";
        if (isSeasoning(item)) actions.classList.add("seasoning-actions");

        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "remove-inline";
        remove.textContent = "x";
        remove.title = `Loại bỏ ${item.tenNguyenLieu}`;
        remove.addEventListener("click", () => syncInlineCart(cart, "remove", item.tenNguyenLieu));

        if (isSeasoning(item)) {
          const buy = document.createElement("button");
          buy.type = "button";
          buy.className = `buy-seasoning${item.purchaseSelected ? " selected" : ""}`;
          buy.textContent = item.purchaseSelected ? "Đã chọn" : "Mua";
          buy.title = `Chọn mua ${item.tenNguyenLieu}`;
          buy.addEventListener("click", () => toggleSeasoningPurchase(cart, item.tenNguyenLieu));
          actions.append(buy, remove);
        } else {
          const decrease = document.createElement("button");
          decrease.type = "button";
          decrease.textContent = "-";
          decrease.title = `Giảm ${item.tenNguyenLieu}`;
          decrease.addEventListener("click", () => syncInlineCart(cart, "decrease", item.tenNguyenLieu));

          const increase = document.createElement("button");
          increase.type = "button";
          increase.textContent = "+";
          increase.title = `Tăng ${item.tenNguyenLieu}`;
          increase.addEventListener("click", () => syncInlineCart(cart, "increase", item.tenNguyenLieu));

          actions.append(decrease, increase, remove);
        }
        info.append(name);
        if (!isSeasoning(item)) info.append(quantity);
        row.append(checkbox, info, actions);
        cart.appendChild(row);
      });

	      const total = document.createElement("div");
	      total.className = "inline-total";
	      total.append(makeText("span", "Tổng tiền", ""), makeText("span", formatMoney(data.totalEstimatedCostVnd || 0), ""));

	      const finalize = document.createElement("button");
	      finalize.type = "button";
	      finalize.className = "inline-finalize";
	      finalize.textContent = "Chốt";
	      finalize.addEventListener("click", () => {
	        renderCheckoutCart(cart._cartData);
	      });

      cart.append(total, finalize);
      chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function addCartList(bubble, data) {
      const ingredients = data.ingredients || [];

      if (!ingredients.length) return;

      bubble.classList.add("with-list");
      const cart = document.createElement("div");
      cart.className = "inline-cart";
      renderInlineCart(cart, data);
      bubble.appendChild(cart);
      chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function addBotResponse(data) {
      const bubble = addMessage("bot", data.reply || "Mình chưa tìm thấy món phù hợp.");
      addCartList(bubble, data);
    }

	    async function sendPrompt(text) {
	      if (!currentUserId()) {
	        showScreen("screen-auth");
	        return;
	      }
	      const userText = (text || chatInput.value).trim();
      if (!userText) return;

      addMessage("user", userText);
      chatInput.value = "";
      sendButton.disabled = true;
      typingIndicator.style.display = "block";

      try {
	        const response = await fetch("/api/chat", {
	          method: "POST",
	          headers: { "Content-Type": "application/json" },
	          body: JSON.stringify({ message: userText, user_id: currentUserId() }),
	        });
        const data = await response.json();
        updateUserNote(data.memory);
        addBotResponse(data);
      } catch (error) {
        addMessage("bot", "Server chưa sẵn sàng. Hãy thử lại sau.");
      } finally {
        typingIndicator.style.display = "none";
        sendButton.disabled = false;
      }
    }

	    document.getElementById("sendButton").addEventListener("click", () => sendPrompt());
	    loginButton.addEventListener("click", () => submitAuth());
	    registerButton.addEventListener("click", () => {
	      setAuthMode(authMode === "login" ? "register" : "login");
	    });
	    [authUsername, authPassword, authPasswordConfirm].forEach((input) => {
	      input.addEventListener("keydown", (event) => {
	        if (event.key === "Enter") submitAuth();
	      });
	    });
	    logoutButton.addEventListener("click", () => {
	      currentUser = null;
	      localStorage.removeItem("grocery_ai_user");
	      currentCheckoutData = null;
	      chatHistory.innerHTML = '<div class="msg bot">Chào bạn! Bạn muốn nấu món gì tối nay?</div>';
	      userNote.textContent = "Chưa ghi nhớ dị ứng";
	      authPassword.value = "";
	      authPasswordConfirm.value = "";
	      authError.textContent = "";
	      setAuthMode("login");
	      showScreen("screen-auth");
	      authUsername.focus();
	    });
	    chatInput.addEventListener("keydown", (event) => {
	      if (event.key === "Enter") sendPrompt();
	    });
	    document.querySelectorAll(".quick-prompts button").forEach((button) => {
	      button.addEventListener("click", () => sendPrompt(button.textContent));
	    });
		    checkoutButton.addEventListener("click", () => {
		      const checkoutData = recalculateCartData(cloneCartData(currentCheckoutData));
		      if (!checkoutItems(checkoutData).length) return;
		      paymentSummary.textContent = `Đơn hàng ${formatMoney(checkoutData.totalEstimatedCostVnd || 0)} đã được thanh toán thành công.`;
		      renderPaidOrder(checkoutData);
		      showScreen("screen-success");
		    });
	    backToChatButton.addEventListener("click", () => {
	      showScreen("screen-chat");
	      chatInput.focus();
	    });
	    newOrderButton.addEventListener("click", () => {
	      showScreen("screen-chat");
	      chatInput.focus();
	    });

		    loadUserMemory();
  </script>
</body>
</html>
"""
