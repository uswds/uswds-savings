import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

# ==========================================
# CONFIGURATION (USWDS Federal Telemetry)
# ==========================================

# 1. Base Cost to Reproduce USWDS (Run on USWDS repo: https://github.com/uswds/uswds)
# Command: `scc --no-min --exclude-dir node_modules,dist,vendor --include-ext scss,js,mjs,html`
COST_TO_REPRODUCE_USD = 1370828

# 2. Total Ecosystem Reach (Live Federal Sites)
# Based on official submitted counts of executive branch sites using USWDS.
# Note: The GSA casual scan counts 985 (https://github.com/GSA/site-scanning-analysis/blob/main/reports/uswds.csv)
# but official submitted counts verify at least 1,095.
FEDERAL_SITES_USING_USWDS = 1095

# 3. Discount Factors (Reuse Percentage)
# Represents the assumed percentage of the total reproduction cost avoided by each federal site.
DISCOUNT_FACTOR_LOW = 0.10   # Extremely conservative (10% reuse)
DISCOUNT_FACTOR_MED = 0.50   # Moderate (50% reuse)
DISCOUNT_FACTOR_HIGH = 0.80  # High adoption (80% reuse)

# Brand Colors
COLOR_USWDS_BASE = "#31a354" # USWDS Mid Green

# Output Configuration
OUTPUT_CHART_BAR = "uswds_federal_savings_bar.png"
OUTPUT_CHART_STACKED = "uswds_federal_roi_stacked.png"

# ==========================================
# EXECUTION
# ==========================================

def calculate_savings(cost, total_dependents, discount):
    return cost * total_dependents * discount

def adjust_color_brightness(hex_color, amount):
    """Utility to generate lighter/darker shades for the Low/Med/High bars"""
    import colorsys
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
    v = max(0, min(1, v + amount))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'

def generate_report():
    savings_low = calculate_savings(COST_TO_REPRODUCE_USD, FEDERAL_SITES_USING_USWDS, DISCOUNT_FACTOR_LOW)
    savings_med = calculate_savings(COST_TO_REPRODUCE_USD, FEDERAL_SITES_USING_USWDS, DISCOUNT_FACTOR_MED)
    savings_high = calculate_savings(COST_TO_REPRODUCE_USD, FEDERAL_SITES_USING_USWDS, DISCOUNT_FACTOR_HIGH)

    print("==========================================================================")
    print("                 USWDS FEDERAL IMPACT & SAVINGS REPORT                    ")
    print("==========================================================================")
    print(f"Base Cost to Reproduce:   ${COST_TO_REPRODUCE_USD:,.2f}")
    print(f"Verified Federal Sites:   {FEDERAL_SITES_USING_USWDS:,}")
    print("--------------------------------------------------------------------------")
    print("Estimated Cost Avoidance Scenarios:")
    print(f"  Low    (10% reuse): ${savings_low:,.2f}")
    print(f"  Medium (50% reuse): ${savings_med:,.2f}")
    print(f"  High   (80% reuse): ${savings_high:,.2f}")
    print("==========================================================================")

    color_low = adjust_color_brightness(COLOR_USWDS_BASE, 0.2)
    color_med = COLOR_USWDS_BASE
    color_high = adjust_color_brightness(COLOR_USWDS_BASE, -0.2)

    # ---------------------------------------------------------
    # CHART 1: Standard Bar Chart Comparison
    # ---------------------------------------------------------
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    
    labels = ['Base Cost (1x)', 'Low (10%)', 'Med (50%)', 'High (80%)']
    values = [COST_TO_REPRODUCE_USD, savings_low, savings_med, savings_high]
    colors = ['#7f7f7f', color_low, color_med, color_high]

    # Apply 1% visual minimum so the base cost is visible against the massive savings
    max_val = max(values)
    min_display_height = max_val * 0.01
    plot_values = [v if v > min_display_height else min_display_height for v in values]

    bars = ax1.bar(labels, plot_values, color=colors)

    for bar, actual_val in zip(bars, values):
        yval = bar.get_height()
        offset = max_val * 0.02
        ax1.text(bar.get_x() + bar.get_width()/2., yval + offset,
                f'${actual_val/1e6:.1f}M' if actual_val < 1e9 else f'${actual_val/1e9:.1f}B',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax1.set_ylabel('Total Cost Avoidance (USD)')
    ax1.set_title(f'USWDS Federal Impact\nSavings Across {FEDERAL_SITES_USING_USWDS:,} Executive Branch Sites')
    ax1.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda y, loc: "{:,}".format(int(y))))
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig(OUTPUT_CHART_BAR, dpi=300)
    print(f"\nBar chart saved to: {os.path.abspath(OUTPUT_CHART_BAR)}")

    # ---------------------------------------------------------
    # CHART 2: Stacked Multiplier (ROI)
    # ---------------------------------------------------------
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    
    scenarios = [
        ("High (80%)", savings_high, color_high),
        ("Med (50%)", savings_med, color_med),
        ("Low (10%)", savings_low, color_low)
    ]
    
    y_pos = [0, 1, 2]
    
    for idx, (label_text, savings_val, row_color) in enumerate(scenarios):
        multiplier = savings_val / COST_TO_REPRODUCE_USD if COST_TO_REPRODUCE_USD > 0 else 0
        int_mult = int(multiplier)
        
        display_val = max(savings_val, min_display_height)
        
        # Base background bar (guarantees the 1% minimum width is visible)
        ax2.barh(y_pos[idx], display_val, color=row_color, alpha=0.8, height=0.6)
        
        # Draw integer chunks
        for m in range(int_mult):
            alpha = 1.0 if m % 2 == 0 else 0.6
            ax2.barh(y_pos[idx], COST_TO_REPRODUCE_USD, left=(m * COST_TO_REPRODUCE_USD), color=row_color, alpha=alpha, height=0.6)
        
        # Draw remainder chunk
        remainder = savings_val - (int_mult * COST_TO_REPRODUCE_USD)
        if remainder > 0:
            alpha = 1.0 if int_mult % 2 == 0 else 0.6
            ax2.barh(y_pos[idx], remainder, left=(int_mult * COST_TO_REPRODUCE_USD), color=row_color, alpha=alpha, height=0.6)
            
        mult_text = f'{multiplier:.1f}x' if multiplier < 10 else f'{int_mult}x'
        ax2.text(display_val + (max_val * 0.01), y_pos[idx], f' {mult_text} Return', va='center', fontweight='bold', fontsize=10, color='#333333')

    ax2.set_yticks(y_pos)
    ax2.set_yticklabels([s[0] for s in scenarios])
    ax2.set_xlabel('Total Cost Avoidance (USD)')
    ax2.set_title('ROI Multiplier: How many times USWDS pays for its own base cost')
    ax2.get_xaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: f"${x/1e9:.1f}B" if x >= 1e9 else f"${x/1e6:.0f}M"))
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig(OUTPUT_CHART_STACKED, dpi=300)
    print(f"Stacked Multiplier chart saved to: {os.path.abspath(OUTPUT_CHART_STACKED)}")

if __name__ == "__main__":
    generate_report()
