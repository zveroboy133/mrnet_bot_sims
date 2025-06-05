class SimCard:
    def __init__(self, number):
        self.number = number
        self.operator = self._determine_operator()
        self._process_number()

    def _determine_operator(self):
        if self.number.startswith("8970199"):
            return "Билайн"
        elif self.number.startswith("8970102"):
            return "Мегафон"
        elif self.number.startswith("8970120"):
            return "Теле2"
        elif self.number.startswith("8970101"):
            return "МТС"
        return "Неизвестный оператор"

    def _validate_number_length(self):
        expected_lengths = {
            "Билайн": 18,
            "МТС": 19,
            "Мегафон": 17,
            "Теле2": 19
        }
        
        if self.operator in expected_lengths:
            expected_length = expected_lengths[self.operator]
            if len(self.number) > expected_length:
                self.number = self.number[:expected_length]

    def _process_number(self):
        self._validate_number_length()
        if self.operator == "Мегафон" and self.number.endswith("464"):
            self.number = self.number[:-3]

def process_sim_numbers(numbers):
    """
    Обрабатывает список номеров SIM-карт
    
    Args:
        numbers (list): Список номеров SIM-карт
        
    Returns:
        list: Список объектов SimCard
    """
    processed_cards = []
    for number in numbers:
        if number.startswith("8970"):  # Проверяем, что это похоже на номер SIM-карты
            sim_card = SimCard(number)
            processed_cards.append(sim_card)
    return processed_cards 