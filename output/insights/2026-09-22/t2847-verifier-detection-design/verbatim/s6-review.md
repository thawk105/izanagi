## 所見

以下の「本文」は `output/insights/2026-09-22/t2847-verifier-detection-design/README.md` を指す。

1. **[must-fix] §4.1 V29「v2 化後は lost update の巡回で N」** — 指定した変更と発生条件から、この検出期待は導けない。同じ key を読む→更新する典型的な lost update では、si が更新時に R を消すため、検出に必要な rw 辺が残らない。例えば、双方が x の初期値を読んで更新しても、trace が異なる commit 版の W 2 件だけなら ww 1 本の DAG になる — 根拠: `external/ccbench/cc/si/transaction.cc:239-247,539-551`、`orchestrator/verifier/dsg.py:641-679` — 「v2 化だけでは典型的 lost update を検出できない。巡回なしなら証拠面不足で I」と修正する。N を期待するなら、残存 R から巡回を手導出できる別の履歴を示す。

2. **[must-fix] §5.1 hot-update-unlock「hot は X だけで indeterminate」** — 4 thread の hot 走には version dup もある。「X だけ」は 1 thread に限られる — 根拠: `output/env/pegasus/calibration/s3_mocc_mutation_proof.json` の `runs.hot_update_unlock_hot_t4`、特に `:111589` は `version_dups=67777`、`:111597` は `lock_coverage_violations=7241088`。判定は I、巡回は 0 — 1 thread と 4 thread を分けて記載する。lockskip / early-unlock の 4 thread 走にも version dup があるため、併発層の説明に補記すると正確になる。

3. **[must-fix] §2.2 phantom 行「範囲読みは R を出さない」** — 範囲読みで見つかった個々の record は R に現れうる。見えないのは述語・範囲境界・結果に現れなかった key に対する依存である — 根拠: `external/ccbench/cc/silo/transaction.cc:304-317` が scan 結果に `read_internal()` を呼び、`:277` が read set に追加し、`:606-610` が R を出す。si も `transaction.cc:448,164,541-544` に同じ経路がある — 「取得 record の R は出るが、述語読みを表す証拠がないため phantom は判定しない。現行 YCSB は scan を呼ばない」と直す。

4. **[must-fix] §2.2 thread file 欠落行の無条件な I、および integrity 各行の判定条件** — file が末尾の取引だけを持っていた場合、証人なしでは欠番にならず certified になりうる。本文 D03 とも不一致である。また orphan・version dup・framing・X/P/I があっても、巡回が残れば N が優先する — 根拠: `orchestrator/tests/test_verifier.py:1312-1321` は明示的に証人を渡し、`missing_txids==0` を確認している。優先順位は `orchestrator/verifier/model.py:505-515` — file 欠落行を D03 と揃え、表全体に「integrity による I は巡回なしの場合」という条件を付ける。

5. **[must-fix] §1・§3末尾・§5.2「既存 fixture と inline test の被覆を除く純増14案」** — 14 という列挙数自体は合うが、未被覆の意味の純増ではない。純増候補には既存 inline test と意味が重なる案が多数ある — 根拠: `orchestrator/tests/test_verifier.py:336`（C03）、`:716`（D02）、`:766`（E03）、`:1252,1265`（D01）、`:1312`（D03）、`:559`（D04）、`:1285`（D05）、`:1326,1484`（D06 の一致／不一致）、`:3003-3008`（F02 の同一取引二重 W・version dup 0） — 「27案、既存 fixture の再説明13案、追加候補14案。ただし追加候補にも inline 被覆済みがある」とし、未被覆・fixture 化・説明の追加を分けて再集計する。F02 の「専用は無し」にも既存 test を補う。

6. **[must-fix] §4.5「35変異、27機構、対照を除く23変更」** — V36 は無改変 si なので、変更機構の数に含められない。現在の族のまとめ方を維持するなら、35項目は「34変異＋無改変対照1」、27族は「26変異族＋無改変対照1」であり、4つの等価・保守的対照を除いた変更機構は22になる。また V09〜V12 をまとめているため、実際の表のデータ行は32行である — 根拠: 本文 `:161,188,211-212`、`verbatim/s4-ruling.md` R3 — 「行数」を「ID項目数」と区別し、無改変対照を変異数から外す。修正後も依頼の20〜40機構は満たす。

7. **[must-fix] §4.3 V07「完走した prefix は S」** — 非 SWO comparator の UB から、完走した部分の S は保証できない。sort が戻っても write set を破損していれば P が発火し、I になりうる。起草にあった限定が本文で落ちている — 根拠: `external/ccbench/cc/silo/transaction.cc:390-432`、`patches/README.md:417-435`。`verbatim/s2-plan.md` C07 は「S の場合あり」「破損時は P 等」とする — 「完全・非空で他の違反がない prefix は S になりうる。P 等による I/N、parse error、停止もあり、UB の結果は固定できない」と修正する。

8. **[must-fix] §6.5「版順を保てば、分割で得た赤を全体の赤として確定できる」** — 真の部分グラフなら成立するが、取引を抜いて再構築したグラフでは、版順の維持だけでは足りない。version dup があると producer が変わり、全体にない巡回を作れる — 根拠: `orchestrator/verifier/dsg.py:353-367,641-679`。例えば全体を `T0@v1:W(x)`、`T1@v1:W(x),R(y,v2)`、`T2@v2:W(y),R(x,v1)` とすると、先に登録された T0 が x の producer となり、辺は `0→2→1`。T0 を除くと x の producer が T1 に変わり、`1↔2` が生じる。版順は変わっていない — 「各局所辺が全体の辺または非空の有向経路に対応すること」を条件にする。再構築の場合は producer の一意性・対応保持も必要。また「全辺を保つ形だけ」は必要条件として強すぎるため、巡回の有無を保存する縮約等も許す表現に直し、認証には全体の integrity・証人の検査も必要と明記する。

