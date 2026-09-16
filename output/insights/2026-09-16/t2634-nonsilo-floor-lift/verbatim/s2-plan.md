## 保留の実体と登録先

**P1〜P4 を支持する。P5 は「D2044 項12による、実証済み較正の用途限定の解除」として記述する。実装は docs-only とする。**

保留の実体は、コードの protocol 拒否設定ではなく、較正取得後にも公式成果物への採用を留保した文書上の状態である。

- `output/insights/2026-09-15/t2224-nonsilo-calibration/README.md:122-123` は「非 silo の within-run floor の embargo を解いていない」と明記する。射影された T2634 起票・裁定逐語も、この保留から実装手番への移行を示す。
- `orchestrator/campaign/layer3_report.py:477-494,545-599` は genome から protocol を取り、`noise_floor` を within-run として `(protocol, records, threads, workload)` で照合する。確認した照合部に非 silo 一律拒否はない。
- `orchestrator/campaign/env_contract.py:253-280,311` は Pegasus g1/g2 の特定較正 record を束縛する registry であり、今回の4対の登録先ではない。
- `docs/phase3.md:533-550` の8b節には silo の較正取得記録があるが、今回の4対の登録項目はない。

**追記位置は `docs/phase3.md:550` の直後、現行551行の前。** `[x] [T-2634]` の1項目として4 record と適用範囲を記す。過去の T-2224 README の embargo 記述は、当時の記録として保持する。

数値の根拠は次のとおり。

| 対象 | request・node | records・LLC miss・CV |
|---|---|---|
| tictoc rr50 | T-2224 README:17 | 同:33 |
| tictoc rr95 | T-2224 README:18 | 同:34 |
| mocc rr95 | T-2224 README:19 | 同:35 |
| mocc rr50 | T-2535 README:25 | 同:35-37 |

T-2224 の3件の完全な registered path は同 README:131-132。mocc rr50 のファイル名は T-2535 README:37、registered にあることは T-2224 README:69-76 が示す。

**mocc rr50 の採用点 LLC miss は指定された一次資料 README に無い。CV は `cv 0.0143` とだけあり、`1.4348%` は無い。** 以下では原表記を保持する。

## phase3.md 8b 節の追記文面案

`docs/phase3.md:550` の直後に、既存項目と同じインデントで挿入する。

```markdown
     - [x] [T-2634] D2044 項 12 に従い、非 silo の within-run floor の保留を、
       実測済みの tictoc / rr50・rr95、mocc / rr50・rr95 の accepted calibration 4 件に限って解除した。
       以下は pegasus / threads 48、ycsb_zipf_skew=0.9、ycsb_rmw=0 の較正記録であり、
       性能比較や床値本走の完了を意味しない。
       tictoc / rr50
       (`output/env/pegasus/calibration/registered/calibration-9b49335d02ad4d2e.json`、
       request `998860.nqsv`、node `bnode093`、records 1,000,000、
       採用点 LLC miss 7.969%、within-run CV 2.2160%)。
       tictoc / rr95
       (`output/env/pegasus/calibration/registered/calibration-cb98513996e5ae35.json`、
       request `998863.nqsv`、node `bnode103`、records 1,000,000、
       採用点 LLC miss 9.557%、within-run CV 0.8336%)。
       mocc / rr50
       (`output/env/pegasus/calibration/registered/calibration-449d0ad22f13e366.json`、
       request `989271.nqsv`、node `bnode020`、records 1,000,000、
       採用点 LLC miss は一次資料 README に記載が無い、
       within-run CV は同資料の原表記 `cv 0.0143`)。
       mocc / rr95
       (`output/env/pegasus/calibration/registered/calibration-b3329d93417c76ad.json`、
       request `998864.nqsv`、node `bnode016`、records 1,000,000、
       採用点 LLC miss 17.008%、within-run CV 1.7204%)。
       解除は上記4対の既取得較正に限り、非 silo の rr5・cicada へ広げない。
       本 wave では新規測定を行っていない。between-run floor は現行 CCBench pin
       `511c953` で起動不能であり、D1373 の関門を維持する。
       一次資料 = `output/insights/2026-09-15/t2224-nonsilo-calibration/README.md`、
       `output/insights/2026-09-10/t2535-certify-offline-fetch/README.md`。
       解除と起動不能の記録 =
       `output/insights/2026-09-16/t2634-nonsilo-floor-lift/README.md`。
```

