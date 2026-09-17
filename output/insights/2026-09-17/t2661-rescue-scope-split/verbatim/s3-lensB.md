## 前提の検算

射影された全ファイルの指定範囲を確認した。ファイル変更、Git 状態変更、pytest、監査の実走は行っていない。byte 数・digest・regex の検算と、Git 履歴・差分の読み取りのみ実施した。

以下、`ADC`＝`tools/audit_dangling_commits.py`、`CBR`＝`tools/check_branch_rescue.py`、`TA/TR/TL/TD`＝指定された audit/rescue/ledger/check_docs の各 test ファイルとする。`brief` と `plan` はそれぞれ指定の [s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2661-rescue-scope-split/s1-brief.md)、[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2661-rescue-scope-split/artifacts/dev-wave-t2661-rescue-scope-split/s2-plan.md) を指す。

- **refuted** — 第2段への移行が未承認という疑い：`rulings-verbatim.md:234,248` は fixture 最大335.8秒と第2段の有効化を明記しており、着手順序に欠落はない。
- **real** — P5 の「off だけで所要受理」は既裁定から自動的には導けない：`brief:67` に対し `rulings-verbatim.md:125,234` は監査変更 wave と走査強制条件を拘束するため、限定を確定せず受理すると D958/D2116 合格の過大申告になる。plan:350 は既にこの補正を要求している。
- **refuted** — findings の包含を commit 数だけで証明する設計ではない：`plan:15,239` は固定 snapshot の `(commit, path)` 対で比較し、部分抑止で取りこぼす問題を避けている。

## 入口固定の穴

| 判定 | 経路・根拠 | 成果物への影響 |
|---|---|---|
| **refuted** | argv に off があり env root が残る場合。`plan:49–53,134` は off が env の取得より先に分岐する。 | env だけの退行では full は復活しない。 |
| **refuted** | argv の off が欠落して env 遮断が残る場合。`ADC:2004`、`CBR:1797` には別の root 指定がない。 | 互換経路の root 未指定になり、走査は復活しない。ただし明示 off の開示契約は失う。 |
| **real／既知の残存** | 両方が退行すれば、`ADC:2007` が継承 env root を採用する。 | 外部 copy による抑止と full 走査が復活し、通知集合・rc・所要が変わる。M4/M5 の個別検査が必要。 |
| **refuted** | `_no_lazy_fetch_child_env` は `CBR:230` で `_child_env()` を呼ぶ。 | Git・landed 子向けに root env が迂回する別 allowlist はない。 |
| **refuted** | landed 子は `CBR:1576` から checker を実行する。`check_branch_landed.py:201,219,230` の環境参照と subprocess は Git 用だけ。 | landed checker を経由した監査再起動は見つからない。 |
| **real／意図した残存** | flag 省略＋env root は `ADC:2007`、`plan:213,360` により full 相当のまま。 | ad-hoc 実行では外部抑止・長時間走査が残る。「全入口を機械的に off 固定」とは報告できない。 |

Markdown 検索は99ファイル・227箇所。現行の運用入口で root 付き実行を示すのは次の3箇所で、plan はすべて扱っている。

- `.claude/commands/cleanup-branches.md:37`：off へ置換。
- `docs/unreachable-object-ledger.md:102`：掃除 off／別作業の triage full に分離。
- `docs/pegasus-runbook.md:854,858`：triage 用途を明記して full を追加。

**refuted** — Codex overlay に第四の実行入口はない：`.agents/skills/cleanup-branches/SKILL.md:14` は共通 command 全文へ委譲し、監査 argv を複製していない。その他の root 付き例は archive、failures、insight の過去実行記録であり、現行手順への変更対象にはしなくてよい。

**unknown／nit** — `brief:58` の「127 test・全 CLI 例の変更が必要」という数量的根拠は未立証。ただし省略時の既存契約を維持し、掃除の規範入口を2箇所に固定する判断自体は妥当である。flag 必須化を採らない理由は、数量よりこの互換契約で説明できる。

## rescue の JSON / rc 契約

**refuted** — summary の追加漏れは plan 上ではない。`plan:144–152` は `CBR:1802` の timeout、1808 の decode 失敗、1838 の通常返却をすべて列挙し、`CBR:1941` の `audit: None` を維持する。未起動と、起動方針が off の失敗を区別できる。

