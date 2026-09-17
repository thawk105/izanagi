## 前提の検算

指定された全射影ファイルとコードの指定範囲を読んだ。追加で台帳の「追記と状態遷移」、runbook §7.2、core snapshot の実装を確認した。ファイル変更・Git 状態変更・pytest・監査の実走は行っていない。

以下の略号を使う。

| 略号 | ファイル |
|---|---|
| B | 親 job dir の `s1-brief.md` |
| P | 親 job dir の `artifacts/dev-wave-t2661-rescue-scope-split/s2-plan.md` |
| R | 親 job dir の `rulings-verbatim.md` |
| ADC | `tools/audit_dangling_commits.py` |
| CBR | `tools/check_branch_rescue.py` |
| TA | `orchestrator/tests/test_audit_dangling_commits.py` |
| TR | `orchestrator/tests/test_check_branch_rescue.py` |
| L | `docs/unreachable-object-ledger.md` |

**結論は、実装方針には受理集合を縮める経路を認めないが、台帳 entry の免除文案は既存契約と矛盾する。P5 の所要受理条件も既裁定からは導けず、明示的な本 wave の判断として確定が必要である。**

## 受理集合の不変

**refuted：off によって抑止が増えるという懸念。**

ADC:1713 で取得した core の findings を、走査なし分岐は ADC:1751 でそのまま返す。P:81〜102 は off で root 検証を迂回し、同じ分岐へ入れる設計である。metadata 読出しより前に返るため、off が外部 copy を根拠に finding を消す経路はない。

full の集約は ADC:1870〜1883 で `original_findings` の各 path を残すか抑止するだけであり、新しい finding を生成しない。したがって、固定した core の対集合を \(C\)、full が抑止する対集合を \(S\) とすると、

`pairs(findings(off)) = C`
`pairs(findings(full)) = C − S ⊆ C`

となる。比較単位を `(commit, path)` にする P:16 は正しい。部分抑止後の path list を含む `Finding` 全体では集合包含にならない。

条件は、同じ core snapshot・除外設定を使い、正常に report を返した実行を比較することである。`_audit_snapshot` 自体は Git 全体の原子的 snapshot ではなく、fsck・log・tip 読出しを順次行う（ADC:1589）。別々の実走で refs が変われば、同じ `--repo` だけでは条件を満たさない。

**影響：P の分岐案どおりなら off の findings は既存の走査なし結果と一致し、full の抑止処理も維持される。**

**real／nit：B:44 の「full は現行と同一出力」は射程が広すぎる。**

明示 full＋root なしは意図的に rc 2 へ変わり、`AuditReport` には field も増える（P:59〜75）。「同じ root を与えた既存経路の findings・suppressions・unreferenced_copies と非時間依存の報告行を維持」と限定すればよい。これは plan 内では整理されており、実際の findings 退行は示せない。

## 未実施と否定結果の分離

**refuted：P の開示案では未実施と確認不能を区別できないという懸念。**

| 状態 | stdout 上の識別根拠 |
|---|---|
| 明示 off | P:113 の専用行。「env 指定も無視」「同一実体は未確認」を明記 |
| flag 省略・root 未指定 | ADC:1911〜1912 の「探索を未実施」「未指定」 |
| full・候補 basename 0 | ADC:1924〜1925 の「候補 basename 0 件のため走査省略」 |
| root 拒否 | ADC:1922〜1923 の拒否理由と「抑止せず」 |
| oversize／blob 確認不能／scan failure／reference failure | ADC:1926〜1937 の個別開示 |

root が全件拒否された場合は「走査したが失敗」ではなく、拒否による走査未実施である。現在の表示はこの状態を確認成功とは扱っていない。oversize だけで候補がなくなる場合も、走査省略と oversize が併記される（TA:2272）。

off の findings 行に外部 copy の注記がない点は、P:113 の一行中の **「repo 外の同一実体は未確認」** で塞がれている。「抑止 0」だけを単独で意味付けしない設計でよい。既存出力にも `scan_performed=True` を全対象の確認成功とする文言は見当たらない。

**影響：専用行と既存 failure 行を維持すれば、抑止 0 や注記なしを「外部控えなし」と誤認して救出・破棄を判断する経路は増えない。**

## 台帳通知の増加の開示

**real／must-fix：B:P4 と P:209 の「台帳 entry 不要」は既存の追記契約に反する。**

CBR の経路は明確である。

1. `_audit` が stdout の要確認 commit を抽出する（CBR:1811）。
2. 台帳にない OID を `missing` に入れる（CBR:1853〜1854）。
3. 各 OID に `unledgered-audit-finding` を生成する（CBR:1855〜1860）。
4. 技術的に完全でも通知があれば rc 3 を返す（CBR:2137〜2142）。

