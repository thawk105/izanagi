# -*- coding: utf-8 -*-
"""Direct Serialization Graph (Adya) の構築と cycle 検出。

理論 (roadmap §3.1 Tier1):
  committed trx を節点、共有オブジェクトへの競合アクセスを辺とする有向グラフ。
  辺は全て「a が直列順序で b より前」を意味する (a -> b):
    ww : a が版 V を書き、b が同キーの次版を書いた             (write-depends)
    wr : a が版 V を書き、b がその V を読んだ                   (read-depends)
    rw : a が版 V を読み、b が同キーで V の **直後版** を書いた (anti-dependency)
  **DSG が非巡回 ⇔ serializable。** cycle が 1 本でもあれば non-serializable。
  - G0  : ww だけで閉じた cycle
  - G1c : wr/ww から成り rw を含まない cycle (wr を 1 本以上含む)
  - G2  : rw (anti-dependency) を 1 本以上含む cycle  ← SI が許し serializable が
          許さない現象 (write-skew)。「G2 まで見る」= rw を含む cycle を捕まえる。

版順序: 同一キー上では版ID (epoch,tid) が全順序を成し producer を一意に決める
(ww 競合で tid が単調増加。trace-hook で版重複 0 を実測)。rw の「直後版」は
この全順序上の immediate successor 一つだけを使う (それ以降は ww で推移的に届く)。
"""
from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple

from .model import (GENESIS, RW, WR, WW, Anomaly, CycleEdge, EdgeReason,
                    Integrity, Txn, Version)


