CREATE DATABASE rbi_banking;
SHOW TABLES;

## NPA Trend by Bank Group (Year-wise Gross NPA Closing)
SELECT
    n.year,
    ROUND(SUM(CASE WHEN b.bank_type = 'PSB'     THEN n.gross_npa_closing ELSE 0 END) / 100000, 2) AS psb_gross_npa_lakh_cr,
    ROUND(SUM(CASE WHEN b.bank_type = 'Private' THEN n.gross_npa_closing ELSE 0 END) / 100000, 2) AS pvt_gross_npa_lakh_cr,
    ROUND(SUM(CASE WHEN b.bank_type = 'Foreign' THEN n.gross_npa_closing ELSE 0 END) / 100000, 2) AS foreign_gross_npa_lakh_cr,
    ROUND(SUM(n.gross_npa_closing) / 100000, 2) AS total_gross_npa_lakh_cr
FROM npa_movement n
LEFT JOIN (
    SELECT DISTINCT bank_name,
        CASE
            WHEN bank_name IN ('STATE BANK OF INDIA','BANK OF BARODA','BANK OF INDIA',
                'CANARA BANK','PUNJAB NATIONAL BANK','UNION BANK OF INDIA',
                'INDIAN BANK','CENTRAL BANK OF INDIA','UCO BANK',
                'BANK OF MAHARASHTRA','PUNJAB AND SIND BANK','INDIAN OVERSEAS BANK')
            THEN 'PSB'
            WHEN bank_name IN ('HDFC BANK','ICICI BANK','AXIS BANK','KOTAK MAHINDRA BANK',
                'INDUSIND BANK','YES BANK','FEDERAL BANK','IDBI BANK',
                'BANDHAN BANK','RBL BANK','IDFC FIRST BANK','SOUTH INDIAN BANK',
                'KARUR VYSYA BANK','CITY UNION BANK','DCB BANK','CSB BANK',
                'NAINITAL BANK','JAMMU AND KASHMIR BANK','KARNATAKA BANK',
                'TAMILNAD MERCANTILE BANK','DHANLAXMI BANK')
            THEN 'Private'
            ELSE 'Foreign'
        END AS bank_type
    FROM npa_movement
) b ON n.bank_name = b.bank_name
GROUP BY n.year
ORDER BY n.year;

## NPA Ratio Trend — PSB vs Private (from bank_ratios)
SELECT
    n.year,
    ROUND(SUM(CASE WHEN n.bank_name IN (
        'STATE BANK OF INDIA','BANK OF BARODA','BANK OF INDIA','CANARA BANK',
        'PUNJAB NATIONAL BANK','UNION BANK OF INDIA','INDIAN BANK',
        'CENTRAL BANK OF INDIA','UCO BANK','BANK OF MAHARASHTRA',
        'PUNJAB AND SIND BANK','INDIAN OVERSEAS BANK')
        THEN n.net_npa_closing ELSE 0 END) / 100000, 2) AS net_npa_psb_lakh_cr,
    ROUND(SUM(CASE WHEN n.bank_name IN (
        'HDFC BANK','ICICI BANK','AXIS BANK','KOTAK MAHINDRA BANK',
        'INDUSIND BANK','YES BANK','FEDERAL BANK','IDBI BANK',
        'BANDHAN BANK','RBL BANK','IDFC FIRST BANK')
        THEN n.net_npa_closing ELSE 0 END) / 100000, 2) AS net_npa_pvt_lakh_cr,
    ROUND(SUM(n.net_npa_closing) / 100000, 2) AS net_npa_all_lakh_cr
FROM npa_movement n
WHERE n.net_npa_closing IS NOT NULL
GROUP BY n.year
ORDER BY n.year;

