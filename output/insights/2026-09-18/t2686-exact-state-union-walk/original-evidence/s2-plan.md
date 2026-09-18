## 変更面

**(a) assess ごとの遅延候補供給 object を採用する。** ただし、timeout を含めた全入力での verdict 不変は証明できない。以下は候補列の等価性を実装・検証する計画であり、末尾の裁定事項を段 4 で確定する必要がある。

行番号は現行コード基準。以下、`C` は [tools/check_branch_landed.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2686-exact-state-union-walk/tools/check_branch_landed.py)、`T` は [orchestrator/tests/test_check_branch_landed.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2686-exact-state-union-walk/orchestrator/tests/test_check_branch_landed.py) を指す。

| file:line | 変更内容・理由 |
|---|---|
| C:767 の直前 | `_HistoryCandidates` と strict parser を追加。固定 `main_oid`、登録 path、limit、成功 memo／失敗を保持する。 |
| C:1721–1726 | 登録 path を確定し供給 object を生成。同じ instance を全 `_proof_unit` に渡す。生成時には走査しない。 |
| C:1365、1380、1426 | signature と通常／spool fallback の両呼出しへ供給引数を追加。分岐条件・例外捕捉は保持する。 |
| C:767–783 | `_find_exact_state` に供給引数を追加。774–776 の tip 照合後、777–783 だけを `supplier.get(required.path)` に置換する。 |
| C:784–810 | 候補照合、1024 件 chunk、正証拠優先、候補数・上限判定は変更しない。 |
| C:2007–2010 | `timing` に union 所要時間と union process 数を追加。既存の総 process 数は `Git.command_count` のまま。 |

登録集合は、`S = states`、`r(s) = s.required`、`spool(p) = bool(SPOOL_RE.fullmatch(p))` として、

```text
P =
 {r(s).path | s∈S ∧ ¬spool(r(s).path)}
 ∪
 {r(s).path | s∈S ∧ spool(r(s).path)
              ∧ ¬r(s).missing
              ∧ r(s).object_type = "blob"
              ∧ r(s).mode ∈ {"100644", "100755"}}
```

distinct 化する。receipt 不一致・fragment 解析成功など、実行時に確定する条件では登録を絞らない。空集合なら走査しない。

初回 `get` で、既存 `Git.run` を使って次を一度だけ実行する。

```text
-c log.showRoot=true log --full-history --diff-merges=separate
--name-only -z --format=%x1e%H <main_oid> -- <P...>
```

全出力を検証してから memo を公開する。失敗も記憶し、spool が例外を捕捉した後の再要求で再走査しない。未登録 path を空候補として扱わない。

commit ごとに全 parent entry の名前を集約し、commit 初出順に処理する。各 path に対し、

```text
matches(name, p) := name == p or name.startswith(p + "/")
candidates[p] := ordered_unique(matching commits)[:limit + 1]
```

とする。path の整列は argv の再現性にのみ使い、候補 OID は整列しない。上限到達後も残りの出力の文法検証は省略しない。

**timing の提案:** 最小変更として `SearchResult.elapsed_seconds` は現在どおり関数入口からの経過を保持する。初回要求 unit には union 時間が含まれることを明記し、別途 `timing.history_candidate_walk_seconds`、`timing.history_candidate_walk_processes` を記録する。両者は重複計上されるため加算用ではない。親 brief の「照合のみ」への変更とは異なるため、段 4 の確認対象とする。判定ロジックは timing を読まない。

**argv 上限:** C:34、2046 の 256／4096 は件数上限であり byte 上限ではない。概算は、

```text
Σ(len(path.encode("utf-8")) + 1)
+ 固定 argv bytes + env bytes + argv/env pointer 領域
```

となる。平均 512 byte × 4096 path だけで 2 MiB を超える。平均 4095 byte なら約 16 MiB である。

