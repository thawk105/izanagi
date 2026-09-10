## 修正した内容

- F-1: [test_check_docs.py:731](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/orchestrator/tests/test_check_docs.py:731)、[test_check_docs.py:1149](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/orchestrator/tests/test_check_docs.py:1149)、[test_check_docs.py:1189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/orchestrator/tests/test_check_docs.py:1189) — 基本 fixture を空台帳・期待総数 0・母数下限 0 に戻した。既知 4 件の台帳、archive 73〜78、README claim は専用 helper だけが一体で opt-in する。全置換に一意性 assert を置いた。
- F-2: [check_docs.py:255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/tools/check_docs.py:255)、[check_docs.py:1935](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/tools/check_docs.py:1935)、[test_check_docs.py:10966](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/orchestrator/tests/test_check_docs.py:10966) — 内側 digest を marker と継続物理行を含む raw slice に変更し、確定 4 digest を反映。ordered marker への書換え負例と継続行 digest テストを追加した。
- F-3: [check_docs.py:1965](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/tools/check_docs.py:1965)、[test_check_docs.py:11124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/orchestrator/tests/test_check_docs.py:11124) — 短縮形 candidate を空白と数字だけの括弧へ限定した。`(D837)` と `(Python 3)` は受理し、先頭ゼロ、末尾空白、不正 legacy 間隔は candidate として拒否する。
- F-4: [check_docs.py:2283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/tools/check_docs.py:2283)、[test_check_docs.py:11344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/orchestrator/tests/test_check_docs.py:11344) — target-keyed dict 4 個を分類別 total counter と先着 20 sample に置換。同一 target の 25 occurrence を各分類で 25 件と数える入力を追加した。
- F-5: [check_docs.py:2195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/tools/check_docs.py:2195) — 既存抑止行を維持しつつ、抑止数が target 数ではなく carry occurrence 数であることを直後の行で明示した。universe/index 集合差は `entry key` 単位と区別した。
- F-6: [test_check_docs.py:11439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/orchestrator/tests/test_check_docs.py:11439) — 採番 archive 正例を、既存の `[T-001]` rotation 鎖を使う形へ変更。current entry への追加 consumer 補正を削除した。
- F-7: [test_check_docs.py:11183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/orchestrator/tests/test_check_docs.py:11183)、[test_check_docs.py:11254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/orchestrator/tests/test_check_docs.py:11254)、[check_docs.py:1904](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/tools/check_docs.py:1904) — key 不在テストを source path、ID、target を含む carry 固有 finding に固定。source/item generator の消費を記録し、最初の `next()` 後が parsed 1 件だけであることを検査する形へ変更した。
- F-8: [test_check_docs.py:11005](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/orchestrator/tests/test_check_docs.py:11005)、[test_check_docs.py:11022](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/orchestrator/tests/test_check_docs.py:11022)、[test_check_docs.py:11043](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/orchestrator/tests/test_check_docs.py:11043)、[test_check_docs.py:11099](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/orchestrator/tests/test_check_docs.py:11099) — M3 は下限 0、M4 は実在台帳 4 件と期待値 5、M5 は個別 sample を同数 finding へ統合、M8 は既知 1 occurrence と同一 target/ID の新 source 1 件へ再照準した。
- F-9: [test_check_docs.py:11216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/orchestrator/tests/test_check_docs.py:11216) — `numbered_archive_input_complete=False` を直接渡し、停止 finding だけが残ることを exact に検査する M10 テストを追加した。

## 変異 M1〜M10 の単一理由性

nodeid は runner 障害で未実走。以下は実装後の静的な kill 設計である。

| 変異 | 殺すテスト | 観測する理由 |
|---|---|---|
| M1 | `carry_same_id_mismatch_is_positive_control` | 同一 ID 比較を外すと拒否から受理へ変わる。受理集合。 |
| M2 | 同上 | 未登録不一致を既知扱いすると拒否から受理へ変わる。受理集合。 |
| M3 | `registered_carry_mismatch_removal_is_violation` | 下限 0 のため per-key `actual=0` だけが拒否理由。受理集合。 |
| M4 | `carry_mismatch_ledger_total_is_enforced` | 実在 4 件を保ち期待総数だけ 5 にするため、総数 pin だけが拒否理由。受理集合。 |
| M5 | `carry_candidate_parse_break_is_positive_control` | 個別 finding を同数 finding に統合したため、同数検査を外すと受理へ変わる。受理集合。 |
| M6 | `carry_reference_population_floor_rejects_shrink` | candidate と parsed は同数で、下限だけが拒否理由。受理集合。 |
| M7 | `carry_target_index_states_are_distinct[missing]` | carry 固有の key 不在分類を検査する。universe finding は残るため、これは診断分類だけの kill。 |
| M8 | `same_target_and_id_from_new_source_is_violation` | 既知 1 件は満たしたまま新 source だけを落とす変異が受理へ変わる。受理集合。 |
| M9 | `entry_universe_and_index_must_match` | 集合一致検査を外すと finding が消えて受理へ変わる。受理集合。 |
| M10 | `incomplete_numbered_archive_stops_carry_validation` | 停止 finding 以外を一切生成しない fail-closed 挙動を検査する。診断文字列だけでなく、部分入力を参照診断へ流さない挙動を固定する。 |

