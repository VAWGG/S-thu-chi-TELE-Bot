import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import re

# Thay bằng token của bạn
BOT_TOKEN = "7869132035:AAF-R1rDOgMea-SAkGt8-StPkGP4n6R8tZk"
bot = telebot.TeleBot(BOT_TOKEN)

# Danh sách lưu trữ giao dịch (giả lập database)
transactions = []

# Hàm chuyển đổi số tiền từ chuỗi
def parse_amount(text):
    text = text.lower().strip()
    text = text.lstrip("+")  # Xóa ký tự +
    if "k" in text:
        return int(float(text.replace("k", "").replace(",", "").strip()) * 1000)
    elif "tr" in text:
        return int(float(text.replace("tr", "").replace(",", "").strip()) * 1000000)
    elif text.isdigit():
        return int(text)
    else:
        return None

# Hàm hiển thị danh sách giao dịch
def list_transactions():
    if not transactions:
        return "Danh sách giao dịch hiện tại trống."
    message = "📋 Danh sách giao dịch:\n"
    for idx, transaction in enumerate(transactions, start=1):
        message += (
            f"{idx}. {transaction['note']} - {transaction['amount']:,} VNĐ "
            f"({transaction['type']}) - {transaction['time'].strftime('%d-%m-%Y %H:%M')}\n"
        )
    return message

# Hàm xử lý tin nhắn "Menu"
@bot.message_handler(commands=['start', 'menu'])
def send_menu(message):
    # Tạo menu dạng nút bấm
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Thêm giao dịch"))
    markup.add(KeyboardButton("Xem thống kê tháng"))
    markup.add(KeyboardButton("Xem giao dịch cụ thể"))
    markup.add(KeyboardButton("Xóa giao dịch"))
    bot.reply_to(message, "📋 Menu chính:\nChọn một tùy chọn bên dưới:", reply_markup=markup)

# Thống kê tổng income và expense theo tháng
def get_monthly_summary(month, year):
    total_income = 0
    total_expense = 0
    for transaction in transactions:
        trans_date = transaction["time"]
        if trans_date.month == month and trans_date.year == year:
            if transaction["type"] == "income":
                total_income += transaction["amount"]
            else:
                total_expense += transaction["amount"]
    return total_income, total_expense

# Lấy danh sách giao dịch theo ngày
def get_transactions_by_date(date):
    result = []
    for transaction in transactions:
        if transaction["time"].date() == date:
            result.append(transaction)
    return result

# Xử lý các tùy chọn từ menu
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_message = message.text.strip()

    # Nếu người dùng chọn "Thêm giao dịch"
    if user_message == "Thêm giao dịch":
        bot.reply_to(message, "Nhập giao dịch của bạn theo dạng: <số tiền> <mô tả> hoặc <mô tả> <số tiền>.")

    # Nếu người dùng chọn "Xem thống kê tháng"
    elif user_message == "Xem thống kê tháng":
        now = datetime.now()
        total_income, total_expense = get_monthly_summary(now.month, now.year)
        bot.reply_to(
            message,
            f"📊 Thống kê tháng {now.month}/{now.year}:\n"
            f"💰 Thu nhập: {total_income:,} VNĐ\n"
            f"💸 Chi tiêu: {total_expense:,} VNĐ\n"
            f"🔄 Cân đối: {total_income - total_expense:,} VNĐ"
        )

    # Nếu người dùng chọn "Xem giao dịch cụ thể"
    elif user_message == "Xem giao dịch cụ thể":
        bot.reply_to(message, "Nhập ngày cần xem giao dịch (dd-mm-yyyy):")

    # Nếu người dùng chọn "Xóa giao dịch"
    elif user_message == "Xóa giao dịch":
        if not transactions:
            bot.reply_to(message, "Danh sách hiện tại trống. Không có gì để xóa.")
        else:
            bot.reply_to(message, list_transactions())
            bot.reply_to(message, "Nhập số thứ tự giao dịch bạn muốn xóa:")
            bot.register_next_step_handler(message, delete_transaction)

    # Nếu người dùng nhập ngày
    elif re.match(r"\d{2}-\d{2}-\d{4}", user_message):
        try:
            date = datetime.strptime(user_message, "%d-%m-%Y").date()
            daily_transactions = get_transactions_by_date(date)
            if daily_transactions:
                response = f"📅 Giao dịch ngày {date}:\n"
                for trans in daily_transactions:
                    response += f"- {trans['note']}: {trans['amount']:,} VNĐ ({trans['type']})\n"
            else:
                response = f"Không có giao dịch nào vào ngày {date}."
            bot.reply_to(message, response)
        except ValueError:
            bot.reply_to(message, "Ngày không hợp lệ. Vui lòng nhập lại (dd-mm-yyyy).")

    # Nếu nhập giao dịch mới
    else:
        # Tìm số tiền và ghi chú
        match = re.search(r"([\+\-]?\d+(\.\d+)?(k|tr)?)|([\+\-]?\d+)", user_message)
        if match:
            amount_text = match.group(0)
            note = user_message.replace(amount_text, "").strip()
            amount = parse_amount(amount_text)
            if amount is not None:
                transaction_type = "income" if amount > 0 else "expense"
                # Lưu giao dịch
                transactions.append({
                    "amount": abs(amount),
                    "type": transaction_type,
                    "note": note,
                    "time": datetime.now()
                })
                bot.reply_to(
                    message,
                    f"Đã lưu: {abs(amount):,} VNĐ cho '{note}' ({transaction_type}) ✅"
                )
            else:
                bot.reply_to(message, "Số tiền không hợp lệ. Vui lòng thử lại.")
        else:
            bot.reply_to(message, "Cú pháp không hợp lệ. Vui lòng nhập dạng:\n<số tiền> <mô tả> hoặc <mô tả> <số tiền>.")

# Hàm xử lý xóa giao dịch
def delete_transaction(message):
    try:
        idx = int(message.text.strip()) - 1
        if idx < 0 or idx >= len(transactions):
            bot.reply_to(message, "Số thứ tự không hợp lệ. Vui lòng thử lại.")
        else:
            deleted = transactions.pop(idx)
            bot.reply_to(
                message,
                f"Đã xóa: {deleted['note']} - {deleted['amount']:,} VNĐ ({deleted['type']}) ✅"
            )
    except ValueError:
        bot.reply_to(message, "Vui lòng nhập số thứ tự hợp lệ.")

# Khởi động bot
print("Bot đang chạy...")
bot.polling()
