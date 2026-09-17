## 前提の検算

射影された全ファイルの指定範囲を読んだ。以下の行番号は変更前の現物に対する位置である。ファイル作成・編集、Git 状態変更、pytest、監査の実走はしていない。実行した検算は検索と、メモリ上の文案置換・byte 数・SHA-256 の算出のみ。

以降、表中の略号を次のように定義する。

| 略号 | ファイル |
|---|---|
| ADC | `tools/audit_dangling_commits.py` |
| CBR | `tools/check_branch_rescue.py` |
| TA | `orchestrator/tests/test_audit_dangling_commits.py` |
| TR | `orchestrator/tests/test_check_branch_rescue.py` |
| TL | `orchestrator/tests/test_branch_rescue_ledger.py` |
| TD | `orchestrator/tests/test_check_docs.py` |

用途分離は実装可能であり、I1〜I7 は維持できる。核は、off で既存の core findings をそのまま返し、既存の抑止処理を一切変更しないことである。集合包含は、**固定した snapshot の `(commit, path)` 対**について検査する。path list を含む `Finding` tuple 自体の集合包含では、部分抑止された commit を正しく比較できない。

brief・依頼の補正点は次のとおり。

- 走査なしの分岐条件は ADC:1721、返却は1750〜1764。off の判定は、これより前の root 検証1704にも必要。
- `_load_blob_metadata`（ADC:564）は `ls-tree` ベースであり、cat-file は起動しない。cat-file の起動点は637、利用開始は1803〜1804。両方を独立に禁止検査する。
- p04（TR:337）は到達不能 finding のない repo と空の外部 directory を使う。変更だけで rc 3 にはならない。rc 0 の正例を残し、landed 参照付き外部 copy の非空 fixture を追加する。
- cleanup command の現状は6,201 bytes。最長行の実測は105文字であり、110は上限。
- `test_plain_runner_coverage.py` が読む allowlist の正本は `orchestrator/tests/README.md`。TA・TRには自走 harness があり、TL は README:133 の allowlist にある。
- `acceptance_duration_ledger.json` の所在は `orchestrator/tests/acceptance_duration_ledger.json`。所要記録は現行 test collection の全件一致を意味しない。
- 第2段の有効化条件は、提示された worklog 1614／D2117 の warm fixture 最大335.8秒で充足する。ただし D2117 の代替受理条件は T-2637/T-2660 限定で、本 wave へ自動適用できない。
- P5 の「掃除入口だけを所要受理対象にする」は、D958/D2116 の逐語から自動的には導けない。本 wave の事前条件として明記すべき設計判断である。

## 入口の設計

ADC:1972付近、`--offrepo-root` の隣に追加する。

```python
parser.add_argument(
    "--offrepo-scan",
    choices=("off", "full"),
    default=None,
    help=(
        "repo 外走査: off は環境変数の探索根も無視、"
        "full は探索根必須。省略時は従来どおり探索根指定時のみ走査"
    ),
)
```

入口の振る舞いを以下に固定する。

| mode | CLI root | env root | 結果 |
|---|---|---|---|
| 省略 | あり | 任意 | CLI root が env を完全に上書き。現行維持 |
| 省略 | なし | あり | env root を利用。現行維持 |
| 省略 | なし | なし | 現行の未実施表示と core findings |
| off | あり | 任意 | usage error、rc 2 |
| off | なし | 任意 | env root を読まず、root 検証・外部走査なし |
| full | あり | 任意 | 現行の CLI root 経路 |
| full | なし | あり | 現行の env root 経路 |
| full | なし | なし | 実行不能、rc 2 |

**usage error と実行不能は分ける。**

- off＋CLI root は `parse_args` 直後、ADC:1996付近で `parser.error("--offrepo-scan off と --offrepo-root は併用できません")`。stderr に usage/error、stdout に elapsed 行なし。既存 TA:356 の `test_cli_argparse_usage_error_precedes_audit_and_has_no_elapsed` と整合する。
- full＋rootなしは `audit_with_offrepo` 冒頭で `RuntimeError`。ADC:2016以降の既存 try/except/finally を通す。stderr に
  `audit_dangling_commits: 実行できません: --offrepo-scan full には --offrepo-root または IZANAGI_DEV_WAVE_JOBS_DIR が必要です`
  を出し、stdout の最後に既存形式の `elapsed_seconds=` を1本出す。超過時の専用行も既存 finally が出す。要確認の正常終了 summary は出さない。

