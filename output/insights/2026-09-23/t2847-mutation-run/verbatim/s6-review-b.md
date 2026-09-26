## 所見

- **B01・should・[test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/tests/test_ccbench_spawn_sites.py:2907)** — 新設の14件の個別照合表は、既存の在庫一致と `DefineSpec.patch_rel` 照合に重なる検査。削除して既存 assertion を使う。**成果物影響:** 検出表の実測には影響しない。R6 の M1・M3 も既存 assertion で赤にできる。
- **B02・should・[launch_mutation_run.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/launch_mutation_run.py:305)** — stock build または同 workload の stock run が失敗しても、後続の変異 build・run を続ける。帰属不能と記録する実装はあるが、検出表に使えない計算を消費する。該当 workload の変異を「帰属不能」と記録して実行を止める。**成果物影響:** node 時間の見積り超過リスクを減らす。
- **B03・nit・[test_condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/tests/test_condition_meaning_gate.py:3706)** — 件数を名前に含む既存 test の改名は不要。assertion 内の数値と文書文字列の更新だけで足りる。**成果物影響:** なし。

## 削れるもの

B01 の14件の個別照合表と B03 の test 改名。14 patch、発火診断、既存 condition gate への登録、既存テストの期待表、README 節、起動器の実測保存は検出表の作成または既存の実行契約に必要で、削除候補にはしない。新しい gate・台帳・互換層は差分に見当たらない。

## 未確認点

- 静的審査のみ。build、発火、verdict、R6 の実際の赤 node は未確認。現時点では四分類を実測で記入できない。
- R6 の M1〜M4 は既存 assertion 上、いずれも赤になる構造。M1 は在庫一致と domain 固定、M2 は witness 一覧と patch 束縛、M3 は裸マクロ許容表と在庫一致、M4 は patch 内の directive 件数で検出する。ただし**単一理由への帰属**は段6の実際の失敗出力で確定する必要がある。
- 実装面のハンクには、commit trailer 上すべて Codex `role=author` がある。README は親の docs として扱える。

## 総括

**GO（条件付き）。** B01 を削り、stock 失敗後の無益な実走を止めたうえで、親が予定する計算ノード実測と変異 matrix を確認する。