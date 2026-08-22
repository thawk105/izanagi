---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-23
wave: dev-wave-codex-sol-xhigh
seq: 2
---

## 新規

### {{F:repin-search-misses-incoming-value}}. 値の張り替えで移行先の値を検索語に入れず、既にその値を持つ箇所が no-op 化した [手順漏れ]

- 事象: dev-wave の codex 権威を `gpt-5.6-luna`/`max` から `gpt-5.6-sol`/`xhigh` へ張り替えた際、
  移行先の値を**既にハードコードしていた 2 箇所**が無変化になった。1 件は
  `test_v2_snapshot_mapping_inconsistency_fails_closed` が `consult_models` へ注入していた
  `gpt-5.6-sol` で、権威自体が sol になったため注入が効かず `DID NOT RAISE` の赤になった。
  もう 1 件は段別 effort fixture の置換が `xhigh` → `xhigh` になり、author / fix と focus が
  同値になって節の取り違えを検出できなくなった (テストは緑のまま証明力だけ失った)。
- 根本原因: 段 2 の閉包探索が**移行元の値だけ**を検索語にしていた。移行先の値を既に持つ箇所は
  grep に掛からず、置換後に `置換前 == 置換後` へ潰れる。緑のまま潰れる側は実走でも見えない。
- 恒久対応: {{D:codex-sol-xhigh-all-stages}} の張り替え手順として、閉包探索の検索語に
  **移行元と移行先の両方**を入れる。加えて `DW-M04` の変異で、段別 fixture の識別力そのものを
  KILL 対象にする (本 wave の M3 = focus effort を author 由来へ誤配線 → 1 node KILLED が実体)。
- 再発検知: `orchestrator/tests/test_dev_wave_launch_authority.py::test_derive_launch_uses_stage_specific_effort_sections`
  が段ごとに相異なる値 (S05-A=medium / S06-A=high / S06-C=low) を要求し、いずれも live 値
  `xhigh` と異なるため、同型の no-op が再び起きれば assertion が落ちる。

## 再発

### F24

- **再発: 2026-08-23** — `tools/dev_wave_wait.py producer` を背景 job で張った待ち手が、
  producer 生存中に **exit 0 かつ出力ゼロ**で戻る偽完了を、同一 wave 内で 2 度起こした
  (段 6 レビュー B の待ち手と、段 6 fix の待ち手)。どちらも `.done` は不在で子は生存しており、
  `pgrep` で runner の生存を確認して張り直した。恒久対応 (`.done` 出現と producer 死の
  両方で判定し、待ち手の rc も通知も信じない) がそのまま効き、実害はゼロだった。
  追加事実は、**待ち手ツール自体は健全だった**点である — 同じ argv を `--max-wait-seconds 20` で
  前景実行すると正しく `rc=70 producer-timeout` を返した。偽完了は待ち手の内部ロジックではなく
  背景 job 側の完了通知経路で起きており、2026-08-17 の「待ち手自身が偽 green を返す」とは
  発生層が異なる。判定を `.done` の実体確認へ寄せる対応は層が変わっても有効である。
