# [T-786] 段 2 実装プラン

結論は、予算定数を上げずに全候補を byte 上は収容可能です。ただし [T-765] は変異免除範囲を広げる非等価変更なので、段 4 の安全裁定を通るまで実装対象に確定してはいけません。[T-765] を除いても他候補はすべて収まります。

byte 数は UTF-8、置換単位末尾の改行は新旧双方から除外して計算しています。

## P1 の検証

P1 は「L1 を縮められる」という結論は成立しますが、「3 義務を prose から完全に除ける」という根拠は部分成立です。

[tools/dev_wave_wait.py:244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/tools/dev_wave_wait.py:244) と [tools/dev_wave_wait.py:386](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/tools/dev_wave_wait.py:386) は以下を実装済みです。

- exact PID / pid-file の択一、starttime 束縛、zombie・PID 再利用を含む生死判定
- producer が死ぬまで一つの継続ループで待つ
- 死後に `.done` と成果物を照合し、欠落は fail-closed
- pattern 入力面を持たず、`pgrep` 自己一致を構造的に排除

代替検査の実 nodeid は次です。

- `orchestrator/tests/test_dev_wave_wait.py::test_producer_waits_while_pid_alive_then_completes_after_death`
- `...::test_producer_dead_without_required_file_fails_closed[done]`
- `...::test_producer_dead_without_required_file_fails_closed[artifact]`
- `...::test_producer_accepts_exactly_one_pid_source[pid-file]`
- `...::test_producer_cli_surface_has_no_pattern_input`
- `...::test_producer_start_time_change_is_original_process_death`
- `...::test_producer_zombie_is_dead_even_when_kill_zero_succeeds`

一方、script は複数 invocation の同時起動を禁止しません。「1 条件 1 本」と「通知ごとに作り直さない」は manager の呼出し規律として残す必要があります。したがって [core.md:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/docs/dev-wave/core.md:17) は全面削除せず、次の短縮形にします。

### `DW-C00` 待ち手

現行 184 bytes:

```text
待ち手は 1 条件 1 本とし、通知ごとに作り直さず状態を読む。生産者を止めるときは待ち手も落とし、
生産者の死も待ち条件に含める。
```

置換後 155 bytes、29 bytes 削減:

```text
待ち手は 1 条件 1 本とし、通知で作り直さず `tools/dev_wave_wait.py` だけを使う。生産者の停止・死で待ち手も終える。
```

呼出し本数・再生成禁止を prose に残し、生死・状態読みを canonical script に委譲するため、義務の外延は狭まりません。

これにより [T-738](c) の「PID だけで producer を推測しない」は exact pid-file・starttime・成果物三点照合へ移り、[T-757] の mtime 判定も不要です。特に O01 側で「producer 自身の pid-file」を明記するため、`setsid` wrapper の一時 PID を掴む経路を残しません。live hang は timeout 時に「死亡」とせず fail-closed にするため、mtime を死亡判定へ追加する必要もありません。

## 意味等価縮約と入庫逐語

### `DW-O01` — [T-773]

対象は [operations.md:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/docs/dev-wave/operations.md:9)。先頭の model/dispatcher authority 行は変更しません。

現行 373 bytes:

```text
`bash -c '<cmd>; echo $? > <log>.done'` で包み、背景 job は `nohup setsid` で detach。
prompt 非空を先に検査し、既存 `.done` は消さず再利用せず再投入を止め、完了は `.done` と exit code だけで判定。
grep も通知も判定にしない（通知は先行しうる）。成果物は最終メッセージから読む（F23/F24）。
```

置換後 416 bytes、43 bytes 増:

```text
prompt 非空を検査し、背景 job は `nohup setsid bash -c '<cmd>; echo $? > <log>.done'` で detach する。
既存 `.done` は消さず再利用・再投入を止める。待機は `tools/dev_wave_wait.py producer` を producer 自身の `--pid-file` で使い、
完了は `.done` の exit code だけ、成果物は最終メッセージで判定する。通知・grep は判定にしない（F23/F24）。
```

canonical waiter 追加前の意味等価縮約形は 324 bytesなので、49 bytes を先に空け、waiter 結線が92 bytesを使う構成です。

