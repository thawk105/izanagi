## 所見

指定資料を読み、静的照合を行った。テスト実行・書き込み・git log の参照はしていない。以下、`V/` は本パッケージの `verbatim/`、`J/` は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-codex-selfrun-precheck/` を指す。

1. **主張：案 A の「許可根拠」が未定義で、A を選ぶ裁定が何を許すのか確定していない。**
   **根拠：** README §0・§4 は許可境界を未定義・本 wave の対象外とする一方、§4 の prompt 文は「親が…許可根拠を明示」すれば実行する形である。`V/s3-consult-out.md:95–97` が要求した「in-process pytest・cgroup scope 不使用」「hook 非拒否・harness 契約・軽量実績だけを許可根拠にしない」は、貼り付け用の文には入っていない。README 全体には前者の説明があるが、許可根拠として何が成立するかは示されていない。
   **重大度：must-fix**
   **修正案：** A の選択だけでは個別 file の実行許可にならず、対象・実行形を覆う明示裁定を引用できる場合だけ適用すると明記する。貼り付け文にも上記の許可限界を加え、根拠未確定なら B の運用を継続すると書く。

2. **主張：D2195 の先例を、適用除外を落として許可根拠に近い形へ広げている。**
   **根拠：** README §2.3 は対照走全体を「D2195 が親に許した形」、§4 は「親に許した形の子への拡張」と記す。しかし `J/verbatim/D2195.md:3` は node 集合一致・login 許可済みを要求し、parametrize、conftest/autouse、環境変数、import 副作用への依存等を除外する。対象 (c) は README 自身が parametrize ありと記載し、`V/s3-consult-out.md:7` も適用外と指摘済み。`V/s4-adjudication.md:25` の親による授権判断は、この D2195 の条件を満たした証拠ではない。
   **重大度：must-fix**
   **修正案：** 「D2195 と同じコマンド形の実行例」に限定し、少なくとも (c) は同裁定の適用外と明記する。今回の probe に対する親の授権判断と、既存裁定による許可を分けて記録する。

3. **主張：「自走 harness 369 本」「自走 harness の 63%」は分母が誤っている。**
   **根拠：** README §0・§2.4。指定の文字列分類を全 `orchestrator/tests/test_*.py` に適用すると、全 file 369、委譲 232、手動列挙 82、`__main__` なし 55。harness を持つ file は 314 本で、232/314＝73.885%。63% は全 test file 369 本を分母にした値である。
   **重大度：must-fix**
   **修正案：** 「全 test file 369 本中232本、約63%」に統一する。harness 保有 file を分母にするなら「314本中232本、約74%」とする。

4. **主張：T-2810 の「新 test 64 件」は一次報告と食い違う。**
   **根拠：** README §2.6。T-2810 の `verbatim/s5-author.md:37,69,112` は新規63ケースと既存 `certificate_same_commit_as_generation_rejected` 1件、計64 passed と報告している。
   **重大度：must-fix**
   **修正案：** 「新規63ケース＋既存負例1件、計64 passed」に修正する。`PermissionError` と git rc=128 の引用はそのままでよい。

5. **主張：一部の数値・実測主張には、追跡できる一次資料が不足している。**
   **根拠：**
   - README §2.1 補足が引く `J/guard-verdicts/09-*`・`10-*` は、指定 directory に存在しない。収録されているのは01〜08と `measured-at.txt`。
   - §2.4 の「直近8本、7対1」は対象名・抽出記録がない。
   - §4 の平均154分と149 bytes は、`V/proposal-draft-v1.md:16,3` の主張以上の一次根拠を確認できない。指定の `V/memory-selfrun-section.md` にも該当値はない。
   - §2.5 の `.done=0`・`worktree-commit: clean` は、指定 receipt の `launcher_rc=0` とは別の主張であり、その生出力は射影にない。
   - `J/verbatim/runbook-s7-policy.md:6–17` はメモリ基準を確認できるが、README が引く §7.0 の `MemoryMax`・scope 記述は抜粋に含まれない。
   **重大度：should**
   **修正案：** 欠けた出力・対象一覧・記憶抜粋を収録するか、検証不能な補足を削る。receipt の値を `.done` や待ち手の検査結果の代用にしない。

6. **主張：「sandbox による所要の増加は…観測されない」は、この比較から言える範囲を超える。**
   **根拠：** README §2.5。(b) は1.51→1.62秒と増えている。`J/parent-control/b-test_floor_pair_job_contract.log:24` と `V/s5-probe-author.md:59` が根拠。各1回で、README の記載時刻でも親07:48・子08:04〜08:07と離れており、並走負荷・cache の条件を揃えた比較ではない。
   **重大度：should**
   **修正案：** 「差は順に−0.14、＋0.11、−0.06秒。sandbox に起因する増減は判定できない」に置換する。§6 に n=1、負荷条件未統制、`hook_verdict` 未観測、probe 上限150 callと通常既定100 callの相違を集約する。

7. **主張：§0 の128秒は、§2.5 と同じ丸めになっていない。**
   **根拠：** README §0 は128秒、§2.5 は128.9秒。`receipt.json` の `actuals.wall_clock_s` は128.893095489。整数四捨五入なら129秒になる。
   **重大度：nit**
   **修正案：** §0 も128.9秒、または「約129秒」に揃える。MAXRSS も生値のKBを併記し、MBへの換算規約を明示すると再照合しやすい。

## 数値照合表

同じ値の再掲はまとめた。「未確認」は不一致の断定ではなく、指定資料から独立に裏付けられなかったもの。

| README の値 | 一次資料の値 | 一致・不一致 | 出所 |
|---|---|---|---|
| 起点 `5efd69367` | `5efd69367b641b9bfbd6fb426478f66ae5762783` | 一致 | receipt `base_commit`、`V/s5-probe-author.md:11` |
| 開始 gate rc=0 | `OK: wave startup checks passed`、数値rcなし | 成功表示一致、rc未確認 | `V/startup-gate.log:1–2` |
| 開始07:44 | 時刻なし | 未確認 | 同上 |
| 静的判定07:46 | 07:46:26 JST | 一致 | `J/guard-verdicts/measured-at.txt:1` |
| 静的判定 pegasus02 | pegasus02 | 一致 | 同`:3` |
| 綴り01 rc=0 | rc=0 | 一致 | `J/guard-verdicts/01-selfrun-pythonpath.verdict.log:1` |
| 綴り02 rc=0 | rc=0 | 一致 | 同 `02-selfrun-bare.verdict.log:1` |
| 綴り03 rc=2 | rc=2 | 一致 | 同 `03-m-pytest.verdict.log:2` |
| 綴り04 rc=2 | rc=2 | 一致 | 同 `04-pytest-head.verdict.log:2` |
| 綴り05 rc=0 | rc=0 | 一致 | 同 `05-run-tests.verdict.log:1` |
| 綴り06 rc=0 | rc=0 | 一致 | 同 `06-c-pytest-main.verdict.log:1` |
| 綴り07 rc=0 | rc=0 | 一致 | 同 `07-m-pytest-collect-only.verdict.log:1` |
| 綴り08 rc=0 | rc=0 | 一致 | 同 `08-selfrun-cd.verdict.log:1` |
| 補足09・10 rc=0、timeout 180 | 対応payload・logなし | 未確認 | 指定 `J/guard-verdicts/` の一覧 |
| live gate rc=0 | rc=0 | 一致 | `V/check-codex-hooks.log:6` |
| codex-cli 0.155.0 | 0.155.0 | 一致 | 同`:2` |
| live gate47秒 | 08:01:59→08:02:46＝47秒 | 一致 | 同`:1,7` |
| 親対照走07:48 | 生logに時刻なし | 未確認 | `J/parent-control/` 4本 |
| 親(a) 3 passed | 3 passed | 一致 | `a-test_t1259_scan_bound.log:10` |
| 親(a) 2.01秒 | 2.01秒 | 一致 | 同`:12` |
| 親(a) 47.8 MB | 47,816 KB | KB÷1000の丸めとして一致 | 同`:12` |
| 親(b) 22 passed、0 failed | 22 passed、0 failed | 一致 | `b-test_floor_pair_job_contract.log:23` |
| 親(b) 1.51秒 | 1.51秒 | 一致 | 同`:24` |
| 親(b) 35.4 MB | 35,368 KB | 同換算で一致 | 同`:24` |
| 親(c) 38 passed | 38 passed | 一致 | `c-test_b5_contrast_launch.log:2` |
| 親(c) 3.35秒 | 3.35秒 | 一致 | 同`:4` |
| 親(c) 57.3 MB | 57,276 KB | 同換算で一致 | 同`:4` |
| 親(d) rc=0・test出力なし | rc=0・time行のみ | 一致 | `d-test_auditor_gate-allowlist.log:1–2` |
| 親(d) 0.22秒 | 0.22秒 | 一致 | 同`:1` |
| 親(d) 28.0 MB | 27,996 KB | 同換算で一致 | 同`:1` |
| (d) test関数16、未実行 | トップレベル `test_*` 関数16、`__main__` なし | 静的確認一致 | `orchestrator/tests/test_auditor_gate.py` 全文・AST |
| 全 test file369 | 369 | 一致 | 指定方法による全file再集計 |
| 委譲232 | 232 | 一致 | 同上 |
| 手動列挙82 | 82 | 一致 | 同上 |
| `__main__` なし55 | 55 | 一致 | 同上。allowlist登録との一致は別検証 |
| 自走 harness369 | harness保有314 | **不一致** | 232＋82 |
| 自走 harnessの63% | 232/314＝73.885% | **分母不一致** | 全file比なら232/369＝62.873% |
| 直近8本、委譲7・手動1、9/17〜20 | 対象一覧なし | 未確認 | `V/brief.md:26` にも8本の内訳根拠なし |
| probe(a) rc=0 | 0 | 一致 | `V/s5-probe-author.md:30` |
| probe(a) 1.87秒 | 1.87秒 | 一致 | 同`:31` |
| probe(a) 47,564 KB | 47,564 KB | 一致 | 同`:32` |
| probe(a) 3件、pytest内0.86秒 | 3 passed、0.86秒 | 一致 | 同`:33,47` |
| probe(b) rc=0 | 0 | 一致 | 同`:58` |
| probe(b) 1.62秒 | 1.62秒 | 一致 | 同`:59` |
| probe(b) 34,964 KB | 34,964 KB | 一致 | 同`:60` |
| probe(b) 22件、0 failed、PASS22行 | 同値 | 一致 | 同`:61,79,83`。全文PASS行数は子の報告 |
| probe(c) rc=0 | 0 | 一致 | 同`:91` |
| probe(c) 3.29秒 | 3.29秒 | 一致 | 同`:92` |
| probe(c) 57,076 KB | 57,076 KB | 一致 | 同`:93` |
| probe(c) 38件、pytest内1.99秒 | 38 passed、1.99秒 | 一致 | 同`:94,100` |
| probe(d) rc=0 | 0 | 一致 | 同`:111` |
| probe(d) 0.37秒 | 0.37秒 | 一致 | 同`:112` |
| probe(d) 27,684 KB | 27,684 KB | 一致 | 同`:113` |
| probe(d) executed_count=null | null | 一致 | 同`:114` |
| probe(d) grep rc=1 | rc=1 | 一致 | 同`:122` |
| 4コマンド各1回、started=true | 同値 | 一致 | 同`:22,28,56,89,109` |
| hook_verdict全件null、拒否0件 | 全件null、4 process起動終了 | 一致。ただしhook判定を直接観測した0件ではない | 同`:22,29,57,90,110` |
| probe 1.6〜3.3秒 | 1.62〜3.29秒 | 丸め一致 | 同`:59,92` |
| probe 35〜57 MB | 34,964〜57,076 KB | 記載換算の概数として一致 | 同`:60,93` |
| codex 10 call | 10 | 一致 | receipt `actuals.model_calls` |
| launcher128.9秒 | 128.893095489秒 | 一致 | receipt `actuals.wall_clock_s` |
| §0の128秒 | 128.893095489秒 | 切捨てなら一致、四捨五入では不一致 | 同上 |
| probe上限150 call | 150 | 一致 | receipt `limits.max_model_calls` |
| `.done=0` | `launcher_rc=0`、`codex_exit_code=0` | launcher成功は一致、`.done`自体は未確認 | receipt各field |
| 08:04〜08:07 | rollout名08:04:42、launcher wall128.9秒 | 概ね整合、detach終了時刻は未確認 | receipt `attempts[0].rollouts[0].path`、`actuals.wall_clock_s` |
| uid31609、Python3.10.12 | 同値 | 一致 | `V/s5-probe-author.md:8–9` |
| 前後status空、rc=0、HEAD不変 | 同値 | 一致 | 同`:128–129` |
| ignored dir2個生成 | `.pytest_cache`、`orchestrator/tests/__pycache__` | 一致 | 同`:16–18,133–140` |
| MAXRSS差±0.5 MB以内 | 差−252、−404、−200 KB | 一致 | 親3logとprobe各maxrss |
| author1本、fix未実施 | author receipt1本、段4でfix省略 | 一致 | receipt `stage`、`V/s4-adjudication.md:17` |
| 通常既定100 call | 段4に100との記録、diffは共通argvを表示しない | 親記録と一致、argvからの独立確認不可 | `V/s4-adjudication.md:17`、`dryrun-author-vs-fix.diff.txt` |
| T-2814 580 passed | 580 passed＋3 skipped | passed数一致 | `J/verbatim/T2814-s5-author-run-results.md:8` |
| T-2814 302.33秒／概数302秒 | 302.33秒 | 一致 | 同`:8` |
| T-2814 他3走 | 他pytest走3本 | 一致 | 同`:7,9–10` |
| T-2810 新test64件 | 新規63＋既存1＝64 passed | **内訳不一致** | T-2810 `s5-author.md:37,69,112` |
| T-2810 git rc=128 | rc=128 | 一致 | 同`:84` |
| 未実走例 rc=16、preflight rc=1、child_started=false | 同値 | T-2803で一致。T-2796抜粋はhook未実走のみ | `J/verbatim/T2803-s5-author-head.md:15`、`T2792-README-s4.md:6`、`T2796-README-s5.md:7` |
| 過去fix5本、2026-09-05 | 同記述 | 記憶抜粋と一致 | `V/memory-selfrun-section.md:12–13` |
| T-1851 fixture誤り2度 | 2度 | 記憶抜粋と一致 | 同`:34–38` |
| T-2796 attempt2＝7分 | 13:13→13:20 | 一致 | `J/verbatim/T2796-README-s5.md:8` |
| 変異probe平均20.7分 | 20.7分 | 一致 | `J/verbatim/D2195.md:6` |
| 最大26.4分 | 26.4分 | 一致 | 同`:6` |
| 参考7〜26分 | 7分〜26.4分 | 上端を整数化した概数として一致 | 上記2資料 |
| wave平均154分 | 草案に154との記述、元の記憶抜粋なし | 未確認 | `V/proposal-draft-v1.md:16` |
| 4.5〜16.9% | 7/154＝4.545%、26/154＝16.883% | 算術一致、154の出所は未確認 | 独立計算 |
| 149 bytes、2026-09-03 | 指定記憶抜粋に該当なし | 未確認 | `V/memory-selfrun-section.md` |
| consumer＋inventory4群 | 指定資料に4群の定義なし | 未確認 | README §4の主張 |
| 所見11件、高5件 | 11件、高は1・2・3・4・8 | 一致 | `V/s3-consult-out.md:5–68,116` |
| 11件すべてreal採用 | 全11件real、6はreal（限定） | 一致 | `V/s4-adjudication.md:9–19` |
| P1 conditional、P2 refuted、P3〜5 conditional | 同判定 | 一致 | `V/s3-consult-out.md:73–77` |
| 正規化2file | 2file | 一致 | `V/NORMALIZATION.md:5,11` |
| worklog fragment1本 | 指定資料は作成方針の記述まで | 実在未確認 | `V/brief.md:47`、README §7 |

## 見つからなかったこと

- **8綴りのrc転記誤り、拒否文の意味改変：** 01〜08のpayloadとlogを照合。03・04の引用は逐語の部分抜粋であり、意味は変えていない。
- **D289の取り違え：** `docs/decisions.md:13201` の見出しで並行投入の裁定と確認した。D103・D2195の見出しも確認した。
- **D103・F121の引用の主要な歪曲：** script／`-c` が強制の射程外という説明、F121の対象が `-m pytest.__main__`／`-m _pytest.main` という説明は一致する。「同族」を親の推論とした限定もある。
- **probeのnullの捏造：** `executed_count=null` を0や成功へ置換していない。`hook_verdict=null`、ignored dir生成も子報告に忠実。
- **段3所見2・4・7・8・10・11の主要な反映漏れ：** 「天井に対し無視できる」「契約上保証」は削除済み。編集ゼロの限定、効果量未測定、A/B排他、固定報告欄は反映されている。許可根拠とD2195の限定には所見1・2の残件がある。
- **規律2を緩める指示：** §0と案A本文の双方に「計測でも受入でもない」がある。親の焦点走・全走の代替禁止、焦点集合を縮めないこと、期待値変更・skip/xfailによる緑化禁止も明記されている。
- **allowlistの代替欠落：** §4案Cに親のdispatchで満たすと明記されている。
- **無断の実装・gate設計への拡大：** C不採用、D対象外、docs予算は別裁定という整理はある。A採用後のprompt運用、裁定待ち、worklog fragmentへの言及もある。
- **live拒否を測ったという断定：** §2.2・§6はpytest綴りのlive拒否未観測を明記する。cold start・ignored bytes・効果量の限界も記載済み。ただし、子のexact経路でhookが発火した証明とは分けて読む必要がある。

## 総括

must-fix は **4件**。判定は **修正後 GO**。
最重要は、案 A の「許可根拠」が未定義なまま、D2195 の適用除外を省いて先例を援用している点である。
probe の主要な実測値は一致するが、harness比率の分母とT-2810の新規件数は修正が必要。
GO は裁定パッケージをユーザーへ返すことについてであり、案 A の実行許可を意味しない。