ADC:2004〜2010 の root 決定は、最初に off を判定して `roots=()` とする。off で env の値を取得したり `Path.resolve` したりしない。

ADC:1688 の signature に keyword-only の `offrepo_scan: str | None = None` を追加する。`None` は互換経路、`"off"` は明示停止、`"full"` は root 必須。bool ではこの3状態を表せない。API に未知の値を渡した場合も、冒頭で実行不能として拒否する。

`AuditReport`（ADC:83の後）には末尾の既定付き field を置く。

```python
offrepo_scan: str = "full"
```

この field は「外部走査を許す方針」を表し、完走の証明ではない。互換経路・明示 full は `"full"`、明示 off だけ `"off"`。実施状況は引き続き `scan_performed`、requested/accepted roots、各 failure field で表す。

これなら TA:224の `_report`、TA:373、TA:1295の直接生成は変更不要。省略＋rootと明示 full＋同じrootは、mode fieldを含めて同一の `AuditReport` にできる。

## off の実装

変更箇所は ADC:1698〜1706、1721、1750〜1764に絞る。

1. API引数検査で full＋空rootsを拒否する。
2. repo・main ref の確認は現行どおり行う。
3. off なら `requested = accepted = rejected = ()` とし、`_validate_offrepo_roots` を呼ばない。
4. core snapshot は現行どおり取得する。
5. 1721の条件を `offrepo_scan == "off" or not requested or not accepted` とし、既存の走査なし返却へ入る。
6. その返却で `offrepo_scan="off"` または `"full"` を設定する。通常経路の1892以降は既定 `"full"` のままでよい。

off では env root を `requested_roots` に載せない。「要求された探索根」と誤読され、正規化で外部 filesystem に触れる原因になるためである。開示は root の具体値ではなく、off が env 指定を無視する方針そのものを示す。

直接API呼出しで `offrepo_scan="off", offrepo_roots=(root,)` とされた場合も、rootsを使わず無視する。CLI の相反する指定は入口で拒否し、API の off は外部アクセスを止める方針として一貫させる。

off の返却条件は次のとおり。

- `findings == core.findings`
- `suppressions == []`
- `unreferenced_copies == []`
- requested/accepted/rejected roots はすべて空
- `scan_performed is False`
- blob/scan failures は0、oversize は空、reference failure はNone
- regenerable exclusion 情報は core からそのまま継承

failure の0は「確認成功」ではなく「その検査を呼んでいない」値である。off の開示行を必ず併記する。

検査は TA:1665 の trap 型を使う。ただし空候補だけでは退行を検出できないため、**非空の core findings**を使い、`_validate_offrepo_roots`、`_load_blob_metadata`、`_enumerate_offrepo_candidates`、`_start_cat_file_batch`、`os.walk`、`os.scandir` を trap にする。fixture構築とcoreの基準取得を終えてから trap を有効にする。Gitの通常のrepo内部読出しまで禁止しない。

## 開示行

ADC:1910 の先頭に off の分岐を追加し、既存の未指定分岐を `elif` にする。文案は1行とする。

```text
audit_dangling_commits: repo 外走査は明示 off（IZANAGI_DEV_WAVE_JOBS_DIR の指定も無視）；repo 外の同一実体は未確認のため、findings は full なら抑止されうる (commit, path) 対を含みうる。救出 triage は --offrepo-scan full --offrepo-root <root> を指定して単独実行する
```

既存の「探索を未実施」「〜が未指定」とは別文字列であり、全走査の否定結果にも見えない。既存の `repo 外の同一実体で抑止 0` は維持し、off 行と組にして解釈させる。既存の非off出力は変更しない。

CBR:1811〜1830との衝突はない。

- 行頭の空白＋`commit <OID> (` に一致しない。
- `要確認の到達不能変更 N commit` を含まない。
- `要確認 0 件` を含まない。
- terminal の完全一致形式を含まない。
- elapsed 行の後には出力しない。

実子processの統合testでも `complete=True` を確認する。JSONのmodeだけでは、子が正しい出力契約を守った証拠にならない。

## rescue gate の固定