### dev-wave command 段 6 / 9 — [T-773]

対象は [dev-wave.md:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/.claude/commands/dev-wave.md:51)。

段 6、現行 218 bytes:

```text
6. **レビュー・fix (codex 並列):** 敵対レビュー 2 本、fix、変異 matrix、受入再走を行う。
   受入直前に runbook の受入 lease を `claim` し、`acquired` のときだけ投入する。
```

置換後 158 bytes、60 bytes 削減:

```text
6. **レビュー・fix (codex 並列):** 敵対レビュー 2 本、fix、変異 matrix 後、`tools/dev_wave_wait.py acceptance` で受入を再走する。
```

`claim` / exact `acquired` 判定の代替実在:

- `...::test_acceptance_non_acquired_state_never_runs_command`
- `...::test_acceptance_ignores_acquired_outside_top_level_state`
- `...::test_claim_once_uses_only_exact_top_level_state`
- `...::test_held_and_queued_refresh_main_before_every_claim`

段 9、現行 260 bytes:

```text
9. **終端・local main (親):** 共通 land operation で監査済み成果だけを取り込み、結果を確定して終了する。
   受入・land の終端で必ず `release` し、land 成功時だけ `message` を照合済み peer へ 1 度送る。
```

置換後 270 bytes、10 bytes 増:

```text
9. **終端・local main (親):** 共通 land で監査済み成果だけを取り込み、結果を確定する。
   `tools/dev_wave_wait.py acceptance` の lease は終端で必ず `release` し、land 成功時だけ照合済み peer へ `message` を 1 度送る。
```

command 全体では 50 bytes 削減、9,497 → 9,447 bytes、余白53 bytesです。

### rulings command — 最優先2義務

対象は [rulings.md:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/.claude/commands/rulings.md:6)、[rulings.md:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/.claude/commands/rulings.md:14)、[rulings.md:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/.claude/commands/rulings.md:37)、[rulings.md:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/.claude/commands/rulings.md:52)。

導入部、401 → 337 bytes、64 bytes 削減:

```text
あなたはユーザーの裁定補佐。通常は read-only のクラス 1（handoff・worklog 追記・編集なし）、
この場の裁定か自己改善 gate 発火時だけクラス 2 に上げる。裁定は `docs/spool/README.md` に従い
`docs/spool/worklog/` fragment へ書き、`docs/worklog.md` を直接編集しない。
```

収集規則、362 → 399 bytes、37 bytes 増:

