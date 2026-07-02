import sys
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def recommend_funds(risk_appetite, top_n=3):
    scorecard = pd.read_csv(ROOT / 'fund_scorecard.csv')
    fm = pd.read_csv(ROOT / 'data' / 'processed' / '01_fund_master.csv')
    data = scorecard.merge(
        fm[['amfi_code','scheme_name','risk_category','expense_ratio_pct','category','sub_category']],
        on='amfi_code', how='left')
    valid = ['Low', 'Moderate', 'Moderately High', 'High', 'Very High']
    if risk_appetite not in valid:
        raise ValueError(f'risk_appetite must be one of {valid}')
    filtered = data[data['risk_category'] == risk_appetite].sort_values('sharpe_ratio', ascending=False).head(top_n)
    cols = ['overall_rank','scheme_name','category','sub_category','risk_category','sharpe_ratio','cagr_3yr_pct','expense_ratio_pct','fund_score']
    return filtered[cols].reset_index(drop=True)

if __name__ == '__main__':
    appetite = sys.argv[1] if len(sys.argv) > 1 else 'Moderate'
    print(f'Top 3 recommendations for risk appetite: {appetite}')
    print(recommend_funds(appetite).to_string(index=False))