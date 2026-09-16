## 実測の再現

**主要な実測は再現できた。P1 の一般化と P3 の規則には訂正が必要。**

以下、パスを短縮する。

- `B/` = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/`
- `R/` = `output/env/pegasus/calibration/registered/`
- `J/` = `output/env/pegasus/calibration/job-staging/`

**refuted — registered 件数・内訳・admission が誤っているという疑い。** 現物 JSON と Git の tracked 集合を照合し、8 件の SHA-256 が親一覧と一致した。`load_verified_calibration` を `env_tag=pegasus / clocks_per_us=2100 / attestation_mode=required` で実行し、**8/8 ADMITTED** を再現した。

| record の SHA 接頭辞 | protocol の根拠 | rratio | submit_epoch |
|---|---|---:|---:|
| `753f535a` | genome 不在、取得 argv は silo | 50 | 1784404710 |
| `94a4b79f` | genome 不在、取得 argv は silo | 50 | 1785983265 |
| `5c836a22` | genome=silo | 95 | 1789310388 |
| `2b7ba072` | genome=silo | 5 | 1789523899 |
| `449d0ad2` | genome=mocc | 50 | 1788976373 |
| `9b49335d` | genome=tictoc | 50 | 1789452628 |
| `b3329d93` | genome=mocc | 95 | 1789452794 |
| `cb985139` | genome=tictoc | 95 | 1789452729 |

根拠は各 `R/calibration-<16 桁接頭辞>.json` の `genome`、`workload.ycsb_rratio`、`acquisition_receipt.qsub.submit_epoch`。silo の内訳は rr5×1 / rr50×2 / rr95×1 で一致する。

**refuted — g1 の method・4 job の argv・CCBench 既定に関する疑い。**

- g1 の method は実際に `proc-cpuinfo`。`R/calibration-753f535a8d024727.json:1442`。
- 他 7 件は plan が固定する rotating-min method。例: `R/calibration-94a4b79fa31bba3c.json:1442`。
- silo の 4 job、`0:867876.nqsv`、`0:892707.nqsv`、`0:995805.nqsv`、`0:478.nqsv` の `J/<job>/calibrate-argv.json` は、いずれも `--extime` がなく、workload は指定の 3 key。`--binary` は各 file の 13〜14 行。
- CLI 既定は `extime=3 / sweep_reps=3 / noise_reps=10`。`orchestrator/calibrator/cli.py:150`。
- `ycsb_max_ope` の CCBench 既定は 10。`external/ccbench/include/ycsb.hh:22`。

**real — 「runner は max_ope を渡さない」は一般論として誤り。** 固定 flags にはないが、workload の全 key を flags に追加するため、渡せる。今回の較正 argv にない、と限定すべきで、plan は修正済み。`orchestrator/calibrator/runner.py:1119`、`:1125`、`B/s2-plan-out.md:49`。

なお親 summary の `schema=None` は schema 不在の証拠ではない。現物の key は `schema_version` で、値は `calibration/v2`。`B/probe-calibrations-summary.txt` の各 `schema=None` 行と `keys` 行。

## 閉包

**real — accepted record は registered 外にも存在する。ただし追加の silo 取得は確認しなかった。**

- silo 4 件には、それぞれ `output/env/pegasus/calibration/attempts/<job のコロンを下線へ置換>/calibration.json` がある。registered と完全 SHA が一致する複製で、別取得ではない。
- `output/insights/2026-09-11/t2563-calibration-runtime/{before,after}/calibration.json` は別 SHA の accepted 較正。両方とも `genome=mocc`、Pegasus、rr50。各 file の `:1573` と `quality.status` が根拠。したがって「accepted 全体が 8 件」は誤りだが、「registered が 8 件」は正しい。
- `output/env/linux-baremetal/calibration/calibration_t48_skew{0,0p9}_rr50_rmw0.json` は別環境の旧記録で、`quality.status=accepted` と v2 admission の証拠を持たない。今回の required admission 候補にはできない。
- `output/env/` と `output/insights/` の圧縮ファイル 1,771 件を展開して検索した。schema への言及は 38 件、解析可能な JSON 内に追加の accepted calibration object は検出しなかった。文字列内に埋め込まれた任意形式の記録まで不存在を証明したものではない。

**refuted — genome 不在 2 件の証拠が untracked、または辿れないという疑い。** 対応 argv は両方 tracked。各 record の `acquisition_receipt.allocation.pbs_jobid` (`:8`) から、次の式で辿れる。

`output/env/pegasus/calibration/job-staging/<pbs_jobid>/calibrate-argv.json`

そこで `--binary` の次要素が silo、`--binary-sha256` の次要素が receipt の `ccbench.binary_sha256` と一致することを確認する形にすれば、親の説明に依存しない。plan の `:141` には、この具体的な対応式と照合 field を補うとよい。

**real、実装修正は scope 外 — D1538 の consumer 側限定は未実装のまま。** 逐語は将来の genome 不在 record を内容 hash 許可リストで拒否すると定めるが、`layer3_report._floor_protocol_and_basis` は genome 不在かつ within-run なら無条件に silo を返す。呼出し前後にもその許可リスト照合はない。

根拠: `B/verbatim-rulings.md:358`、`orchestrator/campaign/layer3_report.py:493`、`:552`、`:579`。

一方、**現行の通常 certify 経路から genome 不在の accepted record が registered に入る経路は確認しなかった**。receipt から genome を導出し、v2 に格納してから publish する。非 certify 経路は genome 不在記録を作れるが、通常の出力先は registered ではない。`orchestrator/calibrator/cli.py:876`、`:771`、`:1089`、`:1241`。この producer の性質を、D1538 の consumer 限定が実効化した証拠にしてはいけない。

## 規則の機械適用性 (P3)

**real — 親 P3 は JSON 単独では判定不能。plan の補正を含む固定規則・Git・実装参照が必要。**

| 条件 | 判定に必要な現物と根拠 |
|---|---|
| c1 | 保存パス、固定 commit、tracked blob と現物 bytes。JSON field ではない。`floor_pair_driver.py:1131`。plan は `20a92f6a6` に集合を固定する (`B/s2-plan-out.md:124`)。 |
| c2 | JSON 全体と SHA、`env_tag`、`clocks_per_us`、`attestation_profile.effective_clock.tolerance_pct`、`quality.status`。admission は `calibration_verify.py:116`、quality は `floor_pair_driver.py:1170`。 |
| c3 | `genome` の protocol 部分。rr95 は `R/calibration-5c836a22eff9ab40.json:1574`。欠落 2 件は前節の receipt→argv 対応と、plan の完全 SHA 限定が必要 (`B/s2-plan-out.md:134`)。 |
| c4 | `env_tag / clocks_per_us / threads / workload`。rr50 は `R/calibration-94a4b79fa31bba3c.json:1568`、`:1569`、`:1685`、`:1686`。比較は `floor_pair_driver.py:1185`。 |
| c5 | `attestation_profile.effective_clock.method` と固定 method literal、既知除外の path/SHA。rr50 の method は同 JSON `:1442`、除外 identity は `layer3_report.py:79`。 |

**real — 「現行 policy の method」という正本はない。** `orchestrator/calibrator/effective_clock_policy.py:6` が定めるのは tolerance=2.0。取得 method の定義は `orchestrator/campaign/env_attestation.py:35` 以降。verifier も tolerance だけを照合する (`calibration_verify.py:130`)。plan の固定 literal と「新しい人手選択条件」という明記は必要であり、妥当。`B/s2-plan-out.md:143`。

**refuted — submit_epoch 欠落・現在の同値衝突。** registered 8 件すべてに整数値があり、相互に異なる。追加の mocc 2 件にも存在する。ただし秒単位の値なので、将来の同値衝突はあり得る。

**real — SHA 昇順は厳密な値非依存順位ではない。** SHA は測定値を含む内容から決まる。plan の `(project, queue, request_id)` 辞書順への変更はこの問題を避ける。これらの field も現物に存在する。例: `R/calibration-94a4b79fa31bba3c.json:53`。同一取得 identity の異内容・順序根拠欠落時に停止する規定も維持すべき。`B/s2-plan-out.md:151`。

適格性適用後は rr50 も g2 の 1 件になるため、**今回の採用結果は取得順序の実例検証にはならない**。複数候補があることと、順位規則が実際に勝者を決めたことを区別する。

## A-4 の束縛可能性 (P2)

**refuted — 提案 3 cell が較正との値照合で落ちるという疑い。** `environment.env_tag=pegasus`、`clocks_per_us=2100` とすれば、指定された 5 照合は一致する。

| workload | 採用 JSON | records | threads / workload の根拠行 |
|---|---|---:|---|
| rr95 | `R/calibration-5c836a22eff9ab40.json` | 1000000 (`:1617`) | `:1690` / `:1691` |
| rr50 | `R/calibration-94a4b79fa31bba3c.json` | 1000000 (`:1612`) | `:1685` / `:1686` |
| rr5 | `R/calibration-2b7ba072b88023ae.json` | 2000000 (`:1618`) | `:1691` / `:1692` |

3 件とも workload は文字列値の exact 3 key で、skew=`"0.9"`、rmw=`"0"`、rratio はそれぞれ `"95"` / `"50"` / `"5"`。JSON の key 順序は辞書比較に影響しない。

**real — `"false"` への置換は束縛を壊す。** spec parser は文字列を保持し、binder は辞書を exact 比較する。bench flag として意味が同じでも `"0" != "false"`。`floor_pair_driver.py:781`、`:1191`。plan の置換禁止は正しい。

**scope 外 — binder 全体の成功は未証明。** `_bind_checkout_inputs` はこれらに先立って binary と build receipt も検査する (`:1135`)。今回確認したのは較正側の整合であり、実 spec・配置済み binary を含むロード成功ではない。

## A-3 の動作点論 (P1)

**real — 「extime/max_ope は変えるが reps は変えない」は、bench 1 回の設定についてのみ成立する。**

- `extime` は `-extime=<値>` として bench に渡る。`runner.py:1122`。
- floor driver は `ycsb_max_ope` を workload に加え、runner が flag 化する。`floor_pair_driver.py:1588`、`runner.py:1125`。
- `reps` は同じ flags による `run_once` を繰り返す回数。`runner.py:1154`、`:1194`。

したがって reps は 1 回の transaction 構成を変えないが、総実行時間・時間的標本化・推定量の標本分布・全反復成功の確率に影響する。「分散だけ」は過剰な主張。plan の訂正を採るべき。

**real — sweep 3 は各 records 点の反復数である。** `sweep.py:101`、`:103` がそのまま測定に渡す。「どちらも 1 測定の反復数ではない」は誤りで、「床値測定に採る reps を一意に指定しない」が正確。

D1854 の resident peak 論との矛盾はない。max_ope は transaction 内の操作数を変え (`external/ccbench/include/ycsb.hh:67`)、rratio/rmw も操作を変える。extime 変更も観測期間を変える。ただし **変更すれば必ず LLC miss 率・RSS の数値が変わる、と実装だけから断言はできない**。較正取得時の構成を維持する、という根拠に留める。

`reps=5` は出力からの導出ではなく今回の承認値。先例の正確な行は `pipeline.py:190`。過去実行 source bytes までの完全検証を未実施とする plan の留保 (`:72`) も必要。

## 成果物の形式

**refuted — plan の方針が fragment 文法と矛盾するという疑い。ただし、そのまま保存できる完成 fragment ではない。**

- decisions frontmatter は必須 key・無引用・seq 1 を満たす。`B/s2-plan-out.md:30`、`docs/spool/README.md:35`。
- 3 見出し案は、実ファイルで `## {{D:slug}}. <題>` にする必要がある。plan の説明用見出しや `D 見出し案:` を転記しない。`docs/spool/decisions/README.md:5`。
- worklog は `## 本文` と `## 次の一手差分` の 2 H2、action は H3、継続 field は 2 space。plan `:187` は組立てを親へ残している。`docs/spool/worklog/README.md:5`。
- `更新` と `完了` に完全な base digest、`完了` に末尾機械 field の `remaining: none` が必要。plan `:197`、`:203` は正しいが、digest の値は未提示なので受理可能性は未確認。
- base は land 先 local main の実体 item から取得する。carry stub 自身の hash や省略 SHA は不可。`docs/spool/worklog/README.md` の `base:` 規則。
- 引用符禁止は frontmatter の値に対するもの。workload JSON の文字列引用符は禁止対象ではない。`docs/spool/README.md:51`。

