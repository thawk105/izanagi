## real 所見

1. **所見:** 非空 `note` の stdout 契約は rc=0 側しか検証されず、rc=1 側だけ旧 formatter のままでも計画済みテストを通過できる。

   - **根拠:** 現行の出力ループは rc=1 側 [tools/check_ai_provenance.py:2076](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:2076) と rc=0 側 [tools/check_ai_provenance.py:2105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:2105) に独立している。新しい `3f2c43…` exact stdout test は単独 range なので rc=0 だけを通る [plan.md:60](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t618-provenance-known-ledger/s3/plan.md:60)。既存 rc=0/1 test は `_known_spec()` の空 note しか使わない [test_check_ai_provenance.py:1766](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:1766)。入力を「note 付き既知 commit + 未台帳 missing commit」にし、rc=1 ループだけ現行式のまま残すと、rc と件数は正しいまま note だけ欠落し、計画済み assertion は検出しない。
   - **成果物影響:** 新規違反がある監査レポートだけ裁定理由を失い、既知例外の参照を stdout から復元できない。
   - **推奨対応:** 空 note の既存 exact test は維持しつつ、非空 note の既知 1 件と新規 1 件を同じ range に置いた rc=1 exact stdout case を追加する。rc=1 呼出箇所だけ helper を迂回する変異も事前登録する。

2. **所見:** 「LF・CR・Unicode line separator を一括拒否」という契約を、LF 1 例しか pin しない。

   - **根拠:** 実装計画は `splitlines()` 相当による全 separator 拒否を要求する [plan.md:31](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t618-provenance-known-ledger/s3/plan.md:31) が、テスト入力は `note="first\nsecond"` だけ [plan.md:70](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t618-provenance-known-ledger/s3/plan.md:70)。実装を `"\n" in note` に弱めてもこの test は識別できず、`note="first\rsecond"` または `note="first\u2028second"` が stdout record に到達する。
   - **成果物影響:** audit report の「1 entry = 1 logical line」という参照境界が CR/U+2028 入力で崩れる。
   - **推奨対応:** `newline` case を少なくとも LF、CR、CRLF、U+2028 の parametrized matrix にする。

3. **所見:** 「新 entry 削除／SHA drift」変異は指名 node 単独へ帰属しない。

   - **根拠:** 候補は `test_ledgered_3f2c43…` だけを指名する [plan.md:126](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t618-provenance-known-ledger/s3/plan.md:126)。しかし entry を削除すると、計画上の次の4経路が同時に不成立になる。

     - exact seven tuple・件数 [plan.md:57](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t618-provenance-known-ledger/s3/plan.md:57)
     - real seven commits の `findings == []` [plan.md:58](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t618-provenance-known-ledger/s3/plan.md:58)
     - empty-registry test の mutation 前 production control [plan.md:59](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t618-provenance-known-ledger/s3/plan.md:59)
     - 対象 singleton range の rc=0 [plan.md:60](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t618-provenance-known-ledger/s3/plan.md:60)

     無効・重複 SHA への drift なら registry validator が先に rc=2 にし、さらに広く波及する。
   - **成果物影響:** mutation ledger が「end-to-end test 一層への単独帰属」と誤記され、試行台帳の検出理由が再現不能になる。
   - **推奨対応:** 単独帰属候補から外す。残すなら integration mutation として4 node以上を期待集合にし、「SHA drift」は deletion と別候補に分ける。

4. **所見:** stale raise 削除変異も指名 node 単独へ帰属しない。

   - **根拠:** 候補は `test_known_violation_missing_expected_finding_diagnoses_regression` だけを指す [plan.md:131](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t618-provenance-known-ledger/s3/plan.md:131)。実際には同じ [stale raise](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:1154) を次も要求する。

     - [selected-clean stale](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:1605)
     - [other-kind stale](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:1658)
     - [off-HEAD policy stale](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:1716)
     - [forward-correction composition](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:2189)
     - [waiver composition](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:2862)

   - **成果物影響:** mutation ledger の単独理由・期待 node 集合が事実と一致しない。
   - **推奨対応:** この wave の単独帰属候補から外す。既存不変層の再測定として残す場合は全到達 node を登録する。

5. **所見:** caller/consumer 列挙が dev-wave の固定 check 層を落としており、公開する note は自動 verification receipt に残らない。

   - **根拠:** plan は launcher を3本だけ列挙する [plan.md:98](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t618-provenance-known-ledger/s3/plan.md:98)。実際は [tools/dev_waves/cli.py:188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/dev_waves/cli.py:188) が provenance fixed check を登録し、[tools/dev_waves/checker.py:328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/dev_waves/checker.py:328) は stdout/stderr を `DEVNULL` にして rc だけを消費する。[task_run_check.py:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/task_run_check.py:43) も receipt へ `counts=None` と exit status しか保存しない。`dev_wave_land.py` 自身は [message-file preflight](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/dev_wave_land.py:1387) だけで full history を実行しない。この既知 gap は既に [worklog T-621](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/docs/worklog.md:939) に記録されている。
   - **成果物影響:** 変更後に fixed check の受理は rc=1→0へ変わる一方、試行台帳から「どの7 SHAを、どの注記で既知扱いしたか」を復元できない。
   - **推奨対応:** 今回直さないなら T-621 を明示的な scope 外として plan v2 に残し、「stdout 公開が効くのは direct checker/relay 層まで」と射程を限定する。自動 receipt まで成果物要件に含めるなら別実装が必要。