## NPA Write-offs vs Recoveries (Systemic Cleanup Analysis)
SELECT
    year,
    ROUND(SUM(gross_npa_addition)  / 100000, 2) AS fresh_slippages_lakh_cr,
    ROUND(SUM(gross_npa_reduction) / 100000, 2) AS total_reductions_lakh_cr,
    ROUND(SUM(gross_npa_writeoff)  / 100000, 2) AS writeoffs_lakh_cr,
    ROUND(
        SUM(gross_npa_writeoff) * 100.0 / NULLIF(SUM(gross_npa_reduction), 0)
    , 1) AS writeoff_pct_of_reduction
FROM npa_movement
WHERE year >= 2015
GROUP BY year
ORDER BY year;

## ROA Comparison: PSB vs Private Banks
SELECT
    year,
    ROUND(AVG(CASE WHEN bank_name IN (
        'STATE BANK OF INDIA','BANK OF BARODA','BANK OF INDIA','CANARA BANK',
        'PUNJAB NATIONAL BANK','UNION BANK OF INDIA','INDIAN BANK',
        'CENTRAL BANK OF INDIA','UCO BANK','BANK OF MAHARASHTRA',
        'PUNJAB AND SIND BANK','INDIAN OVERSEAS BANK')
        THEN roa END), 2) AS avg_roa_psb,
    ROUND(AVG(CASE WHEN bank_name IN (
        'HDFC BANK','ICICI BANK','AXIS BANK','KOTAK MAHINDRA BANK',
        'INDUSIND BANK','YES BANK','FEDERAL BANK',
        'BANDHAN BANK','RBL BANK','IDFC FIRST BANK')
        THEN roa END), 2) AS avg_roa_pvt,
    ROUND(AVG(roa), 2) AS avg_roa_all
FROM bank_ratios
WHERE roa IS NOT NULL AND roa BETWEEN -5 AND 5
GROUP BY year
ORDER BY year;

## CRAR Trend — Capital Adequacy by Bank
SELECT
    year,
    bank_name,
    ROUND(basel3_tier1, 2) AS tier1_crar,
    ROUND(basel3_tier2, 2) AS tier2_crar,
    ROUND(crar_total,   2) AS total_crar,
    CASE
        WHEN crar_total >= 12 THEN 'Well Capitalised'
        WHEN crar_total >= 9  THEN 'Adequately Capitalised'
        WHEN crar_total > 0   THEN 'Under-Capitalised'
        ELSE 'No Data'
    END AS capitalisation_status
FROM crar
WHERE year >= 2018
ORDER BY year, crar_total ASC;

## Credit-Deposit Ratio Trend
SELECT
    year,
    ROUND(AVG(CASE WHEN bank_name IN (
        'STATE BANK OF INDIA','BANK OF BARODA','BANK OF INDIA','CANARA BANK',
        'PUNJAB NATIONAL BANK','UNION BANK OF INDIA','INDIAN BANK',
        'CENTRAL BANK OF INDIA','UCO BANK','BANK OF MAHARASHTRA',
        'PUNJAB AND SIND BANK','INDIAN OVERSEAS BANK')
        THEN credit_deposit_ratio END), 1) AS cdr_psb,
    ROUND(AVG(CASE WHEN bank_name IN (
        'HDFC BANK','ICICI BANK','AXIS BANK','KOTAK MAHINDRA BANK',
        'INDUSIND BANK','FEDERAL BANK','BANDHAN BANK','IDFC FIRST BANK')
        THEN credit_deposit_ratio END), 1) AS cdr_pvt,
    ROUND(AVG(credit_deposit_ratio), 1) AS cdr_all
FROM bank_ratios
WHERE credit_deposit_ratio BETWEEN 30 AND 120
GROUP BY year
ORDER BY year;