CBR:1797 の子 argv を次に変更する。

```python
[
    sys.executable, str(audit_tool),
    "--repo", str(repo),
    "--offrepo-scan", "off",
]
```

CBR:220 の allowlist から `IZANAGI_DEV_WAVE_JOBS_DIR` だけを除く。`IZANAGI_AUDIT_SCAN_WORKERS` は追加しない。

検索結果では `check_branch_landed.py` に対象env名の参照はない。CBR の当該文字列は220のallowlistだけだった。Git子はCBR:277、landed子は1571の `_no_lazy_fetch_child_env` 経由でこの環境を使うが、repo側実装にそのenvの消費箇所は見つからない。この静的確認を、任意の外部Git wrapperまでの証明とは扱わない。

JSONは以下の3返却箇所に `"offrepo_scan": "off"` を追加する。

| CBR位置 | summary |
|---|---|
| 1802〜1805 | timeout、`complete=False` |
| 1808〜1810 | UTF-8 decode失敗、`complete=False` |
| 1838〜1843 | 正常parse／契約不正を含む通常summary |

`_base_payload` の1941の `audit: None` は維持する。未起動・起動前失敗まで「監査offを実行済み」と表示しない。modeは起動方針であり、timeout等の成功を意味しない。

通知生成1847以降、rc判定2137付近、parser／usage契約2148以降には変更を加えない。新しい通知kind・台帳schema fieldは不要。

p04はrc 0を維持し、mode assertionを追加する。別の実audit fixtureで、同じ到達不能commitについて以下を対にする。

- 単独full＋外部copy＋mainにlanded参照：audit rc 0、抑止あり。
- env root付きrescue：audit rc 1、rescue rc 3、`unledgered-audit-finding`。
- env rootなしrescue：同じrc・commit集合・通知。

## cleanup command の exact 文案と digest

`.claude/commands/cleanup-branches.md:37〜38` を次の2行にする。

```text
- `python3 tools/audit_dangling_commits.py --offrepo-scan off` を単独実行
  (パイプ禁止、rc直後保存、F152)。分岐: `docs/unreachable-object-ledger.md`
```

現物にこの置換だけをメモリ上で適用した値は次のとおり。

| 項目 | 値 |
|---|---|
| 2行のbyte数、末尾LF込み | 169 bytes |
| ファイル全体 | 6,181 bytes |
| 現行との差 | −20 bytes |
| byte予算 | 6,204 bytes、残り23 bytes |
| 最長行 | 105文字、上限110 |
| SHA-256 | `7cc008fabc10b3b495eedfeb0bfbee2de14a3c908e1eb5aa6dd7ff4d7ebaf8ae` |

両pathは同じbulletに残り、TL:167の実行edge条件を満たす。commandからrunbook pointerを除いてよい。掃除にはrootが不要になり、救出triageのrootは台帳doc→runbook §7.2で案内する。

更新箇所を以下に固定する。

| ファイル・行 | 更新 |
|---|---|
| `tools/check_docs.py:788〜790` | digestを上記値へ |
| TD:580〜582 | expected digestを上記値へ |
| TD:663〜664 | synthetic commandを同じ2行へ |
| TD:9948 | `6_201` → `6_181` |
| TD:9953 | `6_201` → `6_181` |
| TD:9954 | `original + "\n" + "x" * 23` にして6,205 bytesを生成 |

TD:9955の6,205、9962の違反文、9947および `tools/check_docs.py:285` の予算値は維持する。TD:9934〜9942のdigest assertionも維持する。

TD:10040の1byte変異は `"commit graph"` を対象にしており、今回の文案では変更不要。§2〜§5その他のcommand本文には触れない。

## 台帳 doc と runbook の文案

`docs/unreachable-object-ledger.md:102〜106` の置換案は次の本文とする。既存の小見出しは維持する。

