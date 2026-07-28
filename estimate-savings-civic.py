import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

# ==========================================
# CONFIGURATION (Public Sector Frameworks)
# ==========================================

# We store our metrics in a structured dictionary. 
# Update the development costs, forks, and NPM metrics inline below after running
# the specific `scc` commands provided for each framework.
FRAMEWORKS = {
    "USWDS": {
        # 1. Cost to reproduce (Run on USWDS repo: https://github.com/uswds/uswds)
        # Command: `scc --no-min --exclude-dir node_modules,dist,vendor --include-ext scss,js,mjs,html`
        "cost_to_reproduce": 1370828,
        # 2. GitHub Forks (from https://github.com/uswds/uswds)
        "github_forks": 1100,
        # 3. NPM Dependents (from https://www.npmjs.com/package/@uswds/uswds?activeTab=dependents)
        "npm_dependents": 40,
        "color_base": "#31a354" # USWDS Mid Green
    },
    "GOV.UK": {
        # 1. Cost to reproduce (Run on GOV.UK repo: https://github.com/alphagov/govuk-frontend)
        # Command: `scc --no-min --exclude-dir node_modules,dist,docs --include-ext scss,js,mjs,nunjucks`
        "cost_to_reproduce": 1122301,
        # 2. GitHub Forks (from https://github.com/alphagov/govuk-frontend)
        "github_forks": 369,
        # 3. NPM Dependents (from https://www.npmjs.com/package/govuk-frontend?activeTab=dependents)
        "npm_dependents": 127,
        "color_base": "#005ea5" # UK Gov Blue
    },
    "NYSDS (New York)": {
        # 1. Cost to reproduce (Run on NYSDS repo: https://github.com/ITS-HCD/nysds)
        # Command: `scc --no-min --exclude-dir node_modules,dist,docs,public --include-ext scss,js,html`
        "cost_to_reproduce": 339456,
        # 2. GitHub Forks (from https://github.com/ITS-HCD/nysds)
        "github_forks": 4, 
        # 3. NPM Dependents (from package registry if published, else 0)
        "npm_dependents": 3, 
        "color_base": "#e2a829" # NY State Gold
    }
}

# Discount Factors
# Represents the assumed percentage of the total reproduction cost avoided by downstream projects.
DISCOUNT_FACTOR_LOW = 0.10
DISCOUNT_FACTOR_MED = 0.50
DISCOUNT_FACTOR_HIGH = 0.80

