---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-13
wave: dev-wave-known-red-octopus
seq: 1
---

## {{D:n-parent-history-transition}}. 凍結履歴の遷移契約は親数でなく親状態の順序で決める

**決定:** `orchestrator/campaign/s8c_preregistration.py` の `_assert_history_transition` は、
親が 3 つ以上の merge を**親数だけを理由に拒否しない**。n>=2 の一般規則は次とする。

- 親状態を**異なる状態へ dedup** する (添字で数えない)。
- dedup 後がちょうど 1 状態なら、commit state がそれと一致するときだけ受理する
  (不一致は `merge-state`)。
- そうでなければ、最大世代の状態がちょうど 1 つ存在し、それが他の全状態と同値または
  `_is_successor` であり、commit state と一致するときだけ受理する
  (成り立たなければ `merge-divergent-revision`)。
- 親数だけを理由とする `octopus-merge` reason は**廃止**する。

n=0 / 1 / 2 の受理集合と reason は 1 件も変えない。

**理由:**

- **現行の拒否は偽陽性だった。** F269 の原因 commit `d1de13ad` について、freeze 状態を決める
  3 path (`docs/phase3-8c-preregistration.md`、
  `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json`、
  `output/s8c-preregistration/condition-freeze/`) の blob OID を 4 親と merge 本体で実測したところ
  **5 commit すべて完全一致**した。保護対象は 1 bit も動いておらず、拒否理由は親の個数だけだった。
- **台帳が octopus merge を要求している。** F266 の恒久対応は複数 branch を取り込む land に
  `git merge --no-ff --no-commit <b1> <b2> <b3>` を命じており、親は main + 3 = 4 になる。
  一方 F269 の恒久対応は「3 親以上を作らない」と書いており、**両者は正面から矛盾する。**
  本決定は F266 側を採り、履歴契約の方を直す。F269 の「3 親以上を作らない」は本決定で解消する。
- **n=2 との一貫性。** 現行 2 親規則は既に「親状態のうち唯一の後継と一致すること」を見ており、
  この意味論は n 親へそのまま延長できる。全親同値だけを受理する狭い案は段 3 で検討したが、
  F266 が命じる形は「main + **古い** branch 複数」であり、間に世代更新が 1 回でもあれば
  必然的に世代の混ざった octopus になる。狭い案はその形を将来また恒久赤にするので採らない。

**却下した選択肢:**

- **3 親以上の merge を land で機械的に禁じる** — F266 の恒久対応が実行不能になり、
  `landed-fold-owned-path` (rc=26) の永久赤が戻る。
- **`d1de13ad` を既知例外として commit 単位で登録する** — 検出力が commit ごとに穴あきになり、
  次の octopus を素通しする台帳を育てる。
- **merge の作り直し** — main の履歴書き換え (rebase / force) は禁止されており実行不能。

**残る検出力の欠落 (scope 外・裁定へ返す):** `_HistoryState` は
`docs/phase3-8c-preregistration.md` の §0 / §5 の値と evidence JSON の表記差を hash 対象に
含めないため、「状態は同値だが tree は異なる」merge を受理する。これは **n=2 でも同じ**であり
本決定が作る穴ではない。

## {{D:acceptance-red-attribution-by-rerun}}. 受入赤の「自分のせいか」は宣言でなく再実行で決める

**決定:** 受入全走が赤になったとき、その赤を自 wave の差分に帰属させるかどうかは
`tools/check_acceptance_reds.py` が**実測**で決める。赤 nodeid を受入 log から厳密抽出し、
各 node を tested main の **node ごとに新しい worktree** で単独再走する。

- 全件が main 単独でも赤 → `non-attributable-only` (rc=0)
- 1 件でも main 単独で緑 → `attributable-red` (rc=1) で停止し、該当 nodeid を全件出力する
- log 解析の不成立・probe の同一性違反・cleanup 失敗 → rc=2

**登録簿・自己申告・免除 flag・環境変数・warning-only mode を一切作らない。**

**理由:**

- D316 は「既知赤 waiver (W1 形式) の新設」をユーザー裁定で却下している。却下理由は
  「赤を残したまま迂回する形であり、恒久ルール『テストがおかしければテストを直す』に反する」
  「伸び続ける集合なので waiver は事実上恒久化する」の 2 点である。
  **登録簿型はこの 2 点に真正面から抵触する。**
- さらに致命的なのは、`authority: user` のような field を**書くのは AI 自身**であり、
  人間裁定を要求する機械的拘束にならないことである。自分が壊した赤を自分で「既知赤」と
  登録できる機構は、規律 2 に対する直接の攻撃面になる。
- 再実行による帰属判定にはこの穴が無い。判定材料は宣言ではなく main での再走 rc であり、
  永続状態も持たないので腐らない。これは `DW-O18` に既にある「差分が到達しえない赤は
  単独再走で再現性を実測してから扱う」という**現行規範の機械化**であって、新しい免除ではない。
- F101 とその 2026-08-12 再発は「成立済みの裁定を親が引かずに停止した」手順漏れだが、
  `DW-G03` の意味では**同一 consumer (親の STOP 手順) の 2 例**であり独立 2 例ではない。
  したがって制度としての waiver 一般化は行わない。

**塞げていない残余 (scope 外・裁定へ返す):**

- log が真正な受入走のものであることを機械で束縛できていない。任意の過去 log を渡せる。
  受入 argv・環境・pytest raw rc も receipt に束縛されていない。
- `tools/dev_wave_land.py` は受入結果を一切検証しない (F101 で既知)。本 tool の発火は
  受入 command の rc に依存し、land 層の機械的強制は無い。
- SIGKILL・host crash 経由の probe worktree 残骸は process 内 handler では閉じられない。
