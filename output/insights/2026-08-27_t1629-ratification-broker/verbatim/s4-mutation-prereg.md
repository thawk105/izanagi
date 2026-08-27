# 変異事前登録 (DW-M01) — dev-wave-t1629-ratification-broker

段 4 で実装前に登録する。**anchor (old 逐語) と期待 node は、段 6 の fix 後 commit で
DW-M07 に従って再検証してから本走する。** 本 file は位置・単一理由・期待 node の宣言である。

登録の条件は 3 つ。(i) 位置が一意、(ii) 同じ入力を拒否する層が前後に無い、
(iii) 無効化時の赤理由が一つに絞れる。**(ii) を満たさない候補は登録しない。**

## 登録する変異

| ID | 位置 | 無効化で変わる受理挙動 | 他層が同じ入力を拒否しないことの根拠 | 期待 KILLED node |
|---|---|---|---|---|
| M01 | `ed25519_verify.py` の `if s >= _L:` | `S+L` 形式の可鍛署名が受理される | 検証方程式は cofactor 付きなので `S+L` を通す。後段に S 範囲を見る層は無い | `test_rejects_s_at_or_above_group_order` |
| M02 | 同 `if not _is_identity(_scalar_multiply(public_point, _L)):` | 非単位元の低位数公開鍵が受理される | identity 検査は非単位元を通す。方程式も通る | `test_rejects_nonidentity_small_order_public_key` |
| M03 | 同 `if not _equal(left, right):` | 1 bit 変えた message が受理される | 後段なし | `test_rejects_message_changed_by_one_bit` |
| M04 | receipt の `verify(...)` 呼び出し | 別鍵で署名された過去行が台帳全体を汚染しなくなる | その行の他 field はすべて valid に合成できる | `test_different_signing_key_on_earlier_row_rejects_the_whole_ledger` |
| M05 | receipt の `_DOMAIN_PREFIX + _canonical_json_bytes(signed)` | domain 分離無しの署名が受理される | 後段なし | `test_signature_without_domain_prefix_is_rejected` |
| M06 | receipt の serial 連続性検査 | 正しく署名された重複 serial が受理される | previous hash は正しく合成できるので他層は拒否しない | `test_correctly_signed_duplicate_serial_is_rejected` |
| M07 | receipt の previous hash 検査 | 正しく署名された誤 previous hash が受理される | 履歴の prefix 検査は行の追加しか見ない | `test_correctly_signed_wrong_previous_hash_is_rejected` |
| M08 | receipt 最終照合の `row["closure_paths"] == expected_paths` | 同 digest・別 path 宣言の receipt が一致扱いになる | path schema と paths hash は valid に合成できる | `test_matching_digest_with_different_closure_paths_is_rejected` |
| M09 | v2 の `_assert_full_history_repository` 呼び出し | shallow clone が履歴欠落を隠す | 後段は欠落を知る手段を持たない | `test_v2_shallow_repository_is_rejected` |
| M10 | v2 の tree mode 検査 | JSON を内容に持つ symlink / gitlink が regular 台帳として読まれる | parser は mode を知らない | `test_v2_non_regular_ledger_entries_are_rejected` |
| M11 | v2 の source binding (source commit の 27 blob が署名 digest と一致) | reachable だが別 closure の source commit が受理される | 署名は正しいので署名層は拒否しない | `test_source_commit_must_bind_signed_closure` |
| M12 | v2 の source commit reachability 検査 | HEAD から到達不能な dangling commit が source になる | 同 closure なら M11 の digest 検査は通る (sol F6) | `test_unreachable_source_commit_with_same_closure_is_rejected` |
| M13 | v2 の信頼根 blob 履歴不変性検査 (R13) | 空台帳期間中の信頼根差替えが無検出になる | 行が 0 件なので署名検査は一度も走らない (sol F1) | `test_trust_root_changed_across_history_is_rejected` |
| M14 | broker の信頼根必須分岐を「不在なら作る」へ戻す変異 | TOFU が復活し AI 鍵が信頼根になりうる | 検証子はその鍵を正当な信頼根として受理する | `test_absent_committed_trust_root_never_writes` |
| M15 | broker の承認読み取り seam (`/dev/tty` を `sys.stdin` へ) | pipe から流し込んだ `y` で署名できる | 署名は完全に valid になる | `test_non_tty_cannot_approve` |
| M16 | broker の制御文字 escape | ESC 列で人間の表示を偽装できる | 検証子は表示を見ないので検出不能 | `test_control_bytes_are_escaped_before_prompt` |
| M17 | broker の committed blob CAS | 並行 append が直列 JSONL を壊し、台帳全体が拒否される | HEAD 再確認は worktree の競合を見ない (luna 所見 3) | `test_ledger_changed_between_read_and_append_is_rejected` |

## 登録しない候補と理由 (帰属が成立しない)

- receipt の `decision != "ratify"` parser 検査 — 最終照合の `decision == "ratify"` が同じ入力を拒否する。
- `ed25519_verify` の canonical-y 検査 — 部分群検査か方程式が同じ入力を拒否する。
- `ed25519_verify` の x-zero/sign 検査 — 公開鍵 fixture では identity 検査が拒否する。
- `ed25519_verify` の二度目の parity 検査 — **到達不能**。実装にその旨をコメントで明示する。
- `ed25519_verify` の曲線式再検査 — reachable 入力では冗長。
- broker の remote path tuple 検査 — 最終検証子の expected-path 検査が同じ receipt を拒否する。
- broker の digest 計算を remote 申告値へ付け替える変異 — 検証子の live digest 照合が拒否する。
- `closure_paths_sha256` と `trust_root_sha256` — 実装 docstring どおり診断用の冗長であり、
  独立防壁ではない。**security matrix ではなく schema 契約の matrix へ分ける。**

## luna 所見 11 への対応

plan が挙げた non-TTY と absent-trust の 2 候補は、そのままでは帰属が成立しない。

- **non-TTY:** 承認を `/dev/tty` からだけ読む実装にすると、非 TTY 拒否を消しても
  stdin の `y` は届かない (別層が拒否)。→ **M15 は seam 自体を変異させる形に付け替えた。**
- **absent-trust:** `raise` を消すだけでは後続の `None` parse が拒否する。
  → **M14 は「不在なら作る」分岐を復活させる 1 変更に付け替えた。**

## 受理集合を縮小する側の正例 (DW-M01)

本 wave は受理集合を縮小する (v1 の無署名行を受理しなくなる)。
承認外の過剰拒否を検出する正例を登録する。

- `test_valid_signed_receipt_for_current_closure_is_accepted` — 正しい信頼根・正しい署名・
  source commit が現行 closure と一致する receipt が **受理される**こと。
- `test_three_receipt_chain_accepts_the_matching_earlier_row` — 連鎖の途中の行でも
  digest が一致すれば受理されること。
