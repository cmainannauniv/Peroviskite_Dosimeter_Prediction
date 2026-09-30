import streamlit as st
import pandas as pd
import plotly.express as px
import re

# ==========================================
# 1. MARKET COSTS (2026 Estimates)
# ==========================================
ELEMENT_COSTS = {
    'Cs': 61800.0, 'Rb': 15500.0, 'K': 13.6, 'Na': 2.57, 'Li': 85.6, "Re":87300,
    'Ca': 2.21, 'Sr': 6.68, 'Ba': 0.246,"Mo":40.1,"Mn":1.82,"V":385,"Ru":10600,"Y":31.0,
    'Rh': 147000.0, 'Pd': 49500.0, 'Pt': 27800.0, 'Au': 75430.0, 'Ag': 521.0,"Ta":312,"Zr":37.1,
    'Sc': 3460.0, 'Ge': 1010.0, 'In': 167.0, 'Ga': 148.0, 'Sn': 18.7,"Bi":6.36,"Mg":2.32,
    'Cu': 6.0, 'Ni': 13.9, 'Zn': 2.55, 'Ti': 11.5, 'Co': 32.8, 'Fe': 0.424,"Nb":81.6,"W":35.3,"Tc":100000.0,
    'I': 35.0, 'Br': 4.390, 'Cl': 0.082, 'F': 2.16, 'O': 0.154, 'S': 0.0926, 'Se': 21.4,"Hf":900,"Al":1.79,"Cr":9.4
}

# ==========================================
# 2. DATA PROCESSING
# ==========================================
def parse_formula(formula):
    token_pattern = r'([A-Z][a-z]*|MA|FA|PEA|GUA)(\d*\.?\d*)'
    matches = re.findall(token_pattern, str(formula))
    return {el: (float(count) if count else 1.0) for el, count in matches}

def calculate_cost(formula):
    comp = parse_formula(formula)
    return round(sum(ELEMENT_COSTS.get(el, 10.0) * count for el, count in comp.items()), 2)

@st.cache_data
def load_data():
    try:
        # Fixed path to current directory
        df = pd.read_csv('OUTPUT DATA/Predictions.csv') 
    except FileNotFoundError:
        st.error("Missing 'Predictions.csv'.")
        st.stop()
    
    # Clean column names for the UI
    df.rename(columns={
        'Band_Gap': 'Bandgap',
        'Tolerance_factor': 'Tolerance',
        'Octahedral_factor': 'Octahedral'
    }, inplace=True)
    
    if 'Formation_Energy' in df.columns:
        df = df[df["Formation_Energy"] < 0]
        
    return df

# ==========================================
# 3. FILTERS
# ==========================================
st.set_page_config(page_title="Perovskite Analysis", layout="wide")
st.title("🔬 Perovskite Discovery: Cost vs. Performance")

df = load_data()

st.sidebar.header("🎯 Filter Settings")
bg_range = st.sidebar.slider("Bandgap (eV)", float(df['Bandgap'].min()), float(df['Bandgap'].max()), (1.2, 2.0))

# Fixed quantile and slider for Total_cost
max_cost_val = float(df['Total_cost'].max())
default_cost_val = float(df['Total_cost'].quantile(0.8))
cost_limit = st.sidebar.slider("Max Cost ($/kg)", 0.0, max_cost_val, default_cost_val)

filtered_df = df[
    (df['Bandgap'] >= bg_range[0]) & 
    (df['Bandgap'] <= bg_range[1]) &
    (df['Total_cost'] <= cost_limit)
].copy()

# ==========================================
# 4. VISUALIZATION (THE GRAPH)
# ==========================================
st.subheader("📊 Economic Pareto Front: Cost vs. Bandgap")

if not filtered_df.empty:
    fig = px.scatter(
        filtered_df, 
        x='Bandgap', 
        y='Total_cost',
        color='Crystal_System' if 'Crystal_System' in filtered_df.columns else None,
        hover_data=['Formula_pretty', 'Tolerance'],
        labels={'Bandgap': 'Bandgap (eV)', 'Total_cost': 'Cost ($/kg)'}, # Fixed label key
        template="plotly_white",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No materials match those filter settings. Try broadening your range.")

# ==========================================
# 5. PRETTY TABLE
# ==========================================
st.subheader("📋 Candidate Details")

# Fixed column casing to 'Total_cost'
display_cols = ['Formula_pretty', 'TEF', 'Bandgap', 'Tolerance', 'Octahedral', 'Total_cost']
final_cols = [c for c in display_cols if c in filtered_df.columns]
table_data = filtered_df[final_cols].sort_values('Total_cost').head(5000)

st.dataframe(
    table_data.style.format({
        'Bandgap': "{:.2f} eV",
        'TEF': "{:.3f}",
        'Tolerance': "{:.3f}",
        'Octahedral': "{:.3f}",
        'Total_cost': "${:.2f}"  # Fixed column name here
    }).background_gradient(subset=['Total_cost'], cmap='RdYlGn_r') # Fixed column name here
      .background_gradient(subset=['Bandgap'], cmap='YlGnBu'),
    use_container_width=True
)

st.download_button("Download All Filtered Data", filtered_df[final_cols].to_csv(index=False), "results.csv")