MY_TICKERS = [
    # AI Companies
    'NVDA', 'AMD', 'IBM', 'GOOGL', 'MSFT', 'AAPL', 'INTC', 'BABA', 'PLTR', 'CRM',
    'HPE', 'DELL', 'ADBE', 'AI', 'SHOP', 'TWLO', 'SPOT', 'Z', 'DDOG', 'PINS',
    'SNOW',

    # Semiconductor Companies
    'ASML', 'MU', 'AMAT', 'LRCX', 'AVGO', 'QCOM', 'ON', 'SMCI', 'CRUS',

    # Technology Companies
    'AMZN', 'META', 'CSCO', 'ORCL', 'ANET', 'PANW', 'DLTR', 'HPQ', 'CRWD', 'MDB',
    'GTLB', 'SQ', 'ZM', 'PYPL', 'RBLX', 'CFLT', 'ADSK', 'KEYS', 'NOW', 'SOFI',
    'RIVN', 'QS', 'TEAM', 'ROKU', 'AFRM', 'MNDY',

    # Consumer Discretionary Companies
    'TSLA', 'HD', 'NKE', 'MCD', 'DIS', 'LULU', 'ETSY', 'ULTA', 'CMG', 'TGT',
    'BBY', 'MAR', 'RCL', 'LUV',

    # Energy Companies
    'XOM', 'CVX', 'COP',

    # Healthcare Companies
    'JNJ', 'PFE', 'MRNA', 'GILD',

    # Financial Companies
    'JPM', 'BAC', 'WFC', 'C', 'GS', 'V', 'MA',

    # Consumer Staples Companies
    'PG', 'KO', 'PEP', 'WMT', 'COST',

    # Communication Services Companies
    'T', 'VZ', 'TMUS', 'CMCSA', 'NFLX',

    # Utilities Companies
    'DUK', 'SO', 'EXC',

    # Materials Companies
    'DOW', 'MLM', 'VMC'
]