## 現行の受理・拒否挙動

受理するのは、厳密な `(N)` carry、厳密 legacy carry、参照先の次の一手に同じ ID がある occurrence、および raw bytes が裁定済み 4 行と一致する既知不一致である。`[T-500] (D837)` と `[T-500] (Python 3)` は非 carry として受理する。非採番 archive は従来どおり対象外である。

拒否するのは、同一 ID 不一致、宙吊り参照、索引 key 不在・None・空集合、candidate/parsed 不一致、母数下限割れ、universe/index 不一致、台帳総数または per-key 観測数の逸脱である。`(073)`、`(73 )`、`変わらず ( (73) 参照)` は candidate として拒否する。

既知行の list marker や継続 raw bytesを変えると既知扱いされない。不完全な採番 archive 入力では停止 finding を 1 件だけ出し、carry・台帳・母数・索引診断へ進まない。

## 実走した検査

- `tools/run_tests.py` へ carry 関連 19 function nodeid、静的展開 27 case を要求したが、`qstat -Q preflight rc=1`、runner `rc=16`、`child_started=false` で 0 件実行だった。
- `test_backlog_guard_carry_item_digest_covers_marker_and_continuation` の単独再試行も同じく child 未起動。
- F-1 の親指定 4 nodeidもまとめて再試行したが同じく child 未起動。

  - `test_placeholder_guard_entry_rotation_keeps_ledger_green`
  - `test_placeholder_guard_missing_target_family_is_violation`
  - `test_spool_fold_rotation_output_passes_real_check_docs`
  - `test_spool_guard_accepts_only_explicit_exact_complete_active_transaction`

- `python3 -m orchestrator.campaign.queue_state` は queue 状態を観測不能と報告した。
- 非 nodeid 診断では、2 ファイルの AST parse、`git diff --check`、candidate/raw-digest probe、25 occurrence/早期停止 probe が成功した。
- 禁止 3 テスト名は zero-context diff に現れず、静的に未変更。変更ファイルも指定 2 ファイルだけである。
- nodeid テストはすべて「実装済み・未実走」。緑や closed は主張しない。

## 期待どおり赤になる finding 集合

- 同一 ID positive control: `carry 同一 ID 不一致` 分類だけ。
- list marker 書換え: 新規同一 ID 不一致と、元 digest の `actual=0`。
- M3: 登録 digest の `expected=1, actual=0` だけ。
- M4: 登録総数の `expected=5, actual=4` だけ。
- M5: candidate 5、parsed 4 の統合 finding だけ。
- M6: 母数下限 finding だけ。
- M7: key 不在では carry 固有 findingと universe/index finding。None・空集合ではそれぞれの carry 固有分類。
- M8: 新 source の同一 ID 不一致分類だけ。台帳、母数、candidate finding は出ない。
- M9: universe/index 集合不一致だけ。
- M10: `番号付き archive 入力が不完全` の停止 finding だけ。
- 25 occurrence 入力: detail 20 件、抑止 5 occurrence。key 不在の場合のみ集合不一致も伴う。

これ以外の赤は回帰として扱う。

## 波及可能性の静的列挙

- `_top_level_items` は現行 worklog、採番 archive、次の一手 ID、見送り台帳の共有 scanner であり、iterator 化が全 caller に及ぶ。
- `_validate_entry_universe` は production の current/archive 統合経路と direct consumer tests に及ぶ。
- `_append_sampled_findings` は carry 各分類と universe/index 分類の出力行数に及ぶ。抑止単位の明示行が増える。
- `_build_min_repo` は同テストファイルの広範な consumer が共有する。既定 baseline から entry 73〜78 が消え、専用 helper 使用時だけ復帰する。
- `_archive_readme` と `_write_archive_index` の consumer 全体で、合成 carry archive の無条件 claim が消える。
- `spool_fold` 出力を real checker へ通す統合テスト、placeholder ledger、rotation、archive ordinal 系へ波及し得る。
- repo 全体検索は禁止されていたため、投影された 2 ファイル外の未知の exact diagnostic consumer は未走査である。

## 未完・未実装

実装上の未実装はなし。

検証は runner の queue preflight 障害により、carry nodeid 群、F-1 の 4 nodeid、禁止 3 テスト、`test_check_docs.py` 全体が未実走。性能上限の実測も未実施である。

## 総括

F-1〜F-9 を指定 2 ファイルだけへ実装し、docs と archive bytes は変更していない。  
台帳は raw physical slice に束縛され、候補境界、occurrence 計数、streaming、fail-closed テストを強化した。  
変更状態は指定 2 ファイルだけで、commit、add、stash、branch 操作は行っていない。  
nodeid は child 未起動のため未実走であり、採用前に親側の全走と性能実測が必要である。