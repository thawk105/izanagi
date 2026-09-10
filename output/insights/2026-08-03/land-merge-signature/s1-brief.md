# 段 1 brief — land の fold 署名検査を累積差分へ移す

## scope
`tools/dev_waves/git_state.py` の `verify_declared_fold_commit` にある fold 署名検査が、
`DW-O23` が指示する「land 前の wave 側 main 取り込み merge」を全面的に拒否する欠陥を直す。
編集面は `tools/dev_waves/git_state.py` と `orchestrator/tests/test_dev_waves_git_state.py`
(必要なら `orchestrator/tests/test_dev_wave_land.py`)。**署名 2 条件そのものは変えない。**

## 前提実測 (前 wave [T-313] の段 9 で実測、すべて一次資料)
- land が `status=fold-failed` / `reason=landed-fold-owned-path` で停止。main は未変更。
- 原因: `_commit_diff` が `git diff-tree -m` を使い、merge commit では**親ごと**の差分を出す。
  main 取り込み merge の第 1 親 (wave 側) との差分には、main が既に land 済みの fold 署名
  (`M docs/spool/FOLDED.md`) が必ず含まれる。
- 潜在期間: `-m` は導入時 `2743e0d` からあったが、`27f693f` が署名を「作成 `A` ではなく変更 `M`」へ
  絞ったため FOLDED.md が新規作成だった時期の merge は素通りしていた。
  実証 = 過去に land できた merge `6af21d7` の当該 status は `A`、
  [T-313] の merge `ee28642` は `M`。**2 回目以降の fold が main に載った時点で発火**する。
- 影響: main が動いた後に取り込みが要る wave は今後すべて land 不能。
  rebase / cherry-pick は `DW-STOP` が禁じる迂回なので、**正規の手段が 1 つも残っていない**。
- 説明と実装の食い違い: `verify_declared_fold_commit` の docstring は
  「**landed 区間**に fragment 削除・FOLDED receipt 変更がないことまで」と累積で書いてある。

## 既存テスト被覆と純増検出力 (`DW-S01`)
- 既存 (すべて `orchestrator/tests/test_dev_waves_git_state.py`):
  - `test_n31_landed_interval_cannot_hide_an_earlier_fold` — **本検査の存在理由**。
    wave が landed 区間へ fold commit を紛れ込ませる攻撃を止める。**絶対に弱めない。**
  - `test_landed_interval_rejects_fragment_deletion_signature`
  - `test_landed_interval_rejects_fragment_rename_reported_as_delete_and_add`
  - `test_landed_interval_rejects_fragment_rename_reported_as_rename_record` (述語の単体)
  - `test_landed_interval_rejects_folded_receipt_signature`
  - `test_landed_interval_allows_fragment_modification` (正例)
  - `test_p07_null_declared_fold_accepts_zero_pending_fragments` ほか
- **純増検出力 = 「main 取り込み merge を含む landed 区間が受理される」正例**。
  現在この形のテストは 1 本も無く、だから欠陥が landed まで生き延びた
  (F82 の再発検知が要求する「新設 gate には正例を 1 つ書く」が守られていなかった)。

## 不変条件
1. 署名 2 条件 (`M docs/spool/FOLDED.md` / fragment の削除・rename) の意味を変えない。
2. `test_n31` が守る攻撃 (landed 区間に fold を隠す) を**現在と同じかそれ以上**に検出する。
3. 既存の拒否テストを 1 本も緩めない。期待値の反転・skip・削除を禁じる。
4. `verify_declared_fold_commit` の他の検査 (`wave-tip`, `null-head`, `declared-head`,
   `parent`, `added-path`, `path-status` 等) の受理集合を変えない。
5. 受理集合の変更 (何が赤/緑になるか) を置換前後の表で worklog に残す。

## 親の provisional 裁定 (攻撃対象)
- **(P1) 判定領域** = 署名判定を commit ごとから
  `git diff --name-status --no-renames <landed_main>..<wave_tip>` の**累積差分**へ移す。
  根拠 = ff-only が main へ適用するのは累積差分だけで、途中 commit の状態は main にならない。
  commit ごとの判定は (i) main 自身の既 land 履歴を wave 側の親との差分として再び見る点で過剰、
  (ii) 範囲内で現れて消える変更は land しない点で無意味。
- **(P2) 攻撃の生存確認** = 「wave が fragment を追加し自分で fold する」攻撃は累積差分でも
  `M FOLDED.md` で捕まる (fragment は追加後削除で差分に現れないが receipt は残る)。
  **これが成り立たない攻撃経路があれば (P1) は不採用。段 3 で必ず攻撃させる。**
- **(P3) `test_n31` の扱い** = 現行の呼び出し形 (`landed_main_sha=second_fold`,
  `wave_tip=first_fold`) は累積差分では逆向きの範囲になる。テストの**意図を保ったまま**
  現実的な形へ書き直す。意図を変える書き換えは禁止。
- **(P4) 正例の新設** = 「main が fold を含めて進み、wave がそれを merge して取り込んだ landed 区間が
  受理される」を必ず 1 本入れる。これが本 wave の純増検出力。

## 成果物影響 (`DW-G05`)
放置すると、並行して走る dev-wave はどれも land できない。certified 選択・材料レポート・試行台帳を
生む実装 wave が main へ入らなくなるため、成果物は更新が止まる。
迂回 (rebase / force) を許せば、監査済み commit 列と main の履歴の対応が崩れ、
provenance 監査と land の ff-only 契約が同時に無意味になる。

## 成果物の形
`git_state.py` の判定領域変更 + 既存テストの意図保存な追随 + 正例テストの新設。
受入 = `python3 tools/run_tests.py` 全走緑 (計算ノードへ dispatch) と
`python3 tools/check_docs.py` rc=0。変異 matrix は段 4 で事前登録する。
最終検証 = **修正後の helper で本 wave 自身を land できること**、および
前 wave の branch `worktree-dev-wave-t313-read-budget` (tip `05bb98d`) が land できること。

## 分割方針
編集面は 1 モジュール + そのテストで相互依存が強いため、**段 5 は単一 Codex 実装単位**とする。

## 受入・実測環境
`tools/run_tests.py` を repo root から起動し、テスト本体は Pegasus gen_S 計算ノードへ dispatch する
(`AGENTS.md` が login ノードでの pytest を禁じる)。

## この wave 自身のリスク
main が動くと本 wave も取り込み merge が必要になり、**修正前の helper では land 不能**になる。
main を定期的に確認し、動いたら都度取り込む。land は修正後の checkout から起動するので、
修正が自分の land に効く。
