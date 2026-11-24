"""Model NumPy dari Paper_Machine_Learning.ipynb, sel 1 dan 2."""
import numpy as np


def haversine_km(lat1, lon1, lat2, lon2, radius_km=6371.0088):
    """
    Menghitung matriks jarak Haversine (km) antara titik (lat1, lon1) dan (lat2, lon2).
    """
    lat1_r = np.radians(np.asarray(lat1, dtype=float))[:, None]
    lon1_r = np.radians(np.asarray(lon1, dtype=float))[:, None]
    lat2_r = np.radians(np.asarray(lat2, dtype=float))[None, :]
    lon2_r = np.radians(np.asarray(lon2, dtype=float))[None, :]

    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r

    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1_r) * np.cos(lat2_r) * np.sin(dlon / 2.0) ** 2
    c = 2.0 * np.arcsin(np.minimum(1.0, np.sqrt(a)))
    return radius_km * c

def fit_standardizer(X):
    """Menghitung mean dan std per kolom (hanya dari data latih)."""
    X = np.asarray(X, dtype=float)
    mean = np.mean(X, axis=0)
    std = np.std(X, axis=0, ddof=0)
    std = np.where(std == 0, 1.0, std)
    return mean, std

def apply_standardizer(X, mean, std):
    """Menerapkan transformasi standardisasi ke matriks fitur."""
    return (np.asarray(X, dtype=float) - mean) / std

# ==============================================================================
# MODEL 1: OLS REGRESSOR (LEAST SQUARES + MATRIX SOLVE)
# ==============================================================================
class OLSRegressorScratch:
    def __init__(self, reg_lambda=1e-8):
        self.reg_lambda = reg_lambda
        self.beta = None

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        X_design = np.column_stack([np.ones(X.shape[0]), X])
        xtx = X_design.T @ X_design + self.reg_lambda * np.eye(X_design.shape[1])
        xty = X_design.T @ y
        self.beta = np.linalg.solve(xtx, xty)
        return self

    def predict(self, X):
        X = np.asarray(X, dtype=float)
        X_design = np.column_stack([np.ones(X.shape[0]), X])
        return X_design @ self.beta


# ==============================================================================
# MODEL 2: KNN REGRESSOR (EUCLIDEAN DISTANCE & WEIGHTED/UNIFORM)
# ==============================================================================
class KNNRegressorScratch:
    def __init__(self, k=5, weighted=True, eps=1e-9):
        self.k = k
        self.weighted = weighted
        self.eps = eps
        self.X_train = None
        self.y_train = None

    def fit(self, X, y):
        self.X_train = np.asarray(X, dtype=float)
        self.y_train = np.asarray(y, dtype=float)
        return self

    def predict(self, X):
        X_test = np.asarray(X, dtype=float)
        preds = np.zeros(X_test.shape[0], dtype=float)
        n_train = len(self.y_train)

        for i, x_q in enumerate(X_test):
            dists = np.sqrt(np.sum((self.X_train - x_q) ** 2, axis=1))
            k_eff = min(self.k, n_train)
            idx_sorted = np.argsort(dists)[:k_eff]
            d_k = dists[idx_sorted]
            y_k = self.y_train[idx_sorted]

            if not self.weighted:
                preds[i] = np.mean(y_k)
            else:
                zero_mask = d_k <= self.eps
                if np.any(zero_mask):
                    preds[i] = np.mean(y_k[zero_mask])
                else:
                    weights = 1.0 / d_k
                    preds[i] = np.sum(weights * y_k) / np.sum(weights)
        return preds


