# 裁定パッケージ — [T-2724] freeze v2 g1 候補を発効へ進めるか

候補: `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`、sha256
`7e1114068433b40dc459e5e9c5ffcfa9a38cd360fc798904b7a9842382e19c06`、`frozen_at_head`
`cc82edc8c9f90a9ee659c2d27f71b75b19a56490` (X1')。所在: 保存 branch `freeze-g1-chain-t2724` =
main `1042a1bc9` → P `3b0b75496` (producer 修正、land 済み予定) → X1' `cc82edc8c` (result 5 file + budget
入力) → X2 `4d8fb93b7` (候補)。入力 result: run `20260916T111925Z-2c8cf9be`、sha256 `b111831e…`。
producer 実行 rc=0、静的検証の到達範囲は README §3、未発効。

各項は独立に投げられる (依存は明記)。親の推奨は根拠つきで置くが、決めるのは人間。

## (a) restore 前の判断 — 当該 holdout 集合 (rr20 / rr80、v1 freeze) の official 走行を打ち切るか

D2077 step 4 は「打ち切ると決めてから restore」。本 wave は決めずに保存 branch へ隔離して実施した
(README §5)。ここで決める。

- **択 1: 打ち切る = chain (X1', X2) を main へ取り込む。** 以後、main とそれを継承する checkout では
  official 床値の起動証明 (clean scan) が赤になる (D2077 step 7、設計どおり)。後続の official 床値 wave
  (例: 非 sort 単独構成 [T-2699] の実機通過) は main からは起動できない (別 branch からは可能)。
- **択 2: 打ち切らない = chain は保存 branch のまま。** main は official 床値を起動し続けられる。候補は
  発効せず、いつでも択 1 へ移れる (bundle は固定退避先に残る)。
- **択 3: 隔離候補作成を D2077 の例外として明示承認する** (今回の実施形を追認し、打ち切りは別途)。

親の推奨: **択 1 を急がない。** 候補生成の目的 (承認手番の入力を揃える) は保存 branch で達している。
(c) の床の採否と (b) の承認へ進む意思が固まった時点で択 1 にする。それまでは択 2 + 択 3 (実施形の追認)。

## (b) 世代導入 G → approval A → active pointer X の人間手番へ進むか

技術上の必要条件 (README §3、段 3 レンズ A): G は非 merge・親 == X1'・`AI-Agent` trailer 付き (AI が
作る commit) で `output/s8b-freeze/holdout_freeze.v2.g1.json` を導入する。A / X は非 merge・逐語
`AI-Agent: none` の人間 commit で、X^ == A。H (検証時点の HEAD) から見て G の ancestry と closure path
(result.json / manifest.json / journal.jsonl / launch_certificate.json / 版付き protocol) の bytes が保たれること。
**main への取り込みは批准の技術条件ではない** (branch 名を要求する検査は無い) が、production の consumer は
checkout の HEAD を H とするので、運用上は main へ載せてから A / X を作るのが自然 (レンズ B B-4)。

- 択 1: (a) 択 1 の後、G を AI (Codex author) に作らせ、A / X を人間が commit する。
- 択 2: 候補の保存で留める。
- 依存: (a)、(c)。W-4 の spec 承認 (T-750 P-1) は別件で、oracle 実走にはこれも要る。

親の推奨: (c) が「採用」なら択 1。G を作る wave を別に起票する (本 wave は世代文書を作っていない)。

## (c) この床を g1 の床として採用するか

事実 (README §4): 両 holdout とも床 = 0.03 × stock 中央値 (配線下限が支配、実測 `u_noise` は下限未満)。
1 走行の値で between-run 変動は未実測。**現行 oracle は床の数値を勝敗判定に使わない** (D1985 / D2024) —
g1 発効が変えるのは driver の `floor-null` / `budget-null` 拒否が解けることだけ。

- 択 1: 現行 formula v2 と protocol に従ったこの 1 走行の床を、現行契約の候補充填として採用する。
- 択 2: 追加観測 (別 run) を取ってから判断する。**追加 run は床の出所を差し替えない** (D1311: 最早適格 run 固定)。
  判断材料が増えるだけ。
- 択 3: `wired_min_rel_floor` (0.03) を再検討する = protocol の変更と再測定を伴う別件。

親の推奨: **択 1** (根拠: 現行契約の手続的成立に必要な充填であり、床の数値は現行判定に効かない)。
「科学的に十分な床」とは主張しない。

## (d) growth hold 2 本の帰結

chain が main に載ると、実 repo 全体に 0 hit を要求する held test 2 本 (`test_s8b_repo_scan_invariant.py`、
`test_s8c_preregistration_invariant.py::test_wave_files_do_not_contaminate_production_holdout_scan`) は
解除時に設計どおり赤になる。本 wave は hold・test・走査除外を変えていない。

- 択 1: 帰結を記録して現行 hold のまま (解除時の扱いは別裁定)。
- 択 2: 解除時の扱い (走査の除外集合を候補・official namespace へ広げるか否か) を別途裁定する。
  **除外を広げることは D2077 が却下した選択肢で、規律 2 に触れる。**

親の推奨: 択 1。「赤の予測を受容する」と「検査の弱体化を許可する」は別。

## (e) T-1851 の失敗 run 3 件の退避 (掃除)

`dev-wave-t1851-c3c-official-floor` worktree に `journal.jsonl` + `launch_certificate.json` だけの run 3 件が
未退避で残る。result.json が無いので最早適格判定に影響しない (`_official_earlier_floor_results` が skip)。
固定退避先へ累積 (evacuate) するか、worktree ごと撤去するかは掃除の裁定。本 wave は触れていない。

## (f) [T-750] package の残余

P-1 (承認 authority の pinned literal 形を恒久形にするか)、P-3 (批准 proof chain に budget authorization
field が無い構造) は本 wave でも未解決のまま。本候補の `refreeze_note` は budget 承認 sha を文字列で持つだけ。

## (g) 本 wave が land するもの (裁定不要、記録)

producer 修正 (P、Codex author、焦点走 162 + 669 passed、変異 matrix は worklog)、runbook W-3 / W-4 / §5 R-3 の
訂正、budget 手順書 §2 の追記、本 insight、fragment (worklog T-750 / T-2724 更新、decisions 3 件)。
chain (X1', X2) は land しない。
