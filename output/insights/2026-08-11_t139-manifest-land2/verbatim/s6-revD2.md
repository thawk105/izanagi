## 総括

**NO-GO。** 統合 commit `36937ed4` は D282 の逐語契約とは概ね一致していますが、段 4 で事前登録した M1〜M10 のうち、有効な単独 KILL を静的に書けるのは **M4・M5・M8 の 3 件だけ**です。M1/M2/M3/M9/M10 は別 guard に mask され、M6 はテスト自身を弱める変異、M7 は受理集合ではなく内部表現 assert による赤です。

既知の 8 赤を直すだけでは mutation matrix は閉じません。

### must-fix

1. **M1/M2/M3/M6/M7/M9/M10 の事前登録が単一理由性を満たさない。**

   (a) 具体的破綻は次表のとおりです。段 4 は全件 KILLED を予定していますが、実コードでは 7 件に正当な期待 node がありません。[段4裁定 §4](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2/s4-adjudication.md:124>)

   | 変異 | 静的帰結 | 判定 |
   |---|---|---|
   | M1 operation 数 | `len != 2` を消しても直後の index 集合 `{1,2}` が 1/3 operation を拒否。[erratum.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/erratum.py:552) | **MASKED / node なし** |
   | M2 `較正` exact 2 | 件数検査を消しても出現行集合検査が third occurrence を拒否し、さらに適用後 0 件検査も後段にある。[erratum.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/erratum.py:568) | **MASKED** |
   | M3 適用後 0 件 | 前段が全出現行を対象 operation に束縛し、各 `new_text` を承認 digest に固定するため、単独削除では受理集合が動かない。[erratum.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/erratum.py:577) | **EQUIVALENT / node なし** |
   | M4 index 2 new digest | `test_s7_erratum_rejects_second_new_digest_change` が例外なしになり赤。[test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/tests/test_t139_preregistration_binding.py:484) | **KILL 成立** |
   | M5 registry call | call 削除時は `EmptyErratumSetError` へ進み、`ErratumRegistryError` を期待する node が赤。[test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/tests/test_t139_preregistration_binding.py:551) | **KILL 成立** |
   | M6 禁止集合から名前削除 | 変異対象はテスト内の `forbidden` 集合。名前を削るとテストはそのまま緑であり、production の非 export 状態も変わらない。[test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/tests/test_t139_preregistration_binding.py:842) | **SURVIVES** |
   | M7 exact `str` 正規化 | 正規化だけを戻しても digest 比較は `bytes.fromhex(ref.sha256)` なので迂回不能。[blobref.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/blobref.py:143) node は `type(ref.sha256) is str` で赤になるだけ。[test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/tests/test_t139_blobref_digest_binding.py:56) | **診断赤のみ。KILL 不適格** |
   | M8 fence exact 1 | duplicate fence が先頭 fence として処理され例外が消えるため、duplicate node が赤。[test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/tests/test_t139_approval_payload.py:176) | **KILL 成立** |
   | M9 未知 key | `_claim_key` の早期拒否を消しても最後の exact-key 集合が同じ未知 key を拒否。[approval_payload.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/approval_payload.py:325) | **MASKED / node なし** |
   | M10 role 数 exact 6 | 件数検査を消しても直後の role 集合 exact 検査が欠落 role を拒否。[approval_payload.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/approval_payload.py:406) | **MASKED / node なし** |

   (b) 成立条件は、単独 guard 削除をそのまま KILL と数えることです。M1/M2/M9/M10 は `DW-M02` の前後層 mask、M6 は `DW-M04` の「実効 gate へ注入されていない変異」、M7 は `DW-M03` の「受理集合を動かさない診断赤」に該当します。M1/M10 の既知赤 helper を直しても mask は残ります。

   (c) certified 選択は現時点では `foundation-only` のため値なしのままです。一方、材料レポートと試行台帳の mutation 結果は、これらを `KILLED` ではなく `MASKED` / `EQUIVALENT` / `SURVIVED` と記録しなければ proof chain が虚偽になります。必要なら両層同時変異を別 ID で事前登録し直す必要があります。

2. **lane C の緑 14 node は「拒否」は見るが正しい拒否理由を見ていない。**

   (a) 全負例が `_assert_rejected()` を通じて基底 `ApprovalPayloadError` を捕捉しています。[test_t139_approval_payload.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/tests/test_t139_approval_payload.py:87) 対象となる緑 node は次の 14 件です。

   - `test_missing_d282_heading_is_rejected_without_unicode_normalization`
   - `test_duplicate_d282_heading_is_rejected`
   - `test_missing_target_fence_is_rejected`
   - `test_duplicate_target_fence_is_rejected`
   - `test_nested_fence_is_rejected`
   - `test_mismatched_fence_delimiter_length_is_rejected`
   - `test_unknown_top_level_key_is_rejected`
   - `test_missing_top_level_key_is_rejected`
   - `test_duplicate_top_level_key_is_rejected`
   - `test_erratum_application_order_must_match_approval`
   - `test_not_approved_root_commit_key_is_rejected`
   - `test_alpha_reservation_missing_descriptor_key_is_rejected`
   - `test_alpha_reservation_commit_must_remain_unpinned`
   - `test_non_utf8_document_is_rejected`

   `pytest.raises(Exception)` 自体はありませんが、この基底捕捉は同じ弱点です。特に unknown-key は早期拒否が消えても後段 exact-key エラーで緑のままで、M9 の `first_rejecting_node` を証明しません。

   (b) 成立条件は、対象 guard より前後の別箇所が `ApprovalPayloadStructureError` を投げることです。例外 subclass、reason code、または安定した理由識別子を照合しない限り区別できません。

   (c) certified 選択の受理集合は依然 fail-closed ですが、材料レポートの「どの gate が働いたか」と試行台帳の `first_rejecting_node` / mutation 帰属が誤ります。段 4 が lane C に要求した記録を満たせません。