T-2534 は path と取得状態を記す先例、T-2515 は request・records・LLC miss・CV まで記す先例である。今回の node 併記は依頼に従う。

## decisions fragment 草案

新規ファイル先頭から追加する。

`docs/spool/decisions/2026-09-16-dev-wave-t2634-nonsilo-floor-lift-2.md`

共通形式は `docs/spool/README.md:28-66`、決定本文の形式は `docs/spool/decisions/README.md` に従う。新しい D 番号は先行採番しない。

```markdown
---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-t2634-nonsilo-floor-lift
seq: 2
---

## {{D:nonsilo-within-run-floor-lift}}. 非 silo の既取得較正4対を用途限定で登録し、between-run の起動不能を分離して記録する

**決定:**

1. D2044 項12を実装し、tictoc / rr50・rr95、mocc / rr50・rr95 の
   accepted calibration 4件を、現行 phase doc の8b節へ登録する。
   登録対象は既取得 record の within-run noise floor、すなわち1測定内の
   throughput の変動係数である。性能比較でも床値本走の完了でもない。
2. 登録先は docs/phase3.md の8b節とする。env_contract の世代 registry は変更しない。
   各 record の path・request・node・records・採用点 LLC miss・within-run CV と
   限定を記す。mocc rr50 の LLC miss は一次資料 README に記載が無いと明記し、
   CV は原表記 cv 0.0143 を保持する。
3. between-run floor の実測は本 wave では行わない。親の probe は現行 pin
   511c953 で silo=True、mocc=False、tictoc=False の trace-hook 判定、
   BASELINES が silo/mocc の2件であること、tictoc の引数拒否、
   mocc の引数受理を示した。driver の main は mocc を trace-hook 証拠不在として
   build 前に拒否する。
4. 再開に必要なのは、mocc では実際にコンパイルされる source に hook の証拠を
   含む pin への更新、tictoc では段7 Group B の hook 移植とその pin への反映、
   および driver の baseline 対応である。これらは本 wave の範囲外とする。
   hook の文字列証拠だけで意味論的正しさや verifier 通過を証明したとは扱わない。
5. BASELINES への tictoc 追加、D1373 の関門変更、pin 変更、新たな gate・検査・
   台帳・一般化は行わない。既存の較正 record と凍結成果物の bytes は変更しない。
6. D2044 項12を、実証済み4対の較正を公式成果物へ記録する用途限定の解除として
   適用する。D1360 の stock 専用経路による certified cross-protocol 比較の禁止と、
   D1373 の between-run 生成関門は維持する。rr5・cicada へ解除を広げない。

**理由:**

- D2044 項12は、生産できる protocol の集合を実測で示す前提条件が充足済みとし、
  実証範囲に限って within-run floor の保留を解除した。
- T-2224 の一次資料には較正取得後にも保留を解除していない旨が残り、
  現行 phase doc には当該4対が未登録だった。今回実装するのはこの裁定上の差分である。
- driver の within-run は noise_floor を用いる1セッションのCVであり、
  between-run は独立セッションの中央値のCVである。較正の登録は後者の実測を代替しない。
- 現行 pin の拒否を迂回せずに between-run を測ることはできない。
  tictoc を BASELINES へ追加しても、trace-hook 関門の拒否に移るだけで測定は開通しない。

**却下した選択肢:**

- 全 protocol・全 workload の保留を解除する — D2044 項12の実証範囲を超える。
- 較正CVを between-run floor の実測値として扱う — 測定単位と用途が異なる。
- stock 専用経路や D1373 の関門迂回で測定する — 規律2を緩める。
- 本 wave で pin 更新・hook 移植・tictoc baseline 追加を行う — 裁定実装の範囲を超える。
- 一次資料 README に無い LLC miss やCVの追加桁を推定して埋める — 出典の精度を超える。
```

解除条件は**必要条件**として記す。hook 付き pin への更新だけで測定全体が成功する、という保証にはしない。