OUTPUT_CHART_GROUPED = "civic_design_systems_grouped.png"
OUTPUT_CHART_STACKED = "civic_design_systems_stacked.png"

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
    # 1. Process and structure the data
    processed_data = []
    for name, data in FRAMEWORKS.items():
        total_dependents = data["github_forks"] + data["npm_dependents"]
        cost = data["cost_to_reproduce"]
        
        savings_low = calculate_savings(cost, total_dependents, DISCOUNT_FACTOR_LOW)
        savings_med = calculate_savings(cost, total_dependents, DISCOUNT_FACTOR_MED)
        savings_high = calculate_savings(cost, total_dependents, DISCOUNT_FACTOR_HIGH)
        
        processed_data.append({
            "name": name,
            "cost_to_reproduce": cost,
            "total_dependents": total_dependents,
            "savings": [savings_low, savings_med, savings_high],
            "base_color": data["color_base"]
        })
        
    # Sort the data by the highest savings value (ascending) so the chart scales nicely
    processed_data.sort(key=lambda x: x["savings"][2])

    # ---------------------------------------------------------
    # CHART 1: Grouped Bar Chart
    # ---------------------------------------------------------
    fig1, ax1 = plt.subplots(figsize=(14, 7))
    
    names = [item["name"] for item in processed_data]
    x = np.arange(len(names))
    width = 0.25

    all_values = [val for item in processed_data for val in item["savings"]]
    max_val = max(all_values) if all_values else 1
    min_display_height = max_val * 0.01

    for i, data in enumerate(processed_data):
        color_low = adjust_color_brightness(data["base_color"], 0.2)
        color_med = data["base_color"]
        color_high = adjust_color_brightness(data["base_color"], -0.2)
        
        # Draw the three bars using the 1% visual threshold trick
        plot_vals = [v if v > min_display_height else min_display_height for v in data["savings"]]
        
        rects1 = ax1.bar(x[i] - width, plot_vals[0], width, color=color_low)
        rects2 = ax1.bar(x[i], plot_vals[1], width, color=color_med)
        rects3 = ax1.bar(x[i] + width, plot_vals[2], width, color=color_high)
        
        offset = max_val * 0.02
        for j, rect in enumerate([rects1[0], rects2[0], rects3[0]]):
            actual_val = data["savings"][j]
            ax1.text(rect.get_x() + rect.get_width()/2., rect.get_height() + offset,
                    f'${actual_val/1e6:.1f}M' if actual_val < 1e9 else f'${actual_val/1e9:.1f}B',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Formatting Chart 1
    ax1.set_ylabel('Total Cost Avoidance (USD)')
    ax1.set_title('Civic Design System Savings Comparison\n(Low, Medium, and High Reuse Scenarios)')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f'{item["name"]}\n({item["total_dependents"]:,} reuses)' for item in processed_data])
    ax1.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda y, loc: "{:,}".format(int(y))))
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    
    # Custom Legend (Forced to USWDS Green)
    uswds_color = FRAMEWORKS["USWDS"]["color_base"]
    legend_patches = [
        mpatches.Patch(color=adjust_color_brightness(uswds_color, 0.2), label='Low (10%)'),
        mpatches.Patch(color=uswds_color, label='Med (50%)'),
        mpatches.Patch(color=adjust_color_brightness(uswds_color, -0.2), label='High (80%)')
    ]
    ax1.legend(handles=legend_patches, title="Reuse Scenario", loc='upper left')

    plt.tight_layout()
    plt.savefig(OUTPUT_CHART_GROUPED, dpi=300)
    print(f"Grouped comparative chart saved to: {os.path.abspath(OUTPUT_CHART_GROUPED)}")

    # ---------------------------------------------------------
    # CHART 2: Stacked Multiplier (ROI) Comparison
    # ---------------------------------------------------------
    fig2, ax2 = plt.subplots(figsize=(14, 10))
    
    y_pos = []
    y_labels = []
    
    # Start at y=1 to prevent the bottom row from overlapping the x-axis labels
    current_y = 1 
    
    for data in processed_data:
        name = data["name"]
        cost = data["cost_to_reproduce"]
        base_col = data["base_color"]
        
        scenarios = [
            (f"{name} (Low 10%)", data["savings"][0], adjust_color_brightness(base_col, 0.2)),
            (f"{name} (Med 50%)", data["savings"][1], base_col),
            (f"{name} (High 80%)", data["savings"][2], adjust_color_brightness(base_col, -0.2))
        ]
        
        for label_text, savings_val, row_color in scenarios:
            multiplier = savings_val / cost if cost > 0 else 0
            int_mult = int(multiplier)
            
            # Apply 1% minimum visual width trick for the entire row
            display_val = max(savings_val, min_display_height)
            
            # 1. Base background bar (guarantees the 1% minimum width is visible)
            ax2.barh(current_y, display_val, color=row_color, alpha=0.8, height=0.7)
            
            # 2. Draw actual integer chunks on top
            for m in range(int_mult):
                alpha = 1.0 if m % 2 == 0 else 0.6
                ax2.barh(current_y, cost, left=(m * cost), color=row_color, alpha=alpha, height=0.7)
            
            # 3. Draw the fractional remainder chunk (important for <1x multipliers)
            remainder = savings_val - (int_mult * cost)
            if remainder > 0:
                alpha = 1.0 if int_mult % 2 == 0 else 0.6
                ax2.barh(current_y, remainder, left=(int_mult * cost), color=row_color, alpha=alpha, height=0.7)
                
            end_pos = display_val
            
            # Format text: Show decimals for small multipliers, integers for large ones
            mult_text = f'{multiplier:.1f}x' if multiplier < 10 else f'{int_mult}x'
            ax2.text(end_pos + (max_val * 0.01), current_y, f' {mult_text} Return', va='center', fontweight='bold', fontsize=10, color='#333333')
            
            y_pos.append(current_y)
            y_labels.append(label_text)
            current_y += 1
            
        current_y += 1 # Add gap between frameworks
        
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(y_labels)
    ax2.set_ylim(0, current_y) # Pad bottom and top
    ax2.set_xlabel('Total Cost Avoidance (USD)')
    ax2.set_title('ROI Multiplier Comparison: How many times does the system pay for its own base cost?')
    ax2.get_xaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: f"${x/1e9:.1f}B" if x >= 1e9 else f"${x/1e6:.0f}M"))
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig(OUTPUT_CHART_STACKED, dpi=300)
    print(f"Stacked Multiplier chart saved to: {os.path.abspath(OUTPUT_CHART_STACKED)}")

if __name__ == "__main__":
    generate_report()
