あなたは izanagi の開発 wave の**実装子 (fix 2 巡目)** である。コードとテストだけを編集する。
**docs は編集しない。commit もしない。** cwd は wave の worktree である。

## 必読 (読めなければ即停止し、その旨だけを出力する)

- 焦点再レビュー (直す対象):
  `/work/1/SFC/tanab/dev-wave-jobs/t419-u2-contract-generation/s6-refocus.md`
- 1 巡目の fix 報告: `/work/1/SFC/tanab/dev-wave-jobs/t419-u2-contract-generation/s6-fix.md`
- 裁定 (scope の正本): `/work/1/SFC/tanab/dev-wave-jobs/t419-u2-contract-generation/s4-adjudication.md`
- `orchestrator/campaign/env_contract.py` と `orchestrator/tests/test_env_contract.py` の全文

## 直すもの (should-fix 1 件だけ)

焦点再レビューの 1 件目 (`s6-refocus.md` の 21 行目) だけを直す。

**問題**: 1 巡目の fix で `validate_generations()` の本体を
`_validate_generations_without_bootstrap_fuse(mapping)` への委譲 + fuse に分けた結果、
**委譲の 1 行を削除しても現行テストが検出しない**。負例はすべて private を直接呼び、
public `validate_generations()` に渡しているのは「有効な g1」と
「fuse に到達する有効な 2 世代」だけだからである。

**直し方**: **public `validate_generations()` に、一世代の不正 mapping を渡す負例**を足す。
不正の種類は、fuse を通過しうるもの (例: mapping key と `contract.env_tag` の不一致、
`generation` が 1 でない、要素が `GenerationEntry` でない) から選ぶ。
委譲 1 行を no-op にしたとき、**その入力が受理されてしまう**ことで赤になるようにせよ。

- 既存の private 直接テストは残す (消さない)。
- 追加するのは public 経路の負例である。private の同型テストの単なる複製にしない。
  「public を通しても同じ拒否が起きる」ことが検出内容である。

## 2 件目 (M7 の扱い) は実装対象ではない

焦点再レビューの 2 件目は「M7 を冗長 gate と明記して単一理由性の集計から外す」という
記録上の判断であり、親が段 7 の台帳で処理する。**コードもテストも変更しないこと。**

## 絶対に守ること

- **既存テストの期待値を変更しない。** 反転・緩和・skip・削除・xfail 化を禁じる。
  ただし commit `0324d627` / `7dc3236e` でこの wave が追加したテストは編集対象である。
  期待値のほうが誤りだと判断したら、実装を変えずに報告して止めよ。
- `ExecutionEnvironmentContract` / `_canonical_obj()` / `contract_sha256` / `lookup()` /
  `REGISTRY` の外部から見た挙動を変えない。基準値は pegasus
  `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01`、linux-baremetal
  `1b2ee85346a4c867754bda497b23d649e66027011167cfb0f9c7f9a1a5fa1dc7`。
- `orchestrator/campaign/env_contract.py` と `orchestrator/tests/test_env_contract.py`
  **以外の file を編集しない。**
- 裁定が scope 外とした機能を実装しない。指示にない受理集合の拡大・縮小をしない。
- env 固有 literal を `_build_registry` の FunctionDef の外へ出さない。
- **production コードを変える必要はないはずである。** 変える必要があると判断したなら、
  変える前にその理由を報告せよ。

## 検査と報告

- **pytest を実走してはならない。緑だと主張してはならない。**「実装済み・未実走」と書け。
- 完了報告に次を書け。
  - 追加したテストの名前と、それが検出する欠陥。
  - **`validate_generations()` の委譲 1 行を no-op にしたとき、
    どのテストがどういう理由で赤になるか**の論証 (親がこれを変異 M10 として登録する)。
  - その赤の理由が一つに絞れること (前後に同じ入力を拒否する層が無いこと) の確認。
  - 所有外への波及可能性の静的な列挙。

## 総括

出力の末尾に `## 総括` 節を置き、直した内容を 10 行以内でまとめる。
