import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Global constants
STEP = 1
WORK_HOURS_PER_DAY = 9
DAYS = 5
TOTAL_STEPS = WORK_HOURS_PER_DAY * DAYS
DAILY_SALARY = 2000

SERVICES = [
    {'name': 'Consultation', 'duration': 1, 'cost': 500, 'prob': 0.3},
    {'name': 'Hygiene', 'duration': 1, 'cost': 1500, 'prob': 0.2},
    {'name': 'Caries', 'duration': 1, 'cost': 2000, 'prob': 0.4},
    {'name': 'Extraction', 'duration': 2, 'cost': 3000, 'prob': 0.1}
]
SERVICE_PROBS = [s['prob'] for s in SERVICES]
AVG_SERVICE_COST = sum(s['cost'] * s['prob'] for s in SERVICES)


class Dentist:
    def __init__(self):
        self.busy_time_left = 0
        self.total_worked_hours = 0

    def take_client(self, service=None):
        if not service:
            service = np.random.choice(SERVICES, p=SERVICE_PROBS)
        self.busy_time_left = service['duration']
        return service


class Clinic:
    def __init__(self, num_dentists=1, queue_limit=3, arrival_multiplier=1.0):
        self.num_dentists = num_dentists
        self.dentists = [Dentist() for _ in range(num_dentists)]

        self.queue = 0
        self.lost_clients = 0
        self.lost_profit = 0
        self.total_income = 0

        self.outage_time_left = 0
        self.outages_count = 0
        self.outage_hours_total = 0

        self.current_day = 1
        self.current_hour = 9

        self.queue_limit = queue_limit
        self.arrival_multiplier = arrival_multiplier

    def check_daily_outage(self):
        if self.current_hour == 9:
            if np.random.rand() < 0.05:
                duration = np.random.choice([3, 4])
                self.outage_time_left = duration
                self.outages_count += 1
                self.outage_hours_total += duration

    def generate_clients(self):
        if 9 <= self.current_hour < 12:
            lam = 1.5
        elif 12 <= self.current_hour < 15:
            lam = 0.5
        else:
            lam = 2.5

        lam *= self.arrival_multiplier
        arrived = np.random.poisson(lam)

        # Ємність = місця в черзі + вільні лікарі (якщо немає блекауту)
        free_dentists = sum(1 for d in self.dentists if d.busy_time_left == 0)
        if self.outage_time_left > 0:
            free_dentists = 0

        effective_limit = self.queue_limit + free_dentists

        for _ in range(arrived):
            if self.queue < effective_limit:
                self.queue += 1
            else:
                self.lost_clients += 1
                self.lost_profit += AVG_SERVICE_COST

    def process_service(self):
        if self.outage_time_left > 0:
            self.outage_time_left -= 1
            return

        # 1. Зменшуємо час зайнятості для всіх працюючих лікарів
        for d in self.dentists:
            if d.busy_time_left > 0:
                d.busy_time_left -= 1
                d.total_worked_hours += 1

        # 2. Розподіляємо чергу між вільними лікарями
        for d in self.dentists:
            if d.busy_time_left == 0 and self.queue > 0:
                self.queue -= 1
                service = d.take_client()
                self.total_income += service['cost']
                d.busy_time_left -= 1
                d.total_worked_hours += 1

    def step(self):
        self.check_daily_outage()
        self.generate_clients()
        self.process_service()

        self.current_hour += STEP
        if self.current_hour >= 18:
            self.current_day += 1
            self.current_hour = 9

    def run_simulation(self):
        for _ in range(TOTAL_STEPS):
            self.step()

        # Зарплата виплачується ВСІМ лікарям
        total_salary_costs = DAILY_SALARY * DAYS * self.num_dentists
        net_profit = self.total_income - total_salary_costs

        total_worked = sum(d.total_worked_hours for d in self.dentists)
        avg_load = (total_worked / (TOTAL_STEPS * self.num_dentists)) * 100

        return {
            'Dentists': self.num_dentists,
            'Total Income': self.total_income,
            'Net Profit': net_profit,
            'Lost Clients': self.lost_clients,
            'Lost Profit': self.lost_profit,
            'Avg Load (%)': avg_load,
            'Outage Hours': self.outage_hours_total
        }


def run_multiple_simulations(runs=100, num_dentists=1, queue_limit=3, arrival_multiplier=1.0):
    results = [Clinic(num_dentists, queue_limit, arrival_multiplier).run_simulation() for _ in range(runs)]
    return pd.DataFrame(results).mean().round(2)


if __name__ == "__main__":
    print("=== 14. Перевірка адекватності моделі (Model Adequacy) ===")

    print("\nТест 1: Нульовий потік клієнтів (arrival_multiplier = 0)")
    print(run_multiple_simulations(runs=10, arrival_multiplier=0).to_string())
    # Логіка: Дохід 0, Втрачені клієнти 0, Завантаженість 0%. Чистий прибуток від'ємний (зарплата лікаря).

    print("\nТест 2: Екстремальний потік клієнтів (arrival_multiplier = 10, 1 лікар)")
    print(run_multiple_simulations(runs=10, arrival_multiplier=10).to_string())
    # Логіка: Величезна кількість втрачених клієнтів, завантаженість лікаря близька до максимуму.

    print("\nТест 3: Робота без черги (queue_limit = 0)")
    print(run_multiple_simulations(runs=10, queue_limit=0).to_string())
    # Логіка: Будь-який клієнт, що прийшов коли лікар зайнятий, одразу втрачається. Кількість втрат зростає.

    print("\n\n=== 15. Експерименти: Оптимізація кількості лікарів (100 прогонів на варіант) ===")
    experiments = []
    dentist_counts = [1, 2, 3, 4]

    for n in dentist_counts:
        avg_results = run_multiple_simulations(runs=100, num_dentists=n)
        experiments.append(avg_results)

    df_experiments = pd.DataFrame(experiments)
    print(df_experiments[['Dentists', 'Net Profit', 'Lost Clients', 'Avg Load (%)']].to_string(index=False))

    # Візуалізація результатів експерименту
    plt.figure(figsize=(10, 5))

    plt.subplot(1, 2, 1)
    plt.plot(df_experiments['Dentists'], df_experiments['Net Profit'], marker='o', color='green')
    plt.title('Чистий прибуток від кількості лікарів')
    plt.xlabel('Кількість лікарів')
    plt.ylabel('Чистий прибуток (грн)')
    plt.xticks(dentist_counts)
    plt.grid(True)

    plt.subplot(1, 2, 2)
    plt.plot(df_experiments['Dentists'], df_experiments['Lost Clients'], marker='o', color='red')
    plt.title('Втрачені клієнти від кількості лікарів')
    plt.xlabel('Кількість лікарів')
    plt.ylabel('Втрачені клієнти')
    plt.xticks(dentist_counts)
    plt.grid(True)

    plt.tight_layout()
    plt.show()