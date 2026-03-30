"""
Two-Statement Company Financial Model
=======================================
Links the two core financial statements:
  1. Income Statement  — Revenue → Net Income
  2. Balance Sheet     — Assets = Liabilities + Equity (balanced every period)

Connection logic:
  Net Income  → Retained Earnings (Balance Sheet equity section)
  Dividends   → Reduce Retained Earnings
  The model auto-checks the Balance Sheet equation each period.

Usage:
    python two_statement_model.py

Requirements:
    pip install pandas matplotlib
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ══════════════════════════════════════════════════════════════
# 1.  ASSUMPTIONS  (edit these to model your company)
# ══════════════════════════════════════════════════════════════

ASSUMPTIONS = {
    # --- Income Statement ---
    "revenue_year1":        500_000,   # Starting annual revenue
    "revenue_growth_rate":  0.12,      # 12% YoY revenue growth
    "cogs_pct_revenue":     0.40,      # Cost of Goods Sold as % of revenue
    "opex_pct_revenue":     0.25,      # Operating expenses as % of revenue
    "depreciation":         15_000,    # Fixed annual depreciation (₹/year)
    "interest_expense":     8_000,     # Fixed annual interest on debt
    "tax_rate":             0.25,      # Corporate tax rate

    # --- Balance Sheet ---
    "cash_year0":           80_000,    # Opening cash balance
    "accounts_receivable_days": 45,    # Days sales outstanding
    "inventory_days":       30,        # Days inventory outstanding
    "other_current_assets": 20_000,    # Fixed other current assets
    "fixed_assets_gross_year0": 200_000,  # Gross PP&E at start
    "capex_annual":         20_000,    # Annual capital expenditure
    "accounts_payable_days": 30,       # Days payable outstanding
    "other_current_liabilities": 15_000, # Fixed other current liabilities
    "long_term_debt":       100_000,   # Fixed long-term debt (simplified)
    "share_capital":        150_000,   # Paid-in capital (constant)
    "retained_earnings_year0": 50_000, # Opening retained earnings

    # --- Dividend Policy ---
    "dividend_payout_ratio": 0.20,     # 20% of net income paid as dividends

    # --- Projection horizon ---
    "years":                5,
}

A = ASSUMPTIONS   # shorthand


# ══════════════════════════════════════════════════════════════
# 2.  INCOME STATEMENT
# ══════════════════════════════════════════════════════════════

def build_income_statement(years: int) -> pd.DataFrame:
    """Build a multi-year projected Income Statement."""
    records = []
    for yr in range(1, years + 1):
        revenue = A["revenue_year1"] * ((1 + A["revenue_growth_rate"]) ** (yr - 1))
        cogs    = revenue * A["cogs_pct_revenue"]
        gross_profit = revenue - cogs

        opex    = revenue * A["opex_pct_revenue"]
        ebitda  = gross_profit - opex

        depreciation = A["depreciation"]
        ebit    = ebitda - depreciation

        interest = A["interest_expense"]
        ebt     = ebit - interest

        tax     = max(ebt * A["tax_rate"], 0)
        net_income = ebt - tax

        records.append({
            "Year":           f"Year {yr}",
            "Revenue":        revenue,
            "COGS":           cogs,
            "Gross Profit":   gross_profit,
            "Gross Margin %": gross_profit / revenue * 100,
            "OPEX":           opex,
            "EBITDA":         ebitda,
            "Depreciation":   depreciation,
            "EBIT":           ebit,
            "Interest Expense": interest,
            "EBT":            ebt,
            "Tax":            tax,
            "Net Income":     net_income,
            "Net Margin %":   net_income / revenue * 100,
        })
    return pd.DataFrame(records).set_index("Year")


# ══════════════════════════════════════════════════════════════
# 3.  BALANCE SHEET
# ══════════════════════════════════════════════════════════════

def build_balance_sheet(income_stmt: pd.DataFrame) -> pd.DataFrame:
    """
    Build a multi-year projected Balance Sheet.
    Net Income flows into Retained Earnings each year.
    """
    records = []
    retained_earnings = A["retained_earnings_year0"]
    fixed_assets_gross = A["fixed_assets_gross_year0"]
    accumulated_depreciation = 0.0
    cash = A["cash_year0"]

    for yr_label, row in income_stmt.iterrows():
        revenue    = row["Revenue"]
        net_income = row["Net Income"]
        dividends  = net_income * A["dividend_payout_ratio"]

        # ── CURRENT ASSETS ───────────────────────────────────
        accounts_receivable = revenue * (A["accounts_receivable_days"] / 365)
        inventory           = row["COGS"] * (A["inventory_days"] / 365)
        other_current       = A["other_current_assets"]

        # Simple cash: prior cash + net income - dividends - capex
        cash = cash + net_income - dividends - A["capex_annual"]

        total_current_assets = cash + accounts_receivable + inventory + other_current

        # ── NON-CURRENT ASSETS ───────────────────────────────
        fixed_assets_gross        += A["capex_annual"]
        accumulated_depreciation  += A["depreciation"]
        net_fixed_assets           = fixed_assets_gross - accumulated_depreciation

        total_assets = total_current_assets + net_fixed_assets

        # ── CURRENT LIABILITIES ───────────────────────────────
        accounts_payable = row["COGS"] * (A["accounts_payable_days"] / 365)
        other_cl         = A["other_current_liabilities"]
        total_current_liabilities = accounts_payable + other_cl

        # ── NON-CURRENT LIABILITIES ──────────────────────────
        long_term_debt = A["long_term_debt"]
        total_liabilities = total_current_liabilities + long_term_debt

        # ── EQUITY ───────────────────────────────────────────
        retained_earnings += net_income - dividends
        total_equity       = A["share_capital"] + retained_earnings

        # Balance check: Assets must equal Liabilities + Equity
        balance_diff = total_assets - (total_liabilities + total_equity)

        records.append({
            "Year":                     yr_label,
            # Assets
            "Cash":                     cash,
            "Accounts Receivable":      accounts_receivable,
            "Inventory":                inventory,
            "Other Current Assets":     other_current,
            "Total Current Assets":     total_current_assets,
            "Net Fixed Assets (PP&E)":  net_fixed_assets,
            "Total Assets":             total_assets,
            # Liabilities
            "Accounts Payable":         accounts_payable,
            "Other Current Liabilities": other_cl,
            "Total Current Liabilities": total_current_liabilities,
            "Long-Term Debt":           long_term_debt,
            "Total Liabilities":        total_liabilities,
            # Equity
            "Share Capital":            A["share_capital"],
            "Retained Earnings":        retained_earnings,
            "Total Equity":             total_equity,
            # Totals
            "Total Liabilities + Equity": total_liabilities + total_equity,
            "Balance Check (diff)":     round(balance_diff, 2),
            # Memo
            "Dividends Paid":           dividends,
        })

    return pd.DataFrame(records).set_index("Year")


# ══════════════════════════════════════════════════════════════
# 4.  KEY FINANCIAL RATIOS
# ══════════════════════════════════════════════════════════════

def compute_ratios(income_stmt: pd.DataFrame, balance_sheet: pd.DataFrame) -> pd.DataFrame:
    """Derive key ratios from the two statements."""
    records = []
    for yr in income_stmt.index:
        is_row = income_stmt.loc[yr]
        bs_row = balance_sheet.loc[yr]

        current_ratio   = bs_row["Total Current Assets"] / bs_row["Total Current Liabilities"]
        debt_to_equity  = bs_row["Total Liabilities"] / bs_row["Total Equity"]
        roe             = is_row["Net Income"] / bs_row["Total Equity"] * 100
        roa             = is_row["Net Income"] / bs_row["Total Assets"] * 100
        asset_turnover  = is_row["Revenue"] / bs_row["Total Assets"]
        interest_cover  = is_row["EBIT"] / is_row["Interest Expense"]

        records.append({
            "Year":                yr,
            "Current Ratio":       round(current_ratio, 2),
            "Debt-to-Equity":      round(debt_to_equity, 2),
            "Return on Equity %":  round(roe, 2),
            "Return on Assets %":  round(roa, 2),
            "Asset Turnover":      round(asset_turnover, 2),
            "Interest Coverage":   round(interest_cover, 2),
            "Gross Margin %":      round(is_row["Gross Margin %"], 2),
            "Net Margin %":        round(is_row["Net Margin %"], 2),
        })
    return pd.DataFrame(records).set_index("Year")


# ══════════════════════════════════════════════════════════════
# 5.  PRETTY PRINT
# ══════════════════════════════════════════════════════════════

def fmt(val, decimals=0):
    """Format a number as currency string."""
    if isinstance(val, float) and val != val:
        return "—"
    return f"₹{val:,.{decimals}f}"

def print_statement(title: str, df: pd.DataFrame, currency_cols=None, pct_cols=None):
    print(f"\n{'═'*70}")
    print(f"  {title}")
    print(f"{'═'*70}")
    display = df.copy()
    for col in display.columns:
        if pct_cols and col in pct_cols:
            display[col] = display[col].map(lambda v: f"{v:.1f}%")
        elif currency_cols is None or col in currency_cols:
            display[col] = display[col].map(lambda v: fmt(v) if isinstance(v, (int, float)) else v)
    print(display.T.to_string())

def check_balance(bs: pd.DataFrame):
    print(f"\n{'─'*50}")
    print("  BALANCE SHEET CHECK  (Assets = Liabilities + Equity)")
    print(f"{'─'*50}")
    for yr in bs.index:
        diff = bs.loc[yr, "Balance Check (diff)"]
        status = "✅ BALANCED" if abs(diff) < 1 else f"❌ OUT BY ₹{diff:,.2f}"
        print(f"  {yr}: {status}")


# ══════════════════════════════════════════════════════════════
# 6.  VISUALIZATION
# ══════════════════════════════════════════════════════════════

def plot_model(income_stmt: pd.DataFrame, balance_sheet: pd.DataFrame, ratios: pd.DataFrame):
    years = income_stmt.index.tolist()
    fig, axes = plt.subplots(2, 3, figsize=(17, 10))
    fig.suptitle("Two-Statement Financial Model", fontsize=15, fontweight="bold")

    def bar(ax, data, title, color="#378ADD", ylabel="₹"):
        ax.bar(years, data, color=color, width=0.5)
        ax.set_title(title, fontsize=11)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
            lambda x, _: f"₹{x/1_000:.0f}K" if x < 1_000_000 else f"₹{x/1_000_000:.1f}M"))
        ax.tick_params(axis="x", labelsize=9)
        for rect, val in zip(ax.patches, data):
            ax.text(rect.get_x() + rect.get_width()/2, rect.get_height() * 1.02,
                    f"₹{val/1000:.0f}K", ha="center", va="bottom", fontsize=8)

    # Revenue vs Net Income
    axes[0, 0].bar(years, income_stmt["Revenue"],    color="#B5D4F4", width=0.5, label="Revenue")
    axes[0, 0].bar(years, income_stmt["Net Income"], color="#378ADD", width=0.5, label="Net Income")
    axes[0, 0].set_title("Revenue vs Net Income", fontsize=11)
    axes[0, 0].legend(fontsize=8)
    axes[0, 0].yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"₹{x/1_000:.0f}K"))

    # Gross / Net Margin
    axes[0, 1].plot(years, income_stmt["Gross Margin %"], marker="o", color="#639922", label="Gross Margin")
    axes[0, 1].plot(years, income_stmt["Net Margin %"],   marker="s", color="#D85A30", label="Net Margin")
    axes[0, 1].set_title("Profit Margins (%)", fontsize=11)
    axes[0, 1].set_ylabel("%", fontsize=9)
    axes[0, 1].legend(fontsize=8)
    axes[0, 1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))

    # Balance Sheet composition
    axes[0, 2].stackplot(
        years,
        balance_sheet["Total Current Assets"],
        balance_sheet["Net Fixed Assets (PP&E)"],
        labels=["Current Assets", "Fixed Assets"],
        colors=["#9FE1CB", "#1D9E75"],
    )
    axes[0, 2].set_title("Total Assets Composition", fontsize=11)
    axes[0, 2].legend(fontsize=8)
    axes[0, 2].yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"₹{x/1_000:.0f}K"))

    # Retained Earnings growth
    bar(axes[1, 0], balance_sheet["Retained Earnings"], "Retained Earnings", color="#7F77DD")

    # ROE & ROA
    axes[1, 1].plot(years, ratios["Return on Equity %"], marker="o", color="#534AB7", label="ROE")
    axes[1, 1].plot(years, ratios["Return on Assets %"], marker="s", color="#AFA9EC", label="ROA")
    axes[1, 1].set_title("ROE vs ROA (%)", fontsize=11)
    axes[1, 1].set_ylabel("%", fontsize=9)
    axes[1, 1].legend(fontsize=8)
    axes[1, 1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))

    # Debt-to-Equity
    axes[1, 2].plot(years, ratios["Debt-to-Equity"], marker="D", color="#D85A30", linewidth=2)
    axes[1, 2].set_title("Debt-to-Equity Ratio", fontsize=11)
    axes[1, 2].set_ylabel("Ratio", fontsize=9)
    axes[1, 2].axhline(1.0, color="gray", linestyle="--", linewidth=1, label="1.0x threshold")
    axes[1, 2].legend(fontsize=8)

    plt.tight_layout()
    plt.savefig("two_statement_model.png", dpi=150, bbox_inches="tight")
    print("\nChart saved → two_statement_model.png")
    plt.show()


# ══════════════════════════════════════════════════════════════
# 7.  MAIN
# ══════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("   TWO-STATEMENT COMPANY FINANCIAL MODEL")
    print("   Income Statement  +  Balance Sheet")
    print("=" * 70)

    years = A["years"]

    # Build statements
    income_stmt  = build_income_statement(years)
    balance_sheet = build_balance_sheet(income_stmt)
    ratios        = compute_ratios(income_stmt, balance_sheet)

    # Print Income Statement
    is_pct_cols = ["Gross Margin %", "Net Margin %"]
    is_cur_cols = [c for c in income_stmt.columns if c not in is_pct_cols]
    print_statement("INCOME STATEMENT", income_stmt,
                    currency_cols=is_cur_cols, pct_cols=is_pct_cols)

    # Print Balance Sheet (subset for readability)
    bs_display_cols = [
        "Cash", "Accounts Receivable", "Inventory",
        "Total Current Assets", "Net Fixed Assets (PP&E)", "Total Assets",
        "Accounts Payable", "Total Current Liabilities",
        "Long-Term Debt", "Total Liabilities",
        "Share Capital", "Retained Earnings", "Total Equity",
        "Total Liabilities + Equity", "Dividends Paid",
    ]
    print_statement("BALANCE SHEET", balance_sheet[bs_display_cols])

    # Balance check
    check_balance(balance_sheet)

    # Print Ratios
    print_statement("KEY FINANCIAL RATIOS", ratios,
                    currency_cols=[],
                    pct_cols=["Return on Equity %", "Return on Assets %",
                              "Gross Margin %", "Net Margin %"])

    # Visualize
    print("\nGenerating charts...")
    plot_model(income_stmt, balance_sheet, ratios)

    print("\n✅ Two-Statement Model complete.")
    print("   Tweak the ASSUMPTIONS dict at the top to model any company.\n")


if __name__ == "__main__":
    main()
