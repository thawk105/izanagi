NO-GO。pytest・`check_docs.py` は実行しておらず、以下は read-only の静的検証結果である。

## 所見

### B1 — byte 数値自体は正しいが、詳細を cap 外へ逃がしている — real

UTF-8/LF で再計算した結果は次のとおり。

| 対象 | 現在 | 変更後 | 上限 |
|---|---:|---:|---:|
| `docs/dev-wave/**` 合計 | 25,134 | 25,197 | 25,200 |
| `core.md` | 8,584 | 8,647 | 9,600 |
| `tools/README.md` | 2,989 | 変更なし | 3,000 |
| 個別 cap 総和 | 26,750 | 変更なし | 27,720（ceiling の1.10倍） |

提案 pointer は改行込み63 bytesで、[s2-plan-out.md:174–192](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s2-plan-out.md:174>) の計算は正しい。個別 cap・aggregate・cap総和のいずれの finding 条件も、pointer 単独では成立しない。[check_docs.py:176–181](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/check_docs.py:176>)、[check_docs.py:254–258](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/check_docs.py:254>)、[check_docs.py:3361–3378](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/check_docs.py:3361>)、[check_docs.py:3541–3562](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/check_docs.py:3541>)。

一方、`docs/README.md` に置く手順本体は957 bytes、既存3行の置換を含む同ファイルの純増は887 bytesである。`docs/README.md` は `all_limits` に含まれないため、この957 bytesはaggregateから完全に消える。[check_docs.py:3507–3514](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/check_docs.py:3507>)。同じ本文を正直に`core.md`へ入れれば、`core.md=9,604`、aggregate=26,154となり、個別を4 bytes、aggregateを954 bytes超える。

これは単なる配置工夫ではない。dev-wave手順を4 referenceへ閉じるD85に反し、親が「先例」としたD110も予算外reference案を明示的に却下している。[D85:3729–3745](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/decisions.md:3729>)、[D110:5154–5159](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/decisions.md:5154>)。自己改善契約も、既存leafへ収まらなければ変更を止めて裁定へ返すとしている。[skill-self-improvement.md:28–37](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/skill-self-improvement.md:28>)、[同:48–51](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/skill-self-improvement.md:48>)。

**成果物影響:** 規約違反が land する。

### B2 — 段9 pointerでは開始時刻とselectorを取得できず、死文になる — real

pointerは`DW-S09`、すなわちwave終了時に初めて読まれる。[s2-plan-out.md:174–180](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s2-plan-out.md:174>)、[core.md:107–111](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/dev-wave/core.md:107>)。しかしコマンドは`START_ISO8601`、`END_ISO8601`、2 project slug、cwd selector、保存先を要求し、その導出も禁じている。[s2-plan-out.md:205–227](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s2-plan-out.md:205>)。

wave終了時には正規の開始時刻を遡って取得できない。保存先・slug・cwd selectorの権威ある供給元も定義されていない。「実行時に明示」は値の出所ではない。推測すればD206の母集団根拠とD220の明示指定を破る。[D206:9868–9871](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/decisions.md:9868>)、[D220:10388–10391](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/decisions.md:10388>)。

比較すると、

- 置かない案はU-1を発効できない。
- `docs/README.md`や別ファイルへ置くだけでは、開始時に読まれず、予算外reference問題も残る。
- wave開始時に必ず読む入口または`DW-C00`へ置き、repo外のintent/configへ開始時刻と外部供給operandを保存する案なら実行可能になる。

**成果物影響:** 推測した時間窓・selectorで保存される観測値が偽になる。

### B3 — `files_scanned`による欠測判定は、D220が禁じた偽ゼロを保存する — real

プランは`files_scanned == 0`だけを`missing`とし、それ以外の完全走査・metric 0を`observed_zero=true`にする。[s2-plan-out.md:130–164](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s2-plan-out.md:130>)。さらに、誤ったcwd、正しいselectorだがrequestなし、誤った既存projectを区別できないと自ら認めている。[同:166–172](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s2-plan-out.md:166>)。

