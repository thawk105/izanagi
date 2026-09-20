## 総括

**plan v2 を実装済み・pytest は未実走です。** commit・docs 編集はしていません。

変更は指定された次の3ファイルです。

- [tools/check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2803-unit-impl/tools/check_ai_provenance.py:2239)：`_attribute_fingerprint`、`_receipt_bindings`、`_publish_audit_receipt`、`_receipt_prefix`、`_audit_history` を変更。schema は2。
- [test_check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2803-unit-impl/orchestrator/tests/test_check_ai_provenance.py:8267)：指定テストを追加。既存 fingerprint assertion は `[0]` によって従来の digest 比較を維持。
- [計測 probe](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2803-unit-impl/build/probe/t2803_receipt_attr_cold_rate.py)：指定 usage、同一 checkout での旧新比較、候補包含判定、遷移集計、clean 確認、元の detached HEAD への復帰を実装。ignored であることを確認済み。計測は未実施。

旧形は absent を含む候補集合の追加・削除とも digest 不一致で拒否します。新形は absent 候補の追加を許し、削除は保存候補の包含検査で拒否します。候補列挙、digest の5 key、prune、環境 partition の構造、`main` の dispatch 判定は変更していません。保存直前にも候補集合を再照合し、監査中に変わった候補で受領証を発行しないようにしています。

**追加テスト一覧**

すべて `orchestrator/tests/test_check_ai_provenance.py` 内です。各ケースに受領証を削除した oracle との rc・stdout・stderr 一致を含めています。

| ID | test 名 |
|---|---|
| T-pos-1 | `test_attribute_absent_directory_addition_warm_hit` |
| T-pos-2 | `test_attribute_new_candidate_file_falls_back` |
| T-neg-1 | `test_attribute_retired_directory_falls_back` |
| T-neg-2 | `test_attribute_untracked_file_removal_falls_back` |
| T-neg-3 | `test_attribute_candidate_lstat_unreadable_falls_back` |
| T-neg-4 | `test_attribute_candidates_damage_falls_back` |
| T-neg-5 | `test_attribute_candidates_extra_path_falls_back` |

T-neg-4 は指定の7破損形に、非文字列・復号後の空 payload・空要素を追加し、古い有効受領証の有無と組み合わせた20ケースです。

共有 helper `_attribute_merge_repo` に既定値付き `path` 引数を追加しました。既存呼び出しの fixture は変わりません。T-neg-1 は `tools/retired/shared_lines.py` を使用し、digest 同一・候補減少・merge の finding・全史1回を固定しています。

**変異対応表（静的確認。kill 実測は未実施）**

nodeid は上記ファイル名に `::` と次の test 名を連結したものです。

| 変異 | 赤になる test nodeid の末尾 | 赤理由 |
|---|---|---|
| M-1 `working=[]` | `test_additional_attribute_sources_fall_back[untracked]` | 実在属性追加を見逃し、rc=1 期待が0 |
| M-2 absent 再包含 | `test_attribute_absent_directory_addition_warm_hit` | digest 同一 assertion／delta のみの監査が失敗 |
| M-3 unreadable 除外 | `test_attribute_candidate_lstat_unreadable_falls_back` | digest 変化 assertion／cold 観測が失敗 |
| M-4 包含検査削除 | `test_attribute_retired_directory_falls_back` | merge を再監査せず rc=1 と finding を失う |
| M-5 包含方向逆転 | `test_attribute_absent_directory_addition_warm_hit` | 候補増加で cold となり delta 観測が失敗 |
| M-6 不正形式を空集合扱い | `test_attribute_candidates_damage_falls_back[False-base64]` | 不正受領証を再利用し全史観測が失敗 |
| M-7 空文字で保存 | `test_attribute_candidates_extra_path_falls_back`、`test_attribute_absent_directory_addition_warm_hit` | 保存 field の復号前提／warm 再利用が失敗 |
| EQ-1 `sorted(set(attribute_paths))` | なし | 元が集合なので等価。SURVIVED 期待 |

機構を stub しておらず、実 Git・実受領証を使用しています。T-neg-3 のみ指定の `Path.lstat` 障害注入です。M-6 の key 欠落ケースは別の key 集合検査でも拒否されるため、kill 帰属には使用していません。

**検索・所有外への波及**

指定パターンを `rg -n` で `orchestrator tools hooks` に再帰検索した結果は、**233 matches／229行／68ファイル**でした。別系統の receipt schema も部分一致します。本変更に関係する結果は次のとおりです。

| 対象 | 検索結果・確認 |
|---|---|
| checker 本体 | schema L2239、fingerprint L2271・2375、bindings L2353・2446・2593、候補保存／検査 L2453・2455・2493・2500・2609・2677 |
| 既存 fingerprint テスト | L8165・8167・8169・8171・8231。digest 比較を維持 |
| 新設テスト | L8269〜8406 に fingerprint・候補 field の参照 |
| 所有外 caller | 当該2関数の所有外 caller は検出なし |
| 既存 cold 強制 helper | L8468 の `_receipt_bindings` stub は例外を投げるため、返値 tuple の arity に依存しない |
| duration ledger | `acceptance_duration_ledger.json:3588` は既存 test 名のみ。変更不要 |
| schema／key pin | provenance schema=1 を固定する既存テストは検出なし。既存 schema 負例は `+= 1`。key 集合の固定は本体 `_receipt_prefix` にあり更新済み |

consumer の静的確認結果：

- `test_dev_wave_land.py`：tip/blob/実行 bytes/rc の別受領証と acceptance schema を検査。今回の内部 JSON とは別契約。
- `test_dev_wave_wait.py`：acceptance／producer receipt と checker 実行結果を検査。内部候補 field への依存なし。
- `test_pegasus_dispatch_compute.py`：dispatch receipt v2、task、argv を検査。今回の schema=2 とは別定数。
- `test_hooks.py`／`hooks`：checker のパス・起動形式の literal pin。変更不要。
- `test_check_docs.py`／`tools/check_docs.py`：provenance 実行経路・land receipt の文言 pin。内部 schema／候補 field の pin は検出なし。

**検査結果と未完了事項**

- `git diff --check`：成功。
- 3ファイルの AST 構文検査：成功。
- `python3 tools/check_codex_agents.py`：成功。
- `python3 tools/check_docs.py`：違反なし。
- `python3 tools/run_tests.py orchestrator/tests/test_check_ai_provenance.py -q`：**rc=16。`qstat -Q preflight rc=1`、`child_started=false`。実走 nodeid はありません。**

親での焦点走、consumer test、変異 matrix、E-1／E-2、受入全走が残っています。判定等価性・kill・計測効果を実証済みとは報告しません。候補外 directory の既存限界、および既存2テストが absent 候補差への感度を失う点も、裁定どおり残ります。