**refuted** — 新開示行によって `complete=False` になる疑いは、文案に現物の regex を当てて否定した。

| `CBR:1814–1830` の検査 | off 開示行の一致数 |
|---|---:|
| 行頭空白＋`commit <oid> (` | 0 |
| `要確認の到達不能変更 N commit` | 0 |
| `要確認 0 件` | 0 |
| terminal の `audit_dangling_commits: elapsed_seconds=…` | 0 |

開示行が既存 terminal より前に出る実装なら、正常 summary と commit 行の解釈を壊さない。

**refuted** — rc・通知 kind の追加は不要：`CBR:1847` の通知生成、2137 の rc 分岐、2148 の CLI を変更しない計画なので、0／2／3／64 を維持できる。単独 ADC の finding rc は1であり、rescue の通知 rc3とは区別されている。

**real／解釈上の限界** — `offrepo_scan: "off"` は CBR が付ける起動方針であり、子の実行証拠ではない：`plan:144,348`。JSON 単独を根拠にすると argv 欠落を見逃すが、plan は spawn 観測と実子出力で補っている。

## cleanup command の pin 閉包と予算

現物の37–38行だけを plan の exact 文案へメモリ上で置換した結果：

| 項目 | 再計算結果 |
|---|---:|
| 置換後2行、末尾 LF 込み | 169 bytes |
| command 全体 | 6,181 bytes |
| 現行との差 | −20 bytes |
| 上限までの余裕 | 23 bytes |
| 最長行 | 105文字／上限110 |
| SHA-256 | `7cc008fabc10b3b495eedfeb0bfbee2de14a3c908e1eb5aa6dd7ff4d7ebaf8ae` |

**refuted** — byte 計算の誤りはない。`plan:175–180` と一致する。brief:60 の「予算3 bytes」は変更前の余裕であり、置換後は23 bytesになる。

**refuted** — execution edge は失われない：`TL:167–184` に対して、監査 path と台帳 path は同一 bullet、禁止語4種は不在、該当監査 bullet は1本、既存 rescue bullet も1本のままである。

**refuted** — pin 更新漏れはない：`plan:184–195` は次を列挙済み。

- `tools/check_docs.py:789` と `TD:581` の digest。
- `TD:663–664` の synthetic 本文。
- `TD:9948,9953` の6,201→6,181。
- `TD:9954` の超過 fixture を `+ "\n" + "x" * 23` に変更し、6,205 bytesを維持。

synthetic の現行本文と実 command は一致した。

**refuted** — overlay の digest 更新は不要：`tools/check_docs.py:6604–6612` は skill 自身、6615–6624 は command 自身を別々に hash する。skill 本文を変えなければ skill の digest は変わらない。

**refuted** — runbook pointer 削除による指摘の必須語検査は発火しない：`tools/check_docs.py:738–745` は `CODEX_NEXT_TASKS_SKILL_LITERALS` であり cleanup 用ではない。cleanup は台帳への分岐を維持する。

## test の殺傷力と変異の帰属

plan の新 test 表には12件ある。先頭8件を依頼の(a)〜(h)として点検した。以下は静的評価であり、KILLED の実測結果ではない。

| 対象 | 判定・production 経路／帰属 |
|---|---|
| **(a)** off env無視・core一致（plan:236） | **refuted** — API に加え実 `main` の対象 env key 読出しを trap にするため、M2 を結果一致に隠さず検出できる。API 呼出しだけに縮めてはいけない。 |
| **(b)** off I/O禁止（237） | **refuted** — 実 `audit_with_offrepo` に非空 core と roots を渡し、metadata・列挙・cat-file を別々に trap にする設計。`os.walk` だけの弱い検査ではない。M10/M11 はそれぞれ禁止呼出しで赤になる。 |
| **(c)** off開示と未指定の区別（238） | **refuted** — off行の存在と従来未指定行の不在を検査するため、M6 を検出できる。両ケースで環境を明示的に設定／削除する必要がある。 |
| **(d)** full抑止／off報告（239） | **unknown／nit** — 非空の実 fixture は適切。ただし M1 の指定 killer にするには、off 側を `audit_with_offrepo(..., offrepo_scan="off", offrepo_roots=(root,))` で呼ぶことを明記すべき。CLI off が先に roots を空にすると、M1 がこの node では生存しうる。 |
| **(e)** fullと互換経路の一致（240） | **refuted** — 実 API report と CLI 出力の比較であり、両層 stub ではない。CLI root 優先と env root の双方を通す設計になっている。 |
| **(f)** off＋CLI root拒否（241） | **refuted** — 実 parser の `SystemExit(2)`・usage・elapsed不在を検査するため、M7 を後段の rc2 と取り違えない。 |
| **(g)** full＋rootなし（242） | **refuted** — 実 main/API の拒否を通し、stderr・terminal・正常summary不在を固定する。M3 は拒否欠落で赤になる。core未実行 trap は補助検査として扱える。 |
| **(h)** full失敗時の超過開示（243） | **refuted** — 時計だけを差し替え、実 finally の超過行→terminal順序を検査する。既存の失敗契約を時間超過で変えない証拠になる。 |