> 掃除を実行する AI は、棚卸しで `python3 tools/audit_dangling_commits.py --offrepo-scan off` を単独実行する。`tools/check_branch_rescue.py --ledger-check` が起動する監査の子 process も常に off とし、`IZANAGI_DEV_WAVE_JOBS_DIR` を継承しない。JSON の `ledger.audit.offrepo_scan` は `"off"` を示す。
>
> off は repo 外の同一実体を確認しない。従来 full で抑止されていた対も要確認に含まれうるため、未記帳 commit の `unledgered-audit-finding` が増え、rescue gate の rc が `0` から `3` に変わりうる。これは repo 外に同一実体が無いという判定ではない。
>
> 掃除は結果を `/cleanup-branches` §5 へ報告し、救出 triage を別作業として引き渡す。救出 triage を担当する AI は、`python3 tools/audit_dangling_commits.py --offrepo-scan full --offrepo-root <runbook §7.2 の dir>` を単独実行する。full は探索根がなければ実行不能とする。
>
> full で D247 の全条件を満たして抑止された `(commit, path)` 対は要確認から外れる。全対が抑止され、他に要確認pathがない commit について、その監査結果を理由とする台帳 entry は不要である。一部でも要確認pathが残る commit は従来どおり追記候補とする。破棄は対象 commit ごとの裁定に従う。D970 と D1031 は当時の28件と追加19件についての裁定であり、新規 commit への一般的な破棄許可ではない。
>
> 単独監査はパイプへ渡さず rc を直後に保存する（F152）。掃除の監査で rc `0` は削除手順を続行でき、rc `1` は §5 へ報告して救出を判断し、rc `2` は実行不能なので削除を停止する。抑止行が出た場合は rc `0` でも報告する。最終 `elapsed_seconds=` が欠けた場合と未知の rc は削除を停止する。上限超過行は報告するが、rc と削除可否を変えない。上限の正本は tool の `--help` とする。
>
> flag省略は互換経路として残る。CLI rootがenv rootを優先し、いずれも無ければ既存の未実施表示になる。掃除と救出 triage はそれぞれ明示off／fullの入口を使う。root拒否、巨大blob、読出し失敗、landed参照確認不能は否定結果ではなく、`scan_performed=True` だけでも全対象の確認成功を意味しない。

fullを実行しても、次回のoff rescueが同じ通知を再び出すことはありうる。fullの結果をキャッシュする新gateや台帳は設けず、引き渡した監査証拠で説明する。台帳entryを不要とするために既存通知を消す変更はしない。

逐語pinを守るため、同docのschema、状態遷移、63〜98の運用契約・rc表は保存する。特にTL:199の参照先である stale resolution 文と `accepted-loss` 例外、TL:330〜341が要求するschema・保持なし・被覆境界の文言を変更しない。

runbook §7.2 は以下の差分にする。

- `docs/pegasus-runbook.md:854` の用途を「救出triage」に限定する。
- 858のCLI例に `--offrepo-scan full` を追加する。
- 859のexport例は「探索根の既定値。利用時は `--offrepo-scan full`。CLI root指定が優先」と説明する。export自体は監査実行ではない。
- 864を次の3文へ置換する。

> 掃除の単独監査と rescue gate の子 process は明示 off とし、環境変数の探索根も使わない。救出 triage の明示 full は CLI／環境変数のどちらにも探索根がなければ実行不能となる。flag省略の互換経路では、どちらも未指定なら探索は行われず、その旨が出力される。**黙って縮まることはない。**

865〜867のD247条件は維持する。

## test の設計

新testは既存ファイルへ追加し、新test file・新allowlist登録は作らない。

