## 検証した範囲

- 指定された 5 資料を全文確認した。
- 現行 `git diff` は提示された `s5-diff.patch` と SHA-256 が完全一致した。
- 変更 path は次の 2 ファイルだけだった。
  - `tools/codex_reasoning_ab.py`
  - `orchestrator/tests/test_codex_reasoning_ab.py`
- 報告された 5 nodeid はすべて [test_codex_reasoning_ab.py:15894](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/orchestrator/tests/test_codex_reasoning_ab.py:15894) 以降に実在する。
- AST 解析、`git diff --check`、凍結 snapshot と excerpt の SHA-256 照合は独立に再実行し、いずれも成功した。
- pytest は実行しておらず、緑とは判定していない。

## 段 4 must-fix の対応表 (closed / partial / 未実装)

| 項目 | 判定 | 確認結果 |
|---|---|---|
| A1 非 gate・受理集合不変 | closed | 一致、不一致、非発生、宣言なし、malformed の `valid`、`failure_reasons`、`experiment_complete` を固定している。[test:16066](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/orchestrator/tests/test_codex_reasoning_ab.py:16066) |
| A2 複数試行 axis の最終 count | closed | axis 宣言は全 attempt の集約ループ終了後に生成される。[tool:10247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/tools/codex_reasoning_ab.py:10247) テストも 2 試行の最終 count と identity を固定する。[test:15977](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/orchestrator/tests/test_codex_reasoning_ab.py:15977) |
| A3 no-float と rounding | closed | 最終成果物から全 comparability tree を抽出して float 不在を検査し、top-level と nested の `decimal_places` を exact int で固定する。[test:16178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/orchestrator/tests/test_codex_reasoning_ab.py:16178) |
| A4 比較範囲の hard-code 防止 | closed | scope は `dimensions` から取得し、2 task、2 stage の期待値で固定している。[tool:10002](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/tools/codex_reasoning_ab.py:10002) [test:15902](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/orchestrator/tests/test_codex_reasoning_ab.py:15902) |
| B1 pair identity 入替 | closed | status 別に `(block_id, attempt)` の重複除去済みソート列を持つ。[tool:10024](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/tools/codex_reasoning_ab.py:10024) 同 count で identity が入れ替わるテストもある。[test:16012](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/orchestrator/tests/test_codex_reasoning_ab.py:16012) |
| B2 comparison universe | closed | `material_manifest_sha256` を `basis_key` に含め、null 時の範囲限定を `rule` に明記する。[tool:9994](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/tools/codex_reasoning_ab.py:9994) [test:16214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/orchestrator/tests/test_codex_reasoning_ab.py:16214) |
| B3 異なる arm の fixture | closed | `max` と `high`、sol と luna、2 task、2 stage を含む独立 fixture が追加されている。[test:6557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/orchestrator/tests/test_codex_reasoning_ab.py:6557) |
| プラン v2-1 pair identity | closed | per-attempt は自分 1 件、axis は全寄与 attempt の status 別集合になる。[tool:10203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/tools/codex_reasoning_ab.py:10203) |
| プラン v2-2 universe | closed | manifest SHA-256 の伝播と null 規則を実装済み。[tool:10503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/tools/codex_reasoning_ab.py:10503) |
| プラン v2-3 rule 限定 | closed | partial total だけを保証し、平均、完全費用、実請求額を明示的に除外する。[tool:9988](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/tools/codex_reasoning_ab.py:9988) |
| プラン v2-4 fixture | closed | 異 arm、複数試行 axis、複数 task/stage を満たす。[test:6564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/orchestrator/tests/test_codex_reasoning_ab.py:6564) |
| プラン v2-5 受理集合回帰 | closed | 指定された 3 field の一致と既存 malformed 拒否を固定する。[test:16144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/orchestrator/tests/test_codex_reasoning_ab.py:16144) |
| プラン v2-6 最終成果物 no-float | closed | 最終 result 全体を walk して宣言木を回収し、rounding の値と型も固定する。[test:16184](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/orchestrator/tests/test_codex_reasoning_ab.py:16184) |

