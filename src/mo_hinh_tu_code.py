import time

import numpy as np


def them_cot_1(X):
    return np.hstack([np.ones((X.shape[0], 1)), X])


class HoiQuyTuyenTinh:
    def fit(self, X, y):
        Xb = them_cot_1(np.asarray(X, dtype=np.float64))
        y = np.asarray(y, dtype=np.float64)
        self.w = np.linalg.solve(Xb.T @ Xb, Xb.T @ y)
        return self

    def predict(self, X):
        return them_cot_1(np.asarray(X, dtype=np.float64)) @ self.w


class HoiQuyGradientDescent:
    def __init__(self, toc_do_hoc=0.1, so_vong=500, kich_thuoc_lo=None, seed=42):
        self.eta = toc_do_hoc
        self.so_vong = so_vong
        self.lo = kich_thuoc_lo
        self.seed = seed

    def fit(self, X, y):
        Xb = them_cot_1(np.asarray(X, dtype=np.float64))
        y = np.asarray(y, dtype=np.float64)
        n = len(y)
        rng = np.random.default_rng(self.seed)
        self.w = np.zeros(Xb.shape[1])
        self.lich_su = []
        for _ in range(self.so_vong):
            if self.lo:
                chi_so = rng.choice(n, self.lo, replace=False)
                Xl, yl = Xb[chi_so], y[chi_so]
            else:
                Xl, yl = Xb, y
            sai = Xl @ self.w - yl
            self.w -= self.eta * (2.0 / len(yl)) * (Xl.T @ sai)
            self.lich_su.append(float(np.mean((Xb @ self.w - y) ** 2)))
        return self

    def predict(self, X):
        return them_cot_1(np.asarray(X, dtype=np.float64)) @ self.w


class HoiQuyRidge:
    def __init__(self, lam=1.0):
        self.lam = lam

    def fit(self, X, y):
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        self.x_tb, self.y_tb = X.mean(axis=0), y.mean()
        Xc, yc = X - self.x_tb, y - self.y_tb
        self.w = np.linalg.solve(Xc.T @ Xc + self.lam * np.eye(X.shape[1]), Xc.T @ yc)
        self.b = self.y_tb - self.x_tb @ self.w
        return self

    def predict(self, X):
        return np.asarray(X, dtype=np.float64) @ self.w + self.b


def nhan_rbf(A, B, gamma):
    A = np.asarray(A, dtype=np.float64)
    B = np.asarray(B, dtype=np.float64)
    kc = (A ** 2).sum(axis=1)[:, None] + (B ** 2).sum(axis=1)[None, :] - 2.0 * A @ B.T
    return np.exp(-gamma * np.maximum(kc, 0.0))


class KernelRidgeRBF:
    def __init__(self, gamma=0.02, lam=1.0, lo_du_doan=10000):
        self.gamma = gamma
        self.lam = lam
        self.lo = lo_du_doan

    def fit(self, X, y):
        t = time.time()
        self.X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        self.y_tb = y.mean()
        K = nhan_rbf(self.X, self.X, self.gamma)
        self.alpha = np.linalg.solve(K + self.lam * np.eye(len(K)), y - self.y_tb)
        self.thoi_gian_fit = time.time() - t
        return self

    def predict(self, X):
        X = np.asarray(X, dtype=np.float64)
        out = np.empty(len(X))
        for i in range(0, len(X), self.lo):
            out[i:i + self.lo] = nhan_rbf(X[i:i + self.lo], self.X, self.gamma) @ self.alpha + self.y_tb
        return out