## Net Interest Margin(NIM) Trend
SELECT
    year,
    ROUND(AVG(CASE WHEN bank_name IN (
        'STATE BANK OF INDIA','BANK OF BARODA','BANK OF INDIA','CANARA BANK',
        'PUNJAB NATIONAL BANK','UNION BANK OF INDIA','INDIAN BANK',
        'CENTRAL BANK OF INDIA','UCO BANK','BANK OF MAHARASHTRA',
        'PUNJAB AND SIND BANK','INDIAN OVERSEAS BANK')
        THEN nim END), 2) AS nim_psb,
    ROUND(AVG(CASE WHEN bank_name IN (
        'HDFC BANK','ICICI BANK','AXIS BANK','KOTAK MAHINDRA BANK',
        'INDUSIND BANK','FEDERAL BANK','BANDHAN BANK','IDFC FIRST BANK')
        THEN nim END), 2) AS nim_pvt,
    ROUND(AVG(nim), 2) AS nim_all
FROM bank_ratios
WHERE nim BETWEEN 0 AND 10
GROUP BY year
ORDER BY year;

## Sensitive Sector Exposure — Real Estate vs Capital Markets	
SELECT
    year,
    ROUND(SUM(real_estate_exposure)    / 100000, 2) AS real_estate_lakh_cr,
    ROUND(SUM(capital_market_exposure) / 100000, 2) AS capital_market_lakh_cr,
    ROUND(SUM(commodities_exposure)    / 100000, 2) AS commodities_lakh_cr,
    ROUND(SUM(total_sensitive_exposure)/ 100000, 2) AS total_sensitive_lakh_cr
FROM sensitive_sectors
GROUP BY year
ORDER BY year;

##Top 10 Banks by Gross NPA
SELECT
    bank_name,
    year,
    ROUND(gross_npa_closing / 100000, 2) AS gross_npa_lakh_cr,
    ROUND(net_npa_closing   / 100000, 2) AS net_npa_lakh_cr,
    ROUND(gross_npa_writeoff/ 100000, 2) AS writeoffs_lakh_cr
FROM npa_movement
WHERE year = (SELECT MAX(year) FROM npa_movement)
  AND gross_npa_closing IS NOT NULL
ORDER BY gross_npa_closing DESC
LIMIT 10;

## Bank Profitability Scorecard
SELECT
    bank_name,
    year,
    ROUND(roa,                  2) AS roa,
    ROUND(roe,                  2) AS roe,
    ROUND(nim,                  2) AS nim,
    ROUND(credit_deposit_ratio, 1) AS credit_deposit_ratio,
    ROUND(cost_of_deposits,     2) AS cost_of_deposits,
    ROUND(cost_of_funds,        2) AS cost_of_funds,
    ROUND(crar_total,           2) AS crar_total,
    ROUND(profit_per_employee,  2) AS profit_per_employee
FROM bank_ratios
WHERE year = (SELECT MAX(year) FROM bank_ratios)
  AND roa IS NOT NULL
ORDER BY roa DESC;

## NPA Recovery Rate by Bank
SELECT
    bank_name,
    ROUND(SUM(gross_npa_reduction) * 100.0 /
          NULLIF(SUM(gross_npa_opening + gross_npa_addition), 0), 1
    ) AS recovery_rate_pct,
    ROUND(SUM(gross_npa_writeoff)  * 100.0 /
          NULLIF(SUM(gross_npa_opening + gross_npa_addition), 0), 1
    ) AS writeoff_rate_pct,
    ROUND(SUM(gross_npa_closing) / 100000, 2) AS current_npa_lakh_cr
FROM npa_movement
WHERE year BETWEEN 2018 AND 2025
GROUP BY bank_name
HAVING SUM(gross_npa_opening) > 1000   -- filter tiny/new banks
ORDER BY recovery_rate_pct DESC
LIMIT 15;

## Banking Sector Health Score
SELECT
    b.year,
    ROUND(AVG(b.roa),                  2) AS avg_roa,
    ROUND(AVG(b.nim),                  2) AS avg_nim,
    ROUND(AVG(b.credit_deposit_ratio), 1) AS avg_cdr,
    ROUND(AVG(b.crar_total),           2) AS avg_crar,
    ROUND(AVG(b.cost_of_funds),        2) AS avg_cost_of_funds,
    ROUND(SUM(e.total_income) / 100000, 2) AS total_sector_income_lakh_cr,
    ROUND(SUM(a.total_advances) / 100000, 2) AS total_advances_lakh_cr