**refuted — §11 の長い追記だけで行長予算に掛かるという疑い。** 事前登録は living lint 対象 (`tools/check_docs.py:146`) だが、列挙された `TextLimit` 対象ではない (`:283`、`:5940`)。一般的な全 Markdown 行長上限は確認しなかった。

living 文書への `.md:数字` 参照は拒否されるため、plan の検査用行番号を追記本文へ混ぜない (`check_docs.py:175`、`:6722`)。追記案そのものには該当参照がない。禁止 placeholder 3 語 (`:206`) も追記案にない。最終 fragment の check_docs・fold dry-run は親の実測待ち。

## 焦点走の対象

**refuted — plan が列挙する 4 node で、編集した実文書の無影響を直接証明できるという主張。** 4 node は実在するが fixture を読む。

- `test_p3_b4_admission_record.py:405` は `_section5_document()`。
- `test_p3_b4_floor_artifact_issuer.py:681`、`:703`、`:1312` は tmp 側の事前登録文書。

plan はこの限界を明記済み (`B/s2-plan-out.md`「受入と検査の順序」)。

**今回の追記案によって結果が変わると判断できる node はない。** 根拠は次のとおり。

- admission consumer は `## 5.` から `### 5.1` の表を切り出す。`p3_b4_admission_record.py:623`。
- floor resolver は全文から floor 行 prefix の一致を数える。§11 でも同じ行を追加すれば影響するが、今回の追記案にその行はない。`p3_b4_floor_artifact_issuer.py:1470`。
- 分析 consumer は §5.1.1 を次の H4 以上まで切り出して hash を検証する。§11 は範囲外。`p3_b4_analysis_prereg_consumer.py:301`。