P:205 の rc 0→3 の開示、JSON の `offrepo_scan`、単独 full への引き渡しはこの経路と整合する。

しかし、既存の [台帳の追記契約](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2661-rescue-scope-split/docs/unreachable-object-ledger.md:47) は、**`unledgered-audit-finding` が出た object も追記対象**と明記する。D247 が許すのは、5 条件を満たした path をその監査の報告から外すことである（R:85〜100）。別実行の full 結果によって、既に off が通知した object の追記義務を解除する規則はない。

P:209 は全対抑止・他の要確認 path なしに限定しているが、この限定でも矛盾は解消しない。P:215 の「次回 off では通知が再発する」という認識も、追記免除の根拠にはならない。

最小の是正は、B:65 と P:209 の entry 不要部分を削除し、次の意味に留めることである。

> full で抑止された対は、その full 監査の要確認から外れる。既に出た通知の追記対象・状態遷移は、既存の台帳契約に従う。

**影響：現文案を採ると、既存契約では追記すべき object が台帳から抜け、off の未記帳通知が再発する。追記免除を維持するなら新しい運用例外の制定であり、本 scope の説明追加ではない。**

なお、off の再表示は既存の `rescued` 等に対する stale 通知も増やしうる（CBR:1861〜1874）。この挙動は L:74〜77 に既に開示されており、新しい通知規則は不要である。

## D970 / D1031 の射程

**refuted：P の docs 文案が一般的な破棄許可になるという懸念。**

P:209 は「当時の28件と追加19件」「新規 commit への一般的な破棄許可ではない」と明記しており、R:155〜175 と整合する。D247 による path の報告抑止と、commit の破棄裁定も分けている。

現行 L:102〜106 と runbook:854〜867 には、D970／D1031 を任意の新規 commit に適用する表現は見当たらない。L:103 の「rc 0 は削除手順を続行できる」は掃除手順の分岐であり、到達不能 object の一般的な破棄許可とは読まない。

本 wave の分岐説明へ対象範囲の限定を加えることは、一次資料の条件 4（R:51〜52）に直接対応しており scope 内である。歴史的裁定や他の救出規則の書換えは不要である。

**影響：P:209 の対象限定を維持すれば、外部 copy があるだけで新規 commit の破棄を許す方向には変わらない。**

## D247 との整合

**refuted：明示 off の新設が D247 の根指定契約と矛盾するという懸念。**

D247 は root の供給経路として CLI／env を定め、両方未指定なら探索せず開示するとしている（R:117〜118）。「root があれば、後から導入する明示 off も無視して必ず走査する」とまでは定めていない。用途分離そのものも今回の起票に含まれる（R:17〜22）。

P は省略時の CLI 優先・env 既定・未指定時の開示を維持し、明示 off のときだけ第三の未実施理由を追加する。env を無視することも P:113 に明記するため、runbook:864 の「黙って縮まることはない」と両立する。

**影響：走査範囲は明示された方針によって縮むが、findings は増える側であり、縮小を隠して suppression を増やす変更ではない。**

これは現行 full 実装が D247 を完全に満たすという再認証ではない。既知の境界 helper／hardlink alias の問題は R:59〜62 に残っており、本 wave の等価性はその既知状態に対するものとなる。

## 親 brief の provisional 裁定と実測値の一般化

**real／must-fix：P5 を D958／D2116 の既裁定そのものとして扱う根拠はない。**

D958 は「監査を変更する wave」を対象とし（R:127）、D2116 は実 repo で走査が省略される場合に **fixture で走査を強制した所要も取り、両方で上限内を要求する**（R:223〜228）。fixture を入力にしても off なら走査を測らないため、B:69 の「D2116 の形」は正確でない。

off の所要を測ること自体は用途分離の改善対象に対応している。ただし、それは既裁定からの自動的な帰結ではなく、本 wave の受理対象を限定する判断である。D2117 の例外は T-2637／T-2660 限定であり、流用できない（R:247〜262）。

P:350〜357 はこの問題を認識している。最小の是正は、段4で off 限定を本 wave の判断として明記し、B の完了条件もそれに揃えること。full の一走は機能対照であり、D958 の所要合格や full の性能維持を実測した証拠にはしない。

**影響：未確定のまま進めると、走査を測っていない off の結果だけで「D2116 を満たした」として wave を受理することになる。**

数値と probe の検算は次のとおり。

