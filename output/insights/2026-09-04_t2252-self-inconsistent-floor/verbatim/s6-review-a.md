## must-fix

無し

## nit

- `test_registered_healthy_pegasus_g2_pin_remains_selectable`（[test_layer3_report.py:3593](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/tests/test_layer3_report.py:3593)）は production 差分を空にしても緑になる正例。ただし、g2 の過剰除外を検出するための意図された正例であり、負例群とは役割が異なる。

## 正しく実装されていた点

- 現物差分は `s5-diff.patch` と SHA-256 まで一致し、変更は指定された production/test の 2 file のみ。共有台帳、新 status、schema、`test_env_contract.py`、effective-clock の production 再検査は入っていない。
- 宣言は consumer-local な `frozenset[tuple[str, str]]` で Pegasus g1 の 1 件だけ。[layer3_report.py:77](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:77) の比較は `(contract_pin.path, contract_pin.sha256)` の完全一致で、正規化・部分一致・path-only 比較はない。
- `_validated_pin_path` は除外判定より先に完遂される（[layer3_report.py:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:524)）。SHA 不一致、directory 外、非 file は従来どおり例外になり、missing は `pin-file-missing` 確定後に系列除外される。
- 新たに一致なしへ転じるのは、解決済み v2 authority が Pegasus g1 の exact ref を持ち、従来なら within-run 候補が一致した campaign。linux-baremetal、g2、v1、env mismatch、宣言外の missing pin は変わらず、新しく floor 一致を得る campaign はない。
- 除外は候補 path ではなく campaign の contract ref で決まり、全 within-run document の append 前に作用する（[layer3_report.py:537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:537)、[layer3_report.py:580](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:580)）。したがって genome 有無、直下 copy、hardlink、symlink、pin、exploration suffix のいずれからも候補は戻らない。
- `scanned_files` と `skipped_no_floor_block` の算出位置は不変。除外系列では `candidate_files` と `mismatches` が空になるが、「候補なし／候補間不一致なし」という従来の意味を保ち、理由 key が null の理由を説明する。
- between-run の候補形成、pin-only 除外、一致判定は未変更。理由 key も within-run にだけ付与される（[layer3_report.py:624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:624)）。between-run subtree は従来と同値で、別途 generator SHA だけが当然変わる。
- 追加負例は実 `build_report`、実 authority、実較正 bytes を使用し、直下 copy と系列単位抑止・between-run 維持を検査している（[test_layer3_report.py:3513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/tests/test_layer3_report.py:3513)、[test_layer3_report.py:3545](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/tests/test_layer3_report.py:3545)）。stub・monkeypatch はない。
- g2 正例は registry の実 ref と実 bytes を production 関数へ渡す。[test_layer3_report.py:3621](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/tests/test_layer3_report.py:3621) は全 required 世代の実 bytesを SHA 検証して読み、実 expected 生成・実 predicate で宣言集合の両方向一致を検査し、`test_env_contract.py` の helper を import していない。
- 既存テストの変更は裁定指定の 3 件だけ（[test_layer3_report.py:3469](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/tests/test_layer3_report.py:3469)、[test_layer3_report.py:3818](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/tests/test_layer3_report.py:3818)、[test_layer3_report.py:3849](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/tests/test_layer3_report.py:3849)）。他の既存期待値・literal・pin の変更はない。

## 総括

静的検査では must-fix なし。裁定 v2 の系列単位除外、検証優先、between-run 不変をそのまま実装している。
最も重要な境界は、除外条件が contract ref の exact pair に閉じ、全 within-run path source の候補追加を一律に止めている点。
本レビューでは pytest を実走していない。親は進行中の全ファイル走で、特に実 bytes を読む宣言束縛正例と g2 正例を確認すべき。
段 6 後半では予定どおり M1〜M9 の変異結果を実測すればよい。