FROM bank_ratios b
LEFT JOIN earnings e ON b.bank_name = e.bank_name AND b.year = e.year
LEFT JOIN assets   a ON b.bank_name = a.bank_name AND b.year = a.year
WHERE b.roa  BETWEEN -5 AND 5
  AND b.nim  BETWEEN 0  AND 10
  AND b.crar_total > 0
GROUP BY b.year
ORDER BY b.year;

SELECT * FROM rbi_banking.npa_movement;
SELECT * FROM rbi_banking.bank_ratios;
SELECT * FROM rbi_banking.group_ratios;
SELECT * FROM rbi_banking.sensitive_sectors;
SELECT * FROM rbi_banking.assets;
SELECT * FROM rbi_banking.earnings;
SELECT * FROM rbi_banking.crar;

SELECT DISTINCT bank_name FROM rbi_banking.npa_movement 
WHERE bank_name LIKE '%STATE BANK%' 
   OR bank_name LIKE '%HDFC%'
   OR bank_name LIKE '%BARODA%'
ORDER BY bank_name;

SELECT DISTINCT bank_name FROM rbi_banking.npa_movement
ORDER BY bank_name;

SELECT *,
  CASE 
    WHEN bank_name IN (
        'STATE BANK OF INDIA','STATE BANK OF INDIA*','BANK OF BARODA',
        'BANK OF BARODA*','BANK OF INDIA','BANK OF MAHARASHTRA',
        'CANARA BANK','CANARA BANK*','PUNJAB NATIONAL BANK',
        'PUNJAB NATIONAL BANK*','UNION BANK OF INDIA','UNION BANK OF INDIA*',
        'INDIAN BANK','INDIAN BANK*','CENTRAL BANK OF INDIA','UCO BANK',
        'PUNJAB AND SIND BANK','INDIAN OVERSEAS BANK','ALLAHABAD BANK',
        'ANDHRA BANK','CORPORATION BANK','DENA BANK',
        'ORIENTAL BANK OF COMMERCE','SYNDICATE BANK',
        'UNITED BANK OF INDIA','VIJAYA BANK',
        'STATE BANK OF BIKANER AND JAIPUR','STATE BANK OF HYDERABAD',
        'STATE BANK OF INDORE','STATE BANK OF MYSORE',
        'STATE BANK OF PATIALA','STATE BANK OF SAURASHTRA',
        'STATE BANK OF TRAVANCORE')
    THEN 'Public Sector Banks'
    WHEN bank_name IN (
        'HDFC BANK LTD.','ICICI BANK LIMITED','AXIS BANK LIMITED',
        'KOTAK MAHINDRA BANK LTD.','INDUSIND BANK LTD','YES BANK LTD.',
        'FEDERAL BANK LTD','IDBI BANK LIMITED','IDBI BANK LIMITED#',
        'BANDHAN BANK LIMITED','RBL BANK LTD','IDFC FIRST BANK LIMITED',
        'IDFC BANK LIMITED','CITY UNION BANK LIMITED','DCB BANK LIMITED',
        'CSB BANK LIMITED','KARNATAKA BANK LTD','KARUR VYSYA BANK LTD',
        'SOUTH INDIAN BANK LTD','TAMILNAD MERCANTILE BANK LTD',
        'DHANLAXMI BANK LIMITED','JAMMU & KASHMIR BANK LTD',
        'NAINITAL BANK LTD','LAKSHMI VILAS BANK LTD',
        'ING VYSYA BANK LTD','CENTURION BANK OF PUNJAB LTD.',
        'BANK OF RAJASTHAN LTD')
    THEN 'Private Banks'
    ELSE 'Foreign Banks'
  END AS bank_group
FROM rbi_banking.npa_movement;