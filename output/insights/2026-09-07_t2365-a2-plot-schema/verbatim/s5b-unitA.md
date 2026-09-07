## 総括

単位 A を実装し、legacy と current full の 2 profile のみに対応しました。  
legacy の schema・hash・caption・検証経路は維持し、既存の凍結成果物テストも通過しています。  
current は 12-file closure、受領証、四者 token、`source_binding_status`、median/effect を検証します。  
新 attempt の pin entry と実在する新図は指示どおり追加していません。  
変更は所有対象の 2 file のみで、commit・`git add` はしていません。

## 変更点

変更前は legacy v3/v3/v2 の固定 hash・固定 workload/cell 順だけを受理し、current、schema 交差、partial 系をすべて拒否していました。  
変更後は canonical legacy を従来どおり受理し、repo pin 表に登録された certification に限って current v4/full-v4/v3 も受理しますが、未登録 path、schema 交差、partial 系は fail-closed で拒否します。

- [plot_a2_certification.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2365-unit-a/tools/plotting/plot_a2_certification.py:30): profile 定義と certification path keyed pin 表を追加。
- [plot_a2_certification.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2365-unit-a/tools/plotting/plot_a2_certification.py:106): pin 表にない path と不完全な hash 組を拒否。
- [plot_a2_certification.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2365-unit-a/tools/plotting/plot_a2_certification.py:157): embedded policy を producer の実 validator で検証し、workload/cell 順を導出。
- [plot_a2_certification.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2365-unit-a/tools/plotting/plot_a2_certification.py:237): current の exact 12-file closure と全 member hash を検査。
- [plot_a2_certification.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2365-unit-a/tools/plotting/plot_a2_certification.py:361): receipt/raw/WAL/certification token、stock/adopted role、cell-level `source_binding_status="bound"` を照合。
- [plot_a2_certification.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2365-unit-a/tools/plotting/plot_a2_certification.py:574): current caption/gate note を受領証の観測範囲に限定。
- [test_plot_a2_certification.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2365-unit-a/orchestrator/tests/test_plot_a2_certification.py:179): producer と凍結成果物を使う current fixture、および正負例を追加。凍結 hash 値と caption 期待値は変更せず、pin assertion の容器形だけ表構造へ追随。

## 実走した検査

`MPLCONFIGDIR=/tmp/t2365-mpl PYTHONPATH=. python3 -B /tmp/t2365_plot_harness.py orchestrator/tests/test_plot_a2_certification.py -q`

- 対象 file 全 52 nodeid: **52 passed**
- current 正例・図生成: `test_current_full_profile_uses_producer_policy_and_exact_twelve_file_closure`
- schema 交差／partial: `test_current_rejects_schema_crosses_and_partial_families` 全 6 case
- closure、受領証、token、binding、median/effect、gate 文の追加 nodeid: 全 pass
- 既存 frozen hash、実 durable root、landed caption/closure nodeid: 全 pass
- collection meta-check: **52 tests collected**
- `git diff --check`: pass
- 凍結 directory 8 file の SHA-256: 作業前後一致

新しい図用 `_assert_named_landed_bundle` は実装済み・未実走です。新成果物が存在しないため、それを対象にした test は作成していません。

## 所有外への波及

- current 経路は `paper_story_a2_certification.py` の policy loader、cell validator、receipt parser に依存します。同 producer の schema変更時は追随が必要です。
- `tools/plotting/README.md` の既存 legacy CLI はそのまま動作します。
- 親が新 attempt 完了後に current certification path と certification/raw-manifest hash を pin 表へ追加する必要があります。
- 新図・figures README・results consumer は親所有で、本段では未変更です。
- 共有 fixture の変更はありません。

## 未了・申し送り

- current 用 pin entry は未追加です。この状態では新しい certification path の CLI 実行は意図どおり拒否されます。
- 新 attempt、新図、current landed bundle の実体検査は未実走です。
- `tools/run_tests.py` は使わず、指定どおり `PYTHONPATH=.` の自走 harness で検査しました。