### should-fix

1. **S7 の `old_text` bytes 束縛テストが回帰で消え、等価な負例がありません。**

   (a) 親版の `test_s7_erratum_rejects_old_text_bytes_mismatch` は削除されました。新しい first/second old-digest tests は `old_sha256` field だけを変えており、`old_sha256` を保ったまま `old_text` を変える経路を検査しません。[新テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/tests/test_t139_preregistration_binding.py:447) 実装上の bytes 二重検査は残っています。[erratum.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/erratum.py:526)

   (b) `_validate_operation_binding()` の `old_bytes != target_line` が削除・迂回され、宣言 `old_sha256` だけが承認値のままの場合に成立します。現テストは赤くなりません。

   (c) 現在は erratum blob 自体が commit＋digest で固定されているため certified 選択は直ちには変わりません。ただし validator の proof chain から「文書の `old_text` と対象 core bytes の一致」が脱落しても材料レポートと試行台帳が検知できません。

## 既存テスト回帰の全数照合

`36937ed4^` から削除・改名された node は 11 件です。

| 旧 node | 判定 |
|---|---|
| `test_draft_erratum_is_not_in_approved_set` | 契約変更に対応。`test_both_errata_are_approved_and_draft_registry_is_empty` が等価 |
| `test_overlapping_locators_rejected` | 負例は消失。現 ID の locator hard pin により overlap は先に拒否されるため現在は冗長 |
| `test_s7_erratum_occurrence_must_bind_to_operation_line` | `test_s7_erratum_rejects_missing_333_operation` が等価 |
| `test_s7_erratum_rejects_new_text_line_count_change` | 等価負例なし。固定 new digest＋合成 digest に先取りされるため現在は冗長 |
| `test_s7_erratum_rejects_occurrence_count_not_one` | `test_s7_erratum_rejects_third_core_occurrence` へ更新。ただし M2 の件数 guard 単独検出にはならない |
| `test_s7_erratum_rejects_old_sha256_mismatch` | first/second old-digest tests がより強い等価検査 |
| `test_s7_erratum_rejects_old_text_bytes_mismatch` | **等価検査なし。should-fix** |
| `test_s7_erratum_rejects_operation_count_not_one` | one/three-operation tests へ更新した意図。ただし両方とも既知赤で、fix 後も index guard に mask |
| `test_s7_erratum_rejects_strong_calibration_claim` | 逐語負例なし。承認 new digest と合成 digestが先取り |
| `test_s7_erratum_rejects_unconstrained_reassurance` | 同上 |
| `test_s7_erratum_target_line_digest_is_frozen` | plural 版で 221/333 の両行を pin。等価以上 |

### nit

1. **working-tree の S7 文書を負例 seed にしている。**

   (a) 複数の負例が `S7_ERRATUM_PATH.read_bytes()` を使います。[test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/tests/test_t139_preregistration_binding.py:385) 固定 commit の blobではありません。

   (b) working tree 文書が変わると helper の marker 不在、異なる fence 構造、または別の mutation seed になります。ただし現 helper は多くの場合 no-op・`index()` 失敗・正例のままになって赤くなるため、実装破損を恒真で隠す経路は確認できません。

   (c) certified 選択・材料レポート・試行台帳の値を変える偽緑は静的に構成できません。したがって **nit** です。再現性のため pinned `S7_ERRATUM_REF` に揃える余地はあります。

2. **削除された line-count・強い較正主張・無拘束 reassurance・overlap の負例は直接の等価 node を持ちません。**

   ただし現契約では hardcoded locator、承認 `new_sha256`、最終 composed digest が先取りするため受理集合を動かせません。(c) を書けないので **nit** です。

## 承認契約の照合結果

ここは所見なしです。

- D282 の top-level 10 key と `_TOP_LEVEL_KEYS` は過不足なく一致しています。[D282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/decisions.md:12881) [parser](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/approval_payload.py:37)
- target core 1＋approved blob 6＝7 三つ組で一致しています。
- `not_approved_as_record_items_root` は `{path, sha256, note}` のみで、dataclassにも `commit` がありません。[parser](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/approval_payload.py:87)
- `alpha_reservation` は literal descriptor であり、台帳履歴を読まず、実 commit を pin しません。[parser](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/approval_payload.py:96) §6.7 の全履歴証明は明示どおり後続 validator/consumer の責務です。[record-items-v2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:652)
- `[s15, s7]` と `e0b0caea…8e0c` は parser・テスト双方で pin されています。[approval_payload.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/approval_payload.py:32) [test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/tests/test_t139_approval_payload.py:112)
- 実装を使わない独立再計算でも、固定 core の `較正` は適用前 2 件・適用後 0 件、合成 SHA-256 は `e0b0caeaca9300acffbb5cd6b81db7b6fb7fa8f9eeab81219affb4e2f94a8e0c` でした。
- manifest、resolver、semantic validator、`a13` consumer、submit、certified consumer は段 4 が明示した scope 外です。[段4裁定](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2/s4-adjudication.md:116) これらを今回の must-fix にはしていません。