追加4件について：

- **refuted** — argv 記録（plan:244）は実 `_audit` の spawn 引数を検査するので、env 遮断が M4 の結果差を隠しても検出できる。
- **refuted** — env 記録（245）は親に root を設定し、Git・landed・audit 各子の存在を確認したうえで env 不在を assert すれば M5 を検出できる。`TR:988` の記録方式を使え、`_child_env` 自体を stub にする必要はない。
- **refuted** — 全 summary（246）は実 `_audit` の正常・契約不正・timeout・decode 分岐を通す設計で、M8 の各返却点を被覆する。
- **refuted** — 実 audit 統合（247）は full の rc0 対照と、env有無双方の rescue rc3を通す。fake audit だけでは証明できない parse と通知の連結を被覆する。

**real／既知の限界** — `os.walk` の trap だけなら、`_load_blob_metadata` だけを呼ぶ退行は殺せない：`ADC:1768,1780` は独立した呼出しである。plan:107,237 は metadata 自体の trap を要求しており、この穴は補正済み。

**real／事前登録上の注意** — M1 で off 条件だけを削っても、roots が空なら `ADC:1721` の既存条件で返るため等価変異になる。`plan:296` の指摘は正しい。M1 の具体 patch と(d)の呼出しを組で固定すること。

**refuted** — M9 の killer は適切：`TD:9934` が production digest 定数と expected を比較するので、production 定数だけ旧値に戻す変異を検出できる。ただし全失敗 node 集合は未実測であり、専属候補名を完全一致の結果とは扱えない。

## 既存 test の期待変更の網羅

- **real／補正済み** — `TR:337` の p04 は空の外部 directory と findingsなしの repo なので off 後も rc0。env 遮断の退行を殺せない。`plan:251` の rc0維持＋mode確認と、247 の別非空 fixture が適切であり、p04 自体を rc3 fixture に変える必要はない。
- **refuted** — flag 必須化への逸脱はない：`TA:2084` の env 既定を使う省略実行は `plan:52,263` で保存される。
- **refuted** — fake audit の argv 対応漏れはない：`TR:145` は argv を parse しないため、off 引数追加だけで既存 fixture は壊れない。
- **refuted** — `AuditReport` 生成の修正漏れはない：末尾の既定付き field なら `TA:224,1295` の省略生成と期待値比較を維持できる。
- **refuted** — 走査省略の既存表示を消す必要はない：`TA:2234,2272` は互換経路の test であり、off 専用分岐と分離できる。
- **refuted** — terminal 欠落の扱いは不変：`TR:1492` は引き続き rc2／`complete=False`、modeだけ追加すればよい。

## 親 brief の provisional 裁定と実測値の一般化

| 裁定 | 評価 |
|---|---|
| **P1** | **real／意図した限定** — 第3入口を残す判断。省略互換を明記する plan:213,360 は妥当。「任意の掃除実行を機械的に封鎖」まで一般化しない。127件という根拠は nit。 |
| **P2** | **refuted** — command→台帳の可視 pointer を維持し、plan:203,207 が掃除担当 AI と別作業の triage 担当 AI を明記するので、full を command に直接書かなくても到達 edge は残る。 |
| **P3** | **refuted** — landed checker の env 読取りは `GIT_REPLACE_REF_BASE` と `PATH` のみ（201,219）。repo 内 Git wrapper も root env を消費しない（CBR:243）。任意の外部 wrapper まで無害とする証明ではないが、本変更の根拠として足りる。 |
| **P4** | **refuted** — rc0→3と「外部実体未確認」の開示は plan:205 にあり、新 kind や新台帳を必要としない。fullで全対が抑止された場合と一部残る場合も plan:209 が区別する。 |
| **P5** | **real／凍結前 must-fix** — off限定の所要受理を本 wave の明示判断として確定する必要がある。D2117 の例外を自動継承した扱いにはできない（rulings:248、plan:350–355）。 |
| **P6** | **refuted、M1の細部は unknown** — argv/env の個別検査、metadata/walk の分離、summary全返却点の検査へ plan が補正済み。M1 の非空 API roots だけは具体化を要する。 |

