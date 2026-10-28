"""
Simple linear and polynomial regression for future projections
(check-ins and average social influence).
"""

import numpy as np
import matplotlib.pyplot as plt
import pyodbc

from src.config import get_connection_string


def get_connection():
    return pyodbc.connect(get_connection_string())


def run_predictions():
    print("\n" + "=" * 70)
    print("  FORECAST 2027-2029 (Linear + Polynomial Regression)")
    print("=" * 70)

    conn = get_connection()
    cursor = conn.cursor()

    # Historical check-ins
    cursor.execute(
        """
        SELECT YEAR(checkin_time) AS ano, COUNT(*) AS total
        FROM Coleta_Checkins
        WHERE checkin_time IS NOT NULL
        GROUP BY YEAR(checkin_time)
        ORDER BY ano
        """
    )
    checkins = cursor.fetchall()

    # Average social influence
    cursor.execute(
        """
        SELECT ano, AVG(valor) AS media
        FROM Coleta_Sociais_Agregados
        GROUP BY ano
        ORDER BY ano
        """
    )
    social = cursor.fetchall()
    conn.close()

    years_check = [r[0] for r in checkins]
    values_check = [r[1] for r in checkins]
    years_social = [r[0] for r in social]
    values_social = [r[1] for r in social]

    print(f"Check-in years available: {years_check}")
    print(f"Social data years available: {years_social}")

    _forecast(years_check, values_check, "Total Check-ins")
    _forecast(years_social, values_social, "Average Social Influence")

    print("\nForecasts completed. Charts saved as PNG.")


def _forecast(years, values, title: str):
    if len(years) < 2:
        print(f"Not enough data for {title}. Skipping.")
        return

    x = np.array(years, dtype=float)
    y = np.array(values, dtype=float)

    # Linear
    coef_lin = np.polyfit(x, y, 1)
    pred_lin = np.polyval(coef_lin, [2027, 2028, 2029])

    # Polynomial degree 2
    coef_poly = np.polyfit(x, y, 2)
    pred_poly = np.polyval(coef_poly, [2027, 2028, 2029])

    print(f"\n>>> FORECAST — {title}")
    for year, lin, poly in zip([2027, 2028, 2029], pred_lin, pred_poly):
        print(f"  {year} → Linear: {lin:,.0f}  |  Polynomial: {poly:,.0f}")

    # Chart
    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, color="blue", label="Real data")
    plt.plot(x, np.polyval(coef_lin, x), color="red", label="Linear regression")
    plt.plot(x, np.polyval(coef_poly, x), color="green", label="Polynomial regression")
    plt.scatter(
        [2027, 2028, 2029],
        pred_poly,
        color="orange",
        marker="x",
        s=120,
        label="Forecast",
    )
    plt.title(f"Forecast — {title} (São Paulo 2027-2029)")
    plt.xlabel("Year")
    plt.ylabel(title)
    plt.legend()
    plt.grid(True)

    filename = f"previsao_{title.lower().replace(' ', '_')}.png"
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Chart saved → {filename}")


if __name__ == "__main__":
    run_predictions()
