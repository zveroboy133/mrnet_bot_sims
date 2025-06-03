import easyocr
from sim_card_processor import process_sim_numbers

reader = easyocr.Reader(["en"], verbose=False)
#result = reader.readtext("photo_2025-05-30_21-16-36.jpg")
result = reader.readtext("photo4_2025-05-30_22-28-26.jpg", allowlist='1234567890')

sim_numbers = []
current_number = ""

for item in result:
    text = item[1]
    if text.startswith("8970"):
        if current_number:
            sim_numbers.append(current_number)
        current_number = text
    else:
        current_number += text

if current_number:
    sim_numbers.append(current_number)

# Обработка номеров через наш процессор
processed_cards = process_sim_numbers(sim_numbers)

# Вывод результатов
for card in processed_cards:
    print(f"Номер: {card.number}, Оператор: {card.operator}")