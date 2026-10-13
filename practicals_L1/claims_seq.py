"""The claims-sequence transformer of Lecture 2, Practical 1, packaged for re-use in Lecture 3.

Everything here is explained step by step in L2_P1_claims_transformer. Only the code is collected.
"""
import math, time
import numpy as np, pandas as pd
import torch, torch.nn as nn, torch.nn.functional as F
from sklearn.metrics import log_loss, roc_auc_score
import course_utils as cu

MAXLEN = 128


class Vocab:
    def __init__(self, ev):
        self.CT = sorted(ev.care_type.unique()); self.DG = sorted(ev.diagnosis_group.unique())
        self.cost_edges = np.quantile(ev.gross_cost, np.linspace(0, 1, 17)[1:-1])
        self.sizes = {"ct": len(self.CT) + 1, "dg": len(self.DG) + 1, "cb": 18, "mb": 37}


def load_events():
    ev = cu.load("events")[["person_id", "date", "year", "care_type", "diagnosis_group", "gross_cost"]]
    ev["month"] = pd.to_datetime(ev.date).dt.month
    V = Vocab(ev)
    ev["ct"] = ev.care_type.map({c: i + 1 for i, c in enumerate(V.CT)})
    ev["dg"] = ev.diagnosis_group.map({c: i + 1 for i, c in enumerate(V.DG)})
    ev["cb"] = np.digitize(ev.gross_cost, V.cost_edges) + 1
    return ev, V


def build_origin(ev, py, T):
    """Sequences of the 36 months up to the end of year T; label = inpatient stay in T+1."""
    base = py[(py.year == T) & (py.insured_days >= 360)][["person_id", "age", "sex"]]
    nxt = py[py.year == T + 1][["person_id", "n_inpatient_stays"]]
    base = base.merge(nxt, on="person_id").reset_index(drop=True)
    base["label"] = (base.n_inpatient_stays > 0).astype(int)
    w = ev[ev.year.between(T - 2, T) & ev.person_id.isin(base.person_id)].copy()
    w["mb"] = (T - w.year) * 12 + (12 - w.month)
    w = w.sort_values(["person_id", "date"])
    w["r"] = w.groupby("person_id").cumcount(ascending=False)
    w = w[w.r < MAXLEN]
    row = w.person_id.map(dict(zip(base.person_id, base.index))).values
    col = MAXLEN - 1 - w.r.values
    X = np.zeros((len(base), MAXLEN, 4), dtype=np.int64)
    X[row, col, 0], X[row, col, 1], X[row, col, 2], X[row, col, 3] = w.ct, w.dg, w.cb, w.mb + 1
    static = np.stack([(base.age.values - 45) / 22, (base.sex == "F").astype(float)], 1).astype(np.float32)
    return dict(base=base, X=X, static=static, y=base.label.values)


def attention(q, k, v, pad_mask):
    scores = q @ k.transpose(-2, -1) / math.sqrt(q.shape[-1])
    scores = scores.masked_fill(pad_mask[:, None, None, :], float("-inf"))
    w = torch.softmax(scores, dim=-1)
    return w @ v, w


class MultiHeadAttention(nn.Module):
    def __init__(self, d, h, p=0.1):
        super().__init__(); self.h, self.dk = h, d // h
        self.qkv = nn.Linear(d, 3 * d); self.out = nn.Linear(d, d); self.drop = nn.Dropout(p)

    def forward(self, x, pad):
        B, n, d = x.shape
        q, k, v = self.qkv(x).view(B, n, 3, self.h, self.dk).permute(2, 0, 3, 1, 4)
        o, w = attention(q, k, v, pad)
        return self.drop(self.out(o.transpose(1, 2).reshape(B, n, d))), w


class Block(nn.Module):
    def __init__(self, d, h, p=0.1):
        super().__init__()
        self.ln1, self.ln2 = nn.LayerNorm(d), nn.LayerNorm(d)
        self.mha = MultiHeadAttention(d, h, p)
        self.ffn = nn.Sequential(nn.Linear(d, 2 * d), nn.GELU(), nn.Dropout(p), nn.Linear(2 * d, d), nn.Dropout(p))

    def forward(self, x, pad):
        a, w = self.mha(self.ln1(x), pad)
        x = x + a
        return x + self.ffn(self.ln2(x)), w


class ClaimsEncoder(nn.Module):
    def __init__(self, sizes, d=64, heads=4, layers=2):
        super().__init__()
        self.emb = nn.ModuleDict({f: nn.Embedding(n, d, padding_idx=0) for f, n in sizes.items()})
        self.cls = nn.Parameter(torch.zeros(1, 1, d)); self.static = nn.Linear(2, d)
        self.blocks = nn.ModuleList([Block(d, heads) for _ in range(layers)])
        self.ln = nn.LayerNorm(d); self.head = nn.Linear(d, 1)

    def encode(self, X, s):
        e = sum(self.emb[f](X[..., i]) for i, f in enumerate(["ct", "dg", "cb", "mb"]))
        x = torch.cat([self.cls.expand(len(X), 1, -1) + self.static(s)[:, None], e], 1)
        pad = torch.cat([torch.zeros(len(X), 1, dtype=torch.bool), X[..., 0] == 0], 1)
        W = []
        for b in self.blocks:
            x, w = b(x, pad); W.append(w)
        return self.ln(x), W

    def forward(self, X, s):
        return self.head(self.encode(X, s)[0][:, 0]).squeeze(1)


def length_batches(X, idx, bs):
    L = (X[idx, :, 0] > 0).sum(1)
    order = idx[torch.argsort(L)]
    return [order[i:i + bs] for i in range(0, len(order), bs)]


def trim(Xb):
    L = int((Xb[..., 0] > 0).sum(1).max())
    return Xb[:, -max(L, 1):]


def logits(m, X, S, bs=512):
    m.eval(); out = torch.zeros(len(X))
    with torch.no_grad():
        for b in length_batches(X, torch.arange(len(X)), bs):
            out[b] = m(trim(X[b]), S[b])
    return out.numpy()


def fit(m, Xtr, Str, ytr, Xva, Sva, yva, epochs=3, lr=1e-3, bs=128, seed=2026):
    torch.manual_seed(seed)
    opt = torch.optim.AdamW(m.parameters(), lr=lr, weight_decay=1e-2); best = (np.inf, None)
    for ep in range(epochs):
        t0 = time.time(); m.train()
        bl = length_batches(Xtr, torch.arange(len(ytr)), bs)
        for k in torch.randperm(len(bl)):
            j = bl[k]
            loss = F.binary_cross_entropy_with_logits(m(trim(Xtr[j]), Str[j]), ytr[j])
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(m.parameters(), 1.0); opt.step()
        p = 1 / (1 + np.exp(-logits(m, Xva, Sva))); lv = log_loss(yva.numpy(), p)
        print(f"epoch {ep+1}: validation log-loss {lv:.4f}, AUC {roc_auc_score(yva.numpy(), p):.3f} ({time.time()-t0:.0f} s)")
        if lv < best[0]: best = (lv, {k: v.clone() for k, v in m.state_dict().items()})
    m.load_state_dict(best[1]); return m
