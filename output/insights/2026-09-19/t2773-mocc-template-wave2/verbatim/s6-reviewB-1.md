## 所見 1: 入力由来 check の拒否対照が不足し、Bash 混入対照も単独の検出力を持たない

**real/refuted の判定材料:** **real**。`orchestrator/tests/test_mocc_template_proof.py:262` の検査は、全30 keyの空入力拒否、ON-B identity、12走の正常性を確認するが、残る check の成立入力からの破壊対照がない。

特に同`:273` の Bash 混入入力は必須 `projections` を欠く。driver の tools 比較（`orchestrator/campaign/s3_mocc_template_proof.py:347`）だけを削除しても、`:351` の欠落で False になるため、この対照は緑のままになる。R2 が要求した「Bash 追加による拒否」を実証できていない。

per-key 被覆の補完は **scope 内**。根拠は R19 単独ではなく、設計正本`:297` の機械要件(3)(4)、R2・R8・R17。空入力拒否と完成 JSON の再計算一致だけでは、入力が存在すれば通す弱化を検出できない。ただし、各述語の全組合せ網羅までは要求しない。

**must-fix / should / nit:** **must-fix**

**成果物影響:** 不成立の観測を True とする check の弱化が受入テストを通り、新 JSON の `checks`／`all_pass` の受理集合を広げ得る。

**是正案（逐語、file:line）:**

> `orchestrator/tests/test_mocc_template_proof.py:262`：成立する合成 proof／policy を用意し、各 check の主要入力を一つずつ壊して当該 key が False になる対照を追加する。Bash 対照は projections を含む正常入力で True を先に確認し、tools への Bash 追加だけで False を要求する。旧証拠の必要 key 欠落・False、TRACE=0 不一致、計装保存結果、DQ subtype、consumer 対照結果も対象にする。既存 helper の直接テストは残す。

## 所見 2: 生死確認が停止しており、旧計装の適用結果が報告と矛盾する

**real/refuted の判定材料:** **real（不一致と未完了）**。`s5-author-1.md:24` は旧計装→template適用後を rc=1 と報告する。一方、`liveness-run-1.log:6` は `UNEXPECTED: instr-mocc-lock-coverage applies to tmpl`、`:7` は rc=2。R11 の後続確認を完走したログではない。

実際の patch 不具合か、確認 script の cwd・対象 tree・適用判定の問題かは**不確実**。指定資料には script 本体がなく、原因を断定できない。

**must-fix / should / nit:** **must-fix**

**成果物影響:** R11 の必須確認が途中停止したまま、受入記録に「旧計装不適用・新計装適用・必要 build 成功」を成立済みとして載せられない。

**是正案（逐語、file:line）:**

> `liveness-run-1.log:6` に対応する確認処理を author に戻し、対象 source の SHA、git root、実 argv、適用対象ファイル、stderr、rc を記録して再確認する。R11 の残りも完走させ、`s5-author-1.md:24` との相違理由を記録する。期待 rc の反転だけで解消しない。

## 所見 3: pin 三箇所と登録簿閉包の欠落は確認できない

**real/refuted の判定材料:** **refuted**。

- 統合 diff から auditor 本文をメモリ上で復元した SHA は `dc63a3118393503f7eed4952478f0aa34690b344ee1ca98915e455e210165f34`。現物と `review_ledger.py:19` に一致。
- auditor を含む14 roleすべてで adapter bytes が `render_adapter` 出力と完全一致。description の変更もない。
- `test_reflux_originless_compatibility.py:742` は既存 extension（`:574`）と同型。凍結 baseline の journal 6行、report `[[旧sha, 6]]` と対応する。旧shaの検索結果はこの履歴 extension と新 extension の入力だけ。
- `condition_meaning_gate.py:156` の cache route・mocc owner・target・path・inert値、`:300` の完全一致 witness、`:312` の decode 登録は R14 と一致。静的集計は供給40、witness16、cache23。
- fixture二行、materializer登録、build authority二集合、screening既定値、軸期待表、Counter `36 / 40 / 26 / 26` が追随。`test_ccbench_spawn_sites.py:662` の cache mapping 収集で新defineを拾う。
- 件数変更に既存期待の削除・skip化・反転はない。新 production driver は既存 subprocess helper を再利用している。

**must-fix / should / nit:** **nit（修正不要）**

**是正案（逐語、file:line）:**

