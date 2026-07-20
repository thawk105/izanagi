# 変異台帳 — ruling-A + ruling-C wave (2026-07-20)

事前登録 = 実装前 (B-057)。実測 = 親が変異ハーネスで全走。ハーネスは**置換対象が 1 箇所でなければ
HALT** し、注入されなかった変異を緑と誤報しない構造 (実際に C09 で 1 回 HALT が発火し、変異文字列の
誤りを検出した — 実装の行インデントと不一致だった)。

## 判定基準

kill = 「テストが赤くなった」ではなく **「受理集合または fail-closed 挙動が期待方向へ変わった」**。
診断文字列だけが変わる赤は帰属不成立として**別枠**にする (D67 (8) erratum の再発防止)。

## 実測 (注入 12 / HALT 0 / 全 12 が赤)

### 受理集合を変えた変異 (10 件)

| ID | 変異 | 受理集合の変化 | 代表的な赤 |
|---|---|---|---|
| C01 | `parse_line` の `object_pairs_hook` を外す | duplicate key を持つ WAL が受理される | `test_wal_parse_line_rejects_nested_duplicate_and_unknown_top_level_key` 他 7 |
| C04 | `truncated_tail` を常に `False` | 末尾が切れた WAL が completed へ通る | `test_truncated_raw_tail_after_completed_terminal_is_one_protocol_reason` 他 |
| C06 | exact 5 key を部分集合検査へ | 未知 top-level key を持つ record が受理される | `test_wal_parse_line_rejects_...unknown_top_level_key` 他 |
| C07 | layer3 が共有 parser を使わない | duplicate WAL から layer3 report が生成される | `test_nested_duplicate_wal_key_fails_closed_for_one_reason` 他 5 |
| C09 | plotting が共有 parser を使わない | duplicate `tps` が作図データへ流れる (`DID NOT RAISE`) | `test_plot_backoff_rejects_duplicate_tps_before_it_reaches_plot_data` |
| C11 | payload の object 性検査を外す | **session record の非 Mapping payload が completed を通る** | `test_non_mapping_pipeline_payload_is_shared_wal_protocol_violation` 他 10 |
| C12 | 不正行を `line_issues` に載せず黙殺 | **不正行にすることで後置 record を隠せる** | 14 件 |
| A01 | 位置述語を旧 row-lifecycle/pipeline 検査へ戻す | **terminal 後の正しい `campaign-start` が受理される** | `test_campaign_start_after_completed_terminal_is_one_position_reason` 他 |
| A03 | `truncated_tail` → `protocol_violation` の配線を外す | 末尾が切れた WAL の campaign が公開される | `test_truncated_tail_does_not_mask_definitive_correctness_red` 他 |
| C10 | **[負の対照]** 末尾 crash prefix の許容を外す | **crash-recovery の受理集合が不当に狭まる** (厳格化のやり過ぎを検出) | `test_wal_tolerates_truncated_last_line` |

### fail-closed 挙動を変えた変異 (1 件)

| ID | 変異 | 挙動の変化 | 赤 |
|---|---|---|---|
| C05 | `append` の writer preflight を外す | writer が自分で読めない行を書く (拒否 → 書込) | `test_wal_writer_rejects_json_key_collision_before_writing` |

### 診断保存 pin — **受理集合を変えないので kill 集計から外す** (1 件)

| ID | 変異 | 実際の変化 |
|---|---|---|
| A04 | `terminal_issue` の合成を外す | 判定は `protocol_violation` のまま、`bench_values` も `[]` のまま。**消えるのは理由文字列だけ** (「terminal が一意でない: 2」「status=aborted」等)。規律3 の anti-masking を固定する回帰 pin として価値はあるが、**実効変異として数えない** |

## 事前登録から取り下げた変異 (レビュー指摘を採用)

- **C02** (`WalLineError` を `KeyError` の subclass にする) — 末尾許容が catch するのは `JSONDecodeError`
  だけなので受理集合は変わらない。赤くなるのは class hierarchy の assertion のみ = **無効 kill**。
  例外階層の防壁テストとしては残すが変異 kill には数えない
- **A02** (位置検査を semantic gate の後ろへ戻す) — `aborted terminal + 後置 record` は
  `status=aborted` という独立の赤を持つ**過剰決定 fixture** で、どちらでも `completed` にはならない。
  診断表現だけが変わるため anti-masking 回帰 pin へ格下げ
- **`terminal → trial-result`** — 基準 HEAD の既存 tail gate が既に捕捉する (`trial-result` ∈
  `_ROW_LIFECYCLE_EVENTS`)。単独変異の kill 帰属が成立しないため回帰 pin としてのみ残す
- 位置 helper の呼び出しごと削除 / 規則 (i)(ii) の別登録 — いずれも合成変異・等価変異

## 正例 (偽陽性ガード。常時緑を要求)

- 全走 **2304 passed / 26 skipped / 赤 0**
- 既存 `output/**/wal.jsonl` **30 ファイル / 物理行 3,086 / parse 成功 3,086 / issue 0**
- 正規 driver の通常完了経路と budget-aborted 経路が従来どおり緑