6. **所見:** 過去記録を消さない方針は正しいが、T-618 の新記録で何を supersede するかが plan の acceptance item になっていない。

   - **根拠:** [worklog (289):492](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/docs/worklog.md:492) と [T-621 前の T-618 記述](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/docs/worklog.md:921) は「追加しない／既知6・新規1・rc=1」、T-614 insight も [README:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/output/insights/2026-08-07_t614-known-violation-ledger/README.md:13) と [README:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/output/insights/2026-08-07_t614-known-violation-ledger/README.md:123) で同じ観測を固定している。後の裁定自体は [worklog (293)](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/docs/worklog.md:2317) が supersede 済みだが、実装完了・最終実測はまだ記録されていない。
   - **成果物影響:** 新記録が曖昧だと、canonical worklog/insight の参照者が旧「手作業で1件差し引く」運用を継続する。
   - **推奨対応:** 過去行は変更せず、新しい T-618 記録に「worklog (293) の再裁定で T-614 の運用状態を supersede」「実装後の最終 HEAD 実測値」「T-621 は未解決」を明記する。

## file:line 検証表

明示参照にずれはなかった。新設予定の識別子だけが現物にはまだ存在しない。

| plan 参照 | 判定 | 現物 |
|---|---|---|
| `tools/check_ai_provenance.py:137` | 一致 | `KnownViolationSpec` 宣言 |
| `:146` | 一致 | `_KNOWN_VIOLATION_RULING` |
| `:177` | 一致 | 既存第6 entry の終端。tuple 終端は178 |
| `:181` | 一致 | `_known_violation_registry()` |
| `:184` | 一致 | tuple container 型検査 |
| `:191` | 一致 | entry 型検査 |
| `:196–210` | 一致 | commit 型・full SHA・重複検査 |
| `:211–220` | 一致 | finding kind 型・閉集合検査 |
| `:221–225` | 一致 | ruling 型・非空検査 |
| `:226` | 一致 | registry 登録 |
| `:227` | 一致 | registry return。helper 挿入点として有効 |
| `:820` | 一致 | `_commit_range()`。`--ancestry-path` は824 |
| `:997` | 一致 | full SHA lookup |
| `:1000` | 一致 | expected kind 一致 |
| `:1004` | 一致 | entry 一回消費 guard |
| `:1042` | 一致 | `_known_violation_registry()` 唯一の production call |
| `:1146` | 一致 | selected set 構築 |
| `:1148` | 一致 | `_known_violation_audit()` production call |
| `:1154–1169` | 一致 | stale 判定・診断・`RuntimeError` |
| `:1160` | 一致 | `_ledger_policy_is_visible()` call |
| `:2010` | 一致 | history/message 共通 `try` |
| `:2050` | 一致 | `RuntimeError` 等を rc=2 に畳む `except` |
| `:2076` | 一致 | rc=1 known 出力 loop |
| `:2105` | 一致 | rc=0 known 出力 loop |
| `:2121` | 一致 | `main()` の production invocation |
| test `:266` | 一致 | `_known_spec()` |
| test `:1323` | 一致 | exact-six ledger test |
| test `:1370` | 一致 | real-commit ledger test |
| test `:1496` | 一致 | broken registry type test |
| test `:1766` | 一致 | rc=0/1 exact stdout test |
| test `:1809` | 一致 | empty-registry real findings test |
| test `:1832` | 一致 | `3f2c43…` singleton range test |
| production constructors `:148/:153/:158/:163/:168/:173` | 一致 | 6箇所 |
| `_known_violation_line()` | 不在 | 新設予定なので参照誤りではない |
| `test_broken_registry_note_is_rc2` | 不在 | 新設予定なので参照誤りではない |

AST 静的走査でも、`_known_spec()` は13 caller、`provenance.main()` は65 call / 61 test owner + `_run_range`、production の registry/audit/policy caller は各1箇所で、plan の数と一致した。

## 未 scope の層

- dev-wave fixed check／task-run receipt 層。`tools/dev_waves/cli.py` → `tools/dev_waves/checker.py` → `task_run_check.py` は rc だけを保存し、既知 SHA・件数・note を捨てる。T-621 として既知だが brief/plan の成果物射程には入っていない。
- land helper 層。`dev_wave_land.py` は message-file preflight のみで、固定台帳を読む full-history gate は行わない。
- 過去の T-614 insight/worklog は歴史資料なので編集対象外。新しい T-618 記録による supersede が必要。

consumer 検索結果は以下のとおり。