## worklog fragment 草案

新規ファイル：

`docs/spool/worklog/2026-09-16-dev-wave-t2634-nonsilo-floor-lift-1.md`

以下は親の実装・受入後に使用する草案であり、現段階の実施報告ではない。

```markdown
---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2634-nonsilo-floor-lift
seq: 1
title: [T-2634] 非 silo の既取得較正4対に限って within-run floor の保留を解除
---

## 本文

D2044 項12の解除範囲を、tictoc / rr50・rr95、mocc / rr50・rr95 の
既取得 accepted calibration に限定した。
判断は {{D:nonsilo-within-run-floor-lift}}。

依頼に含まれた between-run 測定は現行 pin では起動できない。
親の probe で tictoc の引数拒否と mocc の trace-hook 証拠不在を確認し、
driver の拒否関門を維持する方針を採った。
本 wave では較正の再取得も between-run の新規測定も行っていない。
性能比較をしておらず、床値本走の完了も主張しない。

mocc rr50 は一次資料 README に採用点 LLC miss の記載が無く、
CV は cv 0.0143 の表記に限られるため、欠けた値や追加桁を補わない。
rr5・cicada への解除、stock 専用経路の解禁、D1373 の変更は行わない。

## 次の一手差分

### 完了

- [T-2634] D2044 項12に基づく既取得較正4対の保留解除と現行phase docへの登録を完了。
  完了範囲は較正の登録であり、性能比較・床値本走を含まない。
  remaining: none
  base: <land先local mainのT-2634実体から取得したsha256>
```

`base:` は草案の未確定値である。親が land 先 local main に対して `python3 tools/spool_fold.py --base-digest '[T-2634]'` で取得する。取得・置換前には受入可能な fragment と扱わない。

親が新設する insight README は、冒頭から「解除した4対」「一次資料への参照」「親 probe と静的判定の区別」「新規測定・性能比較・床値本走は未実施」を記す。verbatim には brief・plan・consult・裁定・親 probe を保存する。

## 実装面差分の要否 (P4 の判定)

**P4 を支持し、Python・test・BASELINES の変更は不要と判定する。**

| 根拠 | 判定 |
|---|---|
| `between_run_floor.py:60-72,285-288` | tictoc は baseline 未登録で、引数解析時に拒否される。 |
| 同:303-307 | baseline があっても source の hook 証拠が無ければ build 前に拒否する。 |
| 同:112-140 | protocol 名の固定許可ではなく、コンパイル対象 source の証拠を判定する。 |
| `test_between_run_floor.py:251-253` | 実 checkout で silo 受理・mocc 拒否を期待する。 |
| 同:440-483 | mocc 拒否時に tenant・build・measure・write が呼ばれないことを検査する。 |
| 同:300-320,486-552 | hook 証拠を持つ source fixture なら mocc の経路が通ることを検査する。 |

tictoc を BASELINES に追加しても、親 probe の `tictoc=False` と driver:304-307 により測定は開通しない。今回の較正登録に寄与しないため追加しない。

ただし、**「起動できない baseline の存在自体が規律違反」という一般論は採らない。** 現行 mocc が、baseline 登録と source 関門を分ける設計の実例である。P4 を支持する理由は、今回の目的に追加が不要で、測定不能の原因を解消しないためである。

実装面差分ゼロのため変異登録候補は設けない。将来の tictoc 開通には、hook 移植に加えて baseline 対応も必要となる。

## 検査計画

本段では静的確認のみ実施した。pytest・測定・文書 checker は実走していない。

親の実装後の確認は次とする。

1. **転記と差分の目視確認**
   - phase3 の4対・数値・出典を上記一次資料と照合する。
   - mocc rr50 の欠落値を推定していないことを確認する。
   - driver・test・registered record・既存凍結成果物に変更がないことを確認する。
2. **既存文書検査**
   - `python3 tools/check_docs.py`
   - `tools/check_docs.py:142` は現行 phase3 を検査対象に含め、`:1259-1315` は spool 検査を呼ぶ。
3. **fragment の既存受入手順**
   - `python3 tools/spool_fold.py --dry-run --show-diff`
   - `docs/spool/README.md:74-89` に従い、base 一致と生成される台帳差分を確認する。wave 側で実 fold はしない。
