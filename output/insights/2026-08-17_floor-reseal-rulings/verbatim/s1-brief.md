# 段 1 brief — [T-1218] 床値 再封印の残る裁定 (2026-08-17 01:0x JST)

wave = `dev-wave-t1218-floor-reseal-rulings` / branch `worktree-dev-wave-t1218-floor-reseal-rulings`
base main tip = `5a19b8ab`

## 確定済みユーザー裁定 (2026-08-16 /rulings 全件 第 3 回 #6)

床値 再封印は **案 3 (pin を進めれば新しい組で測り直せる) を採り、「環境契約 1 世代につき床値 1 件」の
機械化は入れず、versioned artifact を `FROZEN_MANIFEST` へは載せない**。理由 = 既定方針 3 本
(粗い provenance で足りる / 凍結チェーン検証は保留 / 防御的堅牢化は見送り) と束縛機構の追加が衝突し、
1 世代 1 床値は世代が進むたび再取得を義務づけて計測コストを構造的に増やすため。

## scope (この wave が変えるもの)

S-1. **D444 決定 5 の撤去。** `contract_sha256` が組 index に既出なら発行を拒否する機械化を、
     issuer (`s8b_floor_campaign.py:966-975`) と index 不変条件
     (`_index_protocol_record`, 同 `:753-762`) の**両方**から取り除く。
     — 成果物影響: 撤去しないと `contract_sha256` を据え置いたまま pin を進める再封印
     (= 裁定が採った案 3 の唯一の実行形) が機械拒否され、床値 protocol を今後 1 件も発行できない。
S-2. **resolver の意味の確定 (P1)。** `resolve_current_floor_protocol` (同 `:892-911`) は
     現行 contract に一致する record が exact 1 件であることを要求する。S-1 の撤去だけを行うと、
     同一 contract で pin 違いの 2 件目が置かれた瞬間に production consumer
     `certified_writer_admission._admit_floor` (`:201-223`) が fail-closed で落ちる。
     — 成果物影響: 放置すると再封印した翌日に床値 submit の受理が全面停止する
     (certified writer の admission が例外で閉じる)。
S-3. **`FROZEN_MANIFEST` 非登録の確定 (P3)。** `orchestrator/tests/test_frozen_artifacts.py:41` の
     23 key へ versioned artifact を追加しない。追加を強制する scan が実在しないことを実測で示す。
     — 成果物影響: 誤って登録すると 23 key 固定 assert (`:236`) と held/keep 分割 assert が動き、
     凍結台帳の件数という論文用 provenance の数字が変わる。
S-4. **記録。** D444 を改訂する decision fragment、worklog fragment、insights。

## 不変条件 (破ってはいけないもの)

- 組 `(contract_sha256, ccbench_pin)` の一意性 (`_index_protocol_record:748-752`) と create-only は**維持**。
  裁定が落としたのは contract 単位の封鎖であって組単位ではない。
- 既存の凍結 bytes を 1 件も変えない。`output/s8b-freeze/floor_protocol.json` (sealed anchor,
  `contract_sha256=e576e9cd…`, `ccbench_pin=d706650c…`) を書き換えず、
  `FROZEN_MANIFEST` の 23 key と held check 2 件 (`s8b-floor.protocol-bytes-expected-pin` /
  `s8b-floor.sealed-protocol-ccbench-pin-current-head`) の保留状態も動かさない。
- **旧 bytes を要求する consumer を壊さない。** 現在 `_admit_floor` は legacy anchor
  (pin が HEAD gitlink `511c9538…` と不一致) を解決して PASS する (前 wave 実測 M-10)。
  resolver を「HEAD pin と exact 一致する protocol を要求する」形に変えると、
  今日の repo には該当 artifact が無いため床値 submit が即座に停止する。これは受理集合の縮小であり不可。
- 新しい束縛機構・恒真ゲートを足さない (裁定の主旨)。防御的堅牢化は既定で見送り。
- 規律 2 / 3 を緩めない。撤去は「裁定で落ちた機械化 1 本」に限り、他の正しさ検査を巻き込まない。
- D444 決定 1〜4・6・7 (組からの path 一意導出 / chain record pattern 登録 / 不変 16 field の
  byte-exact 継承 / 固定 HEAD blob からの anchor / 恒真ゲート不採用 / 失敗時 artifact を残す) は維持。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** resolver は「現行 (contract, HEAD gitlink pin) の組に exact 一致する record があればそれ、
  無ければ現行 contract に一致する record が exact 1 件のときそれ」とする。
  今日の受理挙動 (legacy anchor が解決される) を 1 bit も変えず、再封印後の曖昧性だけを解消する。
  対案 = resolver を触らず T-1214 (consumer 結線) へ送る。
- **(P2)** 実 repo での**実発行はこの wave では行わない**。前 wave の段 4 裁定 D6
  「consumer 結線と実発行は g2 活性化と同一 chain の後続 wave」に従う。
  この wave の成果は dormant issuer の制約撤去までとする。
- **(P3)** `FROZEN_MANIFEST` 非登録は「載せない」だけとし、「載せてはならない」新検査は足さない。

## 成果物の形

- `orchestrator/campaign/s8b_floor_campaign.py` の 2 箇所撤去 + (P1) 採用時の resolver 変更。
- `orchestrator/tests/test_s8b_protocol_builder.py` の期待値反転
  (`test_reseal_protocol_public_entry_rejects_contract_already_in_index` /
  `test_reseal_protocol_second_issue_preserves_first_bytes` /
  `test_floor_protocol_index_rejects_same_contract_with_different_pin`)。
  **裁定で落ちた gate を撤去する wave なので、この 3 本の期待値変更は指示であり、
  「テストを甘くして緑にする」ではない。** 反転先は「pin 違いの 2 件目は発行でき、
  同一組の 2 件目は依然拒否され、先行 bytes は不変」という正例 + 残る負例。
- 撤去後も pair 単位の拒否が生きていることを示す負例と、resolver の受理挙動不変を示す回帰テスト。
- decisions / worklog fragment (`docs/spool/`)、insights。

## 分割方針

編集面は `s8b_floor_campaign.py` + `test_s8b_protocol_builder.py` の 2 file に閉じる見込みで、
所有が素集合にならないため段 5 は**単一 Codex 実装子**とする。段 2・3・6 のレビュー子は省かない
(受理集合が変わり正しさ防壁 `_admit_floor` に触るため、`DW-C00` の軽量版条件を満たさない)。