class DSG:
    """trace から構築した依存グラフ。辺の type/witness は軽量化のため**保持せず**、
    cycle witness を見つけた後にその数本だけ再構成する (数百万辺の type を全保持
    するとメモリを食うため)。"""

    def __init__(self, txns: List[Txn]):
        self.txns = txns
        self.by_id: Dict[int, Txn] = {t.txid: t for t in txns}
        # (key, version) -> 産んだ trx の txid
        self.producer: Dict[Tuple[str, Version], int] = {}
        # key -> その上の版の昇順リスト (real のみ。genesis は含めない)
        self.versions: Dict[str, List[Version]] = {}
        # 軽量隣接 (type を捨てた純粋な有向グラフ)。SCC 検出にこれだけ使う
        self.adj: Dict[int, Set[int]] = defaultdict(set)
        self.integrity = Integrity()
        self._build()

    # ---- 構築 ----

    def _build(self) -> None:
        per_key: Dict[str, List[Version]] = defaultdict(list)
        for t in self.txns:
            # commit が genesis 番兵 (1,0) と衝突する trx は非物理 (Silo の tid は 1 始まり)。
            # この版を産むと「genesis 読み」と区別できず wr 辺が落ちるため integrity 違反として弾く
            # (= verdict は indeterminate になる)。FIX2 と対で安全側に倒す。
            if t.commit == GENESIS:
                self.integrity.genesis_commits += 1
                self.integrity.notes.append(
                    f"txid {t.txid} commits at genesis sentinel (1,0) (non-physical)")
            for w in t.writes:
                kv = (w.key, t.commit)
                if kv in self.producer and self.producer[kv] != t.txid:
                    self.integrity.version_dups += 1
                    self.integrity.notes.append(
                        f"version dup: key={w.key} ver={t.commit} "
                        f"by txid {self.producer[kv]} and {t.txid}")
                else:
                    self.producer[kv] = t.txid
                per_key[w.key].append(t.commit)
        for k, vs in per_key.items():
            self.versions[k] = sorted(set(vs))

        self._add_read_edges()
        self._add_ww_edges()

    def _add(self, u: int, v: int) -> None:
        if u != v:                       # 自己ループ (RMW で自分が直後版を書く等) は辺にしない
            self.adj[u].add(v)

    def _add_read_edges(self) -> None:
        prod = self.producer
        for t in self.txns:
            tid = t.txid
            for r in t.reads:
                k, rv = r.key, r.ver
                # wr: 読んだ版そのものを書いた producer -> 読み手。
                # **genesis 判定は「値が (1,0) か」でなく「producer が居るか」で行う** (FIX2)。
                # genesis (1,0) は誰も書かないので producer 不在 → wr 辺なし。逆に万一 (1,0) を
                # 書いた trx が居れば producer が居るので wr 辺を張る (落とさない)。非 genesis
                # なのに producer 不在 = orphan (abort 版の dirty read 等) として integrity に記録。
                p = prod.get((k, rv))
                if p is not None:
                    if p != tid:
                        self._add(p, tid)
                elif rv != GENESIS:
                    self.integrity.orphan_reads += 1
                # rw (anti-dependency): 読んだ版の直後版を書いた trx へ 読み手 -> 上書き手
                vs = self.versions.get(k)
                if vs:
                    idx = bisect_right(vs, rv)
                    if idx < len(vs):
                        w_tx = prod.get((k, vs[idx]))
                        if w_tx is not None and w_tx != tid:
                            self._add(tid, w_tx)

    def _add_ww_edges(self) -> None:
        prod = self.producer
        for k, vs in self.versions.items():
            for i in range(len(vs) - 1):
                a = prod.get((k, vs[i]))
                b = prod.get((k, vs[i + 1]))
                if a is not None and b is not None:
                    self._add(a, b)

    @property
    def n_edges(self) -> int:
        return sum(len(s) for s in self.adj.values())

    # ---- cycle 検出 (Tarjan SCC, iterative) ----

    def _sccs(self) -> List[List[int]]:
        """非自明な (size>1) SCC のみ返す。自己ループは辺にしていないので
        singleton SCC は cycle ではない。"""
        index: Dict[int, int] = {}
        low: Dict[int, int] = {}
        on_stack: Dict[int, bool] = {}
        stack: List[int] = []
        counter = 0
        out: List[List[int]] = []

        for root in list(self.adj.keys()):
            if root in index:
                continue
            work: List[Tuple[int, "object"]] = [(root, iter(self.adj.get(root, ())))]
            index[root] = low[root] = counter
            counter += 1
            stack.append(root)
            on_stack[root] = True
            while work:
                node, it = work[-1]
                advanced = False
                for w in it:
                    if w not in index:
                        index[w] = low[w] = counter
                        counter += 1
                        stack.append(w)
                        on_stack[w] = True
                        work.append((w, iter(self.adj.get(w, ()))))
                        advanced = True
                        break
                    elif on_stack.get(w):
                        if index[w] < low[node]:
                            low[node] = index[w]
                if advanced:
                    continue
                if low[node] == index[node]:
                    comp: List[int] = []
                    while True:
                        x = stack.pop()
                        on_stack[x] = False
                        comp.append(x)
                        if x == node:
                            break
                    if len(comp) > 1:
                        out.append(comp)
                work.pop()
                if work:
                    parent = work[-1][0]
                    if low[node] < low[parent]:
                        low[parent] = low[node]
        return out

    def _shortest_cycle(self, scc: Set[int]) -> List[int]:
        """SCC 内の (ある節点 s を通る) 最短 cycle を BFS で取り、節点列で返す。
        非自明 SCC では必ず存在する。返りは [s, ..., u] (閉じる辺 u->s は含めず)。"""
        s = min(scc)
        parent: Dict[int, Optional[int]] = {s: None}
        q = deque([s])
        while q:
            u = q.popleft()
            for v in self.adj.get(u, ()):
                if v not in scc:
                    continue
                if v == s:
                    path = [u]
                    x = u
                    while parent[x] is not None:
                        x = parent[x]  # type: ignore[assignment]
                        path.append(x)
                    path.reverse()
                    return path
                if v not in parent:
                    parent[v] = u
                    q.append(v)
        return [s]  # 到達不能 — 理論上起きない

    # ---- witness 辺の再構成 (type と key/版を取り戻す) ----

    def _reasons(self, u: int, v: int) -> List[EdgeReason]:
        ut, vt = self.by_id[u], self.by_id[v]
        reasons: List[EdgeReason] = []
        u_writes = {w.key: ut.commit for w in ut.writes}
        v_writes = {w.key: vt.commit for w in vt.writes}

        # ww: u の版の直後版を v が書いた
        for k in u_writes.keys() & v_writes.keys():
            vs = self.versions.get(k)
            if not vs:
                continue
            iu = bisect_left(vs, u_writes[k])
            if iu < len(vs) and vs[iu] == u_writes[k] and iu + 1 < len(vs) \
                    and vs[iu + 1] == v_writes[k]:
                reasons.append(EdgeReason(WW, k, u_writes[k], v_writes[k]))

        # wr: u が書いた版そのものを v が読んだ
        for r in vt.reads:
            if r.key in u_writes and r.ver == u_writes[r.key]:
                reasons.append(EdgeReason(WR, r.key, u_writes[r.key], None))

        # rw: u が読んだ版の直後版を v が書いた
        for r in ut.reads:
            vs = self.versions.get(r.key)
            if not vs or r.key not in v_writes:
                continue
            idx = bisect_right(vs, r.ver)
            if idx < len(vs) and vs[idx] == v_writes[r.key]:
                reasons.append(EdgeReason(RW, r.key, r.ver, v_writes[r.key]))
        return reasons

    @staticmethod
    def _classify(edges: List[CycleEdge]) -> str:
        """cycle を G0/G1c/G2 に分類する。

        **realizable な (物理的に起こりうる) trace では戻り値は常に G2。** 証明:
        大域順序を commit (epoch,tid) の辞書式順とすると、ww は版順=commit 順なので
        前向き (a.commit<b.commit)、wr も b が a の commit 済み版を読むので前向き。
        commit 順を**減少**させられるのは rw だけ。cycle は始点に戻る以上、減少辺を
        最低1本含む → 必ず rw を含む → G2。よって G0 (ww のみ)/G1c (wr のみ) は
        realizable trace では出ない。G0/G1c 枝は **非 realizable な手製/破損 trace**
        (例: 複数 trx が版スタンプを共有) でのみ到達するが、verdict は cycle の有無
        (= total==0) だけで決まり分類に依存しないので無害。詳細は
        tests/fixtures/README.md と output/insights/。
        """
        all_types = {t for e in edges for t in e.types}
        if RW in all_types:
            return "G2"
        if WR in all_types:
            return "G1c"
        return "G0"

    def anomalies(self, max_report: Optional[int] = None) -> Tuple[List[Anomaly], int]:
        """検出した anomaly のリストと、全 cycle (SCC) 数を返す。
        max_report で報告本数を絞る (全数は第2返り値)。"""
        sccs = self._sccs()
        total = len(sccs)
        # 大きい順より「小さく読みやすい witness」を優先したいので size 昇順
        sccs.sort(key=len)
        out: List[Anomaly] = []
        for comp in sccs:
            if max_report is not None and len(out) >= max_report:
                break
            scc_set = set(comp)
            nodes = self._shortest_cycle(scc_set)
            edges: List[CycleEdge] = []
            ring = list(zip(nodes, nodes[1:] + nodes[:1]))
            for a, b in ring:
                reasons = self._reasons(a, b)
                if not reasons:
                    self.integrity.notes.append(
                        f"witness edge {a}->{b} had no reconstructable reason")
                edges.append(CycleEdge(src=a, dst=b, reasons=reasons))
            out.append(Anomaly(cycle=nodes, phenomenon=self._classify(edges),
                               edges=edges))
        return out, total
