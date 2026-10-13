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

    def take_client(self):
        service = np.random.choice(SERVICES, p=SERVICE_PROBS)
        self.busy_time_left = service['duration']
        return service


class Clinic:
    def __init__(self, queue_limit=3, arrival_multiplier=1.0):
        self.dentist = Dentist()
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

        effective_limit = self.queue_limit
        if self.dentist.busy_time_left == 0 and self.outage_time_left == 0:
            effective_limit += 1

        for _ in range(arrived):
            if self.queue < effective_limit:
                self.queue += 1
            else:
                self.lost_clients += 1
                self.lost_profit += AVG_SERVICE_COST

    def process_service(self):
        if self.outage_time_left > 0:
            self.outage_time_left -= 1
            return "Outage"

        if self.dentist.busy_time_left > 0:
            self.dentist.busy_time_left -= 1
            self.dentist.total_worked_hours += 1
            return "Working (Continues)"

        elif self.queue > 0:
            self.queue -= 1
            service = self.dentist.take_client()
            self.total_income += service['cost']
            self.dentist.busy_time_left -= 1
            self.dentist.total_worked_hours += 1
            return f"Started: {service['name']}"

        return "Waiting"

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
        net_profit = self.total_income - (DAILY_SALARY * DAYS)
        return {
            'Total Income (UAH)': self.total_income,
            'Net Profit (UAH)': net_profit,
            'Lost Clients': self.lost_clients,
            'Lost Profit (UAH)': self.lost_profit,
            'Dentist Load (%)': (self.dentist.total_worked_hours / TOTAL_STEPS) * 100,
            'Outages Count': self.outages_count,
            'Outage Hours Lost': self.outage_hours_total
        }


def run_multiple_simulations(runs=100, queue_limit=3, arrival_multiplier=1.0):
    results = []
    for _ in range(runs):
        clinic = Clinic(queue_limit=queue_limit, arrival_multiplier=arrival_multiplier)
        results.append(clinic.run_simulation())

    df_results = pd.DataFrame(results)
    averages = df_results.mean().round(2)
    return averages, df_results


def plot_single_simulation_results(results):
    # Window 1: Financial indicators
    plt.figure(figsize=(8, 6))
    labels = ['Total Income', 'Net Profit', 'Lost Profit']
    values = [results['Total Income (UAH)'], results['Net Profit (UAH)'], results['Lost Profit (UAH)']]
    bars = plt.bar(labels, values, color=['#4C72B0', '#55A868', '#C44E52'])
    plt.title('Weekly Financial Indicators (1 Run)')
    plt.ylabel('Amount (UAH)')
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval + (max(values) * 0.02),
                 round(yval, 2), ha='center', va='bottom')
    plt.tight_layout()

    # Window 2: Time distribution
    plt.figure(figsize=(8, 6))
    worked_hours = (results['Dentist Load (%)'] / 100) * TOTAL_STEPS
    outage_hours = results['Outage Hours Lost']
    idle_hours = TOTAL_STEPS - worked_hours - outage_hours
    idle_hours = max(0, idle_hours)  # Protection against negative values

    time_labels = ['Working with clients', 'Power outages', 'Waiting for clients (idle)']
    time_sizes = [worked_hours, outage_hours, idle_hours]
    colors = ['#55A868', '#C44E52', '#DDDDDD']

    filtered_labels = [label for size, label in zip(time_sizes, time_labels) if size > 0]
    filtered_sizes = [size for size in time_sizes if size > 0]
    filtered_colors = [color for size, color in zip(time_sizes, colors) if size > 0]

    plt.pie(filtered_sizes, labels=filtered_labels, autopct='%1.1f%%',
            startangle=140, colors=filtered_colors, wedgeprops={'edgecolor': 'black'})
    plt.title('Clinic Time Distribution (1 Run)')
    plt.tight_layout()

    # Display both windows simultaneously
    plt.show()


