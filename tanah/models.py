"""Model global dan Gaussian GWR; scaler dipasang hanya pada observasi latih."""
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.neighbors import KNeighborsRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor

class LocalSingularError(ValueError):
    """Rank desain lokal kurang dari jumlah koefisien."""

def estimate(model, param, train, test, x, y, dist):
    scaler = StandardScaler().fit(x[train])
    a, b = scaler.transform(x[train]), scaler.transform(x[test])
    if model == "GWR":
        design = np.column_stack([np.ones(len(a)), a])
        values = []
        for row, i in zip(b, test):
            logw = -0.5 * (dist[i, train] / param) ** 2
            w = np.exp((logw - logw.max()) / 2)
            coef, _, rank, _ = np.linalg.lstsq(design * w[:, None], y[train] * w, rcond=None)
            if rank < design.shape[1]:
                raise LocalSingularError(f"Regresi lokal singular: baris {i}, bandwidth {param} km, rank {rank}/{design.shape[1]}.")
            values.append(np.r_[1, row] @ coef)
        return np.asarray(values)
    if model == "Linear":
        m = LinearRegression()
    elif model == "KNN":
        m = KNeighborsRegressor(param, weights="distance")
    elif model == "Decision Tree":
        m = DecisionTreeRegressor(max_depth=param, min_samples_leaf=3, random_state=124)
    else:
        raise ValueError(f"Model tidak dikenal: {model}")
    return m.fit(a, y[train]).predict(b)