> `orchestrator/campaign/condition_meaning_gate.py:156`、`orchestrator/tests/test_reflux_originless_compatibility.py:742`：現状を維持する。歴史 extension の旧 SHA は削除しない。

## 所見 4: 親作成 script の所有は逸脱、adapter の例外は限定して扱う

**real/refuted の判定材料:** **一部 real**。

repo差分17 fileは R20 の所有集合内。`3e7463217` は16 fileと Codex author trailer、`2d76e785f` は adapter だけの別commitで、renderer完全一致も確認した。旧 driver・旧 patch・旧 JSON・Silo gate・`spec.py`・`tools/**` 等の変更はなく、`.scratch-t2773/` も存在しない。

ただし、親が `liveness-run.sh` を書いた点は R20 と D95 決定(2)に対する所有逸脱。repo外の shell 資材も実装面であり、「親の計測操作 script」という呼称だけでは例外にならない。

adapterについては、提示された D105 waiver を前提とすれば、限定された機械生成物の別commitという処理は妥当。D105本文自体は射影にないため、例外条項との完全な照合は**不確実**。この waiver を生死確認 script に拡張する根拠はない。

**must-fix / should / nit:** **nit（所有・帰属の指摘。script の成果物問題は所見2）**

**是正案（逐語、file:line）:**

> `s4-ruling.md` の R20、`s5-author-1.md:101`：script の親作成を DW-O12 の逸脱記録に残し、修正資材は Codex author が担当する。adapter は commit `2d76e785f` の waiver と renderer 完全一致を別記し、Codex author が書いたと帰属させない。

## 所見 5: gate の鍵・consumer 束縛に過剰な閉鎖主張はない

**real/refuted の判定材料:** **refuted**。`test_mocc_template_proof.py:94` は `patches/*.patch` 全件を走査する。`axis_mocc_temperature.py:165` は `+++ b/` で対象を決め、`diff --git` ごとに状態をリセットする。現物の header 間に対象不一致はない。

束縛関数（同`:54`）と完成 proof consumer（test`:52`）は分離され、正しい literal は通し、別path・別OIDは拒否する。任意の直書き経路・全consumerを閉じたという記述は確認できない。汎用台帳、探索driver、broken-template版、verifier編集、auditor型番号拡張もない。R16・R17、D2134項6の範囲に収まる。

**must-fix / should / nit:** **nit（修正不要）**

**是正案（逐語、file:line）:**

> `orchestrator/campaign/axis_mocc_temperature.py:54`：束縛APIとしての限定を維持し、将来consumerの実checkout接続は、その導入時の検査に残す。

## 所見 6: 焦点走は整合するが、受入全走・時間上限の証明ではない

**real/refuted の判定材料:** **報告の集計矛盾は refuted、証拠の限界は real**。新testは実際に13関数で、JSON consumerを呼ぶのは指定2 node。system tmp、読取用 `git archive`、自走入口（test`:323`）を備える。B-4 pin・duration ledgerに変更はない。

`focus-1.log:29` は658 passed／2 skipped／94.05秒で親報告と一致。ただしログ冒頭自体が受入全走ではないと明記する。個別node時間・最大lock保持時間はこのログから確定できない。author報告のadapter未完は後続commitで補完された時系列差であり、虚偽とは判定しない。

設計§12の実装成果物と§7末尾の6 check種は対応する。compute・新JSON・n=1三候補は R20・R21 の親担当であり、author差分にないこと自体は実装漏れではない。

**must-fix / should / nit:** **nit**

**是正案（逐語、file:line）:**

> `focus-1.log:1`：焦点走として引用する。完成JSONを用いた指定2 nodeの復帰、受入全走、n=1完了は、それぞれ後続の実測記録で報告する。

## 総括

**NO-GO。**

must-fixは次の2件。

1. 入力由来checkの成立→破壊対照を補い、Bash混入対照の欠落による空振りを直す。
2. R11生死確認のrc=2とauthor報告の矛盾を解消し、必須確認を完走する。

**所有逸脱:** repo差分の範囲逸脱なし。親作成の生死確認scriptにはR20／D95上の逸脱あり。adapterは提示されたD105 waiverの限定内として条件付き妥当。

**報告と実体の不一致:** 旧計装適用結果にあり。file数、SHA、登録件数、新test数、焦点走集計に矛盾は確認できない。

pytest・build・計測は実行していない。静的読解、SHA・renderer照合と、指定された親ログに基づく判定。