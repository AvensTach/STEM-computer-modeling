import numpy as np
import pandas as pd

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
    # Added parameters to change queue limit and flow intensity (for task 9)
    def __init__(self, queue_limit=3, arrival_multiplier=1.0):
        self.dentist = Dentist()
        self.queue = 0
        self.lost_clients = 0
        self.lost_profit = 0
        self.total_income = 0

        self.outage_time_left = 0
        self.outages_count = 0  # Track number of outage events
        self.outage_hours_total = 0  # Track total hours lost due to outages

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
        # Determine flow intensity based on the time of day
        if 9 <= self.current_hour < 12:
            lam = 1.5
        elif 12 <= self.current_hour < 15:
            lam = 0.5
        else:
            lam = 2.5

        lam *= self.arrival_multiplier
        arrived = np.random.poisson(lam)

        # Determine "effective capacity" for this step
        # If the doctor is free and there is no outage, the client can sit in the chair, bypassing the queue
        effective_limit = self.queue_limit
        if self.dentist.busy_time_left == 0 and self.outage_time_left == 0:
            effective_limit += 1

        # Distribute clients (into the clinic or rejected)
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


# --- EXECUTION OF TASK 10: 100 MODEL RUNS ---
def run_multiple_simulations(runs=100, queue_limit=3, arrival_multiplier=1.0):
    results = []
    for _ in range(runs):
        clinic = Clinic(queue_limit=queue_limit, arrival_multiplier=arrival_multiplier)
        results.append(clinic.run_simulation())

    df_results = pd.DataFrame(results)
    averages = df_results.mean().round(2)
    return averages


print("=== TASK 10: Averaged results over 100 runs (Base model) ===")
base_averages = run_multiple_simulations(runs=100)
print(base_averages.to_string())
print("\n")

# --- EXECUTION OF TASK 9: MODEL ADEQUACY CHECK ---
print("=== TASK 9: Model adequacy check ===")

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