実装上、`files_scanned`はfileを開いた時点で増え、cwd/time filterはその後requestごとに適用される。[claude_session_ledger.py:963–978](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:963>)、[同:995–1005](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:995>)。`records_seen`もfilter前である。[同:569–580](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:569>)。したがって「fileは200件読んだが対象requestは0件」が`complete + observed_zero=true`になり得る。これはD220の「該当0件は観測値0でなく欠測」と正面衝突する。

collectorからfilter一致request数を直接返し、artifactの母集団へ保存する必要がある。metricから逆算してはならない。少なくとも、既存だが誤ったproject、cwd一致0、空時間窓の3ケースが必要である。

**成果物影響:** 保存される観測値が偽になる。

### B4 — 非gateのrc契約と標準`argparse`が未接続 — 限定付き

プランは全引数を必須にしつつ、selector/config/output失敗もhelper rc=0とする。[s2-plan-out.md:72–88](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s2-plan-out.md:72>)、[同:124–126](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s2-plan-out.md:124>)。しかし通常の`ArgumentParser.parse_args()`は必須引数欠落・型エラーで`SystemExit(2)`を送出する。現collectorもこの形である。[claude_session_ledger.py:905–911](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:905>)。

プランが明示的にcatch/custom parserを実装すれば解消するが、現在の記述とテスト一覧では「実processのCLI parse failureでもrc=0」が固定されていない。public関数だけのテストでは不足する。

**成果物影響:** parse/config失敗が伝播するとwaveが止まる。

### B5 — 実行場所P8は誤り。ただし段2の修正は妥当 — 限定付き

親briefの143.7 MiBは単一process RSSであり、`local-ok`の証拠にならない。[brief.md:32–54](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/brief.md:32>)。規範量は全子孫を含むcgroup charged-memoryで、per-process RSSの代用は禁止されている。[tools/README.md:11–23](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/README.md:11>)、[pegasus-runbook.md:374–413](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/pegasus-runbook.md:374>)。

分類測定はユーザー端末の手番であり、AIが測った271.7 MiBを登録根拠にできない。[pegasus-runbook.md:484–498](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/pegasus-runbook.md:484>)。この理由は定期実行だけでなくwave末の手動実行にも及ぶ。手動であることはメモリ分類を免除しない。

ただし新helperは`tools/pegasus/**`外なので、admission registryへの登録対象ではない。分類は`unknown`のまま計算ノードで実行するか、非gateの欠測として終える。段2プランはこの結論へ修正済みである。[s2-plan-out.md:293–300](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s2-plan-out.md:293>)。

**成果物影響:** P8を残せば規約違反が land する。段2の`unknown`修正を採ればrefuted。

### B6 — U-2の漏洩面は手動境界に残る — 限定付き

| 経路 | 判定 |
|---|---|
| docs例示 | `WAVE_ID`等のplaceholderだけで、実値漏洩はrefuted。[plan:205–227](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s2-plan-out.md:205>) |
| tool既定値 | `~/.claude/projects`は機体非依存の記号であり、保存先・slug・windowに既定値を置かない案は妥当。[ledger.py:28–30](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:28>) |
| artifact/error | reportは展開済み`projects_root`を持ち、missing/unreadable issueとstderrにも実pathが入る。[ledger.py:848–858](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:848>)、[同:1022–1028](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:1022>)。repo外artifact・stderr内なら許容されるが、worklogへ転記してはならない。 |
| test fixture | 既存fixtureの`/synthetic/izanagi`のような合成値を使えばよい。[test_claude_session_ledger.py:49–55](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_claude_session_ledger.py:49>)。実slug・実時間窓をfixtureへ写す必要はない。 |
| commit message | provenance checkerは本文を任意としており、privacyは検査しない。[ai-provenance.md:9–17](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/ai-provenance.md:9>)。実行command、error、OUT pathをsubject/bodyへ入れない手動監査が必要。 |
| spool/worklog | 提案されたU-4 fragment本文にはoperandは不要。[plan:301–318](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s2-plan-out.md:301>)。nodeid・statusだけを記録し、実commandを貼らない。 |