| 配置 | 提案node名 | 検査内容 |
|---|---|---|
| TA:2066付近 | `test_explicit_off_ignores_env_and_preserves_core` | 非空fixture、env rootあり。API結果がcoreと完全一致。mainがenv rootを取得しないことも対象key限定trapで確認 |
| TA:1665付近 | `test_explicit_off_touches_no_offrepo_io` | 非空core＋rootsを渡すAPI呼出し。root検証、metadata、列挙、cat-file、walk/scandirをtrap |
| TA:2066付近 | `test_explicit_off_disclosure_is_distinct_from_missing_root` | off専用行あり、未指定行なし、triage案内あり、抑止0。省略＋rootなしでは従来行 |
| TA:1866付近 | `test_explicit_full_suppresses_copy_that_off_reports` | 同一snapshotのlanded参照付きcopy。full抑止・off報告。pair集合包含とoff==coreを確認 |
| TA:1981付近 | `test_explicit_full_matches_legacy_root_report` | CLI/env rootをparameterize。API report完全一致、CLIの時間・進捗以外の報告行一致 |
| TA:356付近 | `test_explicit_off_with_cli_root_is_usage_error` | env有無をparameterize。SystemExit(2)、stderr usage、elapsedなし、audit未呼出し |
| TA:337付近 | `test_explicit_full_without_root_is_execution_failure` | env削除／空文字。rc2、stderr実行不能、stdout terminal1本、正常summaryなし、core未実行 |
| TA:上記隣 | `test_explicit_full_missing_root_preserves_elapsed_overrun` | 偽時計で上限超過。rc2維持、超過行→terminalの順序 |
| TR:988付近 | `test_audit_child_argv_is_explicit_off` | spawn記録でaudit子のargvに正確なoff指定 |
| TR:988付近 | `test_child_env_omits_offrepo_root` | 親envにrootを設定し、Git・landed・audit子のenvに存在しないこと |
| TR:1790相当のunit配置 | `test_audit_summary_discloses_off_for_all_outcomes` | 正常0／finding／契約不正／timeout／decode失敗をparameterize。全summaryにoff、既存issueとcomplete維持 |
| TR:337付近 | `test_real_audit_off_reports_landed_external_copy_with_or_without_env` | 実audit使用。単独fullのrc0対照後、rescueはenv有無ともrc3、同じ未記帳commit、mode off、complete true |

fixtureはcopyで抑止されるpathだけでなく、抑止されないpathも含めると、部分抑止とcommit数の混同も防げる。実audit rc0→rescue rc3の正例は、全pathがfullで抑止される別ケースを使う。

既存testへの変更・維持を1件ずつ整理する。

| 既存位置 | 新期待／扱い |
|---|---|
| TR:337 p04 | rc0・count0・未記帳空を維持し、`offrepo_scan=="off"` とcompleteを追加 |
| TR:830 m14 | rc3・通知辞書を維持。summaryのoff確認を追加可 |
| TR:988 m16 | 現在の安全検査を維持。新argv/env検査は別nodeにして専属killerを明確化 |
| TR:1492 m22 | terminalなしは引き続きrc2。summaryはoffかつcomplete false |
| TA:224 `_report` | 変更不要。新field既定値で互換 |
| TA:373／1295 `AuditReport` | 既存期待を維持。新field既定値で等値比較維持 |
| TA:1981 CLI優先 | 既存期待維持。明示fullの対を追加 |
| TA:2066 root未指定 | 省略時の既存表示・rc1維持 |
| TA:2084 env既定 | 省略時の抑止・rc0維持 |
| TA:2234 候補なし | scan false維持 |
| TA:2272 巨大blob | oversizeと候補basename0の既存表示維持 |
| TD:9912 digest契約 | 新digestとsynthetic本文の一致 |
| TD:9945 byte予算 | baseline6,181、違反6,205、上限6,204を維持 |
| TL:199／330／337／344 | 期待変更なし |

`_make_fake_audit`（TR:145）はargvをparseしないため、flag追加で修正不要。ただしfakeだけでは入口固定を証明できないのでspawn検査と実auditの双方を残す。

## 変異 matrix の事前登録候補

以下の12件を候補とする。行番号は変更挿入点。nodeは前節の提案名であり、まだ実行結果ではない。

| ID | 対象 | 変異 | 期待・killer |
|---|---|---|---|
| M0 | ADC:1697 | docstringだけ変更 | SURVIVED、等価対照 |
| M1 | ADC:1704／1721 | offでも渡されたAPI rootsを検証し、通常走査経路へ送る | KILLED：`test_explicit_full_suppresses_copy_that_off_reports` |
| M2 | ADC:2004〜2010 | offでenv root取得を復活 | KILLED：`test_explicit_off_ignores_env_and_preserves_core` の対象env読出しtrap |
| M3 | ADC:1698 | full＋rootなし拒否を削除 | KILLED：`test_explicit_full_without_root_is_execution_failure` |
| M4 | CBR:1797 | 子argvからoff指定を削除 | KILLED：`test_audit_child_argv_is_explicit_off` |
| M5 | CBR:220 | root envをallowlistへ戻す | KILLED：`test_child_env_omits_offrepo_root` |
| M6 | ADC:1910 | offを従来の未指定表示に替える | KILLED：`test_explicit_off_disclosure_is_distinct_from_missing_root` |
| M7 | ADC:1996付近 | off＋CLI rootのusage拒否を削除 | KILLED：`test_explicit_off_with_cli_root_is_usage_error` |
| M8 | CBR:1803／1808／1838 | 各summaryからmodeを削除 | KILLED：`test_audit_summary_discloses_off_for_all_outcomes` |
| M9 | `tools/check_docs.py:789` | digestを旧値へ戻す | KILLED：TDの `test_codex_cleanup_branches_skill_contract_pins_exact_surface` |
| M10 | ADC:1722付近 | off早期返却前にmetadata読出しを追加 | KILLED：`test_explicit_off_touches_no_offrepo_io` |
| M11 | ADC:1722付近 | off早期返却前に外部walk/scandir呼出しを追加 | KILLED：`test_explicit_off_touches_no_offrepo_io` |

