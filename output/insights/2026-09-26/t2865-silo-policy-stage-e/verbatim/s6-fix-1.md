## F1〜F9 の対応

| ID | 状態 | 対応 |
|---|---|---|
| F1 | closed | [driver](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-core/orchestrator/campaign/p3_s4_loop_policy.py:97) で性能構成を campaign identity に束縛し、両実行入口で照合。 |
| F2 | closed | [driver](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-core/orchestrator/campaign/p3_s4_loop_policy.py:191) で EvalResult と WAL の構造化 field から outcome・verifier digest を射影。履歴と self_history の key 集合は維持。 |
| F3 | closed | [driver](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-core/orchestrator/campaign/p3_s4_loop_policy.py:64) で preview は coder のみ、run は coder・auditor を要求。重複 key も拒否。 |
| F4 | closed | [driver](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-core/orchestrator/campaign/p3_s4_loop_policy.py:268) の dry-pass で WAL・履歴・admitted view・critic digest を作らず結果を返す。 |
| F5 | closed | [driver](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-core/orchestrator/campaign/p3_s4_loop_policy.py:342) に `--critic-output` を追加し、`--emit-coder-input` と組の場合だけ K2 の 6 field に変換。 |
| F6 | closed | [namespace 登録](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-core/orchestrator/tests/test_p3_exploration_namespace.py:455) と [caller inventory](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-core/orchestrator/tests/test_campaign.py:5439) に新 driver を追加。driver の selector 宣言も契約に合わせた。 |
| F7 | closed | [proof test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-core/orchestrator/tests/test_mocc_template_proof.py:79) の指定 1 行を items の意味検査に変更。次行の全真検査は維持。 |
| F8 | partial | [実 policy_gate の型 22〜26 test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-core/orchestrator/tests/test_p3_s4_loop_policy.py:117) を追加。M-E1→P-E2、M-E7 の両層変異という再登録は下表に示す。変異注入の実走は親担当。 |
| F9 | closed | [loader](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-core/orchestrator/campaign/p3_s4_loop_policy.py:84) の重複 `validate_ir` を削除。 |

## 変更した既存 test

F6 では namespace の driver 表・名前列と新 driver 用 fixture 分岐、caller 件数表へ追加登録した。F7 では `_consumer` の指定 1 行だけを置換した。その他の既存期待値は変更していない。

## 確認の実走

`python3 -m py_compile`（変更した 5 ファイル）と `git diff --check` は成功。関数の直接呼出しで preview、性能 identity、dry-pass の正例・拒否例、履歴射影、critic 入力、型 22〜26 の実 gate、namespace の CLI・build spy・iteration・AST、caller inventory を確認した。proof items と現行 auditor 定義の一致も直接確認した。

**pytest は未実走。** 親の計算ノードでの焦点走が必要。

## 変異 M-E1〜M-E14・P-E1/P-E2 に使える fixture と単一理由性の見立て

| 変異 | fixture・見立て |
|---|---|
| M-E1 / P-E2 | grammar 拒否 fixture。subtype の診断 pin であり kill に数えない。 |
| M-E2 | TU だけが拒否する `unused_local`。静的には単一理由。 |
| M-E3 | auditor digest 不一致。静的には単一理由。 |
| M-E4 | 型 22〜26 を実 `policy_gate` に通す新 test。loader test と veto test の二層で確認。 |
| M-E5 | auditor 既定上限 21 の既存負例。静的には単一理由。 |
| M-E6 / M-E7 | IR 未知 key／bool 混同の既存負例。M-E7 は parser と `validate_ir` の**両層変異**として扱う。 |
| M-E8 | proposal の重複 key 負例。静的には単一理由。 |
| M-E9 / M-E10 | `excluded` と `justification` を落とす coder 入力 fixture。静的には単一理由。 |
| M-E11 | verify mode の cfg fixture。静的には単一理由。 |
| M-E12 | 実行時 threads を変えた性能 identity 拒否 test。静的には単一理由。 |
| M-E13 | WAL の `indeterminate`・`trace-timeout`・`build-error` 分類 test。静的には単一理由。 |
| M-E14 | coder のみの preview 正例と余分な key・重複 key の負例。静的には単一理由。 |
| P-E1 | reject subtype の既存診断 fixture。kill に数えない。 |

変異注入後の失敗 node 完全集合と単一理由性は未実走のため未確定。

## 所有外への波及

変更前は異なる性能動作点を同じ campaign に入れられ、coder のみの preview は拒否され、初回 dry-pass は admitted view で失敗していた。変更後、これらの境界が上記の挙動になる。`run_campaign` の caller inventory と coder entrypoint 閉集合を静的に点検し、既存 entry は維持した。spawn site 台帳と build sink 行番号 pin に新たな登録対象は見つからなかった。所有外ファイルは編集していない。

## 総括

F1〜F7・F9 を修正し、F8 の実 gate test と変異再登録の見立てを用意した。pytest・変異注入は未実走。commit は作成していない。