| 主張 | 判定・根拠 |
|---|---|
| warm 有効6走 max 335.8秒 | **refuted：誤引用ではない。** R:305〜306 と一致し、第2段の有効化根拠になる。全環境での超過は示さない |
| 約185万 file | **refuted：誤引用ではない。** R:322 の当時の実根規模と一致する。off がこの数を走査する意味ではない |
| 「現在145本」 | **unknown／nit。** B:11 の根拠は射影資料と追加確認した一次資料・entry 1521 で確認できない。採取時刻付きの根拠がなければ「現在」は外す。findings・rc への直接影響は示せない |
| env あり rc 0／なし rc 3 | **refuted：rc の読みは正しい。** `probe_env_inherit.json:6` と `:21`、監査 rc はそれぞれ0／1。同じ lost OID が後者で未記帳通知になる |
| probe が子の走査・抑止を直接記録した | **unknown／nit。** JSON は監査要約と hash であり、生 stdout・走査件数・抑止対は含まない。機序は CBR:220、ADC:2004〜2010 と整合するが、この JSON 単独の直接観測とは分ける |

## 既存 test の見落とし

**refuted：指定された既存 test が、P の互換設計によって赤になるという懸念。** 静的判定は以下のとおりであり、実行結果ではない。

| test | 判定 |
|---|---|
| TA:1981 `test_positive_cli_roots_override_environment` | flag 省略なので既存経路。CLI 側だけ抑止し、env 側の path を残す rc 1 は維持される。明示 full の被覆にはならないため、P の追加対照が必要 |
| TA:2084 `test_positive_offrepo_environment_default_is_used` | flag 省略＋env root の互換経路として、抑止1・rc 0 を維持。掃除の off 固定を検査する test ではない |
| TR:337 `test_p04_missing_ledger_and_real_audit_zero_is_rc0` | 到達不能 finding がなく、外部 directory も空。off に替えても rc 0。rc 3 に期待変更する根拠はなく、P:22 の補正が正しい |
| TR:830 `test_m14_unledgered_audit_finding_returns_rc3` | fake audit が返す OID に対する通知契約は維持。外部走査の遮断は検査しない |
| TR:988 `test_m16_git_allowlist_rejects_forbidden_command_before_spawn` | Python argv は先頭2要素しか照合せず、env は既存安全項目を確認する。off の argv 追加・root env 削除では赤にならず、専用検査が必要 |
| TA:2234／2272 | 省略時の候補なし・oversize の走査省略は維持される。明示 full も同じ既存処理へ入る |

P はこれらの被覆限界を認識し、専用 argv／env test と非空 fixture の実子 test を追加する。上記の test が意味を失う、または予期せず赤になる具体例は見つからなかった。

**影響：既存 test だけでは掃除の off 固定は証明できないが、P の追加 test を実装すればその穴を対象化できる。未実行なので合格とは判定しない。**

## 所見一覧 (real / refuted / unknown、must-fix / nit)

| ID | 判定 | 根拠・放置時の影響 |
|---|---|---|
| A1 | **real／must-fix** | B:65、P:209 は L:47〜48 の追記契約と矛盾。通知済み object の台帳 entry が抜ける |
| A2 | **real／must-fix** | B:67〜69 の P5 は R:223〜228 から導けない。off のみの測定を D2116 合格として wave を受理する危険 |
| A3 | real／nit | B:44 の full「同一出力」は root なし拒否・report field 追加を含めると過剰。P が既に区別し、findings 退行は示せない |
| A4 | unknown／nit | B:11 の「現在145本」の採取根拠未確認。監査成果物への直接影響は示せない |
| A5 | unknown／nit | probe JSON は rc 差を示すが走査・抑止の生出力なし。機序の直接実測としては証拠が不足 |
| A6 | refuted／修正不要 | ADC:1751、1870〜1883、P:81〜102。固定 core について off の抑止増加経路なし |
| A7 | refuted／修正不要 | P:113、ADC:1911〜1937。off・未指定・候補なし・確認不能の表示は区別可能 |
| A8 | refuted／修正不要 | P:209、R:155〜175。D970／D1031 の一般的破棄許可への拡張なし |
| A9 | refuted／修正不要 | R:117〜118、P:113。明示 off と env 無視の開示は D247 の根指定契約と両立 |
| A10 | refuted／修正不要 | TA:1981、2084、TR:337、830、988。指定 test の互換性破壊は認めず、追加被覆は P にある |

## 総括

**must-fix は2件。** 台帳 entry 免除の文案を撤回して既存追記契約へ戻すことと、off 限定の所要受理条件を既裁定の読み替えではなく本 wave の判断として確定すること。

off の早期返却、full の既存抑止処理維持、専用開示、既存 test の扱いは静的検査上妥当である。実装・テスト・性能の合格は本レビューでは判定していない。