ALL_TICKERS = [
    'A', 'AAL', 'AAP', 'AAPL', 'AIG', 'AIZ', 'ALB', 'ALK', 'ALL', 'AMAT', 'AMD',
    'AMCR', 'AMED', 'AMP', 'AMT', 'AMZN', 'ANET', 'AON', 'APA', 'APAM', 'APD',
    'APTV', 'ARE', 'AVGO', 'AWK', 'B', 'BA', 'BAC', 'BAX', 'BBY', 'BDX', 'BEN',
    'BIG', 'BIO', 'BK', 'BKR', 'BLK', 'BMY', 'BR', 'BSX', 'BWA', 'BXP', 'C',
    'CAG', 'CAH', 'CAR', 'CAT', 'CB', 'CBOE', 'CBRE', 'CCL', 'CDNS', 'CDW', 'CE',
    'CF', 'CFG', 'CHTR', 'CHWY', 'CI', 'CINF', 'CL', 'CLX', 'CMA', 'CMG', 'CMI', 'CMS',
    'CNA', 'CNC', 'CNP', 'COF', 'COO', 'COP', 'COST', 'COTY', 'CPB', 'CPRI', 'CRL',
    'CRM', 'CROX', 'CSCO', 'CME', 'CMTL', 'CNQ', 'CNP', 'COO', 'COP', 'COST', 'COTY',
    'CPB', 'CRWD', 'CSX', 'CTAS', 'CTRA', 'CTSH', 'CVS', 'CWH', 'CWT', 'D', 'DAL',
    'DD', 'DHR', 'DLTR', 'DOV', 'DOW', 'DRI', 'DTE', 'DVA', 'DVN', 'DXCM', 'EBAY',
    'ECL', 'ED', 'EFX', 'EIX', 'EL', 'EMN', 'EMR', 'ENB', 'ETN', 'ETR', 'EVRG', 
    'EXAS', 'EXC', 'EXPD', 'F', 'FAST', 'FC', 'FIS', 'FISV', 'FITB', 'FIVN', 'FL',
    'FMC', 'FND', 'FOXA', 'FOX', 'FRT', 'FTI', 'FTV', 'GD', 'GE', 'GILD', 'GIS',
    'GL', 'GLW', 'GME', 'GNRC', 'GOOGL', 'GPC', 'GPN', 'GPS', 'GRMN', 'GS', 'GWW',
    'HAL', 'HAS', 'HBI', 'HCA', 'HCC', 'HCP', 'HD', 'HES', 'HIG', 'HII', 'HLT', 
    'HMC', 'HPE', 'HP', 'HST', 'HSY', 'HUBS', 'HUM', 'IBM', 'ICE', 'IDXX', 'IEX',
    'IFF', 'ILMN', 'INCY', 'INTU', 'IP', 'IR', 'IRM', 'ISRG', 'IT', 'ITW', 'IVZ',
    'J', 'JAZZ', 'JBHT', 'JCI', 'JELD', 'JNJ', 'JPM', 'JWN', 'K', 'KEY', 'KHC',
    'KMB', 'KMI', 'KMX', 'KO', 'KR', 'KSS', 'L', 'LB', 'LDOS', 'LEN', 'LH', 
    'LHX', 'LIN', 'LKQ', 'LLY', 'LMT', 'LNC', 'LOW', 'LUV', 'LVS', 'M', 'MA',
    'MAC', 'MCD', 'MCHP', 'MCK', 'MCO', 'MDLZ', 'MDT', 'MET', 'MFC', 'MHK', 'MKTX',
    'MLM', 'MMC', 'MMM', 'MNST', 'MO', 'MPW', 'MRK', 'MRO', 'MS', 'MSCI', 'MSFT',
    'MTB', 'MTCH', 'MTD', 'MU', 'NAVI', 'NDAQ', 'NDSN', 'NEE', 'NEM', 'NFLX', 'NKE',
    'NMR', 'NOC', 'NOW', 'NRG', 'NSC', 'NTAP', 'NTRS', 'NUE', 'NVDA', 'NVO', 'NVR',
    'NXST', 'O', 'ODFL', 'OHI', 'OI', 'OKE', 'OMC', 'ORCL', 'OXY', 'PAYC', 'PAYX',
    'PBI', 'PCG', 'PDP', 'PEG', 'PEP', 'PFE', 'PFG', 'PG', 'PGR', 'PH', 'PLD',
    'PM', 'PNC', 'PNW', 'POOL', 'PPL', 'PRGO', 'PRU', 'PSA', 'PSX', 'QGEN', 'QRVO',
    'R', 'RCL', 'REG', 'RF', 'RH', 'RHI', 'RJF', 'RL', 'RMD', 'ROK', 'ROP', 'ROST',
    'RRC', 'RSG', 'S', 'SAIC', 'SBAC', 'SBUX', 'SCHW', 'SEE', 'SEIC', 'SHW', 'SJM',
    'SLB', 'SLG', 'SNA', 'SNPS', 'SO', 'SPG', 'SPGI', 'SRE', 'STI', 'STT', 'STZ',
    'SWK', 'SWKS', 'SYF', 'SYK', 'SYY', 'T', 'TAP', 'TDG', 'TEL', 'TFC', 'TFX',
    'TGT', 'THC', 'TJX', 'TMUS', 'TMO', 'TRIP', 'TROW', 'TRV', 'TSCO', 'TSLA', 'TTWO',
    'TXN', 'UNH', 'UNP', 'UPS', 'URBN', 'USB', 'V', 'VFC', 'VLO', 'VMC', 'VNO',
    'VRSN', 'VZ', 'WBA', 'WBD', 'WDC', 'WELL', 'WFC', 'WMT', 'WRB', 'WST', 'WU',
    'WYNN', 'XEL', 'XOM', 'XPO', 'YUM', 'ZBH', 'ZBRA', 'ZION', 'ZTS'
]