briefのM0〜M10は方向として妥当だが、次を事前登録時に補正する。

- M4はenv遮断が残るので、findingsだけを見るtestでは生存する。argv自体が契約である。
- M5もoff指定が残るので、結果だけでは生存する。env自体を検査する。
- M2はenv値を読むだけで捨てれば結果は同じ。今回の「読まない」実装契約をtrapで固定する場合だけKILLEDを要求できる。
- `or offrepo_scan == "off"` だけを削除しても、offのrootsが空なら既存条件で早期returnする。この局所変異は等価であり、M1として登録しない。
- M10を「cat-file」と呼ぶのは不正確。metadataとfilesystem列挙を分けてM10/M11とし、cat-file起動も同じtrap testに含める。
- M8は全返却箇所を対象にする。正常summaryだけの検査ではtimeout/decodeの欠落を殺せない。

実装確定後にpatch位置と期待失敗node集合を凍結する。ここでは専属killer候補を示しており、全失敗nodeの完全一致を実証したとは主張しない。

## 焦点テスト集合と影響範囲

検索で確認した2段までのconsumerは以下。

| 変更面 | 直接consumer | 次段 |
|---|---|---|
| ADC | TA、CBR:1797、cleanup:37 | TR、TL:344、TD:663 |
| CBR | TR、TLのschema検査、cleanup:39 | 台帳docの運用契約 |
| cleanup command | `tools/check_docs.py:6615`、TL:167 | TD:9912／9945／10040以降 |
| 台帳doc | TL:187／199／330／337 | cleanupの分岐pointer |
| 既存testファイル | `test_plain_runner_coverage.py:49/60/77` | README allowlist／各自走harness |
| test node名・所要 | `acceptance_duration_ledger.json` | `conftest.py:1577/1679`、`tools/acceptance_shards.py:63` |

所要台帳の該当範囲はTAが594〜737、TRが4135〜4214、TLが2109〜2143、TDが4233〜4809、plain runnerが13978〜13980。これらは過去のnode別所要であり、本変更の所要ではない。

後続author/fixでの焦点集合は次の5ファイルとする。

- `orchestrator/tests/test_audit_dangling_commits.py`
- `orchestrator/tests/test_check_branch_rescue.py`
- `orchestrator/tests/test_branch_rescue_ledger.py`
- `orchestrator/tests/test_check_docs.py`
- `orchestrator/tests/test_plain_runner_coverage.py`

実行は `tools/run_tests.py` を通す。docs統合後に `tools/check_docs.py`、`tools/check_codex_agents.py`、commit後にprovenance監査も行う。

新testは小さいtmp repoとfake clockを使い、実根走査・sleep・性能測定を受入testへ入れない。5分の受入全走目標とADC自身の所要上限は別の判定である。純増所要は未測定で、達成見込みを緑とは記録しない。

所要台帳は今回の機能実装のために推測値で編集しない。既存p04を改名しないことで不要なnode消失も避ける。実測から更新する場合だけ既存updaterを使い、その際は `test_update_acceptance_duration_ledger.py` と `test_acceptance_schedule_order.py` を追加検査する。

## 計測計画の検算

依頼されたlogin計測を、この監査の限定的な比較計画として扱う。本段では実行しない。

すべて**変更後toolの絶対path**を用い、`--repo` を明示する。実repoのmainにある変更前toolを誤って起動しない。tool bytes／commit、repo main OID、hostname、env、開始時刻、stdout/stderr、rcを保存する。監査をパイプへ渡さず、rcを直後に保存する。

