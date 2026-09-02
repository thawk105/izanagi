# 段 1 brief — [T-1806] 事前登録契約 C10 の field_paths 拡張 (D967)

wave: dev-wave-t1806-prereg-c10-fieldpaths / base local main: cb4a11b6e

## 確定済みユーザー裁定 (D967、逐語は verbatim-D967.md)

C10 の `field_paths` を新規 field まで**広げる**。凍結を再発行し判定器版を bump する。
既存 campaign が `E1-stale` になることは**正直な migration として記録する**。
契約の記述が実装より弱い状態を残さない。親の初版推奨「広げない」は相談で逆転済みで、
段 4 で非同値な択一へ戻さない。

## scope (成果物影響、DW-G05)

放置すると、cross-binding 証拠 `proposal_build_source_bindings` を落とす実装弱体化を
正式 gate が検知できないまま certified 選択の受理集合が通る。これは規律 2 に触れる。

## 親が実測した原典事実 (段 2 は再測してよいが、覆すなら根拠を出すこと)

1. 差分はちょうど 1 件 `proposal_build_source_bindings` (契約 12 / 実装 13)。
2. `_evaluate_c10` は契約 JSON を読まない。強制しているのは定数 `_C10_FIELDS`。
3. `proposal_build_source_bindings` は `verify_s8c_cross_binding` 内に文字列リテラルとして実在
   (AST で確認)。`_C10_FIELDS` に足しても終端は動かず回帰しない。
4. 凍結 g11 の `evidence_contract_sha256` は live 契約と exact 一致 (実行確認)。本 wave は g12。
5. 強制ソース閉包は現物 24 path。契約 JSON は閉包外、`s8c_preregistration.py` と
   `s8c_preregistration_evidence.py` は閉包内。E1-stale は閉包内 .py を変えたときだけ起きる。
6. `DECIDER_VERSION` は `s8c-decider/v6`。exact 比較は core:2404,2454,2477 と gate_report:84。

## 親の provisional 裁定 (割れうる前提 = 段 3 の攻撃対象)

- **(P1) `_C10_FIELDS` も広げる。** 根拠: D967 の理由が名指しする「正式 gate」は
  `_C10_FIELDS` であり、JSON だけでは検知力が増えない。かつ D967 が E1-stale の発生を
  明言している事実は、閉包内 .py の変更を織り込んでいる証拠である (事実 5)。
- **(P2) 契約 JSON と `_C10_FIELDS` の drift 検査を D613 の既存 idiom で入れる。**
  `_c06_reachable_from_verdict` と同型の `all(... in probe.requirement(kind).field_paths)`。
  `field_paths` は既に `RequiredEvidence` dataclass に載っており新規機構ではない (規律 5)。
  これを入れないと JSON の拡張は文書のままで load-bearing にならない。
  **反論があれば段 3 で出せ。** ユーザーは「仮想リスク向けの gate 追加は scope 外」と明示した。
  争点は「これが仮想リスク向けの新設か、D967 の本題そのものか」である。
- **(P3) 規範文書 `docs/phase3-8c-preregistration.md:257-259` は変更しない。**
  条件 10 の散文は field 名を列挙していないため freeze の
  `section6_condition_hashes[number=10]` は動かない見込み。段 2 が file:line で確認する。
- **(P4) 契約 JSON での新 field の表記は `proposal.build_source_bindings` とする。**
  既存 12 件が `role_event.` / `provider.` / `proposal.` / `campaign_wal.` / `layer3.` の
  接頭辞付きであるため。ただし `_C10_FIELDS` 側は実装の literal
  `proposal_build_source_bindings` を使う (両者は元々この対応関係にある)。

## 不変条件 (緩めない)

- C10 の終端は `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` のまま。
  `SATISFIABLE_CONDITION_IDS` は空集合のまま。受理集合を広げない。
- 規律 2: 検査を弱める方向の変更を採らない。skip / xfail / 期待反転で緑にしない。
- 強制ソース閉包 24 path の**構成は変えない** (中身の .py は変わる)。
- push・remote 操作なし。実装面は Codex author (D95) だけが書く。

## 成果物の形

1 commit に: 契約 JSON C10 の `field_paths` 拡張 / `_C10_FIELDS` 拡張 / (P2 採用なら) drift 検査 /
`DECIDER_VERSION` v6→v7 / 凍結 g12 の発行 / exact pin 4 箇所の更新 / 影響テストの追随。
記録は spool fragment (worklog / decisions / failures は直接編集しない)。
E1-stale migration を worklog へ正直に書く。insight は output/insights/ へ直接。

## 並列分割方針

段 2 は plan 1 本。段 3 は敵対相談 2 レンズ (A: 規律 2 と gate 検知力、B: 凍結・閉包・E1-stale の
波及と pin 閉包の取り残し)。段 5 は実装子 1 本 (編集面が 1 commit に閉じるため分割しない)。
段 6 はレビュー 2 本 + fix + 変異 matrix。

## 受入・実測環境

login node で `tools/dev_wave_wait.py acceptance` 経由の受入全走。perf は不要。
