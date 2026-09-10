# 段 1 brief — B-2 (descriptor 条件付き合成の因果証拠) の設計と事前登録

wave: `dev-wave-b2-descriptor-prereg` / branch: `worktree-dev-wave-b2-descriptor-prereg`
worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b2-descriptor-prereg`
base: local main `e29084e02d626d812281be6f97f45bb2dde3a843`

## 依頼

`docs/paper-story/2026-08-26.md` §8 の B-2「descriptor を条件にした合成の因果証拠」に対し、
descriptor を与えたアーム / 与えないアーム / 入替え対照を同一予算・同一判定規則で走らせる設計を固め、
因子・セル・反復・判定規則を実走前に commit する。実走は批准の閂が開いた後の後続として起票する。

## 段 1 で実測した前提 (すべて上記 base 上で現物実行。伝聞・docs 記述を根拠にしていない)

1. **批准の閂は閉じている。** `capture_contract_loader_binding()` →
   `require_ratified_closure()` を現物で呼び、closure (25 file) digest
   `dabeada30868a5f790b25b86a9f0a34fafb24946f0e73de48fb90d97d9332eb9` が read-only 台帳に不在。
   → 新規 campaign lock 作成経路は通らない。本 wave で実走しない。
2. **B-2 の事前登録は既に存在する。** `docs/phase3-8c-preregistration.md` §2 が
   「8b 設計 §7 の段階 2『generation/search 実験』に対応する」と明記する。
   同書 §4 が **セル = 2 holdout × 3 arm = 6**、**世代予算 = 全 cell 厳密に `G=2`**、
   停止規則、全件報告母集団、seed 規約を凍結。arm (on/off/swapped) と derangement は
   `docs/phase3-8b-descriptor-design.md` §4、判定規則は同 §6 (+ §10.1 が条件 3 と結論を上書き) が正本。
3. **未凍結は §5 の 7 欄と前提条件 12 件だけ。** library 経路
   (`s8c_preregistration.activation_report_at`) の実測は `NOT_EFFECTIVE freeze=valid`、
   §5 は 9 欄中 8 欄が `UNFILLED`(検定 4 点だけ `FILLED`)、条件は
   `C03 UNSATISFIED: manifest-registry-proof-undefined`、
   `C05 EVIDENCE_UNDEFINED: schedule-schema-absent`、
   `C08 EVIDENCE_UNDEFINED: prereg-binding-proof-undefined`、
   残り 9 件が `EVIDENCE_UNDEFINED: completion-proof-not-machine-checkable`。
4. **判定パラメータの機械検証 consumer は既に実在する。** 8b §10.2 と 8c §5 記入規約が
   記入の解除条件に挙げる「型・有限性・符号・単位・向きを機械検証する consumer」は
   `orchestrator/campaign/s8c_preregistration.py:877-930` (n>=2 整数 / delta_min 有限正 /
   sd_max 有限非負 / unit・direction 同時固定) と
   `orchestrator/campaign/s8c_result_judge.py:225-232` に実在する。
   同 judge は条件 3 種と 3 表 (`descriptive_only` / `official_status` / `selection_evaluation`) を持つ。
5. **CLI `python3 -m ... check` が 12 件を `evaluator-exception` へ潰す件は F369 として既知**であり
   恒久対応 (library 経路で取る) と CLI 修理 [T-1288] が台帳にある。本 wave の scope 外。
   親は一度 CLI 出力を採り、library 経路で訂正した。
6. **編集面の重複なし。** 稼働中 `worktree-dev-wave-b4-prereg-enactment` の `main...branch` 差分は
   `p3_b4_closed_critic.py` / `p3_s4_loop{,_sort,_trigger_gating}.py` と各 test のみ、
   同 worktree の `git status --porcelain` は空。全 `worktree-*` branch のうち `s8b_*` /
   `phase3-8b*` に触るのは `worktree-dev-wave-t1484-floor-restart-registry`
   (`s8b_attempt_profile.py`, `docs/phase3-8b-restart-runbook.md`) だけで、本 wave の編集面と別。

## 不変条件 (緩めない)

- 規律 2: correctness gate (legacy + S2) を緩める提案・「片方だけ通す」「screen-reject を certified 扱い」
  を一切採らない。事前登録の受理集合を広げる変更は本 wave で行わない。
- 8b §8 の変更手続き: 発効済み凍結項目 (holdout・schema・variant 集合・予算・gate・floor・
  選択規則・判定基準・統計数値・screening 範囲) を本 wave で書き換えない。必要なら裁定パッケージへ。
- 8b §10.2 の順序: `n` / `delta_min` / `sd_max` を本 wave で §5 へ記入しない
  (解除条件が全部揃うまで空欄が唯一の担保である、と同節が明記している)。
- 設計文書が「証拠に数えない」と宣言したもの (selector 実験・配線 demo / dry-run・
  既知 rr5/rr50/rr95 の pilot) を本 wave の成果として数えない。
- 二重の事前登録を作らない。B-2 の正本は 8c prereg + 8b 設計であり、判定規則を分岐させない。

## 成果物の形 (provisional。以下 (P1)〜(P4) は親の provisional 裁定であり攻撃対象)

- **(P1)** B-2 用の新規「事前登録」文書は作らない。既存の 8c prereg が正本である。
- **(P2)** 本 wave の中心成果物は **`docs/phase3-8b-pair-planning-pilot-preregistration.md` (新規、
  発効前 living、承認待ち draft)** とする。これは 8b §10.2 が `n` / `delta_min` / `sd_max` の
  記入解除条件として名指しする**対計画用 pilot** の事前登録であり、正式系列 (8c 6 cell) とは別実験である。
  凍結するのは pilot の因子・セル・反復・判定規則・予算・成功条件と、
  その出力から `n` / `delta_min` / `sd_max` を**結果を見る前に**決める規則である。
  pilot の結果を B-2 の因果証拠に数えないことを本文で明示する。
- **(P3)** 同文書の冒頭に「現在地」節を置き、上記 3 の実測 (§5 欄 × C01〜C12) と各欄の解除条件、
  依存順序を載せる。実測値は本 wave で測った値だけを書き、docs の記述を根拠にしない。
- **(P4)** 実装面は **`tools/check_docs.py` の `LIVING_DOCS` への新文書登録と `docs/README.md` の
  地図追記だけ**とする。これは Codex `role=author` が書く。
  `orchestrator/tests/test_check_docs.py` の合成 fixture との整合を同じ commit で確認する (DW-O27)。
  判定器・8c 消費経路・campaign 起動経路には触れない。

## 成果物影響 (DW-G05)

- (P2) を作らない場合: 8c prereg §5 の判定パラメータ欄は永久に空欄のままとなり、
  `activation_report_at` は `NOT_EFFECTIVE` を返し続け、B-2 の 6 cell は 1 行も certified な
  結果を作れない (公式性能表の `official_status` が生成されない)。
- (P4) を作らない場合: 新文書が `check_docs.py` の living lint 網の外に落ち、
  可変状態の再掲・行番号参照が検出されないまま残る。

## 段 2 / 段 3 への攻撃点 (親が割れると見ている前提)

- (a) **(P2) は時期尚早ではないか。** 8b §10.2 の解除条件のうち「schedule generator・manifest・
  反復束縛が固定済み」は C03/C05 の実測どおり未充足である。pilot の設計だけ先に凍結する価値があるか、
  それとも本 wave は「現在地の確定 + 後続起票」に留め、pilot 設計は束縛が固まった後にすべきか。
- (b) **判定規則が selector 語彙で書かれている問題。** 8b §6 / §10.1 と
  `s8c_result_judge.py` の条件 ID (`on_off_prediction_difference` /
  `swapped_follow_through` / `paired_repeat_contrast`) は「予測構成」を前提とする。
  generation/search arm の出力は**合成された variant** であって予測選択ではない。
  この読み替えがどこかで凍結されているか、未凍結なら本 wave の scope に入れるべきか。
  (未凍結なら 8b §8 の再凍結 + ユーザー承認が要るため、実装せず裁定パッケージへ送る想定)
- (c) **(P4) の実装面が本当に最小か。** 新文書を `output/insights/` に置けば `check_docs.py` を
  触らずに済み実装面ゼロになるが、事前登録は living doc であるべきで insights (追記型・凍結) ではない。
  この置き場所の択一。
- (d) 上記 3 の実測に、親が読み落とした反証 (別の消費経路・別の凍結先) がないか。

## 並列分割方針

段 2 は plan 子 1 本 (read-only)。段 3 は敵対相談 2 本 (レンズ = 「既存被覆と二重登録」/
「規律 2・凍結手続きの迂回と恒真な保証」)。段 5 は実装面が小さいので author 1 本。
段 6 は review 2 本 + fix。
