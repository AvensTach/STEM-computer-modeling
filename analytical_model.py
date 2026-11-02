import math
import pandas as pd
import matplotlib.pyplot as plt

# Analytical model parameters
lambda_rate = 1.5
t_service = 1.1
mu_rate = 1 / t_service
c = 3
m = 3
work_hours_per_week = 45
salary_per_week_per_dentist = 10000  # 2000 UAH * 5 days
avg_service_cost = 1550  # 500*0.3 + 1500*0.2 + 2000*0.4 + 3000*0.1

rho = lambda_rate / mu_rate

# Calculate P0 (Probability of empty system)
sum_c = sum((rho**k) / math.factorial(k) for k in range(c + 1))
sum_m = sum((rho / c)**i for i in range(1, m + 1))
p0 = 1 / (sum_c + ((rho**c) / math.factorial(c)) * sum_m)

# Calculate Probability of rejection (Prej)
p_rej = ((rho**c) / math.factorial(c)) * ((rho / c)**m) * p0

# Calculate Throughput characteristics
Q = 1 - p_rej
A = lambda_rate * Q

# Calculate System state metrics
k_busy = A / mu_rate
load_percent = (k_busy / c) * 100
k_free = c - k_busy

# Calculate Weekly Financial metrics
served_weekly = A * work_hours_per_week
lost_weekly = (lambda_rate - A) * work_hours_per_week

total_income = served_weekly * avg_service_cost
total_salary = salary_per_week_per_dentist * c
net_profit = total_income - total_salary
lost_profit = lost_weekly * avg_service_cost

# --- TABULAR OUTPUT (Pandas) ---
metrics_data = {
    "Показник": [
        "Приведене навантаження (Rho)",
        "Ймовірність простою системи (P0)",
        "Ймовірність відмови (P_відм)",
        "Відносна пропускна здатність (Q)",
        "Абсолютна пропускна здатність (A) [кл/год]",
        "Середня кількість зайнятих лікарів (k_зайнятих)",
        "Завантаженість лікарів (%)",
        "Очікувані втрачені клієнти за тиждень",
        "Очікуваний загальний дохід (UAH)",
        "Очікуваний чистий прибуток (UAH)",
        "Очікуваний втрачений прибуток (UAH)"
    ],
    "Значення": [
        f"{rho:.2f}",
        f"{p0:.4f}",
        f"{p_rej:.4f}",
        f"{Q:.4f}",
        f"{A:.4f}",
        f"{k_busy:.2f}",
        f"{load_percent:.2f}%",
        f"{lost_weekly:.2f}",
        f"{total_income:.2f}",
        f"{net_profit:.2f}",
        f"{lost_profit:.2f}"
    ]
}

df_metrics = pd.DataFrame(metrics_data)
print("\n" + "="*70)
print("=== Результати Аналітичної Моделі (M/M/c/m) ===")
print("="*70)
print(df_metrics.to_string(index=False, justify='left'))
print("="*70 + "\n")


# --- VISUALIZATION (Matplotlib) - 3 Separate Windows ---

# Window 1: Financial Metrics (Matches Simulation Model style)
plt.figure(figsize=(8, 6))
labels_fin = ['Загальний дохід', 'Чистий прибуток', 'Втрачений прибуток']
values_fin = [total_income, net_profit, lost_profit]
bars_fin = plt.bar(labels_fin, values_fin, color=['#4C72B0', '#55A868', '#C44E52'], edgecolor='black')
plt.title(f'Тижневі фінансові показники (Аналітична модель, Лікарів: {c})')
plt.ylabel('Сума (UAH)')

for bar in bars_fin:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + (max(values_fin)*0.02),
             f"{yval:.0f}", ha='center', va='bottom')
plt.tight_layout()

# Window 2: Average Dentist Load (Matches Simulation Model Pie Chart style)
plt.figure(figsize=(8, 6))
pie_labels = ['Робота з клієнтами', 'Очікування клієнтів (простій)']
pie_sizes = [k_busy, k_free]
plt.pie(pie_sizes, labels=pie_labels, autopct='%1.1f%%', startangle=140,
        colors=['#55A868', '#DDDDDD'], wedgeprops={'edgecolor': 'black'})
plt.title(f'Середній розподіл часу клініки (Аналітична модель, Лікарів: {c})')
plt.tight_layout()

# Window 3: Probabilities
plt.figure(figsize=(8, 6))
labels_prob = ['P0\n(Вільна)', 'P_відм\n(Відмова)', 'Q\n(Прийнято)']
values_prob = [p0, p_rej, Q]
bars_prob = plt.bar(labels_prob, values_prob, color=['#DDDDDD', '#C44E52', '#55A868'], edgecolor='black')
plt.title('Ймовірності системи (Аналітична модель)')
plt.ylabel('Ймовірність')
plt.ylim(0, 1.1)

for bar in bars_prob:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 0.02,
             f"{yval:.4f}", ha='center', va='bottom')
plt.tight_layout()

# Show all windows simultaneously
plt.show()