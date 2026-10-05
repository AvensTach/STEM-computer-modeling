import numpy as np
import pandas as pd

# Глобальні константи
STEP = 1  # Крок модельного часу - 1 година
WORK_HOURS_PER_DAY = 9
DAYS = 5
TOTAL_STEPS = WORK_HOURS_PER_DAY * DAYS
QUEUE_LIMIT = 3
DAILY_SALARY = 2000

# Параметри послуг: [назва, тривалість (год), вартість, ймовірність]
SERVICES = [
    {'name': 'Consultation', 'duration': 1, 'cost': 500, 'prob': 0.3},
    {'name': 'Hygiene', 'duration': 1, 'cost': 1500, 'prob': 0.2},
    {'name': 'Caries', 'duration': 1, 'cost': 2000, 'prob': 0.4},
    {'name': 'Extraction', 'duration': 2, 'cost': 3000, 'prob': 0.1}
]
SERVICE_PROBS = [s['prob'] for s in SERVICES]
AVG_SERVICE_COST = sum(s['cost'] * s['prob'] for s in SERVICES)  # Для розрахунку втраченого прибутку


class Dentist:
    def __init__(self):
        self.busy_time_left = 0
        self.total_worked_hours = 0

    def take_client(self):
        # Випадковий вибір послуги згідно заданих ймовірностей
        service = np.random.choice(SERVICES, p=SERVICE_PROBS)
        self.busy_time_left = service['duration']
        return service


class Clinic:
    def __init__(self):
        self.dentist = Dentist()
        self.queue = 0
        self.lost_clients = 0
        self.lost_profit = 0
        self.total_income = 0

        self.outage_time_left = 0
        self.current_day = 1
        self.current_hour = 9  # Робочий день з 09:00 до 18:00

        # Для логування
        self.log = []

    def check_daily_outage(self):
        # Перевірка на початку робочого дня (о 09:00)
        if self.current_hour == 9:
            if np.random.rand() < 0.05:  # Ймовірність 5%
                self.outage_time_left = np.random.choice([3, 4])  # 3 або 4 години

    def generate_clients(self):
        # Визначення інтенсивності потоку
        if 9 <= self.current_hour < 12:
            lam = 1.5
        elif 12 <= self.current_hour < 15:
            lam = 0.5
        else:
            lam = 2.5

        arrived = np.random.poisson(lam)

        # Розподіл клієнтів (у чергу або відмова)
        for _ in range(arrived):
            if self.queue < QUEUE_LIMIT:
                self.queue += 1
            else:
                self.lost_clients += 1
                self.lost_profit += AVG_SERVICE_COST

    def process_service(self):
        # Якщо немає світла/води
        if self.outage_time_left > 0:
            self.outage_time_left -= 1
            status = "Outage"
            return status

        status = "Waiting"
        # Якщо лікар зайнятий з минулої години
        if self.dentist.busy_time_left > 0:
            self.dentist.busy_time_left -= 1
            self.dentist.total_worked_hours += 1
            status = "Working (Continues)"

        # Якщо лікар звільнився (або був вільний) і є черга
        if self.dentist.busy_time_left == 0 and self.queue > 0:
            self.queue -= 1
            service = self.dentist.take_client()
            self.total_income += service['cost']

            self.dentist.busy_time_left -= 1  # Віднімаємо поточну годину
            self.dentist.total_worked_hours += 1
            status = f"Started: {service['name']}"

        return status

    def step(self):
        self.check_daily_outage()
        self.generate_clients()
        status = self.process_service()

        # Запис статистики поточного кроку
        self.log.append({
            'Day': self.current_day,
            'Hour': f"{self.current_hour}:00",
            'Queue': self.queue,
            'Dentist Status': status,
            'Lost Clients': self.lost_clients
        })

        # Просування часу
        self.current_hour += STEP
        if self.current_hour >= 18:
            self.current_day += 1
            self.current_hour = 9

    def run_simulation(self):
        for _ in range(TOTAL_STEPS):
            self.step()

        # Підсумкові розрахунки
        net_profit = self.total_income - (DAILY_SALARY * DAYS)

        results = {
            'Total Income (UAH)': self.total_income,
            'Dentist Salary Expenses (UAH)': DAILY_SALARY * DAYS,
            'Net Profit (UAH)': net_profit,
            'Lost Clients': self.lost_clients,
            'Lost Profit (UAH)': self.lost_profit,
            'Dentist Load (%)': round((self.dentist.total_worked_hours / TOTAL_STEPS) * 100, 2)
        }
        return results


# Запуск моделі на 1 тиждень
clinic = Clinic()
final_results = clinic.run_simulation()

# Виведення підсумків
print("--- Підсумки симуляції за 1 тиждень (1 канал) ---")
for key, value in final_results.items():
    print(f"{key}: {value}")

# Виведення фрагменту логу (перший день)
df_log = pd.DataFrame(clinic.log)
print("\n--- Лог першого дня моделювання ---")
print(df_log[df_log['Day'] == 1].to_string(index=False))