| 系列 | 入力とmode | 手順・目的 |
|---|---|---|
| a | `/work/1/SFC/tanab/izanagi`、off | warm-up1走廃棄＋独立3走 |
| b | `/work/1/SFC/tanab/t2637-audit-fixture/repo`、off | 別途warm-up1走廃棄＋独立3走 |
| c | 同fixture、full＋`/work/1/SFC/tanab/dev-wave-jobs` | bと同じ時間帯に1走。Aの抑止を確認 |
| d | 実repo、変更後CBR `--ledger-check`、親env rootあり | 1走。実際の子argv/envとJSONを観測 |

a/bそれぞれでmax/min>1.5なら3走追加し、全6走の最大で判定する。bのwarm-upをaで代用しない。主観的な外乱を理由に遅い値を落とさない。ほかの監査走行がないことを確認して逐次実施する。

cの比較単位はfixtureのAの `(commit, path)`。B〜D等の残存pathがあるので、「fullでfixture全体がrc0になる」とは期待しない。offではAが残り、fullではD247の条件を満たすAが抑止されることを確認する。core snapshotや外部copyのchurnがあれば差を記録し、同一条件の比較と混同しない。

dは `ledger.audit.offrepo_scan=="off"` だけでは子の実挙動を証明できない。spawn観測と、実子のoff開示行または捕捉したstdoutを合わせる。実repoにfindingsがなければfullでも走査を省略するため、短い所要だけではoffの証拠にならない。非空fixtureの統合testがこの穴を補う。

P5の妥当性は次のように限定する。

- 用途分離後の**掃除入口**をa/bのoffで判定するのは、改善対象との対応として妥当。
- ただしD958は「監査を変更するwave」、D2116は走査強制fixtureも含むため、offへの限定を既裁定の単なる読替えとは記録しない。
- 段4で「本waveの所要受理対象は掃除のoff。fullは変更せず、上限達成も主張しない」と事前条件を固定する。
- fullの1走は差集合の実根デモであり、warm-up＋3走ではない。これをfullの性能再判定や改善倍率に使わない。
- D2117の限定例外を本waveの超過救済へ流用しない。a/bが超過した場合は不合格をそのまま記録する。

## リスクと未確定点

- **第3の入口。** flag省略＋env rootは今後もfull相当になる。互換性のため残すが、掃除の規範入口には使わない。今回閉じるのは指定された2入口であり、任意のad-hoc呼出し全体ではない。
- **開示の読み飛ばし。** stdoutにoff専用行、rescue JSONにmode、台帳docにrc0→3と引渡し契約を置く。JSONだけでfullの確認済み状態を表現しない。
- **通知の再発。** fullで抑止されたcommitも次のoffで再表示されうる。通知抑止の新状態を足さず、別実行の証拠として引き渡す。
- **fullの意味。** 明示fullでも候補なしなら走査省略、root拒否・I/O失敗なら確認不能が残る。「full指定＝全件確認成功」と説明しない。
- **二重防壁の検査。** argvとenvは片方が正常なら結果が変わらない場合があるため、個別の直接assertionが必須。
- **T-2662/T-2664との重複。** ADCとTAが共通編集面。今回の変更はmode入口、早期return、開示、関連testに限定し、境界helper・hardlink alias・D247の抑止述語には触れない。統合時にこれらの変更が混入していないことを確認する。
- **T-2639残骸。** `.codex/worktrees/t2639-impl` の差分は本件の実装根拠・取込み元にしない。現物を本段で調査しておらず、その内容やclean状態は主張しない。
- **P5。** 所要判定の入口限定は段4で明文化が必要。実測後に都合よく受理条件を替えない。
- **稼働中cleanup。** 親briefの指示どおり、現在走っているcleanupへ変更後toolを途中投入しない。

## 総括

実装は、明示mode、offの早期returnと専用開示、rescue子のargv/env固定、cleanup §1の置換に限定する。offはcore findingsをそのまま返し、fullの抑止条件は変更しない。

command案は6,181 bytesで予算内。p04はrc0を維持し、非空fixtureでfull抑止／off報告とrescue rc0→3を別途固定する。段4で確定すべき主要点は、P5の掃除入口に限定した所要受理条件と、変異の具体patch・期待node集合である。