## 所見 (重大な順)

通し番号を付すべき所見は 0 件。今回の静的検査範囲では、成果物、受理集合、参照を意図せず変える欠陥も nit も検出しなかった。

## 禁止事項の遵守状況

- 新しい `ValidationError`、`raise`、拒否条件、production の failure reason、`reasons` 更新は追加されていない。差分中の `failure_reasons` は新テストの assertion だけである。
- 比較 helper は `reasons` を受け取らず、生成値は `cost["comparability"]` と `axis["comparability"]` に代入されるだけである。[tool:10226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/tools/codex_reasoning_ab.py:10226)
- `valid` は従来どおり `not reasons`、`experiment_complete` と `decision` の出力制御も従来の `reasons` 経路だけで決まる。[tool:10833](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/tools/codex_reasoning_ab.py:10833) [tool:10883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/tools/codex_reasoning_ab.py:10883)
- テスト差分は 454 行の追加だけで、既存期待値の変更、反転、緩和、skip、削除はない。
- 凍結 literal は変更されていない。[tool:174](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/tools/codex_reasoning_ab.py:174) 実 bytes の SHA-256 も snapshot `a0b2...b3b1`、excerpt `32d0...8d4` と一致した。
- `coverage_status="partial"`、`certification_status="not-certified"` は per-attempt と axis の双方で維持されている。[tool:9961](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/tools/codex_reasoning_ab.py:9961) [tool:10191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/tools/codex_reasoning_ab.py:10191)
- `basis_key` に `requested_model`、`unit_prices`、`arm`、`accounted_amount` は入っていない。
- verifier / correctness 経路への変更はない。
- `block_id` または `attempt` が欠ける場合、新コードは `pair_unit=None` として identity 列を空にし、KeyError、TypeError、AttributeError を追加発生させない。[tool:10203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/tools/codex_reasoning_ab.py:10203) なお `attempt` 欠落は後段の既存 `row["attempt"]` が失敗し得るが、これは今回追加された経路ではない。[tool:10521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/tools/codex_reasoning_ab.py:10521)
- `material_manifest_sha256=None` は JSON の null と限定付き rule を生成し、例外経路にならない。
- comparison key は文字列、null、整数、list、dict だけで構成される。Decimal と float は入らず、内部 set は返却前に tuple ソート済み list へ変換される。[tool:10029](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/tools/codex_reasoning_ab.py:10029)
- 既存の完全一致比較は [test:9378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1705-normalized-cost/orchestrator/tests/test_codex_reasoning_ab.py:9378) の同一 pipeline 間比較であり、双方に additive field が付くため静的には壊れない。既存 cost テストは部分 dict または投影値の比較で、親 dict 全体の固定期待値はない。

## 判断できなかった点と、その理由

- 5 nodeid の pytest 結果は判断できない。実装報告自身が `rc=16`、`child_started=false`、nodeid 未実走と明記しているためであり、「緑」とは扱っていない。[s5-author.md:14](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1705-normalized-cost/codex-artifacts/t1705-normalized-cost/s5-author.md:14)
- `tools/run_tests.py` を 3 回起動したこと、当時の queue preflight と headroom の状態は、射影された資料に runner ログがないため独立確認できない。ただし列挙された nodeid の実在と、未実走という報告内容には食い違いがない。
- repo 外の closed-schema consumer や成果物 bytes の固定 hash consumerへの影響は、その consumer が射影されていないため判断できない。repo 内の既存テストについては上記のとおり破壊的な完全一致期待値を認めなかった。

## 総括

段 4 の A1〜A4、B1〜B3、プラン v2 の 1〜6 はすべて closed と判断する。禁止事項違反、受理集合への新しい波及、比較 helper 由来の新しい境界例外、差分と実装報告の食い違いは検出しなかった。

結論は「静的 review 受理可能、pytest 未実走」である。