# ==============================================================================
# MODEL 3: DECISION TREE REGRESSOR (CART MSE VARIANCE REDUCTION)
# ==============================================================================
class DecisionTreeRegressorScratch:
    def __init__(self, max_depth=4, min_samples_leaf=3, min_samples_split=6):
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.min_samples_split = min_samples_split
        self.root = None

    def _mse(self, y):
        if len(y) == 0:
            return 0.0
        return float(np.mean((y - np.mean(y)) ** 2))

    def _best_split(self, X, y):
        n_samples, n_features = X.shape
        best_gain = -1.0
        best_feat = None
        best_thresh = None
        parent_mse = self._mse(y)

        for feat in range(n_features):
            vals = np.unique(X[:, feat])
            if len(vals) <= 1:
                continue
            thresholds = (vals[:-1] + vals[1:]) / 2.0
            for thresh in thresholds:
                left_mask = X[:, feat] <= thresh
                right_mask = ~left_mask
                n_l, n_r = np.sum(left_mask), np.sum(right_mask)
                if n_l < self.min_samples_leaf or n_r < self.min_samples_leaf:
                    continue
                weighted_child_mse = (n_l / n_samples) * self._mse(y[left_mask]) + (
                    n_r / n_samples
                ) * self._mse(y[right_mask])
                gain = parent_mse - weighted_child_mse
                if gain > best_gain:
                    best_gain = gain
                    best_feat = feat
                    best_thresh = float(thresh)

        return best_feat, best_thresh, best_gain

    def _build_tree(self, X, y, depth):
        leaf_val = float(np.mean(y))
        if depth >= self.max_depth or len(y) < self.min_samples_split or np.std(y) == 0:
            return {"is_leaf": True, "value": leaf_val}

        feat, thresh, gain = self._best_split(X, y)
        if feat is None or gain <= 0:
            return {"is_leaf": True, "value": leaf_val}

        left_mask = X[:, feat] <= thresh
        right_mask = ~left_mask
        return {
            "is_leaf": False,
            "feature": feat,
            "threshold": thresh,
            "left": self._build_tree(X[left_mask], y[left_mask], depth + 1),
            "right": self._build_tree(X[right_mask], y[right_mask], depth + 1),
        }

    def fit(self, X, y):
        self.root = self._build_tree(
            np.asarray(X, dtype=float), np.asarray(y, dtype=float), depth=0
        )
        return self

    def _predict_row(self, row, node):
        if node["is_leaf"]:
            return node["value"]
        if row[node["feature"]] <= node["threshold"]:
            return self._predict_row(row, node["left"])
        return self._predict_row(row, node["right"])

    def predict(self, X):
        X_arr = np.asarray(X, dtype=float)
        return np.array([self._predict_row(row, self.root) for row in X_arr])


# ==============================================================================
# MODEL 4: GWR REGRESSOR (LOCAL WLS + HAVERSINE + GAUSSIAN/BISQUARE KERNEL)
# ==============================================================================
class GWRRegressorScratch:
    def __init__(self, bandwidth=20.0, kernel="gaussian", adaptive=False, reg_lambda=1e-3):
        self.bandwidth = bandwidth
        self.kernel = kernel
        self.adaptive = adaptive
        self.reg_lambda = reg_lambda
        self.X_train = None
        self.y_train = None
        self.coords_train = None

    def _kernel_weights(self, dists, bw):
        if not self.adaptive:
            h = max(float(bw), 1e-6)
            if self.kernel == "gaussian":
                return np.exp(-0.5 * (dists / h) ** 2)
            elif self.kernel == "bisquare":
                w = np.zeros_like(dists, dtype=float)
                mask = dists < h
                w[mask] = (1.0 - (dists[mask] / h) ** 2) ** 2
                return w
            else:
                raise ValueError(f"Kernel tidak dikenal: {self.kernel}")
        else:
            k_nn = int(min(max(2, round(bw)), len(dists)))
            sorted_d = np.sort(dists)
            h_adap = max(float(sorted_d[k_nn - 1]) * 1.000001, 1e-6)
            if self.kernel == "bisquare":
                w = np.zeros_like(dists, dtype=float)
                mask = dists < h_adap
                w[mask] = (1.0 - (dists[mask] / h_adap) ** 2) ** 2
                return w
            return np.exp(-0.5 * (dists / h_adap) ** 2)

    def fit(self, X, y, coords):
        self.X_train = np.asarray(X, dtype=float)
        self.y_train = np.asarray(y, dtype=float)
        self.coords_train = np.asarray(coords, dtype=float)
        return self

    def predict(self, X, coords):
        X_test = np.asarray(X, dtype=float)
        coords_test = np.asarray(coords, dtype=float)
        X_design_train = np.column_stack([np.ones(self.X_train.shape[0]), self.X_train])
        X_design_test = np.column_stack([np.ones(X_test.shape[0]), X_test])

        dist_matrix = haversine_km(
            coords_test[:, 0],
            coords_test[:, 1],
            self.coords_train[:, 0],
            self.coords_train[:, 1],
        )

        preds = np.zeros(X_test.shape[0], dtype=float)
        n_params = X_design_train.shape[1]

        for i in range(X_test.shape[0]):
            w = self._kernel_weights(dist_matrix[i], self.bandwidth)
            if np.sum(w) <= 1e-12:
                w = np.ones_like(w)

            # Local WLS via sqrt weighting: (X_w)^T (X_w) beta = (X_w)^T y_w
            w_sqrt = np.sqrt(w)[:, None]
            X_w = X_design_train * w_sqrt
            y_w = self.y_train * w_sqrt.ravel()

            xtwx = X_w.T @ X_w + self.reg_lambda * np.eye(n_params)
            xtwy = X_w.T @ y_w
            beta_local = np.linalg.solve(xtwx, xtwy)
            preds[i] = float(X_design_test[i] @ beta_local)

        return preds
