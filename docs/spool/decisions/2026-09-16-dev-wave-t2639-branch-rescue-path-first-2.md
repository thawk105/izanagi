---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-t2639-branch-rescue-path-first
seq: 2
---

## {{D:spool-exact-state-positive-fallback}}. spool fragment の着地証明は fold receipt を一次とし、exact-state 履歴探索を正例専用の fallback に据える

**決定:** `tools/check_branch_landed.py` は spool fragment に対し、従来どおり fold receipt の
`content_sha256` と identity の一致を一次判定とする。**一致しないときは、通常 blob
(mode `100644` / `100755`) に限り D922 の決定的証拠 (a) すなわち exact-state の履歴探索へ落とす。**
落とし先の判定関数は `search` と receipt の理由だけを受け取り、`state` を受け取らない。
戻り値は `landed` と `indeterminate` の 2 値に限る。

削除 fragment (`required.missing`) は fallback の対象外とする。receipt の parse error・blob 上限・
fragment 解析失敗は fallback の成功で覆い隠さない。

**理由:**
- **これは新しい証拠種別ではなく、既に認可された証拠の適用範囲の拡大である。** D922 点 2 の (a) は
  `(path, mode, object type, oid)` の同時状態が main から到達可能であることを決定的証拠としており、
  spool fragment を除外していない。除外していたのは実装の分岐であって裁定ではない。
- **着地済み wave の fragment は main 履歴に実在する。** land merge が追加し fold commit が削除
  するため、path は main 履歴に残る。実測では、着地済み wave の fragment blob は候補 6 commit の
  うち 5 commit で四要素一致し、残り 1 件 (main tip) が `missing` だった。
- **未着地 wave の fragment は候補 0 件で落ちる。** 実測した未着地 wave の fragment 2 本は、
  main 履歴の候補 commit が 0 件、exact blob も不在だった。正例専用にすれば負例は
  `indeterminate` のまま残る。
- **`state` を渡さないことが D922 点 5 の構造的な担保になる。** 通常の判定関数へ流すと、候補 0 件の
  pure add が `not-landed` へ落ち、fold receipt の不在を未着地の証拠に使ってしまう。引数から
  `state` を外せば、この枝へ到達する経路がコード上存在しない。
- 変異で裏取りした。正例専用の戻り値を `not-landed` へ変える変異は、wave 開始前から在った 10 本を
  含む 12 本のテストを赤にした。

**却下した選択肢:**
- **fold receipt を identity (`authored`, `wave`, `seq`) でも索引する** — 最終条件を保つなら
  新しい正例を増やさず、保たないなら決定的証拠そのものを変える。再 home では wave も
  `content_sha256` も変わる実例があり、identity 索引だけでも解決しない。
- **path が `docs/spool/` 配下であることを既知正常の根拠にする** — 述語が候補集合に含意されて
  恒真になる。未着地の fragment も同じ path の下に在る。
- **削除 fragment にも fallback を足す** — required の不在を探索すると main tip の不在だけで
  受理でき、old blob を探索すると分岐前の共通履歴だけで成功しうる。どちらも削除という required
  state の到達を証明していない。

## {{D:rescue-carries-unproven-unit-reasons}}. 掃除の可視化は未証明 unit の理由を consumer へ運ぶ

**決定:** `tools/check_branch_rescue.py` は `landed_assessment` に `unproven_unit_details` を足し、
未証明 unit ごとの `commit` / `path` / `change` / `required_state` / 判定理由と、証拠層の
`layer` / `decisive` / `outcome` / `reason` / `candidate_count` / `candidate_limit` /
`matched_commit`、および理由別の件数表を運ぶ。件数は 100 を上限とし、超過は `truncated` を明示する。
子 report を得られなかった場合は欠落理由を書き、「全 unit を説明できた」と書かない。

運ぶ証拠層は decisive な層に加え、**`exact-tree-state` 層は `outcome` が `not-applicable` でない
とき非 decisive でも運ぶ**。各層には `decisive` の真偽を必ず付ける。

`complete` / `conclusive` / `verdict` / rc / `decision_inputs` の既存 field は 1 bit も変えない。

**理由:**
- **rc だけでは情報を運べない。** D1231 により rc は「完全な絵を描けたか」しか表さず、
  未証明が 1 件でも残れば 2 である。何が未証明かを人が知る経路が別に要る。
- **従来は集約理由と report の sha256 しか返していなかった。** hash から説明は復元できない。
  実データでは、判定不能の commit について「どの path がなぜ未証明か」が JSON から読めなかった。
- **decisive な層だけでは spool の探索事情が落ちる。** 正常な receipt 不在 + exact 不一致では
  exact 層が非 decisive になるため、「候補 0 件」と「複数候補を調べたが不一致」を区別できない。
  実際に探索が走った層は、判定を決めていなくても人の次の一手を決める材料である。
- **`decisive` を付けないと「運ばれた層はすべて判定を決めた」と誤読される。** 非 spool では
  receipt 層が `not-applicable` のまま decisive であり、この誤読は実際に起こりうる。

**却下した選択肢:**
- **「decisive な層はちょうど 1 つ」という一般不変条件を新設する** — D922 は証拠種別を限定して
  いるが、層の本数を要求していない。そのためだけの状態管理とテストは複雑さだけを増やす。
- **本文の逐語一致や別 path の同一 object を説明へ昇格する** — D922 点 3 が観測に留めている。
  運ぶのは既存の証拠層の値だけとし、新しい探索を足さない。
- **説明を無制限に出す** — 出力が膨らむ。上限と `truncated` の明示で足りる。
