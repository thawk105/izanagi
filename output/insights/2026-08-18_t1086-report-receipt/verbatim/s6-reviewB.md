## must-fix

[RB-1] real — M10 の指定 killer は後段検査に先取りされる  
根拠: containment は `orchestrator/campaign/s8b_oracle_report.py:1837` だが、これを削除しても親 symlink は `:1876`、leaf symlink は `:1905` で拒否される。指定された `test_store_reverification_rejects_out_of_root_symlink[parent/leaf]` は成功したままで、赤になるのは F226 の source-pin 2 件だけ。M10 は containment と no-follow 層の同時変異へ変更するか、等価変異として登録から外す必要がある。  
成果物影響: 現 M10 単独では observations、oracle verdict、combined verdict の値・受理集合は変わらず、機能的 kill と数えると symlink 外部参照を拒否する実効ゲートの検出力を過大申告する。

[RB-2] real — M6 の登録位置では receipt 欠落経路を変異できない  
根拠: 登録は validator が欠落時に `[]` を返す変異だが、欠落は `orchestrator/campaign/s8b_oracle_judge.py:607-611` で validator 呼出し前に処理される。validator は `:330` から始まり、実際の呼出しは receipt が存在する場合だけの `:613-622`。validator 側を変異しても `test_official_store_reverification_absence_is_indeterminate` は緑のままで、F226 pin だけが赤になる。M6 を caller の欠落分岐削除へ再登録すべき。  
成果物影響: receipt 欠落拒否の機能変異を検査できないため、このままでは欠落 official observations が determinate oracle verdict、続いて determinate combined verdict に到達し得る回帰への変異証拠が成立しない。

## nit

[RB-3] real、nit — report テストの `_judge` が receipt を暗黙に偽造する  
根拠: `orchestrator/tests/test_s8b_oracle_report.py:380-400` は official observations に receipt が無ければ正常 receipt を自動挿入する。これにより、同ファイルの既存 report→judge テストは production の「direct API は non-certifying」という意味ではなくなった。専用の欠落対照と実 v2 E2E は別に存在するため、現時点の land blocker とはしない。  
成果物影響: production 成果物は変わらない。将来 report 側の receipt 配線が退行した際、一部の統合テストがその欠落を隠す検出力上の nit。

## 確認済み事項

- M1〜M5、M8、M9 は、現在の実装位置へ正しく注入すれば指定 nodeid が機能差を直接検出する。
- report/judge の全変異では、指定どおり F226 の source-pin 2 件も赤になる。
- `PIN_GATE_SPEC_RAW` の report、judge、artifacts SHA-256 は現在の source bytes と完全一致した。
- `PIN_GATE_SPEC_SHA256=a2228d3179c876201c355d5f5e0531b55e8e0d98519121ea75a7ed5a9fbdf633` も raw bytes の実計算値と一致した。
- official exact-key pin は新 key を含み、legacy exact-key pin は従来集合を維持している。
- judge は report の定数を import しておらず、新規 `errno`、`os`、`stat` は先頭 import かつ使用済み。
- manifest-contract、official-perf-closure、n-pilot、exploration に新しい直接 consumer は無い。

## 総括

既知の `_resolve_store_path(resolve(strict=True))` 2 件は再掲していない。  
新たな production 値の破損は確認できなかった。  
ただし M10 は no-follow 層にマスクされ、指定 symlink nodeid では機能的に kill されない。  
M6 も登録位置が実装後の欠落分岐と一致せず、validator 変異では指定 nodeid を殺せない。  
両者とも source-pin の赤だけで KILLED と誤認できるため、変異 matrix 前の修正が必要である。  
PIN_GATE_SPEC、exact key 集合、独立 import、周辺 consumer の静的整合は確認できた。  
pytest はこの read-only レビューでは再実走していない。