def plot_multiple_simulation_results(df_results, averages):
    # Window 1: Net profit histogram
    plt.figure(figsize=(8, 6))
    plt.hist(df_results['Net Profit (UAH)'], bins=20, color='skyblue', edgecolor='black')
    plt.axvline(averages['Net Profit (UAH)'], color='red', linestyle='dashed', linewidth=2,
                label=f"Average: {averages['Net Profit (UAH)']}")
    plt.title('Net Profit Distribution (100 runs)')
    plt.xlabel('Net Profit (UAH)')
    plt.ylabel('Frequency (number of runs)')
    plt.legend()
    plt.tight_layout()

    # Window 2: Lost clients histogram
    plt.figure(figsize=(8, 6))
    plt.hist(df_results['Lost Clients'], bins=20, color='salmon', edgecolor='black')
    plt.axvline(averages['Lost Clients'], color='red', linestyle='dashed', linewidth=2,
                label=f"Average: {averages['Lost Clients']}")
    plt.title('Lost Clients Distribution (100 runs)')
    plt.xlabel('Number of Lost Clients')
    plt.ylabel('Frequency')
    plt.legend()
    plt.tight_layout()

    # Window 3: Financial indicators (Bar chart)
    plt.figure(figsize=(8, 6))
    labels = ['Total Income', 'Net Profit', 'Lost Profit']
    values = [averages['Total Income (UAH)'], averages['Net Profit (UAH)'], averages['Lost Profit (UAH)']]
    bars = plt.bar(labels, values, color=['#4C72B0', '#55A868', '#C44E52'])
    plt.title('Average Financial Indicators (100 runs)')
    plt.ylabel('Amount (UAH)')

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval + (max(values) * 0.02),
                 round(yval, 2), ha='center', va='bottom')
    plt.tight_layout()

    # Window 4: Time distribution (Pie chart) for 100 runs
    plt.figure(figsize=(8, 6))
    worked_hours = (averages['Dentist Load (%)'] / 100) * TOTAL_STEPS
    outage_hours = averages['Outage Hours Lost']
    idle_hours = TOTAL_STEPS - worked_hours - outage_hours
    idle_hours = max(0, idle_hours)  # Protection against negative values

    time_labels = ['Working with clients', 'Power outages', 'Waiting for clients (idle)']
    time_sizes = [worked_hours, outage_hours, idle_hours]
    colors = ['#55A868', '#C44E52', '#DDDDDD']

    filtered_labels = [label for size, label in zip(time_sizes, time_labels) if size > 0]
    filtered_sizes = [size for size in time_sizes if size > 0]
    filtered_colors = [color for size, color in zip(time_sizes, colors) if size > 0]

    plt.pie(filtered_sizes, labels=filtered_labels, autopct='%1.1f%%',
            startangle=140, colors=filtered_colors, wedgeprops={'edgecolor': 'black'})
    plt.title('Average Clinic Time Distribution (100 runs)')
    plt.tight_layout()

    # Display all windows simultaneously
    plt.show()


if __name__ == "__main__":
    # --- 1 RUN ---
    print("=== RUN 1: Single simulation results ===")
    single_clinic = Clinic()
    single_results = single_clinic.run_simulation()

    for key, value in single_results.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")

    print("\nGenerating charts for 1 run... (Close the chart windows to let the program continue)")
    plot_single_simulation_results(single_results)

    print("\n" + "=" * 50 + "\n")

    # --- 100 RUNS ---
    print("=== RUN 100: Averaged results over 100 iterations ===")
    base_averages, base_df_results = run_multiple_simulations(runs=100)
    print(base_averages.to_string())

    print("\nGenerating charts for 100 runs... (Opened 4 new windows)")
    plot_multiple_simulation_results(base_df_results, base_averages)

    print("Model adequacy check")

    # Test 1: Zero client flow (nobody arrives)
    print("\nTest 1: Zero client flow (arrival_multiplier = 0)")
    test1_avg = run_multiple_simulations(runs=10, arrival_multiplier=0)
    print(test1_avg.to_string())
    # Expectation: Income 0, Lost clients 0, Load 0%, Outages may still occur.

    # Test 2: Extremely high client flow (arrival_multiplier = 10)
    print("\nTest 2: Extremely high client flow (arrival_multiplier = 10)")
    test2_avg = run_multiple_simulations(runs=10, arrival_multiplier=10)
    print(test2_avg.to_string())
    # Expectation: Huge number of lost clients, dentist load close to 100% (minus Outage Hours Lost).

    # Test 3: No queue capacity (queue_limit = 0)
    print("\nTest 3: Operation without queue (queue_limit = 0)")
    test3_avg = run_multiple_simulations(runs=10, queue_limit=0)
    print(test3_avg.to_string())
    # Expectation: Any client arriving when the doctor is busy is immediately lost. Number of lost clients will increase compared to the base model.