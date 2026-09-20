## レンズ A

**must-fix / should はありません。指定条件下で判定を変える実装不具合は見つかりませんでした。** テストの環境依存と変異の帰属には nit があります。

以下、`checker` は `tools/check_ai_provenance.py`、`tests` は `orchestrator/tests/test_check_ai_provenance.py` の行番号です。pytest・変異試験は未実走です。

### must-fix

該当なし。

### should

該当なし。

### nit

**N1 — merge 高速経路を期待するテストが ambient config に依存する。**

- **根拠:** tests:145–148 の `_init_repo` は user 設定だけを追加する。tests:8608、8670、8763 は merge gate が通る、または注入しない側の設定が未設定であることを前提とする。
- **成果物への影響:** checker の判定差はない。ambient `diff.relative` / `diff.ignoreSubmodules` により、正しい実装でもテストが赤になり、意図した変異箇所まで到達しない。
- **是正案:** 新規テスト群の環境で system/global/環境注入設定を隔離する。設定 gate の実 Git 検査では、その隔離環境に対象設定を明示的に加える。指定範囲外の共通 fixture による隔離の有無は未確認。

**N2 — 冗長 gate と変異の具体的編集を区別する必要がある。**

- **根拠:** checker:1663 の `headers != requested` が偽なら、現在の構築方法では key 集合も必ず一致する。`result.keys()` 検査だけを削除しても挙動は変わらない。author 報告:59 の M-4 は「部分辞書を返す」変異であり、「見出し検査の片側を削除する」変異とは異なる。
- **成果物への影響:** 現行判定は変わらない。冗長検査の削除を M-4 と扱うと、survivor と期待 kill の説明が食い違う。
- **是正案:** M-4 は最終不一致分岐の `return None` → `return result` など、編集を固定する。M-5/M-8 も具体的編集を記録し、最初の失敗 assertion と公開結果差を分けて報告する。

**N3 — 親表の空行検査は、空行からの fallback を保証しない。**

- **根拠:** checker:1987 が空 row の `row[0]` を参照するため、空行は checker:2015 より前に `IndexError` になる。
- **成果物への影響:** patch 前からの例外挙動であり、新しい判定差ではない。ただし「すべての不正行で親表を `None` にして継続する」という説明は成立しない。
- **是正案:** 「既存 ancestry 計算が成功した出力に対する追加キャッシュ検証」と限定する。例外維持という計画に従うなら、検査順を安易に変更しない。

**N4 — 一部境界はコード上正しいが、専用の到達テストがない。**

- **根拠:** tests:8489–8494 に先頭非見出し token がない。tests:8389 は空 path の helper 検査であり、worker が取得済み `[]` を使う検査ではない。tests:8836 は空 delta、8856 は correction による全史復帰で、通常の非空 delta の path stdin は pin しない。tests:8813 は CAB parser の呼出し順を観測しない。
- **成果物への影響:** 現行の判定差は認めない。これらの分岐の将来回帰を局所化する証拠が不足する。
- **是正案:** 先頭 path、authoritative worker の空 list、通常の非空 receipt delta、CAB より先の parser 失敗をそれぞれ直接 pin する。

### 実装の検査結果