新しいprivacy lintまで足すのはD205上過剰であり、見送ってよい。ただし段7・commit前の実値監査は省けない。

**成果物影響:** 実operandやerrorをtracked文面へ転記すれば規約違反が land する。提案された固定文面だけならrefuted。

### B7 — 新schemaは直ちにU-3違反ではない。D206のimport再利用もforkではない — 限定付き

D220はwaveごとのtyped artifactを明示的に許可している。[D220:10385–10386](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/decisions.md:10385>)。新envelopeは新しい形式だが、task-run v2、定期実行、A/B、CC成果物の凍結受理集合ではない。`ledger_report`へcanonical schema v2 objectを残し、既存schemaを変更しない案ならscope内である。[s2-plan-out.md:90–124](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s2-plan-out.md:90>)。

また、collectorを公開関数へ抽出し、そのdictをimport参照する案はraw transcript parserのforkではない。[s2-plan-out.md:21–33](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s2-plan-out.md:21>)。D206が禁じる別parserには該当しない。[D206:9863–9877](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/decisions.md:9863>)。

ただしB3の一致母集団を保存しなければ、「母集団を必ず出す」要件は形式上ではなく意味上破れる。envelopeを将来「第2台帳」やcanonical reportの代替validatorへ昇格させるのも別裁定が必要である。

**成果物影響:** B3を直さなければ保存される観測値が偽になる。schema新設そのものによる規約違反はrefuted。

### B8 — 新test fileは既存meta-test契約を満たす計画がない — real

`orchestrator/tests/test_collect_claude_wave_usage.py`という配置・命名自体は正しい。[s2-plan-out.md:229–250](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s2-plan-out.md:229>)。しかし全`test_*.py`は、自走harnessを持つかREADME allowlistへ載る必要がある。[test_plain_runner_coverage.py:44–74](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_plain_runner_coverage.py:44>)。プランにはどちらもない。

既存ledger testと同じ`pytest.main([__file__, "-x"])`の`__main__`を付ければ、allowlist変更は不要である。[test_claude_session_ledger.py:1347–1348](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_claude_session_ledger.py:1347>)。

その他の衝突はない。

- 新toolは`check_docs.py`のtool inventory対象ではない。
- `DW-S09`本文への1行追加はH2・段dispatch・条件dispatch集合を変えない。[check_docs.py:444–505](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/check_docs.py:444>)。
- hooksは一般Python script内部のwriteを見ないため、衝突しない代わりに防壁にもならない。[hooks/README.md:182–190](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/hooks/README.md:182>)。
- `tools/`とテストは実装面なので、統合commitにCodex `role=author` trailerが必要。[ai-provenance.md:44–55](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/ai-provenance.md:44>)。

**成果物影響:** 自走harnessもallowlist追加も無ければwaveが止まる。

## 総括

**(a) 判定: NO-GO。** 主因は、(1) filter一致0件を正常な消費0として保存する設計、(2) 開始時刻・selector供給元のない段9契約、(3) 957 bytesの規範手順をaggregate外へ逃がす予算迂回、の3点である。

**(b) must-fix**

1. collectorがfilter一致request数を直接返し、artifactへ母集団として保存する。これが0なら`missing`とし、metric 0から推測しない。
2. 収集契約をwave開始時に読まれる面へ移し、開始時刻・slug・cwd selector・repo外保存先の権威ある供給元を定める。
3. 手順本体を`docs/README.md`へ逃がさない。既存dev-wave family内で実byteを捻出するか、予算外referenceを認める明示裁定へ戻す。
4. 実processのparse/config/output失敗でもwaveへ非0を伝播させないことを固定する。
5. 新test fileへ自走harnessを付ける。

**(c) 見送ってよい所見**

- admission registry登録、新しい自動dispatch task、定期実行、task-run v2、A/B、gate化。
- envelope専用validatorやproduction級のsymlink/race多層防御。
- U-2専用の新規privacy lint。既存のtracked差分・commit messageの実値監査で足りる。
- `tools/README.md`、dispatch集合、凍結済みCC成果物の変更。