**real／補正済み** — 実 repo の `--ledger-check` 1走の短い所要だけでは off を証明できない：`rulings-verbatim.md:234` は findingsなしなら full でも省略することを明記する。`plan:342,348` の子 argv/env 記録＋実子 stdout と、非空 fixture の統合 test を実施するなら足りる。JSON の mode 値だけに縮めてはならない。

## 他 wave との編集面と残骸

**refuted** — T-2639 の残骸を本 wave の未実装差分と扱う必要はない。

対象は現在の worktree 内ではなく、`/work/1/SFC/tanab/izanagi/.codex/worktrees/t2639-impl` に存在した。対象2ファイルの差分は staged である。

- 当該 worktree の `diff HEAD` と `99125e783^..99125e783` の対象2ファイル patch は、13,478 bytesで完全一致。
- 両ファイルの作業木 blob は、`99125e783` と本 checkout の HEAD の blob に一致。
- `99125e783` は本 checkout の HEAD の祖先。

根拠の変更箇所は `CBR:1498` 付近の説明伝達と `TR:1639` 以降の追加 test。本 wave が残骸を取り込む必要はなく、取り込めば重複作業になる。

**refuted／計画上** — T-2662 は `ADC:1272,1292` の境界 helper、T-2664 は `ADC:971,1219` の owner/alias 配布。本 wave の mode入口・1688以降の早期返却・1909以降の開示とは production の予定編集行が分かれている。

**unknown／nit** — 他 wave の未確定 patch まで行単位の無衝突は保証できない。ADC と TA は共通ファイルなので、統合時に差分確認は必要だが、現時点で本 wave の findings・rc を変える混入は示されていない。

## 所見一覧 (real / refuted / unknown、must-fix / nit)

| ID | 判定・重要度 | 根拠と放置時の影響 |
|---|---|---|
| B1 | **real／must-fix、凍結前** | brief:67、rulings:125,234、plan:350。off限定の受理条件を未確定のまま使うと、D958/D2116達成を過大申告する。plan 自身が是正を要求済み。 |
| B2 | **unknown／nit** | plan:239,279。M1 killer の off 呼出しに非空 API roots を明記しないと、その node の KILLED 帰属が成立しない可能性がある。 |
| B3 | **unknown／nit** | brief:58。「127 test・全CLI例」の変更量は未立証。互換維持の設計判断は成立するが、却下理由の数量的断定は弱い。 |
| B4 | **real／nit、意図した残存** | ADC:2007、plan:360。省略＋env rootはfull相当のままなので、入口固定の成果を任意のad-hoc実行へ一般化できない。 |
| B5 | **refuted／修正不要** | CBR:230,1576、landed:201,219。別env経路・landed経由のfull復活は見つからない。 |
| B6 | **refuted／修正不要** | CBR:1802–1843、plan:144。JSON返却点と出力parseは整合し、rc・通知kind追加も不要。 |
| B7 | **refuted／修正不要** | check_docs:789,6615、TD:9948。文案・予算・digest更新閉包は整合する。 |
| B8 | **refuted／修正不要** | TR:337、plan:247,251。p04の弱さは別の実audit fixtureで補う設計になっている。 |
| B9 | **refuted／修正不要** | `99125e783`、CBR:1498、TR:1639。T-2639対象差分は着地済みpatchと完全一致し、本waveへの取込みは不要。 |

## 総括

レンズBでは、実装設計を差し戻す新たな欠陥は確認しなかった。入口2箇所、JSON／rc、command の pin 閉包、主要な検査の穴は plan で扱われている。

凍結前に P5 の所要受理対象を明示判断として確定し、M1 の killer に非空 API roots を固定すること。テスト・変異・性能は未実行であり、合格や KILLED はまだ主張できない。