- 通常は argv を使う。
- 超過時は `Git.run(input_data=...)` で `--stdin` を使用し、固定 OID、`--`、改行を含まない path を行単位で渡す案を採る。
- LF を含む path は argv 側へ残す。混在時の pathspec 合成は Git 2.34.1 の実 fixture で検証する。C quoting が解釈されると仮定しない。
- LF を含む path 群だけで argv 上限を超える入力は、この案では未解決。新たな入力制限を黙って導入せず裁定へ送る。
- chunk 分割は採用しない。各 chunk の順序だけでは、異なる chunk にしか現れない commit の相対順を復元できない。別途同一 traversal の全体 rank が必要になり、一走査案を逸脱する。

## 不変の根拠

| 対象 | 現行箇所 | 維持する条件 |
|---|---|---|
| 通常 unit | C:1379–1380 | 既存分岐で exact-state を呼ぶ。 |
| spool fallback | C:1422–1429 | receipt 不一致・registry 非 error・通常 blob・非 missing の条件、例外の SearchResult 化を保持。 |
| tip 早期 return | C:774–776 | 供給要求より先に実施。全 unit が tip／receipt で証明できれば union は 0 本。 |
| batch 適用条件 | C:785–792 | 通常 blob・mode・空白判定、1024 件 chunk を保持。 |
| 実 tree 再確認 | C:696–711、793–800 | batch の一致だけでは受理せず、`ls-tree` の四要素一致を要求。 |
| 候補上限 | C:798–809 | `limit+1` 件を照合し、正証拠がなければ `>limit` を truncated とする。D2123 を保持。 |
| per-command timeout | C:207–244 | 既定45秒と残り全体予算の min。上書き・retry を追加しない。 |
| 通常 unit の timeout | C:1380 → 1989–2002 | `assessment-timeout`／`truncated` → assessment の `indeterminate`。 |
| spool の timeout | C:1427–1429、1333–1340、1603付近 | unit exact evidence は `assessment-timeout`／`truncated`。終端まで進めれば集約 reason は `one-or-more-states-unproven`。 |
| 終端期限・ref 確認 | C:1941–1959 | 残り予算で再照合。期限超過・ref 移動を正証拠で覆さない。 |
| 判定と rc | C:1343–1362、1584–1608、26 | 判定関数、集約、exit mapping は変更しない。 |

parser／派生処理にも `git.remaining()` の確認を置き、期限切れは同じ `AssessmentError(..., outcome="truncated")` とする。deadline の延長・再起算はしない。

**要求 3 の「verdict が変わる経路が無い」は論証できない。** 旧版は path ごとに `--max-count=limit+1` で終了するが、提示された union command は全履歴を走査する。少数 path・長い履歴・小さい limit なら、旧版が短時間で候補を取得し正証拠を見つける一方、union が45秒で打ち切られる経路を排除できない。未要求の tip 一致 path も union 登録集合に入る。

したがって、`union >45秒 ⇒ 旧版合計 >60秒` は実測値から一般化できない。D2106 が区別する「証拠の受理述語」と「時間内に証拠を集め切れる入力集合」を分ける必要がある。

双方が正常完走し候補列が一致する条件では、同じ候補順・照合・集約により verdict、unit、evidence、summary の一致を検証できる。timeout／parse failure を含む全入力の payload 不変までは主張しない。

## parser 文法と逸脱の扱い

提示された文法を次のように扱う。

```text
stream := entry*
entry  := RS oid NUL LF (name NUL)+
oid    := lowercase-hex{40} | lowercase-hex{64}
name   := 非空の strict UTF-8 byte 列（NUL を含まない）
```

- 空 stream は候補ゼロとして正常。
- entry が存在する場合の name ゼロ件は異常。
- OID、`NUL LF`、末尾 NUL、UTF-8 を検査する。
- 名前の LF／CR／TAB／空白を削除しない。`strip`、`splitlines`、全体の `split(b"\x1e")` は使わない。
- 同一 commit の複数 entry は候補数に重複計上しない。
- 不正 OID、区切り欠落、不正 UTF-8、name ゼロ件はすべて `AssessmentError("history-candidate-parse-error", ..., outcome="error")`。
- C:783 と同じ code を維持する理由は、失敗した責務が引き続き「履歴候補の解析」だからである。UTF-8 エラーを外側の一般 decode error に流さない。

