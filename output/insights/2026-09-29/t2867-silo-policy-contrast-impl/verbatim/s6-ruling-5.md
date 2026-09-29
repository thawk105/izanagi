# [T-2867] 段 6 裁定 5 (焦点再レビュー 3 巡目を受けて、親、2026-09-29 17:5x JST)

入力: `codex/s6-focus-3/out.md` (NO-GO。焦点 2 巡目の所見 1・2、F14、N2 は closed)。DW-O16 の上限 3 巡に達したので、以後は焦点再レビューを重ねず、親がテストと変異で裏取りして閉じる。

| P | 判定 | 処置 | 成果物への影響 |
|---|---|---|---|
| P1 driver の異常終了 (compiler 不在など) を schema 却下として A に計上 | real・must-fix | **X (driver):** 対照 (`--contrast-ledger`) の `--preview-diff` で、proposal の読込 (`load_proposal_file`・`load_machine_proposal`・IR の parse) が `ValueError` を出したら `{"passed": false, "working_diff": null, "diff_digest": null, "subtype": "proposal-schema", "rule_id": <例外文の先頭 80 字>}` を stdout に出して rc=1、`policy_gate` が `AuditorGateFailure` を出したら同形で `subtype` を `auditor-gate` (digest 不一致は `auditor-digest`) にする。compiler 不在などそれ以外の例外は今どおり (構造化 JSON なし・非 0)。**Z (round):** `check`・`finalize` は、driver の stdout が構造化 JSON で `passed=false` のときだけ却下 (`rejected`、driver の `subtype`・`rule_id` をそのまま記録) にし、構造化 JSON の無い非 0 終了は終端を書かず例外で返す (親は役割の異常終了として数える)。coder・auditor の出力そのものが JSON として読めない場合 (round 自身の読込の失敗) は今どおり `coder-schema`・`auditor-schema` の却下 | 環境の異常で正常な提案が却下され A・停止時点・endpoint が変わる |
| P2 digest 不一致が `auditor-schema` と数えられる | real・should-fix | P1 の `auditor-digest` subtype で閉じる | report の拒否内訳の混同 |
