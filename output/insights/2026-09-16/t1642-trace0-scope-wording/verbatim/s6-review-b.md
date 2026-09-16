**[所見 1] 焦点走の「間接経路2段まで追加漏れなし」は訂正が必要**

**判定 (must-fix / nit): nit**

**成果物影響 (1 行):** 検査範囲の記録が不正確になるが、今回の差分による certified 選択・受理集合の変化は確認できない。

**根拠 (file:line):**

- 親の `s4/adjudication.md:21` は4ファイルで追加漏れなしとする。
- `orchestrator/tests/test_pegasus_policy_registry.py:434` のテストは、`:485` から `_tracked_live_sources` → `_source_moved_reads` を呼ぶ。`:343` の列挙には変更した両ファイルが入り、`:329` で本文を読む。
- `orchestrator/tests/test_pegasus_dispatch_compute.py:2246` のテストも、`:2249` で `tools/**/*.py` を列挙し、checker 本文を `_best_effort_qdel_references` に渡す。

前者は移管済み policy key の読取り、後者は関数参照の検査であり、今回の文言変更による違反は静的には認められない。しかし、参照関係がないとは記録できない。

**この所見が誤りである場合の条件:** 「追加漏れなし」が consumer の網羅を意味せず、上記2検査を確認して差分非影響と除外した記録が別途存在する場合。

**訂正案:** 上記2 nodeid を参照表に追記し、「直接関係する焦点走4ファイル。横断 consumer 2件は静的に差分非影響と判断」と記す。必要なら親の受入全走で実行結果を確認する。本レビューでは実行しない。

**[所見 2] 過去 insight を対象外にする根拠は、歴史記録という属性だけでは不足する**

**判定 (must-fix / nit): nit**

**成果物影響 (1 行):** 過去レポートの見出しだけを引用した際の過大解釈が残るが、本文全体から完全除去の証明という主張や受理集合の変化は確認できない。

**根拠 (file:line):**

- `output/insights/2026-08-11/t816-fn2-trace-v2/README.md:38` は「規律1」の見出し、`:40` は3本 pass。
- 同 `:120` は保証を選定 macro context の正規化 preprocess 出力・include 活性に明確に限定している。
- `s4/adjudication.md:61` は追記訂正が可能と認めながら、`:62` で D780 の対象外とする。
- `verbatim/d780.md:5` の決定1には、歴史記録一般を除外する記述はない。

今回の非編集判断自体は、既存の限定説明があるため妥当と判断する。ただし「過去だから対象外」は一般化できない。

**この所見が誤りである場合の条件:** 対象外という記述が、歴史記録一般ではなく、この文書の既存限定説明を根拠にした個別判断のみを意味する場合。

**訂正案:** 裁定理由を「本文全体では完全除去を主張していないため、必須訂正とはしない」に限定する。日付付きの射程注記は任意改善として残す。

## 総括

**must-fix はゼロ、nit は2件。** 静的検査で、正しさゲートの緩和は確認しなかった。

- **受理集合:** 基準 commit と現物を独立に AST 比較し、module docstring を除いて一致した。CLI は `tools/check_trace0_preprocess_identity.py:729` で `GUARANTEE` を参照する。当該 docstring を `__doc__`・`inspect.getdoc` 等から判定に使う consumer は走査範囲で見つからなかった。ソース bytes の参照は存在するが、digest 束縛の変更と判定ロジックの変更は区別すべきである。
- **manifest:** `tools/pegasus/mocc_trace_pilot.sh:200`、`:568` の単一行条件と `:575` 以降の禁止表現に新文言は抵触しない。生成・validator・receipt/job-result/pair の確認範囲で、今回の長さを拒否する上限や旧 manifest digest の固定照合は見つからなかった。生成 JSON bytes は変わる。
- **変異登録ゼロ:** 「十分条件」への置換を殺す既存 gate は見つからなかった。placeholder 検査は `tools/check_docs.py:2591` の文書族、禁止語検査は同 `:5639` の operations 本文が対象。hooks も当該文言の意味を検査しない。登録ゼロは支持する。ただし SURVIVED は未実走の予測であり、実測結果ではない。文言 pin の追加は別防壁と同じではなく、D780 が禁止しているとも読めないが、今回必須にする根拠はない。
- **焦点走:** 提示された **785 passed, 1 skipped、rc=0** を与件として採用する。`test_mocc_trace_job_contract.py:76` には pilot の `bash -n` 検査もある。実装子の直接実行が拒否された事実と、親の焦点走による検査結果を混同しない。

段7の worklog / insight には、次を残すべきである。

1. 基準 commit、変更した2ファイルと A1/A6/A7、統一文言の逐語。
2. checker の保証・受理条件・report schema は不変、manifest の `reason` と bytes は変更したこと。
3. checker SHA の採取箇所 `mocc_trace_pilot.sh:1753`、pilot SHA の採取箇所 `submit_mocc_trace.sh:319`。将来の束縛は変わり、過去 receipt・台帳は変更していないこと。
4. 親の焦点走結果、実装子が報告した比較結果、本レビューの独立 AST 比較を、実施主体別に記録すること。
5. 受入全走の結果は本レビューには未提示。性能再計測・完全除去の実証・変異実走・未知の全 digest pin の不在証明はしていないこと。
6. 変異ゼロの探索根拠、横断 consumer の追記、過去 insight を非編集とした個別理由。
7. 「完全除去を証明」「admission toolchain と同一」「全 consumer を実走済み」とは主張しないこと。

本レビューではファイル変更・テスト実行を行っていない。