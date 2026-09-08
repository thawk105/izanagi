## 書いた spec

[mutation-probe-spec.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/output/insights/2026-09-08_t1998-stock-inline-parts/mutation-probe-spec.json)

- M1〜M16 の全 16 件を登録
- 全件 `expected_status: SURVIVED`、`expected_nodes: []`、`hang_risk: false`
- `estimated_run_seconds: 150` は実測 83 + 5 + 60 = 約 148 秒を丸めた値
- `timeout_seconds: 1800`、`hang_timeout_seconds: 2400`
- category は harness が受理する `negative` と `positive` のみ使用

## 変異ごとの単一理由性の判定

| ID | 変異位置 (file:line) | 同じ入力を先に拒否する層の有無 | 単一理由か |
|---|---|---|---|
| M1 | `orchestrator/campaign/t1998_stock_inline_pair.py:526` | なし。arm 別 preregistered source digest は admission が比較しない | はい |
| M2 | `orchestrator/campaign/t1998_stock_inline_pair.py:719` | なし。sibling failure receipt を読む他層はない | はい |
| M3 | `orchestrator/campaign/t1998_stock_inline_pair.py:855` | なし。campaign lock の短縮 gitlink と preregistration の比較だけを無効化し、冗長な WAL 比較は触らない | はい |
| M4 | `orchestrator/campaign/t1998_stock_inline_pair.py:1095` | なし。upstream admission は `unstable` を拒否しない | はい |
| M5 | `orchestrator/campaign/t1998_stock_inline_pair.py:938` | なし。upstream は全 8 点を通し、target 選択は consumer のこの位置だけ | はい |
| M6 | `orchestrator/campaign/t1998_stock_inline_pair.py:208` | なし。`expected` と `actual` の拒否 payload 投影は `as_dict()` だけ | はい |
| M7 | `orchestrator/campaign/t1998_stock_inline_pair.py:915` | なし。事後に job body digest を比較する他層はない | はい |
| M8 | `tools/pegasus/submit_t1998_balanced_stock_inline.sh:96,112,172` | なし。workload 集合と qsub 回数を固定するのは launcher contract だけ | はい |
| M9 | `tools/pegasus/submit_t1998_balanced_stock_inline.sh:54` | なし。repository の親を output parent にした場合、生成 root は repository の sibling となり job body の内側検査とは重ならない | はい |
| M10 | `orchestrator/campaign/t1998_stock_inline_pair.py:371` | なし。型付き CMake define を正規化する他層はない | はい |
| M11 | `orchestrator/campaign/t1998_stock_inline_pair.py:585` | なし。bench executable の argv 位置を検査する他層はない | はい |
| M12 | `orchestrator/campaign/t1998_stock_inline_pair.py:661` | なし。他の比較は記録済み digest 同士で、manifest からの canonical 再計算はここだけ | はい |
| M13 | `orchestrator/campaign/t1998_stock_inline_pair.py:498` | なし。`verify_done` を含む env tag 集合比較はここだけ | はい |
| M14 | `orchestrator/campaign/t1998_stock_inline_pair.py:970` | なし。attempt 外 record の anomaly、verdict、所属を全件走査する他層はない | はい |
| M15 | `orchestrator/campaign/t1998_stock_inline_pair.py:864` | なし。off-pair genome の診断 knob を全走査するのはここだけ | はい |
| M16 | `tools/pegasus/submit_t1998_balanced_stock_inline.sh:115,130,142` | なし。submit receipt schema literal を固定するのは launcher contract test だけ | はい |

## 登録しなかった変異とその理由

M1〜M16 は全件登録しました。以下の冗長 gate は裁定どおり登録していません。

- `pair-cardinality`
- `producer-rejected-variant` の receipt 欠損、abort、stage 欠損部分
- WAL gitlink の一致検査
- COMMIT の environment contract digest
- `admission.lock_sha256` と `admission.wal_sha256` の TOCTOU guard

いずれも同じ入力を upstream admission、finalizer、または同じ bytes から作られた admitted view が先に拒否するためです。

## 総括

全 replacement の `old` が HEAD source 内で逐次ちょうど 1 箇所に一致すること、全変異後の Python AST と shell 構文、JSON 契約、ID 順序、結合文字不在を静的確認しました。

source は変更せず、指定 JSON 以外の file は作成していません。HEAD は `4a5f2cae50838f6a446e17eb8e9ac3e61ed010ca` のままです。harness、test、build、benchmark、qsub は実行せず、git add と commit も行っていません。