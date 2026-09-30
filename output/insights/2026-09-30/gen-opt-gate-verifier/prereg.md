# 事前登録 — 正しさ関門の記録と判定器 ([T-2884]) の再検証の発火条件と生死確認の期待

authority: none
default_effect: no-state-change

- 登録: 2026-09-30、wave `dev-wave-t2884-gate-verifier` (branch `worktree-dev-wave-t2884-gate-verifier`)。段 4 裁定の §3・§4 の写し。**計算ノードの投入と判定器の実走より前に commit する。** この commit より後に得た結果でこの file を書き換えない (訂正は追記で行う)。
- 設計の正本: `output/insights/2026-09-29/gen-opt-correctness-gate/README.md` (§3.2〜§3.5、§5.4、末尾の訂正節)。U0: `output/insights/2026-09-29/gen-opt-gate-liveness/README.md`。

## 1. 判定器の意味の版

- 本 wave の前の判定器 (`orchestrator/verifier/`) を意味の版 1、本 wave で `gate_<thid>.log` の照合 (D1・D2a・D2b・D5) を足した判定器を意味の版 2 とする。版は判定器の定数として持ち、gate の照合が有効な判定結果に載せる。gate file が無く要求もしない判定結果の形は版 1 と同じにする。

## 2. 再検証の発火条件

1. 版 1 の判定器が出した判定は、記録どおり残す。再判定も certified への昇格もしない。
2. 版 2 で読み直す対象は、gate file を持つ trace に限る。repo 内の campaign (CCBench の pin C `68106660`) の trace は gate file を持たないので対象外 (版 2 でも要求しない呼び出しは同じ判定を返すことを test で固定する)。repo 外の U0 (md_5) と Silo 修正 wave の trace archive は gate file を持つが certified の主張に使われていないので、今は読み直さない。後の wave がそれらを主張に使うときは版 2 以上で読み直す。
3. 本 wave の生死確認 (§3) は版 2 (gate の要求あり) で判定する。
4. 意味の版が上がるたびに、それより前の版の記録は昇格させない。新しい版を要する主張は、保持した原 trace と gate archive から読み直す。
5. gen-opt の候補の certified は、版 2 以上・gate の要求あり・D5 成立・D1/D2a/D2b (全 key) の違反 0・既存の検査 (commit 件数、枠、X/P) と巡回なし、をすべて満たすときだけとする。

## 3. 生死確認の期待 (計算ノード、各条件 1 job、W-rmw・W-blind を各 1 回)

共通の flags は U0 と同じ (`ycsb_tuple_num=200 ycsb_zipf_skew=0.9 ycsb_rratio=50 ycsb_max_ope=5 thread_num=4 extime=1 clocks_per_us=1800`、`KEY_SORT` 既定 0、W-rmw は `ycsb_rmw=true`、W-blind は false)。判定器は本 wave の production CLI に `--require-gate-witness` を付けて呼ぶ。

| 条件 | build | 期待 (両 workload とも) |
|---|---|---|
| S | U1 の tip (Silo 修正なし) | 到達不能 0、D1 全項 0、D2a 0、D2b (i)+(ii) ≥ 1、巡回 0、verdict indeterminate |
| X | U1 の tip + Silo 修正 patch (`fix-silo-intra-txn-values.patch`、sha256 `2fca96512edab25ed5d097fb201b2d975782a7c8ef607e0adc50fba4f8618c3b`、厳密適用) | 到達不能 0、D1・D2a・D2b 全項 0、発生条件 (自分の書きの後の読みを含む取引・書きのある取引) 各 ≥ 1、D5 成立、commit 件数の証人と一致、certified |
| B | U1 の tip + B1 (初回の読みを読み集合に載せない壊し、U1 用に作り直した patch) | B1 の発火 (commit した取引) ≥ 1、D1(b1) の違反取引数 = B1 の発火数、verdict indeterminate |
| N | U1 の tip + 刻印だけを外す patch (手順列・値の刻印の行は残す) | 記述だけ (commit・abort を S と並べる)。判定に使わない |

- 発生条件が 0、trace / gate archive の欠落、build の失敗は、期待との一致に数えず、原因を記す。
- U0 の照合器 (`gate_check.py`) の D1・D2b の件数は診断として並べる (同じ trace parser を共有するので独立の証拠とは呼ばない)。食い違えば調べて記し、照合を緩めない。
- 修正なしの S が D2b で赤になるのは正しい結果である (設計 §3.5)。これに合わせて照合を緩めない。

## 4. 判定器への変異 (login / dispatch の test、各 1 条件だけ外す)

M1 D1(a)、M2 D1(b1)、M3 D1(b2)、M4 D1(c) (手順列と枠の 1 対 1)、M5 D2a (genesis 以外)、M6 D2a (genesis)、M7 D2b(i)、M8 D2b(ii) を「最初の書き」と照合、M9 V と UPDATE の W 行の 1 対 1、M10 thread 集合の一致、M11 要求時の gate 全欠落を合格扱い、M12 要求時の D5 を `clean()` から外す、M13 不正な gate file 名を無視、M14 gate 有効時の legacy 経路の素通し、M15 要求なしで gate を読まない (presence 起動を外す)。各変異は対応する test が赤 (KILLED = 期待 node の完全一致) になることを期待する。単一理由性は実装後に確かめ、崩れた変異は fixture を差し替えて記録する。
