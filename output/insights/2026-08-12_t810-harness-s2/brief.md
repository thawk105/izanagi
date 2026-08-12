# 段 1 brief — [T-866]+[T-867] 測定装置 slice 2 (wave: dev-wave-t810-harness, 2026-08-12)

## scope (ユーザー裁定 2026-08-12 指示で確定)

- [T-866] protocol §9.1 item 1 の (a) N-job group barrier・共有 release・取り消し marker・
  coordinator 側開始ばらつき測定 (coordinator の同一時計、上限 5 秒)・N 件 exact 完了 verifier、
  (b) T-810 専用 PBS wrapper (単独性確認・静穏 gate (load avg ≤1.0 を 30 秒間隔 3 連続、最大 1200 秒)・
  binary 配布と前後照合・receipt・投入 argv 正規形照合)、(c) runner policy module = 測定 runner の
  argv allowlist ((b) と同一 wave 必須 — 単独 mediation 点が無い限り receipt-only になるため)、
  (d2) 測定ノード上の repo 不在 (唯一の構造的防壁、§6.1)。
- [T-867] (f) 並走ガードの機械化 (割当てジョブ状態の exact parser・未知状態の拒否・A 系 (T-139) 優先の
  receipt・競合時の取り下げ)、(g) 予算残枠との突合による投入 admission。
- **scope 外:** 実測の投入 (本走・生死確認・builder とも投入しない)。[T-868] trust root (ユーザー裁定待ち)。
  protocol 本文の訂正 (§9.1 item 2 列挙 — 裁定パッケージ候補のまま)。人間の承認 ID 発行。

## 不変条件

1. `tools/pegasus/policies/t810_prereg_v1.json` の **bytes を変えない** (loader が raw bytes digest を
   approval receipt と照合する凍結物。DW-O09 実測: 参照は loader・test 2 本・registry_v1.json)。
2. slice 1 の dormant seal (`run_authorized`)・§6.3 validator・loader の受理集合を緩めない。
3. 非流入 (§6): 新規実装は repo へ書く経路を作らない。qsub の `-o`/`-e`・作業/出力 root は repo 外
   絶対 path。calibration certify 経路 (自動 publish) を流用しない。trace 記号ゼロ (規律 1)。
4. 新規 policy JSON を `tools/pegasus/policies/` に置く場合は `registry_v1.json` の `policy_paths` へ
   追加する (test_pegasus_policy_registry が検査)。prereg 以外に凍結 bytes は増やさない。
5. 既存 `dispatch_compute.py` / `mutation_fanout.py` の挙動を変えない (参照・pattern 流用のみ)。

## 実測済みの前提 (Explore 2026-08-12)

- 素材: group manifest + authority sha256 (`tools/mutation_fanout.py:97-108,826-843,1411-1464`)、
  qstat identity parser (`:1099-1119`、汎用)、orphan 検出 pattern (`:846-1084`)。
- qsub 形と receipt v2: `tools/pegasus/dispatch_compute.py:1475-1488,1270-1285`。qstat -Q parser:
  `orchestrator/campaign/queue_state.py:46-122`。
- **単独性確認・静穏 gate・計算資源予算の既存機構は無い** (grep 根拠あり)。(g) の予算台帳は新設になる。
- prereg の凍結 field 実在確認 (DW-O13): `canonical_benchmark_argv`(:607)、`qsub_argv`(:574)、
  `build_argv`(:131)、`submission_argv_comparison: exact`(:697)。

## 親の provisional 裁定 (攻撃対象)

- (P1) (g) の予算正本 = 新設の機械可読 budget policy (総枠と見積り式) + repo 外 output root の消費
  ledger。admission は「凍結 walltime 見積り × attempt 数 ≤ 残枠」を fail-closed 判定。
- (P2) 実装の置き場 = `tools/pegasus/t810_*.py` (coordinator / wrapper / policy / guard) の新規
  ファイル群 + `orchestrator/tests/test_t810_*.py`。既存 file の改変は registry への 1 行追加のみ。
- (P3) (d2) の実装形 = wrapper preflight の「測定ノード上に repo 作業木が無い」検査 (git dir 検出で
  `pre_release_invalid`) + job script が repo を参照しない正規形。coordinator 側は §6.3 validator を
  投入前後に呼ぶ。
- (P4) qsub/qstat は投入しないため、テストは記録済み出力の fixture と injection seam で行う。
  「実装済み・未実走」を完了形とし、実走裏取りは生死確認 wave (§8、承認後) に送る。

## 成果物影響 (DW-G05)

実装しなければ §9.1 item 1 が不充足のまま生死確認も本走も投入できず、[T-810] の測定は開始できない。
certified 選択・受理集合・proof chain へは本 wave では影響しない (dormant のまま)。

## 並列分割方針

- 子 A: (a) coordinator 一式 + tests (group manifest schema v1・barrier・release・cancel・開始ばらつき・
  完了 verifier)。
- 子 B: (b) PBS wrapper + (c) runner policy module + (d2) + tests。
- 子 C: (f) 並走ガード + (g) 予算 admission + tests。
- 受入環境: Pegasus。受入全走は lease (`dev-wave-jobs/land-lease`) 取得後に計算ノード dispatch。
