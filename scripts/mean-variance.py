import scipy.optimize
import numpy as np
from datetime import datetime

# Hardcoded values replacing worksheet data
cashInfo = ['Cash', '', '0.5%', '0%']
spyInfo = ['SPY', '', '10%', '16%']
tltInfo = ['TLT', '', '4%', '12%']
gldInfo = ['GLD', '', '6%', '18%']
gbtcInfo = ['GBTC', '', '15%', '65%']

# Correlation values
corrInfo = [
    ['-0.3'],   # spy_tlt
    ['0.4'],    # spy_gld
    ['0.6'],    # spy_gbtc
    ['-0.1'],   # tlt_gld
    ['-0.2'],   # tlt_gbtc
    ['0.3'],    # gld_gbtc
]

# RETURNS
asset_returns = np.array([
    # cash: 0.5% per year (also represents borrowing costs)
    float(cashInfo[2].strip('%')) / 100,
    float(spyInfo[2].strip('%')) / 100,     # SPY
    float(tltInfo[2].strip('%')) / 100,    # TLT
    float(gldInfo[2].strip('%')) / 100,   # GLDM
    float(gbtcInfo[2].strip('%')) / 100,     # GBTC
])

# VOLATILITY
asset_volatility = np.array([
    .0,     # cash: 0% volatility
    float(spyInfo[3].strip('%')) / 100,    # SPY
    float(tltInfo[3].strip('%')) / 100,   # TLT
    float(gldInfo[3].strip('%')) / 100,    # GLDM
    float(gbtcInfo[3].strip('%')) / 100,   # GBTC
])

# CORRELATIONS
spy_tlt = float(corrInfo[0][0])
spy_gld = float(corrInfo[1][0])
spy_gbtc = float(corrInfo[2][0])
tlt_gld = float(corrInfo[3][0])
tlt_gbtc = float(corrInfo[4][0])
gld_gbtc = float(corrInfo[5][0])
asset_correlations = np.array([
    [1,              0,              0,              0,              0],
    [0,              1,              spy_tlt,        spy_gld,        spy_gbtc],
    [0,              spy_tlt,        1,              tlt_gld,        tlt_gbtc],
    [0,              spy_gld,        tlt_gld,        1,              gld_gbtc],
    [0,              spy_gbtc,       tlt_gbtc,       gld_gbtc,       1],
])

# GAMMA: Coefficient of risk aversion
# 1.0 = Highly risk seeking. Maximizes returns irrespective of risk
# 3.0 = Risk neutral. Maximizes returns at moderate risk level
# 5.0+ = Highly risk averse. Maximizes returns at very low risk level
gamma = 3.0

# Cash / asset upper and lower bounds
cash_bounds = (-1, 1)
spy_bounds = (0.001, np.inf)
tlt_bounds = (0.001, np.inf)
gld_bounds = (0.001, .15)
gbtc_bounds = (.001, .1)


def mean_and_std(asset_weights):
    r = np.dot(asset_weights, asset_returns)
    std = asset_weights * asset_volatility
    std = std.reshape((1, len(std)))
    var = np.matmul(np.matmul(std, asset_correlations), std.transpose())
    return r, var[0][0]**.5


def utility(asset_weights):
    mean, std = mean_and_std(asset_weights)
    return mean - .5 * gamma * std**2


solution = scipy.optimize.minimize(
    lambda x: -utility(x),
    x0=np.full_like(asset_returns, .5),
    bounds=[cash_bounds] + [spy_bounds] +
    [tlt_bounds] + [gld_bounds] + [gbtc_bounds],
    constraints=[{'type': 'eq', 'fun': lambda x: x.sum() - 1}, ],
    method='SLSQP',
    tol=1e-20
)

print(solution.message)
print("asset weights: ", solution.x)
print("return: {:6.2%}, std: {:6.2%}".format(*mean_and_std(solution.x)))

# Print current timestamp instead of updating worksheet
print("Calculation completed at:", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))