| 対象 | 結論 |
|---|---|
| parser の六条件 | checker:1646–1664 は、末尾 hex path、要求 OID と同名の path、見出し欠落、先頭 path、空 token、終端 NUL 欠落を拒否する。同名 path が辞書を上書きしても、`headers` に重複が残り全体破棄される。 |
| 見出し欠落の限界 | 単独の欠落は拒否する。ただし「欠落した見出しと同名の hex path が代役になる」という複合破損まで識別する形式ではない。正常 Git が `--always` で全見出しを出す前提と区別すべき。 |
| LF 混入 | 指定実験の空差分・末尾空差分・commit pair は NUL 見出しで、余分な LF はない。path 内の LF と、tree pair の別形式を混同していない。CR の text-mode 変換も旧経路と共通。 |
| 捕捉例外 | `_git` は非ゼロ終了を `RuntimeError` にする。`check=True` / timeout 指定がないため、通常のこの呼出しから `CalledProcessError` / `TimeoutExpired` は発生しない。固定正規表現の構文エラーもない。`MemoryError` は捕捉されないが、計画は資源障害までの等価性を対象外としている。 |
| PIPE と量 | `subprocess.run` は stdin 書込みと stdout/stderr 回収を `communicate` で処理するため、PIPE 容量を超えるだけでは deadlock しない。12k OID の stdin は約0.5–0.8 MB。stdout の全保持と parser の追加メモリは残る。 |
| merge 部分結果 | checker:1708–1711 で `None` を返すと、呼出し側:2612 に部分辞書は渡らない。worker:2119–2120 から `parent_paths=None` となり、1786–1787 で全親を従来取得する。 |
| config gate | checker:1689 は両方 rc=1 の場合だけ有効。rc=0、その他の rc、捕捉例外では無効。読み取り専用確認で、多値の最後の値・大小文字違い・`GIT_CONFIG_COUNT` はいずれも rc=0 になった。通常の設定読込み対象は system/global/local と、有効化された worktree 設定を含む。 |
| worker / oracle | checker:2113 は ancestry あり・authoritative の両方を要求する。空 `[]` は2116の `is None` を通過せず使用される。merge gate 無効時は従来の親別 diff。oracle の `shared_values` は `{}` で、実装 path があれば従来の2回 parse。 |
| parser 失敗順 | checker:2077 の呼出しは、旧 `validate_message` 冒頭の parse を直前へ移したもの。CAB parse:1485、waiver、worker 内 path 取得より先という順序は維持される。 |
| 親表検証 | checker:2022 の向きは正しい。逆 topo index は親＜子。空 tokens では `len(set()) != 1` は **True**。要求根の欠落、閉包外親、混在長は親表全体を無効化する。bits/mask はその前に計算済みで、追加検証は変更しない。 |
| 取得位置 | checker:2604–2615 は correction 再選択後・pool 前。receipt 再利用時は最終 delta のみ取得する。merge ゼロ件でも config の2 subprocess は走るが、指定計数テストはそれを一律計数していないため衝突しない。 |
| 既存互換性 | tests:7312 は message の log/show のみ計数し、parse 回数変更では壊れない。7366 の比較も parse 回数を pin しない。`_Ancestry.parents` は末尾の既定値付き field なので、既存3/4引数の positional construction は維持される。 |

### 追加26テストの到達性

名前は `test_` を省略。「直接」は helper/validator を直接呼び、高速経路の配線全体は検査しない意味です。

