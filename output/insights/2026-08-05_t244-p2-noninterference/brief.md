# [T-244] D121 P2 — 段 1 brief (payload 射影面の非干渉検査)

```text
authority: none
default_effect: no-state-change
```

**scope.** 8c 自律試行が untrusted role (planner / coder / auditor / critic) へ渡す **入力 payload
だけ**を対象に、実効 diff とその digest・5-bit wire・IR schema SHA が現れないことを機械が
fail-closed で拒否する検査を新設する。射影点は `p3_autonomous_workload_trial.py::_invoke`
(line 904) の 1 seam で、4 role すべてがここを通る。

**確定済みユーザー裁定.** D121 決定 (1)(3)(4)(4-b) と §7 P2。P2 は無条件義務 8 件 (D150) の 1 つ。
本依頼は対象を「payload 射影側に閉じる」と明示した。

**前提実測 (brief 前).** (a) T-244 P2 の branch / worktree / handoff は不在 = 本 wave が初回起動。
(b) `reflux_ir.py` (IR + 32 点 golden) と 5-bit wire の coder 契約は land 済み。
(c) **依頼の前提 1 件が反証された** — 未着手は P2 だけでなく P7・P9 も未着手 (worklog (186)
「P2 / P7 / P9 は未着手」、(187)〜(193) は変わらず)。scope は変えず記録のみ。

**純増検出力 (性質で検索した既存被覆).**
- 性質 A「role 入力 payload の top-level key が閉集合」= `test_p3_autonomous_workload_trial.py`
  の 1 シナリオ内 assert のみ。**auditor は未被覆**、かつ生成点の gate ではなくテスト内 assert。
- 性質 B「payload の**値**が禁止 vector (実効 diff 全文 / その digest / wire / IR SHA) を含まない」= **被覆ゼロ**。
- 性質 C「未知 role への射影を拒む」= **被覆ゼロ** (`ROLE_FILES` の key で暗黙に閉じるだけ)。
- 純増 = B と C の全部 + A の auditor 分 + A の生成点 gate 化。

**不変条件.** (1) payload の field も値も変更しない — 変更が要ると判明したら実装せず段 4 で裁定へ返す
(受理集合と凍結 bytes に触れるため)。(2) `MAX_APPROVED_GENERATIONS = 1` 不変。(3) 拒否 message は
disclosure-free (`reflux_ir._REJECTION_MESSAGE` 様式)。(4) 「P2 充足」と名乗らない — 名乗れるのは
「P2 の payload 射影面だけを閉じた部分実装」まで。D51 逐次 provenance (`reports/` の
`auditor_diff_digest`、実在を確認済み)・driver 戻り値・artifact path・trial report は **scope 外の残余**。

**成果物影響 (DW-G05).** 本検査は payload 内容を変えないため certified 選択・材料レポート・
proof chain・凍結 bytes・受理集合はいずれも不変。実装しない場合に変わるのは cap-lift 判定の
受理集合だけ — P2 が payload 面でも未拘束のまま FAIL 固定になり、D114 の上限 1 を解除する判定材料が増えない。

**親の provisional 裁定 (攻撃対象).**
- **(P1)** auditor は `working_diff` と `diff_digest` を受け取ってよい。両者は auditor が監査する
  当該候補の関数であり、機械制御状態 (禁止集合・予算・他候補) の関数ではない。D121 が禁じた
  「実効 mask・両 SHA」は reflux-control 未実装の現在は raw mask と同一で、diff 全文を渡す以上
  digest を隠すのは恒真。
- **(P2)** critic payload の `harness_result.variant` と `critic_digest` 全文は、字面に wire を
  含みうる。**段 2 は現行 production 値を実測し、値レベル検査が現行コードで赤になるかを判定すること。**
  赤なら不変条件 (1) により実装せず段 4 で裁定へ返す。
- **(P3)** 非干渉の定義は「payload は (a) 凍結定数と (b) 当該 generation の role 許可入力のみの関数」
  とし、**per-role field allowlist + 禁止 vector の再帰的値走査**の二段で近似する。字面 denylist 単独は恒真
  (§7 P2 の「観測面の閉集合を定義しないと恒真化する」)。凍結定数 (`GATING_SPEC`、
  `DESIGNATED_SOURCE_CONTEXT`) は byte 比較で pin し値走査から除外する。
- **(P4)** 同名識別子の二義化を禁じる (DW-O13) — auditor **入力**の digest と auditor **出力** verdict の
  `diff_digest` は別物として命名する。

**成果物の形.** `orchestrator/campaign/reflux_noninterference.py` (純関数 leaf) + 専用テスト、
および `_invoke` 直前 1 点の結線。docs は段 7 で spool fragment。

**並列分割方針.** 段 5 を 2 所有に分ける — 所有 A = leaf + 専用テスト、所有 B = 結線 + 既存テスト調整。

**環境.** login ノードで `pytest` のみ。CC campaign の実走・性能計測は行わない (計測層に触れない)。