9. **[must-fix] §7 方法節の certified 条件と置換表** — 方法節の条件では、非巡回・integrity clean な空 trace まで certified と読める。また `:323` の「巡回を検出しなかった (certified)」は、非巡回だが I の場合を混同している — 根拠: `orchestrator/verifier/model.py:505-520`、`orchestrator/tests/test_verifier.py:336-351` — 方法節に「取引1件以上」を入れ、置換表は「非空の観測履歴について、非巡回性と完全性・証拠面の条件を満たし certified と判定された」とする。有限観測に限るという中心的な射程は論文稿と整合している。

10. **[must-fix] §2.1「commit 証人は pipeline だけが渡す」** — CLI からも指定できる — 根拠: `orchestrator/verifier/cli.py:65-74`、`orchestrator/tests/test_verifier.py:1473-1499` — 「pipeline は外部 counter を渡す。API・CLI では任意指定」と直す。併せて、証人未指定の両値 None は clean 条件を満たすこと（`model.py:451-458`）、source evidence の必須条件は X/P であり I は必須でないこと（`:79-84`）を §2.1 でも明示する。

11. **[should] §4.1 V36「emitter を v2 に上げた後は N」** — SI が write skew を許すことは、有限走で必ず巡回が出ることを意味しない。未発生時は、si の証拠面不足により S ではなく I になるため、§4 の共通注記「起きなければ S」でも補えない — 根拠: `external/ccbench/cc/si/transaction.cc:614-616`、`orchestrator/verifier/model.py:450-467,505-515` — 「残存 R/W が巡回を形成する schedule なら N、巡回なしなら I」とする。

12. **[should] §4.3 V28「v2 化後は abort 版の読みが orphan」** — orphan になるには、その R の版に対応する W がないという追加条件が要る。si は読取り時の版番号を値で保存せず、commit 時に version pointer から cstamp を再取得している。inflight 版が後で commit すれば、dirty read が orphan として現れない経路がある — 根拠: `external/ccbench/cc/si/transaction.cc:164,283-285,509,541-544` — abort の確定、非 genesis、同じ key・版の producer 不在、R が update で消されない条件を付ける。V28 は「緑のまま通る盲点14項目」の中にも適切に収まらないため、現状 E と将来の条件付き検出を別分類にする。

13. **[should] §6.1「新版だけの job はこれより短い」** — compare の Elapse から、その一般的な実測結論は出ない。提示された raw には `P-wh10.log=2717S` もあり、`C-wh10.log=805S` より長い。P job の版・条件が異なる可能性もある — 根拠: `raw/verifier-capacity-job-elapse.txt` — 「compare は旧新版の両方を含み、新版単独 job の費用とは異なる」と留める。0.13／0.25 node 時間は verify 本体の換算値として、投入費用の Elapse と区別する。

## 照合できた主要な主張

- 必読4ファイルは読めた。対象 commit `cb2ce0c38`、v2 専用化 `fb5e74a17` の日付と内容、`0ffb2a3c2` の日付・positive control の対応を確認した。
- 非空なら巡回を integrity 不良より優先すること、空 trace は I、X/P source evidence が認証条件であることは実装と一致する。
- B04・B05 の辺と変異時の巡回消失、B06 の G1c、D01・D03 の証人有無の対、F02・F06 の期待は、明記された前提の下で辺の定義と整合する。
- V17 の lock 検査除去、V19 の固定版、V20 の公開版不一致、V21 の writePhase 省略の主要な検出経路は source と一致する。V35 は、YCSB の点更新で版の単調増加と validation を維持する変更として S の見込みと整合する。
- raw の16本は silo 11本が rc=0、mocc 4本と trigger-misattr が rc=1。本文の各 offset も一致する。再実行はしていない。
- mocc JSON は36走。lockskip の4 thread 巡回数587／3,882／3,622、early-unlock の3,636／1,556／1,437、permutation-erase 全6走の巡回0・Pのみは一致する。
- si の `:539-552` の v1 emitter、parser `:323-326` の拒否、update/delete の read-set 消去の行番号は正しい。
- 容量表の取引数・辺数・297／478／896秒・15.2／32.4／81.2 GiB、追加11本、compare の Elapse 805／1,224／1,868秒は引用資料と一致する。
- 既存 fixture の8／9／5分類と22件の凍結集合検査、D799とD1455の歴史的な区別は資料と一致する。
- 過去の si 3,576巡回を当時の記録として保存し、現行の検出力から分ける扱いは適切。今回の依頼にない gate・検査・台帳の追加は提案されていない。

## 判定

NO-GO

## 総括

設計の主要な構成と、既存記録を現行の検出力から分ける方針は妥当である。
修正の中心は、V29の検出期待、moccの単一理由性、純増・変異の件数である。
範囲読みの説明は、取得 record の R と述語の証拠を区別する必要がある。
分割検査の赤の保存には、版順だけでなく producer と辺の対応の条件が要る。
論文用の射程文には、非空条件と「非巡回だけでは certified でない」という区別を補いたい。
V35については、指定された変更だけから期待を逆転させる根拠は見つからなかった。
レビューは静的な読取りと記録照合のみで行い、ファイル編集・テスト・build・実走は行っていない。