4. **phase3 の現物を読む既存 focus test**
   - `orchestrator/tests/test_spool_fold.py:4060` の
     `test_phase3_real_canonical_plan_accepts_unique_and_rejects_generated_duplicate_id`
   - 同:4040-4056 で現物の canonical family を複製し、同:4064 で phase3 を読む。
   - 親が実走する場合は `tools/run_tests.py` を通す。これは台帳構造の検査であり、追記した測定値の正しさを保証するものではない。

今回の登録文を直接検査する新 test は追加しない。`test_between_run_floor.py` は変更せず、P4 の静的根拠として用いる。親の通常の完了検査にある `check_codex_agents.py`、commit 後の `check_ai_provenance.py` も親側で実施・結果記録する。

検索した `tools/tests` は存在しなかった。検査を中断せず、実在する `orchestrator/tests` を確認した。

## P5 の整合

- D1360 は「stock 専用計測経路は偵察としても解禁しない」「公式 report・selector・比較表・順位・headline のいずれにも入れない」と定める。
- D2044 項12は後続の限定裁定として、実証済み protocol/workload の「within-run floor の保留を解除する」と定める。
- 今回はこの用途限定の解除を適用し、「較正が取れたことを性能比較や床値本走の完了とは扱わない」を併記する。
- D1373 の「trace hook の証拠がある場合だけ受理する」は between-run 生成に引き続き適用し、変更しない。
- この限定解釈では矛盾なし。ただし「D1360 は性能比較値だけを禁じる」と一般化する P5 の理由付けは狭める。

## 親 brief への訂正 (file:line の誤り、前提の誤り)

1. **F3 の mocc rr50 `1.4348%` は指定一次資料 README から取得できない。**  
   T-2535 README:36 は `cv 0.0143`。採用点 LLC miss も同 README に無い。今回の文面は原表記と欠落を保持する。

2. **F2 の親 probe は、CLI の終了コードと `main()` の例外実走までは記録していない。**  
   `parent-probe-gate.txt` が示すのは hook 述語・BASELINES・argv 判定である。tictoc の rc=2 は driver:292-298、mocc の build 前 ValueError は同:303-307 と test:440-483 から静的に確認できる。probe の実測範囲とコードによる帰結を分けて記す。

3. **P1 の tictoc 再開条件に baseline 対応が必要。**  
   hook 移植だけでは driver:285-288 を通らない。段7 Group B は `docs/phase3.md:489` にあるが、driver 対応も将来の必要条件として記す。

4. **P2 の「同じ定義」は統計量の意味に限定する。**  
   driver:159-164 は `noise_floor`、`:77` は reps=10。T-2224 README:31-35 は3件について n=10 を示す。一方、T-2535 README は mocc rr50 の reps を明記しないため、README だけを根拠に4件すべての reps=10 を断言しない。producer・測定条件の同一性や代替可能性も主張しない。

5. **P3 の先例の行範囲を補正する。**  
   T-2534 は `phase3.md:537-541`、T-2515 の詳細は `:542-550`。request・records・LLC miss・CV の一式があるのは T-2515 の `:544-545` である。

6. **P4 の結論は維持し、理由を限定する。**  
   baseline 登録だけで測定不能を解消できず、今回の裁定実装に不要だから追加しない。現行 mocc の存在と矛盾する一般的禁止にはしない。

7. **「本 wave は output/ を書かない」と成果物指定が矛盾する。**  
   brief は新規 insight README＋verbatim を `output/insights/2026-09-16/…` に置くとも指定する。親の実装範囲は「既存 record・凍結成果物を変更せず、新規 insight 記録のみ作成」と整理する。本 plan 段では一切書き込んでいない。

## 総括

docs-only で、既取得4対の within-run 較正を8b節へ登録する。D1373 の関門・driver・test は変更せず、新規測定は行わない。

実装前に反映すべき訂正は、mocc rr50 の原表記・欠落値、親 probe の実測範囲、tictoc の将来の baseline 対応、P5 の用途限定解釈、新規 insight 作成と既存成果物不変の区別である。