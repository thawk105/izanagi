# 変異事前登録の訂正 (erratum) — 段 6 レビュー B の実測を受けて

2026-09-02 21:55 JST。`DW-M02` に従い、初回登録 (段 4 裁定 7 節) は消さずに残し、訂正をここへ書く。
判定材料は段 6 レビュー B の「変異 11 件の成立判定」で、全件が実装後の現物 file:line を伴う。

## 成立したまま (7 件) — 変更しない

| ID | 置換点 (fix 前の行) | kill 期待 node |
|---|---|---|
| M1 | `attempt_registry_core.py:1015` seed の適用 | `test_seeded_budget_replay_rejects_invalid_counts_and_accepts_exact_limit[True]` ほか 3 node と `test_seeded_budget_replay_rejects_eleventh_start_and_old_apis_are_unchanged` |
| M2 | `attempt_registry_core.py:999` seed 値検証 | `test_seeded_budget_replay_rejects_invalid_counts_and_accepts_exact_limit[True\|-1\|1.5]` |
| M3 | `s8b_attempt_profile.py:560` 既定 separator | `test_serialize_session_line_uses_spaced_sorted_utf8_json_and_newline` |
| M4 | `s8b_attempt_profile.py:566` 末尾 newline | 同上 (別 byte 位置) |
| M9 | `s8b_attempt_registry.py:747` path と genesis の protocol 比較 | `test_generation_resolver_rejects_protocol_path_mismatch_and_accepts_match` |
| M10 | `s8b_attempt_registry.py:1323` 外殻の prelock hook 呼出し | `test_root_lock_serializes_two_updates_after_same_old_snapshot_barrier` と `test_locked_update_seam_does_not_reacquire_lock_or_run_prelock_hook` |
| M11 | `s8b_attempt_registry.py:995` slot 比較を 4 軸へ戻す | `test_v2_profile_is_rejected_by_public_mutation_but_slot_lookup_is_five_axis` |

## 訂正 (4 件)

### M7 — 置換の形を変える (spec だけの訂正。コードは変えない)

**初回登録の誤り:** 「不完全世代拒否 (`registry.jsonl` 欠落) を消す」とだけ書いた。
`_fail` の呼出しだけを消すと、直後の `_read_regular_bytes()` (`s8b_attempt_registry.py:676`) が
**同じ欠落を別 message で拒否する**。test は message 差で赤になり、`DW-M03` の
「診断文字列だけの赤を kill にしない」に抵触する。

**訂正後:** 変異を「`registry.jsonl` が無い世代を `continue` で読み飛ばす」形へ変える。
これなら後段 read へ落ちず、不完全世代を静かに無視した結果として
`test_generation_enumerator_rejects_unsafe_hex_authority_and_accepts_real_one[missing-registry]`
が受理側へ倒れる。単一理由になる。

### M8 — 両層同時変異へ変える (spec だけの訂正。コードは変えない)

**初回登録の誤り:** 「profile resolver の recovery-policy digest 比較を消す」を単独変異として
登録した。実際には adapter の比較 (`s8b_attempt_registry.py:757`) を消しても、直後の
`core.assert_registry_rows()` が **core 側の同じ digest 比較** (`attempt_registry_core.py:721`)
で拒否する。message 差で赤になるだけで、resolver 固有の gate を測っていない。

**訂正後:** `DW-M04` に従い、adapter `:757` と core `:721` の**両層同時変異**として登録し直す。
片側だけの adapter 変異は **SURVIVED 期待**の対として別途登録し、生存が「効かない」ではなく
「core が拒否していた」ためだと実証する。

- **M8a (単独、adapter `:757`)** — SURVIVED 期待 (core に mask される)
- **M8b (両層同時、adapter `:757` + core `:721`)** — KILLED 期待、node は
  `test_generation_resolver_rejects_stale_recovery_policy_and_accepts_current`

### M5 / M6 — 現行 fixture では成立しない。fixture を足してから登録する

**初回登録の誤り:** 「列挙の symlink 拒否を片側だけ消すと `_read_regular_bytes` の
親 component 検査に mask される」と想定したが、**2 段構えで外れていた。**

1. 明示的な symlink 判定 (`:659`) だけを消しても、**同じ条件式の
   `not stat.S_ISDIR(lstat-mode)` が即座に拒否する**ので、mask 元とした `:532` へ到達しない。
2. さらに、現行 fixture の `directory-symlink` はリンク先が**空 directory** である
   (`test_s8b_attempt_registry.py:1919`)。両検査を消しても `registry.jsonl` 欠落を `:665` が
   **同じ期待 message で**拒否するため、対象 node は赤にならない。**M6 は空振りする。**

**訂正後:** symlink 防壁を単一理由で測るには、**リンク先が完全な世代 (real directory +
妥当な `registry.jsonl`) である fixture** が要る。そうでない限り、symlink 拒否は
lstat の directory 判定と欠落判定に覆われた**冗長 gate**であり、`DW-M03` に従えば
単独変異の証拠から外すしかない。

この防壁は実効性がある。64 hex の symlink がそのまま世代として列挙されると、**同じ台帳が
実体と symlink で二重に予算計上される**。段 4 裁定 2 節 S8 が「世代権威を騙るので拒否する」と
書いた形そのものである。したがって **fix 第 2 巡で fixture を足し**、そのうえで登録し直す。

- **M5' (単独、`:659` の symlink 判定と同条件式の lstat directory 判定を両方消す)** —
  完全世代を指す symlink fixture の下では、`_read_regular_bytes` の親 component 検査が
  拒否するため **SURVIVED 期待**。
- **M6' (両層同時、上記 + `_read_regular_bytes` の親 component 検査 `:532`)** —
  **KILLED 期待**。二重計上が実際に起きることを示す node で kill する。

**fixture を足す fix が入らなければ、M5 / M6 は登録せず、symlink 拒否を「冗長 gate」として
記録し、単独変異の証拠から外す。** 不到達・冗長を到達可能に見せる test は作らない。

## 訂正後の集計

- 単独 KILLED 期待: M1、M2、M3、M4、M7 (訂正)、M9、M10、M11 = 8 件
- 事前登録 SURVIVED: M8a、(M5' が入るなら) M5' = 1〜2 件
- 両層同時 KILLED 期待: M8b、(M6' が入るなら) M6' = 1〜2 件

## 親の登録が外していた理由 (段 8 の材料)

初回登録は**実装前**に書いた。段 4 の時点では新設 gate の実コードが無く、
「どの層が先に拒否するか」を現物で確かめられなかった。`DW-M01` は「各変異は位置に加え、
同じ入力を拒否する層が前後に無いことを**コードで確認する**」と要求しているが、
実装前の登録ではその確認が原理的にできない項目がある。今回は 11 件中 4 件が外れた。
