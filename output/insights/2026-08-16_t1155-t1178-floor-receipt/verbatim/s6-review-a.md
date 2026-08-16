[severity: must-fix]

[攻撃シナリオ] sibling `journal.jsonl` から全 `session-start` を削除し、`result.sessions`、消費 marker、attempt ledger は残す。holdout freeze は result の完了 session を渡し、inspector は start が 0 件だと完了 session 自身を認可集合へコピーするため、durable authorization が欠落した成果物を受理する。

[根拠 orchestrator/campaign/s8b_holdout_freeze.py:1431] journal は strict JSONL parse のみで、start を抽出後に result sessions を追加している。同 `s8b_holdout_freeze.py:1443`。`orchestrator/campaign/s8b_holdout_admission.py:1793` が start の有無だけで mode を選び、同 `:1867`〜`:1871` が completed session を start とみなす。

[提案] 公開 consumer では completed-only fallback を削除し、全完了 session に canonical start を必須化する。positive control は candidate fixture の journal から全 start を除去し、`session-start-coverage-mismatch` で holdout freeze が落ちること。テスト fixture も completed session だけで evidence を生成しない。

[成果物影響] durable authorization のない attempt を含む floor result が holdout freeze の受理集合へ入り、その admission 台帳 digest が正当な証拠として固定される。

[severity: must-fix]

[攻撃シナリオ] schedule の planned seq `S` に対し、`kind="planned"` のまま `attempt_id="<cell>::retry1"` とした偽 `session-start` を journal に追加し、その retry1 の marker と ledger 行を足す。planned 分岐は cell、round、trigger しか確認せず canonical attempt ID や seq 一意性を確認しないため、失敗 planned trigger のない retry 消費が通る。holdout freeze は journal の意味検証も行わない。

[根拠 orchestrator/campaign/s8b_holdout_admission.py:1355]〜`:1371` の実行時認可、および同 `:1834`〜`:1847` の inspector 再検査に `attempt_id == f"{cell_id}::seq{seq}"` がない。marker は同 `:1910` の start 集合だけで正当化される。一方、正しい強い検査は `orchestrator/campaign/s8b_ratified_freeze.py:2057`〜`:2075` に既に存在するが、holdout freeze は利用していない。

[提案] planned/retry 共通の canonical authorization validator を作り、consume、inspector、ratified、holdout freeze で共有する。planned attempt ID、retry ordinal、retry attempt ID、seq/attempt の一意性、start/completion の対応を完全照合する。positive control は上記の偽 planned→retry1 start と対応 marker/ledger を作り、marker の存在にかかわらず拒否させる。

[成果物影響] 未認可 retry の ledger 行を追加でき、`attempt_row_count` と `ledger_projection_sha256` を攻撃者が増やした状態が有効な台帳として受理される。

[severity: must-fix]

[攻撃シナリオ] holdout freeze 入力の `result.json` だけで sort cell の `binary_sha256`、`bin_hash_short`、binary admission subject、outer SHA、SWO receipt の `binary_sha256` を同じ偽値へ更新する。sibling manifest と session の実測 SHA は元のままにする。manifest は bytes hashしか確認されず、live verifier に `expected_binaries` が渡らないため、SWO identity は result record 自身との自己照合になり、改変が通る。

[根拠 orchestrator/campaign/s8b_holdout_freeze.py:1417]〜`:1429` は sibling manifest の存在と bytes hashだけを検査し、内容を result と比較しない。同 `:1451`〜`:1459` は `expected_binaries` を省略する。`orchestrator/campaign/s8b_floor_stats.py:1004`〜`:1010` は binary/SWO identity の期待値を record 自身から取り、外部 SHA 照合は同 `:1013`〜`:1018` で `expected_binaries` がある場合だけ発火する。ratified 側には対照的に `orchestrator/campaign/s8b_ratified_freeze.py:2286`〜`:2293` の manifest/journal 再導出照合がある。

[提案] holdout freeze でも sibling manifest を完全検証し、`result.binaries == manifest.binaries` を要求する。さらに検証済み journal から cell→`binary_sha256_at_measure` を導出して `expected_binaries` に渡す。positive control は上記の result-only SHA 改変を行い、manifest または journal receipt 不一致で拒否させる。

[成果物影響] 実測されていない binary identity と SWO receipt に床値を結び替えた result が freeze 入力として受理され、将来の certified 選択が誤った binary の証拠鎖を参照する。

## 総括

最も危険なのは、holdout freeze が result の binary identity を manifest・実測 journal に束縛せず、SWO identity 5 項目のうち binary SHA を自己照合にしている点である。

受理集合は fix2 で「start＋marker、completion なし」を正当に広げた一方、completed-only fallback と canonical attempt ID 未検査によって不正にも広がっている。fix1 の runtime/portable 分離、および既存 assert の変更には独立した緩和・skip・xfail 化は見つからなかった。

台帳削除は ratified、holdout freeze、report の現行公開経路で fail-closed になる。再構成攻撃の保証外 docstring、固定 leaf の軸許可、raw `compiler_version` の公開成果物・journal・Markdown への漏洩にも問題は見つからなかった。pytest は実行しておらず、以上は静的レビュー結果である。