- `known-violations=`: checker/test を除く `tools/ orchestrator/ hooks/ .claude/` は **0件**
- `known-violation `: 同 **0件**
- `KNOWN_PROVENANCE_VIOLATIONS`: 同 **0件**
- `known_violations`: 同 **0件**
- `hooks/` と `.claude/` は、除外前でも上記 stdout 語の hit **0件**

したがって repository 内に field 数や `known-violations=N` を parse する consumer は見つからなかった。存在したのは「parse せず出力を捨てて rc だけ読む」consumer である。

## refuted

1. **4本の反転が恒真になる攻撃:** refuted。変更前 source に対し、exact-seven は constructor/schemaまたはtuple差、real-commit test は対象 finding、empty-registry test は mutation 前 production control、singleton test は rc=1 により、それぞれ assertion が成立しない。特に empty-registry test は先に production known=7 を確認するため、「自分で空にして空を確認」型ではない。

2. **matching note test が stale 等の前段拒否に救われる攻撃:** 改行 case について refuted。full SHA・kind・ruling が妥当で対象 commit が missing finding を1件生成すれば、guard 除去後は [消費経路](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:997) を通り stale は空になる。

3. **既存 exact stdout test を helper 集約だけで壊す攻撃:** refuted。空 note に suffix を出さない限り、現行 rc=0/1 の逐語は維持できる。ただし非空 note の rc=1 欠落は real 所見1。

4. **既存13個の `_known_spec()` が壊れる攻撃:** refuted。3引数 construction と `note: str = ""` は互換で、13 caller はすべて無変更で構築可能。

5. **PR-A02 が新形式と矛盾する攻撃:** refuted。[PR-A02](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/docs/provenance/audit.md:22) は known record の exact field grammar を規定せず、「stdoutへ出る」「count付き rc=0 を緑と読まない」だけなので、条件付き `note=` と矛盾しない。更新は説明改善にはなるが必須ではない。

6. **D221 が scope から完全に落ちている攻撃:** refuted。ただし実装だけ land すれば実際に矛盾する。[D221:10424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/docs/decisions.md:10424) は3要素 schema と明記しており、plan 自身が [decision fragment 必須](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t618-provenance-known-ledger/s3/plan.md:148) と認識している。これは最終 land の必須条件である。

7. **`implementation-author-waived=8` が未計上の違反で brief と矛盾する攻撃:** refuted。waiver は [validate_implementation_author():710](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:710) で finding を空にして別 record 化され、[main():2054](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:2054) で公開される。baseline の「新規1・既知6」は正しいが、「例外的受理は計7件だけ」と一般化してはいけない。

8. **1走だけでは同一 snapshot の変換も推論不能という攻撃:** refuted。同じ1702 commit集合に exact SHA/kind entryだけを加えるなら、静的経路上は新規1→既知1の移動になる。ただし新しい実装・docs commit を含む最終 `HEAD` の rc=0 はその1走から証明できず、最終 full audit の再実測が必要。brief はその再走を受入に含めている。

9. **別の live byte hash pin が壊れる攻撃:** refuted。`tools/codex_reasoning_ab.py` に checker/test の SHA256 は実在するが、これは POS/NEG の封印済み歴史 snapshot 用 [CASE_HASHES](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/codex_reasoning_ab.py:122) であり、live working-tree bytes の pin ではない。

10. **変異候補のうち suffix 全削除、改行 guard 全削除、一回消費 guard 削除の単独帰属攻撃:** refuted。静的にはそれぞれ target exact stdout、`newline` case、duplicate-kind test に限定される。

## speculative / nit

- **speculative:** `note=None` の型 guard 除去が「rc=0まで到達する」かは、まだ存在しない改行 predicate の書き方に依存する。`if spec.note and ...` なら到達するが、`if spec.note != "" and spec.note.splitlines()...` なら `AttributeError` になり、[main の except](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:2050) に捕捉されない。plan v2 で predicate を逐語指定し、parametrize の `ids=["non-str", "newline"]` と `site=site_policy.OTHER` も固定すべき。

- **speculative:** repository 外の parser が空白区切り field 数を固定している可能性は検索不能。repository 内では該当 consumer 0件だった。

- **nit / 分割判断:** 「別々では一時的に assertion 不成立になるから1単位必須」という理由は誤り。[DW-S05-B](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/docs/dev-wave/workers.md:26) は他単位の統合まで意図的に不成立となる test を許し、内訳報告を要求する。checker と test は所有ファイルが素なので並列2単位に分割できる。ただし最終受理集合は変わらず、差は wall-clock と作者分離だけなので real には上げない。

## 総括

最も危ないのは、非空 `note` が rc=1 側だけ欠落しても計画済みテストが検出しない点である。  
変異候補では「entry 削除／SHA drift」と「stale raise 削除」の単独帰属が成立せず、候補から外すべきである。  
全ての既存 file:line は一致し、存在しないのは予定どおりの新 helper/test だけだった。  
D221 addendum と過去 T-614 記録を supersede する新記録は最終 land の必須条件である。  
pytest は実行しておらず、以上は全ファイル読解・AST・`rg` による静的所見である。