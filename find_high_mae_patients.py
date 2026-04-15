#!/usr/bin/env python3
"""
Script to find patients with high Threshold_MAE values and retrieve their
structure lists and MRN information from related CSV files.
"""

import pandas as pd
from pathlib import Path


def find_high_mae_patients(threshold: float = 0.1, treatment_site: str = None):
    """
    Find patients with Threshold_MAE greater than the specified threshold.

    Args:
        threshold: MAE threshold value (default 0.1)
        treatment_site: Filter by treatment site (e.g., "Head & Neck")

    Returns:
        DataFrame with patient info, structure lists, and MRNs
    """
    # Define file paths
    base_path = Path(__file__).parent
    dose_results_path = base_path / 'dose_evaluation_results.csv'
    filtered_contours_path = base_path / 'Final_Joined_Site_Rx_and_Contours_filtered.csv'
    all_contours_path = base_path / 'Final_Joined_Site_Rx_and_Contours.csv'
    vmat_plans_path = base_path / 'Filtered_VMAT_Plans_Non_Anon_All.csv'

    # Read CSV files
    dose_results = pd.read_csv(dose_results_path)
    filtered_contours = pd.read_csv(filtered_contours_path, encoding='latin-1')
    all_contours = pd.read_csv(all_contours_path, encoding='latin-1')
    vmat_plans = pd.read_csv(vmat_plans_path, encoding='latin-1')

    # If treatment_site is specified, filter dose_results to only include matching patients
    if treatment_site:
        # Get patient IDs that match the treatment site
        site_patients = filtered_contours[filtered_contours['Site'] == treatment_site]
        site_patient_ids = set(site_patients['MRN_Hash'].tolist() + site_patients['FOR_UID_Hash'].tolist())
        dose_results = dose_results[dose_results['Patient_ID'].isin(site_patient_ids)]
        print(f"Filtered to {len(dose_results)} patients with TreatmentSite = '{treatment_site}'")

    # Filter rows where Threshold_MAE > threshold
    high_mae = dose_results[dose_results['Threshold_MAE'] > threshold].copy()
    print(f"Found {len(high_mae)} patients with Threshold_MAE > {threshold}\n")

    results = []

    for _, row in high_mae.iterrows():
        patient_id = row['Patient_ID']

        # Find structure list and target volume from filtered contours
        match_filtered = filtered_contours[
            (filtered_contours['MRN_Hash'] == patient_id) |
            (filtered_contours['FOR_UID_Hash'] == patient_id)
        ]
        structure_list_filtered = match_filtered['Structure_List'].values[0] if len(match_filtered) > 0 else None
        target_volume_id = match_filtered['TargetVolumeId'].values[0] if len(match_filtered) > 0 else None
        site = match_filtered['Site'].values[0] if len(match_filtered) > 0 else None

        # Find structure list from all contours
        match_all = all_contours[
            (all_contours['MRN_Hash'] == patient_id) |
            (all_contours['FOR_UID_Hash'] == patient_id)
        ]
        structure_list_all = match_all['Structure_List'].values[0] if len(match_all) > 0 else None

        # Find MRN from VMAT plans
        match_vmat = vmat_plans[
            (vmat_plans['MRN_HASH'] == patient_id) |
            (vmat_plans['FOR_UID_HASH'] == patient_id)
        ]
        mrn = match_vmat['MRN'].values[0] if len(match_vmat) > 0 else None

        results.append({
            'Patient_ID': patient_id,
            'MAE': row['MAE'],
            'Threshold_MAE': row['Threshold_MAE'],
            'High_Threshold_MAE': row['High_Threshold_MAE'],
            'MRN': mrn,
            'Site': site,
            'TargetVolumeId': target_volume_id,
            'Structure_List_Filtered': structure_list_filtered,
            'Structure_List_Full': structure_list_all
        })

    return pd.DataFrame(results)


def print_patient_details(df: pd.DataFrame):
    """Print detailed information for each patient."""
    for _, row in df.iterrows():
        print("=" * 80)
        print(f"Patient_ID (hash): {row['Patient_ID']}")
        print(f"MRN: {row['MRN']}")
        print(f"Site: {row['Site']}")
        print(f"TargetVolumeId: {row['TargetVolumeId']}")
        print(f"Threshold_MAE: {row['Threshold_MAE']:.4f}")
        print(f"MAE: {row['MAE']:.6f}")
        print(f"High_Threshold_MAE: {row['High_Threshold_MAE']:.4f}")
        print()
        print(f"Structure_List (filtered):")
        print(f"  {row['Structure_List_Filtered']}")
        print()
        print(f"Structure_List (full):")
        print(f"  {row['Structure_List_Full']}")
        print()


def main():
    # Find patients with highest Threshold_MAE for Head & Neck
    treatment_site = "Head & Neck"
    print(f"Finding highest Threshold_MAE for {treatment_site}...\n")

    # Use threshold=0 to get all patients, then find the highest
    results_df = find_high_mae_patients(threshold=0, treatment_site=treatment_site)

    if results_df.empty:
        print(f"No patients found for treatment site: {treatment_site}")
        return

    # Sort by Threshold_MAE descending
    results_df = results_df.sort_values('Threshold_MAE', ascending=False)

    # Get the highest Threshold_MAE patient(s)
    max_threshold_mae = results_df['Threshold_MAE'].max()
    print(f"\nHighest Threshold_MAE for {treatment_site}: {max_threshold_mae:.4f}\n")

    # Show top patients with highest Threshold_MAE
    top_n = 10
    top_results = results_df.head(top_n)

    # Print detailed results for top patients
    print(f"Top {len(top_results)} patients with highest Threshold_MAE:")
    print_patient_details(top_results)

    # Print summary table
    print("\n" + "=" * 80)
    print(f"SUMMARY TABLE - Top {len(top_results)} {treatment_site} Patients by Threshold_MAE")
    print("=" * 80)
    summary = top_results[['Patient_ID', 'MRN', 'Site', 'TargetVolumeId', 'Threshold_MAE', 'Structure_List_Filtered']].copy()
    summary['Threshold_MAE'] = summary['Threshold_MAE'].round(4)
    print(summary.to_string(index=False))

    # Save all results to CSV
    output_path = Path(__file__).parent / 'high_mae_patients.csv'
    results_df.to_csv(output_path, index=False)
    print(f"\nAll results saved to: {output_path}")


if __name__ == '__main__':
    main()