```text
1. `docs/worklog.md` 末尾「次の一手」のユーザー裁定項。『裁定』1 語で全 `- [T-` 実体項を総ざらいし、
   索引確定前に実体 ID と索引 ID の差集合を検査する。裁定なしに消えた・降格した ID は前 entry へ
   遡って fragment 上書きの退行を疑う（裁定要・裁定軸・択一など見出し定型句には依存しない）
```

推奨規則、155 → 164 bytes、9 bytes 増:

```text
- **選択肢と推奨** — 各択の帰結を対にし、親推奨も独立評価して rulings 自身の推奨・根拠として示す。蹴った場合も 1 行
```

自己改善終端、345 → 245 bytes、100 bytes 削減:

```text
今回、収集漏れ・正本との不一致・誤解を招く規則を実測した場合だけ、クラス 2 起動後に
`docs/skill-self-improvement.md` の `rulings` routing / commit 契約を適用する。未発火なら編集しない。
```

4ブロック合計で118 bytes削減し、4,991 → 4,873 bytes、余白127 bytesです。frontmatter、`$ARGUMENTS`、自己改善 pointer は不変です。

### `DW-M01` — t657 候補 B

対象は [mutation.md:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/docs/dev-wave/mutation.md:7)。

現行 485 bytes:

```text
段 4 で B-057 の変異を実装前に登録する。各変異は位置に加え、同じ入力を拒否する層が前後に
無いこと、無効化時の赤理由が一つに絞れることをコードで確認する。確認できなければ
登録せず実効 gate へ再照準する（F28）。受理集合を縮小する wave では、承認外の過剰拒否を検出する
正例も登録する。テスト強化だけの wave は `DW-M08` の新旧両走も登録する。
```

置換後 497 bytes、12 bytes 増:

```text
段 4 で B-057 変異を実装前登録する。各変異は位置を示し、同じ入力を拒否する前後層がなく、
無効化時の赤理由が一つになることをコードで確認する。満たさなければ登録せず実効 gate へ再照準する
（F28）。短絡連結は単一項でなく条件全体を潰す。受理集合を縮小する wave は承認外の過剰拒否を検出する
正例も、テスト強化だけなら `DW-M08` の新旧両走も登録する。
```

既存義務だけの縮約形は439 bytesで46 bytesを空け、短絡連結義務が58 bytesを使います。section は533 → 545 bytesです。

### `DW-S04` — [T-765]、段4裁定必須

対象は [core.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/docs/dev-wave/core.md:79)。

現行 216 bytes:

```text
免除は実装差分ゼロの「実装しない」裁定の変異 matrix だけ。受入全走は免除せず、実 repo を読む
テストがあれば段 7 の記録前に実走し、結果を worklog へ書く。
```

置換後 186 bytes、30 bytes 削減:

```text
変異 matrix の免除は実装差分ゼロの wave だけ。受入全走は免除せず、実 repo を読むテストは
段 7 の記録前に実走し、結果を worklog へ書く。
```

これは意味等価縮約ではありません。「実装しないと裁定した wave」から「実装差分ゼロの全 wave」へ免除範囲を広げます。受入全走は維持されますが、変異義務は弱くなるため、段4で安全義務弱化に当たらないと明示裁定された場合だけ採用します。採用しなくても他候補は収まります。

### `DW-S05-C` — [T-775](i)

対象は [workers.md:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/docs/dev-wave/workers.md:36)。

現行 1,041 bytes:

```text
- 緑を主張するなら走らせた nodeid・範囲を併記する。子の実走は親の全走を代替せず、実走できない子は
  所見や要件を `closed` と申告しない (「実装済み・未実走」と書く)。
- テストを新設・改名する単位は、それを制約する meta-test も走らせる（F42）。
- fixture への現行 hash 差し込みなど、テストを甘くして緑にしない（F27）。
- 期待値に working tree の hash 等の揮発する診断 payload を焼き込まない。理由と件数を固定して
  揮発部分を外し、揮発源を実際に編集しても緑か確認する。
- 完了報告に、所有外の caller、共有 fixture、consumer test への波及可能性を静的に列挙する。
- 指示にない受理集合の拡大・縮小をしない。scope を書く前に現行の受理・拒否挙動を明記する。
- 親 docs が未 land なら期待して赤くなる finding 集合を事前指定し、それ以外は回帰として報告する。
```

置換後 956 bytes、85 bytes 削減:

```text
- 緑には実走 nodeid・範囲を併記する。子の実走は親の全走を代替せず、未実走なら所見・要件を
  `closed` とせず「実装済み・未実走」と書く。
- テストを新設・改名する単位は、親の名指しを網羅とせず制約 meta-test を自ら洗い出して走らせる（F42）。
- fixture へ現行 hash を差し込むなど、テストを甘くして緑にしない（F27）。
- 期待値に working tree の hash 等の揮発する診断 payload を焼き込まない。理由と件数を固定して
  揮発部分を外し、揮発源を実際に編集しても緑か確認する。
- 完了時、所有外 caller・共有 fixture・consumer test への波及を静的列挙する。
- 指示外の受理集合変更をせず、scope 前に現行の受理・拒否挙動を書く。
- 親 docs 未 land 時は期待赤 finding 集合を事前指定し、他は回帰として報告する。
```

既存義務だけの縮約形は902 bytes、139 bytes削減。新義務が54 bytesを使います。section は1,153 → 1,068 bytesです。

### `DW-S06-A` — t657 候補 A

対象は [workers.md:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/docs/dev-wave/workers.md:48)。

現行後半 172 bytes:

```text
実装面に Codex `role=author` のないハンクがあればレビューで代替せず停止する。
所見ゼロは変異で裏取りするまで緑と数えない。
```

置換後 214 bytes、42 bytes増:

```text
段 3 所見を段 6 の観点へ渡す。実装面に Codex `role=author` のないハンクがあればレビューで代替せず停止する。
所見ゼロは変異で裏取りするまで緑と数えない。
```

直前の `reasoning=high` 文は逐語 pin のため一字も変更しません。section は325 → 367 bytesです。

### `DW-M08` — [T-769] + [T-775](ii)

対象は [mutation.md:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/docs/dev-wave/mutation.md:51)。

現行 699 bytes:

```text
harness は rc に加え赤くなった test node を毎回記録する。pytest は `-rf` を指定し、
node 抽出は F71 に従う（正本は job stdout 全文、行前置と ANSI を除去、` - ` 無しは行末まで、
rc≠0 で 0 件は fail-closed 停止）。
事前登録の期待 node と記録 node は突き合わせ前に同じ形式へ正規化する（F33）。
受理集合を変えず構造化シグナルだけを pin する変異は、kill でなく diagnostic sensitivity pin と
して別枠に記録する。テスト強化だけの wave は、新テストと変更前 HEAD 版テストの双方へ変異を走らせ、
新テストだけが検出する差分を示す。
```

置換後 690 bytes、9 bytes削減:

```text
harness は rc と失敗 test node を毎回記録する。pytest は `-rf`、node 抽出は F71
（job stdout 全文を正本に行前置・ANSI を除き、` - ` 無しは行末まで、rc≠0 で 0 件なら
fail-closed 停止）に従う。
期待 node は完全集合で、同形式へ正規化した記録 node との完全一致だけを KILLED とする。
予測を実測へ揃える走行を見込む（F33）。
受理集合不変で構造化シグナルだけを pin する変異は KILLED でなく diagnostic sensitivity pin として別枠記録する。
テスト強化だけなら新テストと変更前 HEAD 版へ走らせ、新テストだけの検出差分を示す。
```

既存義務だけの縮約形は597 bytes、102 bytes削減。新義務が93 bytesを使います。section は740 → 731 bytesです。

### `DW-O09` — [T-784]

対象は [operations.md:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/docs/dev-wave/operations.md:49)。

現行 890 bytes:

```text
着手前に `grep -rn "<成果物パス>" --include=*.py` を使い、
bytes を pin する台帳・test・trust root を全列挙する。
`FROZEN_MANIFEST`、generator source hash pin、key→canonical path 束縛、output 外の
review ledger も対象に含める。path 検索が見つけるのは path を key にする
pin だけである。review ledger のように role 名を key に張る pin は key 側でも検索し、
path の hit 0 件を pin なしと結論しない（F30）。
durable manifest が未発行か再発行要かを区別して brief の不変条件へ書く（F27/F30、D84）。
統一系 wave では各出現を live copy / 独立 golden / 凍結 snapshot / 歴史記録へ分類してから
scope を裁定する（F39）。
**docs のみの wave でも成立する** — 判定をコードの有無で代用せず docs path も検索する（F78）。
```

置換後 791 bytes、99 bytes削減:

```text
着手前に `grep -rn "<成果物パス>" --include=*.py` で byte pin の台帳・test・trust root を全列挙する。
`FROZEN_MANIFEST`、generator source hash pin、key→canonical path 束縛、output 外 review ledger、
全 field から同一性 hash を導く dataclass・schema も含む。path 検索は path-key pin しか拾わないため、
role 名など key 側も検索し、path hit 0 を pin 無しとしない（F30）。durable manifest の未発行/
再発行要を分け brief の不変条件へ書く（F27/F30、D84）。統一系 wave は各出現を live copy /
独立 golden / 凍結 snapshot / 歴史記録へ分類後に scope を裁定する（F39）。
**docs-only でも成立する**。コード有無で代用せず docs path も検索する（F78）。
```

既存義務だけの縮約形は728 bytes、162 bytes削減。dataclass/schema 義務が63 bytesを使います。`DW-O09` は935 → 836 bytes。L2 最大節は `DW-O19` の861 bytesへ移り、上限まで139 bytes残ります。

## 新設する機械検査

[tools/check_docs.py:3779](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/tools/check_docs.py:3779) 付近に次を追加します。

```python
def _check_dev_wave_waiter_consumer_pins(
    dev_wave_text: str | None,
    core_text: str | None,
    operations_text: str | None,
    findings: list[str],
) -> None:
```

検査契約:

- command の `## 9 段状態機械` から番号付き項目6・9を個別抽出する。
- `DW-C00` と `DW-O01` は既存の可視 H2 抽出器で個別抽出する。
- 可視 top-level の required literal を exact 1 件要求する。

| consumer | required literal |
|---|---|
| command 段6 | `` `tools/dev_wave_wait.py acceptance` `` |
| command 段9 | `` `tools/dev_wave_wait.py acceptance` `` |
| `DW-C00` | `` `tools/dev_wave_wait.py` `` |
| `DW-O01` | `` `tools/dev_wave_wait.py producer` `` と `` `--pid-file` `` |

さらに `tools/dev_wave_wait.py` が symlink でない regular file として存在することも検査します。

赤になる条件は、対象項・節が非一意、literal が0件または複数、別段への移動、HTML comment/fence 内への隠蔽、target script の不在・symlink 化です。

通る正例:

- `orchestrator/tests/test_check_docs.py::test_dev_wave_waiter_consumer_pins_accept_current_docs_contract`

恒真でない根拠となる入力変形:

- 段6の literal を段5へ移し、whole-file の出現数を変えない。段6 scope が0件になるため赤。
- `DW-O01` の `--pid-file` を `--pid` に置換する。script path は残っていても赤。
- `DW-C00` の literal を fence 内へ移す。raw bytesには残るが可視命令から消えるため赤。

予定 nodeid:

- `...::test_dev_wave_waiter_consumer_pin_is_scoped[stage6-relocated]`
- `...::test_dev_wave_waiter_consumer_pin_is_scoped[stage9-deleted]`
- `...::test_dev_wave_waiter_consumer_pin_is_scoped[dw-c00-hidden]`
- `...::test_dev_wave_waiter_consumer_pin_is_scoped[dw-o01-wrong-pid-source]`
- `...::test_dev_wave_waiter_target_must_be_regular_file`

[最小 repo fixture:598](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/orchestrator/tests/test_check_docs.py:598) に段6/9の最小状態機械を加え、[同:695](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/orchestrator/tests/test_check_docs.py:695) の synthetic `DW-C00` / `DW-O01` body と `tools/dev_wave_wait.py` fixture を同期します。既存 `_COMMAND_GUARD_CASES`・needle・件数表にも各変異を登録します。

既存検査との重複はありません。現状の該当 surface・`check_docs.py`・関連テストには waiter path が0件で、既存検査が担うのは section/dispatch edge、O01 model authority、reasoning pin、予算だけです。したがって純増検出力です。

## pin 閉包

| 編集 | 既存 pin への影響 |
|---|---|
| `DW-C00` | section ID と条件24 edgeは不変。既存 literal pinなし。新 waiter pinだけ追加 |
| `DW-O01` | [check_docs.py:285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/tools/check_docs.py:285) の dispatcher route literalとmodel行を変更しない。[test_dev_wave_launch_authority.py:129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/orchestrator/tests/test_dev_wave_launch_authority.py:129) は再走のみ |
| command 段6/9 | `入力と開始` exact section、D2/D4 regex、dispatch表は不変。新 waiter pinを同期 |
| `DW-S06-A` | exact pinned first sentenceを維持し、その後へ追加。[test_dev_wave_launch_authority.py:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/orchestrator/tests/test_dev_wave_launch_authority.py:113) の期待値は不変 |
| `DW-S04` / `DW-S05-C` / `DW-M01` / `DW-M08` / `DW-O09` | H2 ID・typed dispatch edgeは不変。内容の exact pinなし |
| rulings | frontmatter、`$ARGUMENTS`、自己改善 pointerを維持。whole-file pinなし |
| `.agents/skills/dev-wave/SKILL.md` | 編集不要。command を dispatcher として読むため、waiter pathを重複記載しない |
| `REQUIRED_REFERENCE_SECTIONS` / stage・condition contracts | section集合・分類・edgeに変更がないため編集禁止 |
| 予算定数 | 一切変更しない |

## 入庫判定

| 優先 | 件 | byte 判定 | 結論 |
|---:|---|---|---|
| 1 | rulings 2義務 | 164 bytes縮約後に46 bytes使用、純減118 | 入る |
| 2 | [T-773] | C00純減29、O01は純縮約後92使用、command純減50 | 入る |
| 3 | [T-769]+[T-775](ii) | M08を102空けて93使用、純減9 | 入る |
| 4 | [T-775](i) | S05-Cを139空けて54使用、純減85 | 入る |
| 5 | [T-765] | 置換自体が30 bytes削減 | byte上は入るが、免除拡大につき段4安全裁定待ち |
| 6 | [T-784] | O09を162空けて63使用、純減99 | 入る |
| 7 | t657 A | L1.5へ42 bytes追加 | 入る |
| 8 | t657 B | M01を46空けて58使用、純増12 | 入る |
| 9 | [T-757] | T-773結線で独自mtime義務不要 | 0 bytesで解消 |
| 10 | [T-738](c) | exact pid-file/starttime＋三点照合へ束縛 | 0 bytesで解消 |

## 除外した「テスト化」候補

`DW-S01`、`DW-S07`、`DW-O23` などの長い prose は削除候補にしません。既存 `check_docs` は節・dispatch・一部 literal の存在を検査するだけで、各本文義務を代替していないためです。削れば単なる安全義務の削除になります。

L2 節削除も提案しません。repo 全体の発火実績と各義務の機械代替を両方実測していないため、「発火実績なし × 機械代替済み」を満たす候補は今回確定できません。

## 検証計画

実装後、親が次を `tools/run_tests.py` 経由で実測します。

- `orchestrator/tests/test_check_docs.py`
- `orchestrator/tests/test_dev_wave_wait.py`
- `orchestrator/tests/test_dev_wave_launch_authority.py`
- `python3 tools/check_docs.py`
- `python3 tools/check_codex_agents.py`
- acceptance 全走
- 4 consumer literal の削除・移動・隠蔽変異
- commit 後の全史 provenance 監査

本 plan worker はテストを実行しておらず、緑を主張しません。

## 総括

(a) 空けられる bytes は、純縮約・部分テスト化の段階で L1 75 bytes、L1.5 290 bytes、`DW-O09` 162 bytes、rulings 164 bytesです。全入庫後の純減は L1 47 bytes、L1.5 9 bytes、`DW-O09` 99 bytes、rulings 118 bytes、dev-wave command 50 bytesです。

最終予算見込み:

| 予算 | 最終値 | 上限 | 余白 |
|---|---:|---:|---:|
| L1（T-765込み） | 10,578 | 10,625 | 47 |
| L1（T-765保留） | 10,608 | 10,625 | 17 |
| L1.5 | 9,545 | 9,566 | 21 |
| L2最大 `DW-O19` | 861 | 1,000 | 139 |
| `DW-O09` | 836 | 1,000 | 164 |
| rulings command | 4,873 | 5,000 | 127 |
| dev-wave command | 9,447 | 9,500 | 53 |
| cleanup command | 3,959 | 4,000 | 41 |

(b) byte 上入らない件はありません。7件はそのまま入庫可能、[T-765] だけは予算ではなく安全裁定で条件付きです。[T-757] と [T-738](c) は T-773 に吸収し、追加 prose は不要です。

(c) 予算引き上げが不可避な件はありません。

(d) 最大の弱点は、新 checker が canonical waiter の「命令上の参照」を保証するだけで、manager が runtime に本当に一度だけ invocation したことまでは証明しない点です。そのため `DW-C00` の本数・再生成禁止を削除していません。

(e) 未調査のまま残した面は、全 L2 節の repository-wide 発火履歴、`check_docs.py` の指定外範囲に潜む未検索 literal、実装後の実テスト結果です。L2 削除候補はこの未調査を理由にゼロとしました。