**文法上の未解決点:** Git の名前には RS も使える。`RS + 40桁hex` という名前と、次の `LF` 始まりの名前は、entry 境界に似た byte 列を作れる。この文法だけで任意の合法名に対する一意な framing は保証できない。厳密 parser の完成条件に含め、境界を曖昧なく表現する出力形式への変更を裁定候補とする。

参考 probe は `%H %P`、RS split、名前の改行除去、完全一致のみを使う初版であり、そのまま移植しない。親が提示した修正済み派生規則を仕様にする。

## test 設計

新規群は **T:2020 の後**へ追加。既存 helper `_init_repo`（66）、`_git`（26）、`_write`（48）、`_commit`（60）、`_history_fixture`（1807）、`_fragment`（168）を再利用する。

全正例で、同じ固定 OID・同じ `Git.run` 環境による以下の出力と、派生列を**list として直接比較**する。

```text
log --full-history --format=%H --max-count=<limit+1> <oid> -- <path>
```

| 新規 node | fixture／検証内容 |
|---|---|
| `test_union_candidates_match_per_path[ordinary]` | `tmp_path`、通常更新と無関係 path の更新。候補の集合・順序を比較。 |
| `...[one_parent_merge]` | 片親と同一、他方と異なる tree の merge。対照 command に merge OID が含まれることも明示 assertion。 |
| `...[both_parent_merge]` | 両親と異なる競合解決。merge OID が一度だけ現れることを検証。T:362 の構築を参考にする。 |
| `...[root]` | `_init_repo` の `base.txt`。repo config を `log.showRoot=false` にし、argv の強制が効くことを検証。 |
| `...[delete_readd]` | `_history_fixture` を拡張し、削除→再追加→再更新。 |
| `...[file_directory]` | `f` を削除して `f/child` を追加、子を更新。`f` と `f/child` の両方を登録し prefix 規則を検証。 |
| `...[gitlink]` | `update-index --cacheinfo 160000,...` で実在 commit を指す gitlink を追加・更新・削除。 |
| `...[limit_plus_one]` | limit を超える履歴を作り、長さが厳密に `limit+1`、順序が対照と同じと検証。 |
| `test_union_parser_invalid[...]` | `monkeypatch`／bytes 注入。不正 hex、`NUL LF` 欠落、不正 UTF-8、name ゼロ件。code と outcome を直接検証。 |
| `test_union_parser_preserves_names[...]` | T:1839 の特殊名に先頭／末尾 LF、RS を追加。40／64桁 OID、空 stream、末尾 NUL 欠落も検証。境界衝突は裁定後の仕様で検証。 |
| `test_union_timeout[...]` | 通常／spool × command timeout／deadline。通常は assessment reason、spool は unit evidence と既存集約 reason を検証。 |
| `test_union_walk_once_per_assess` | 複数通常 path、同じ path の複数 unit、spool fallback を併存させ、候補走査が計1本であることを記録。 |
| `test_union_walk_not_needed[...]` | tip 一致のみ、receipt 一致のみ、空 closure で走査0本。 |
| `test_union_failure_is_not_retried` | spool が供給失敗を捕捉した後も2本目を起動しない。 |
| `test_union_stdin_matches_argv` | stdin と argv 混在、特殊名、長い path 集合。双方を同じ per-path 対照と比較。 |
| `test_union_payload_matches_legacy` | test 専用の旧候補供給へ差し替えた assess と比較。除外は `elapsed_seconds` と `timing` のみ。 |

既存テストの**期待値は変更しない**。ただし次の注入面は更新が必要。