実文書を読む追加確認先は `test_p3_b4_analysis_prereg_consumer.py::test_current_document_contract_literals_match_implementation` (`:95`)。§5 表の bytes 不変確認と併用する plan は妥当。pytest は実行していない。

## 親 brief の誤り

**real として採る訂正候補は以下。**

1. `B/s1-brief.md:29` の runner 一般・reps の分散限定・sweep 反復数の説明は不正確。前述の実装に合わせて plan の限定へ直す。
2. `:31` の「現行 policy の method」は参照先が成立しない。固定 literal の新しい人手条件として記録する。
3. `:31` の genome 不在 fallback は無限定。plan の完全 SHA 2 件限定を必須とし、層 3 自体は D1538 未閉包と別記する。
4. `:31` の同 epoch SHA 順は測定値を含む内容に依存する。plan の取得 identity 順へ置換する。
5. `:36` の「C 群が発火する」は適格性検査と順位決定を分ける。今回は c5 適用後に rr50 も 1 件。
6. `:32` の §11.3「第 1 bullet」はアンカーの誤記。指定追記は現物の第 2 bullet に属する。`docs/phase3-b4-reflux-ablation-preregistration.md:1292`、`:1297`。
7. 「結果を見る前に定めた」とは記録できない。親 probe は既に較正値を表示している。D2044 の逐語 (`B/verbatim-rulings.md:13`) と閲覧時系列の関係は、plan `:167` が残した親裁定事項のまま。
8. 「残前提は A-5 のみ」を凍結可能性全体へ広げない。較正照合の一致だけでは binary/build receipt を含む binder の成功を保証しない。`floor_pair_driver.py:1135`。

## 総括

**plan は条件付き採用候補。P2 の 3 cell と P1 の設定案を覆す実物不一致はなかった。**

親裁定・記録で必要なのは、P3 の固定集合・固定 method・歴史的 SHA 例外・取得 identity 順の明文化、D2044 の閲覧時系列の決着、D1538 の consumer 未閉包と今回の人手規則の区別である。

本段の実測は **8/8 admission、tracked/SHA/JSON/argv 照合、外部記録の探索**。書き込み、pytest、spec loader、床値測定、最終 fragment の受入検査は行っていない。