| テスト（開始行） | Git・stub と到達先 |
|---|---|
| ancestry_parent_rows_match_show_parents（8316） | 実 Git。親表を直接検査、非 authoritative。 |
| parent_cache_invalid_rows_fall_back（8336） | rev-list 出力だけ注入。他は実 Git、authoritative worker。 |
| range_and_oracle_keep_legacy_parent_acquisition（8370） | 実 Git、range/oracle の除外を検査。 |
| batch_nonmerge_always_emits_empty_headers（8389） | 実 Git、batch helper 直接。 |
| batch_nonmerge_paths_equal_legacy_in_order（8419） | 実 Git、旧取得と helper を直接比較。 |
| batch_nonmerge_hex_paths_discard_entire_batch（8438） | 実 Git、helper と authoritative history fallback。 |
| batch_nonmerge_invalid_output_restores_public_result（8463） | batch subprocess のみ破損注入。実 validator・authoritative CLI。 |
| batch_merge_parent_sets_equal_legacy（8519） | 実 Git、merge helper 直接。 |
| batch_merge_parent_slots_and_headers（8534） | 実 Git、helper の stdin/stdout 契約。 |
| batch_merge_keeps_combined_diff_contract（8576） | 実 merge・実 `--cc`、cache 注入を直接比較。 |
| batch_merge_late_failure_discards_all_parent_batches（8608） | batch 出力注入、実 legacy diff・validator・authoritative CLI。 |
| batch_merge_ignore_submodules_uses_legacy_verdict（8635） | 実設定・実 gitlink・実 CLI。gate 無効化を検査。 |
| merge_path_batch_config_gate（8670） | 一方の config rc を stub、他方は実 Git。gate 直接。 |
| normal_audit_reuses_agent_values_once（8689） | 実 parser、ancestry あり。authoritative path 最適化は通らない。 |
| agent_values_none_and_empty_are_distinct（8708） | 実 parser、validator 直接。 |
| shared_agent_values_preserve_validator_results（8734） | 実 parser・実設定、validator 直接。 |
| shared_agent_values_stay_with_their_commit（8749） | 実 parser・authoritative CLI、oracle と比較。 |
| path_batch_subprocess_counts_and_selected_order（8763） | normal は実高速経路、fallback は出力注入、oracle は ancestry=None。 |
| shared_values_parser_failure_precedes_paths（8813） | parser 例外注入、oracle と ancestry 経路。 |
| path_batches_follow_receipt_final_selection（8836） | 実 receipt・CLI。warm の selected は空。 |
| path_batches_follow_correction_full_history_fallback（8856） | 実 receipt・CLI・再選択後の batch。 |
| range_path_batches_stay_disabled_at_repository_boundaries（8883） | 実 shallow/graft/replace、非 authoritative。 |
| path_cache_misses_and_empty_root_keep_distinct_contracts（8911） | 実 Git、親表欠落を注入、authoritative worker。 |
| merge_path_batch_config_failure_disables_optimization（8935） | config 例外 stub、gate 直接。 |
| path_batch_does_not_swallow_interrupt（8950） | `_git` 中断 stub、helper 直接。 |
| shared_values_leave_message_file_and_waiver_calls_unchanged（8964） | 実 staged Git・parser・message-file CLI。履歴高速経路外。 |

**追加テストに「旧新版の validator / `--cc` を両方 stub にして緑になる」構成は見つかりません。** `_path_oracle_audit`（8292）は旧取得経路へ戻す wrapper で、判定器を偽の結果に置換していません。ただし同じ変更後モジュールを使うため、旧 blob との全史比較の代替にはなりません。

### M-1〜M-9 の静的評価

| 変異 | 期待 kill の評価 |
|---|---|
| M-1 | 親 tuple 一致で検出可能。 |
| M-2 | `[outside]` の `ancestry.parents is None` が先に失敗する。契約 kill として妥当。 |
| M-3 | tests:8404 の exact argv assertion が出力検査より先に失敗する。契約 kill。 |
| M-4 | 最終不一致時に部分辞書を返す編集なら、`bad: []` が使われ author finding が消える。判定差 kill。 |
| M-5 | 真の見出しを維持して hex path を受理する編集なら検出可能。単に全 hex 判定を無効化する編集は別物で、先頭 token 拒否により生存し得る。 |
| M-6 | gate を迂回すると gitlink が実装 path となり、公開 rc=0→1。判定差 kill。 |
| M-7 | 最後の失敗で先行集合を返すと、注入した空集合により author finding が消える。判定差 kill。 |
| M-8 | 混在 fixture は取り違えを検出できる構成。ただし具体的な編集未確定のため、あらゆる取り違えの kill は保証できない。 |
| M-9 | 取得済み空値の再 parse が tests:8721 を破る。判定差ではなく契約 kill。 |

author の「実装済み・未実走」は資料と矛盾しません。consumer の波及列挙は報告として確認しましたが、今回の射影外の consumer 本体や実行結果までは裏付けていません。

## 総括

**GO — 静的実装レビューとして。**

判定差を生む must-fix は認めません。全体 fallback、oracle/range の除外、merge 設定 gate、値共有の失敗順は裁定と整合します。

これは実走合格の認定ではありません。残る確認は、環境を固定した追加・既存テスト、具体的編集を固定した M-1〜M-9、親担当の旧 blob／新版全史比較と性能測定です。