- **T:395–412:** 旧 log 出力への順序注入を供給境界へ移す。batch 全行検証の期待はそのまま。
- **T:455–475:** 重複 OID 1025件という batch 専用の人工入力は供給 stub から渡す。union の重複除去を通さない。process 数5の検証を維持できるよう、stub の候補取得も既存同様1 command を消費させる。
- **T:488–512:** 新しい供給引数へ対応し、非通常 state の `ls-tree` 呼出順の期待を維持。
- **T:1037–1117:** Python 側の `args[0] == "log"` 判定を先頭 `-c` 対応にし、stdin 使用時の selector も対応させる。実 `TimeoutExpired` を起こす検証は保持する。

T:963、986、1919、1970、1997 の上限・正証拠優先・spool integrity／削除禁止は既存回帰として残す。実走は親が行う。本段では実行していない。

## 変異候補

node 名は上記新規群の略記。

| id | 変異内容 | 期待 killer node／扱い |
|---|---|---|
| a | prefix 規則を削除 | `match_per_path[file_directory]` |
| b | 候補順を OID sort に変更 | `match_per_path[ordinary]`。fixture の対照列が lexical sort と異なることも確認する。確実性のため非整列 OID の parser fixture を併設。 |
| c | `limit+1` を `limit` に変更 | `match_per_path[limit_plus_one]`、既存 T:986 |
| d | `--diff-merges=separate` を削除 | `match_per_path[both_parent_merge]`。候補欠落または name ゼロ件 error で KILLED。 |
| e | `--full-history` を削除 | `match_per_path[one_parent_merge]`。対照に含まれる TREESAME merge を失う fixture にする。 |
| f | `log.showRoot=true` を削除 | `match_per_path[root]`。明示した repo-local false により検出。既定 true の fixture だけでは検出不能。 |
| g | name ゼロ件検査を削除 | `union_parser_invalid[zero_names]` |
| h | path ごとの旧走査へ戻す | 候補意味論では等価で SURVIVED 期待。`union_walk_once_per_assess` では process 契約違反として KILLED。分類を混同しない。 |
| i | コメントだけ変更 | 等価対照、SURVIVED 期待。killer なし。非等価変異の全 KILLED 集計から除外。 |

b は偶然 sort 済みの実 OID 列、f は既定 config のままでは有効な変異検査にならない。上記 fixture 条件を満たせない場合は事前登録から外す。

## 裁定パッケージ候補

1. **P5 の修正が必要。** 全入力での timeout verdict 同一性は成立未証明で、旧版の有限候補走査と新版の全履歴走査には逆転経路がある。推奨する受入条件は「正常完走時の候補列・判定 payload 同一、timeout の保守的処理維持、固定 OID の交互 A/B と process 数削減」。全入力の verdict 同一を必須とするなら現案は採用できない。

2. **任意 path 名の framing。** RS を含む合法名との衝突を解消する出力形式を確定する。単純 RS split や名前制限で隠さない。形式変更は候補抽出専用とし、raw diff の new side を証拠にしない。

3. **argv 超過と LF path。** stdin／argv 混在で通常の超過を解消する案を検証し、LF path だけで上限超過する場合の方針を決める。無断の chunk 化・新たな入力上限は導入しない。

4. **timing の意味。** 遅延走査を初回 unit の elapsed に含める提案と、親 brief の「照合のみ」の差を確定する。後者なら供給待ち時間だけを控除し、tip 照合時間は残す。

5. **parse 対象拡大による差。** union は旧版が `limit+1` で止めた先の名前も解析する。不正 UTF-8 や出力異常で旧版より早く indeterminate になる可能性がある。これも全入力 payload 不変の主張から分離する。

並列化、予算変更、any-path／cherry／ledger、closure／`_introduced_states` の一括化は提案しない。

## 総括

遅延供給を両 exact-state 呼出しへ渡し、候補列取得だけを一括化する。
tip 早期終了、実 tree 再確認、正証拠優先、既存 timeout 処理を保持する。
候補列は合成 repo の旧 command 出力と順序込みで直接比較する。
timeout 全入力同一性、名前 framing、argv 極端例は段 4 の未解決事項。
本段は読み取り・静的確認のみで、変更・pytest 実走は行っていない。