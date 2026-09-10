あなたは izanagi の開発 wave の**実装子 (fix 3 巡目)** である。コードとテストだけを編集する。
**docs は編集しない。commit もしない。** cwd は wave の worktree である。

## 必読 (読めなければ即停止し、その旨だけを出力する)

- 焦点再レビュー 2 巡目 (直す対象):
  `/work/1/SFC/tanab/dev-wave-jobs/t419-u2-contract-generation/s6-refocus2.md`
  の `## 残所見` にある **should-fix 1 件だけ**を直す。
- 2 巡目 fix の報告: 同 dir の `s6-fix2.md`
- 裁定 (scope の正本): 同 dir の `s4-adjudication.md`
- `orchestrator/campaign/env_contract.py` と `orchestrator/tests/test_env_contract.py` の全文

## 直すもの

**問題**: 2 巡目で足した public 負例
`test_validate_generations_public_rejects_invalid_single_generation_candidate` は、
変異 M10 (`validate_generations()` から `_validate_generations_without_bootstrap_fuse(mapping)`
への委譲 1 行を no-op にする) で赤になるが、**private 側の連番検査を削除しても赤になる**。
よって「委譲専用の単一理由 witness」にはなっていない。

**直し方** (レビュアの提案どおり):

- **有効な一世代 mapping** を使い、`_validate_generations_without_bootstrap_fuse` を
  monkeypatch の spy に置き換えて、`validate_generations(mapping)` が
  **同じ mapping オブジェクトで spy をちょうど 1 回呼ぶ**ことを直接 assert する
  専用テストを新設する。
  - spy に置き換えるので private の実装 (連番検査など) は遮断され、
    赤の理由が「委譲が無い」ことだけに絞れる。
  - 呼ばれた引数が `validate_generations` に渡した mapping と同一であることも assert する。
- **2 巡目の public 負例テストは残す** (public の機能テストとして有用)。消さない。
- production コードは変えなくてよいはずである。変える必要があると判断したら、
  変える前に理由を報告せよ。

## 絶対に守ること

- **既存テストの期待値を変更しない。** 反転・緩和・skip・削除・xfail 化を禁じる。
  ただしこの wave が追加したテスト (`0324d627` / `7dc3236e` / `b7046b8a`) は編集対象。
  期待値のほうが誤りだと判断したら、実装を変えずに報告して止めよ。
- `ExecutionEnvironmentContract` / `_canonical_obj()` / `contract_sha256` / `lookup()` /
  `REGISTRY` の外部から見た挙動を変えない。基準値は pegasus
  `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01`、linux-baremetal
  `1b2ee85346a4c867754bda497b23d649e66027011167cfb0f9c7f9a1a5fa1dc7`。
- `orchestrator/campaign/env_contract.py` と `orchestrator/tests/test_env_contract.py`
  **以外の file を編集しない。**
- 裁定が scope 外とした機能を実装しない。指示にない受理集合の拡大・縮小をしない。
- env 固有 literal を `_build_registry` の FunctionDef の外へ出さない。
- monkeypatch は test 内に閉じ、他テストへ漏れないようにする
  (`monkeypatch` fixture を使い、手動の代入・復元をしない)。

## 検査と報告

- **pytest を実走してはならない。緑だと主張してはならない。**「実装済み・未実走」と書け。
- 完了報告に次を書け。
  - 新設したテストの名前。
  - **委譲 1 行を no-op にしたとき、この新テストが赤になる理由**と、
    **private の実装を壊す他の変異ではこの新テストが赤にならない**ことの論証。
  - monkeypatch が他テストへ漏れないことの確認。
  - 所有外への波及可能性の静的な列挙。

## 総括

出力の末尾に `## 総括` 節を置き、直した内容を 10 行以内でまとめる。
