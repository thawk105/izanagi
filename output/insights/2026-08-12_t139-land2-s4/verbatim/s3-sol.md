NO-GO

## 総括

現行プランは解除 decision を land できない。主な理由は次の三点である。

1. `a12` が未実装・未実走なので受理集合が空であり、解除 gate は休眠する。
2. `submit_pilot` の実 caller、Pegasus admission、collector の実行 site が scope から落ち、実務経路が端から端まで結線されていない。
3. F5 の前提が半分誤りである。`a09` の意味的な再導出は承認済み仕様の実装だが、canonical TSV・157 行という serialization は未承認の閉包 4 である。

現在の実効経路は次の二箇所で切れている。

`operator CLI（未特定）→ submit_pilot → a12（実体なし）→ intent/binding → PBS driver → collector（login 実行不可）→ receipt/report/ledger consumer（不存在）`

したがって、certified 選択・材料レポート・試行台帳に値が入らないこと自体ではなく、将来値を生む production path も現状では使えないことが NO-GO の理由である。

## 所見 (real/refuted・成果物影響つき)

1. **real — `a12` を scope 外にすると解除 gate は休眠する。**

   `a12` は pilot 1 本目より前の完走を要求し、未完了なら `design_not_feasible` である [addendum-a.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:769)。brief は実装・結果とも 0 件と認めながら scope 外に置き [s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2-s4/s1-brief.md:85)、plan 自身も実正例が構成不能と認めている [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2-s4/s2-plan.md:143)。F82・F204 の「過剰拒否を正例で検出できず、全機能を無効化」の再発可能性が高い。

   T-793 とトポロジーは完全同型ではない。CLI が実在すれば gate の caller はある。しかし受理集合が空なので、「active gate を機械執行した」と名乗れない点では同型である [T-793 package.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/output/insights/2026-08-11_t793-pubcore-impl/package.md:17)。

   **成果物影響:** pilot は常時拒否され、試行台帳・材料レポート・certified 選択はすべて不変。解除 decision だけが実行不能な許可として残る。

2. **real — 実務経路が効く全層を scope に入れていない。**

   plan 本文に operator-facing submit CLI の所有ファイル・argv・実行 site がなく、lane 表に「新規 submit CLI」とだけ現れる。また collector は `login-side のみ` とされる [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2-s4/s2-plan.md:69) が、Pegasus では `tools/pegasus/` の未登録実行体を login node で拒否し、`local-ok` 新設には実測が必要である [pegasus-runbook.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/docs/pegasus-runbook.md:424)。既存 collector も `unknown` / `compute-only` である [tools/pegasus/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/tools/pegasus/README.md:17)。

   これはF208「文書化した起動 route が実際には起動不能」の直接的な再発候補である。scope には少なくとも submit CLI、self-gate、admission registry、Pegasus README/runbook、PBS body、driver、collector の実行経路まで必要である。

   **成果物影響:** sanctioned な qsub または回収経路が成立せず、submission intent・binding・raw collection record のいずれも実環境で生成できない。

3. **refuted — `a09` の独立再導出そのものが Q1/Q2 禁止の新機構、という B2 の一般化。**

   承認済み `a09` は seed、preimage grammar、sort、tie-break を固定し、validator がゼロから再導出することを明記している [addendum-a.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:453)。意味的 schedule generator / validator は承認済み仕様の実装であり、新しい受理規範ではない。

   同じ理屈は、固定入力・RNG・反復数・判定式が規定済みの `a12` 実装にも当てはまる。`a09` だけ実装扱い、`a12` だけ scope 外とする P6 の区別は「driver が直接読むか」以外に根拠がない。

   **成果物影響:** 再導出を省くと caller 提供 schedule が通り、実行順・288 run の identity・将来の試行台帳が producer 選択になる。

4. **real — F5 の「canonical TSV・157 行も a09 で凍結済み」は事実でない。**

   指定された `a09` 範囲は canonical bytes の hash を要求するだけで、serialization を定めていない [addendum-a.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:483)。TSV・header・157 行は、承認済み文書から一意に導けない閉包 4 として別途明記されている [record-items-v2.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:840)。

   plan の「authoritative canonical 157 行 TSVを再導出」は、Q1/Q2 で見送った固定 semantic closure を再導入する。F154 の「見送り済み機構が依存計画から復活」の再発である。

   **成果物影響:** 同じ意味的 schedule から異なる `schedule_sha256` が生成可能となり、intent・binding・collector record の hash が実装依存になる。

5. **refuted — 三つの最終成果物に値が入らないなら land 価値がゼロ、とは限らない。**

   P1 の「本 wave では投入しない」は安全側である。非空の受理集合を持つ実 CLI → driver → collector が成立すれば、後続投入を安全に可能にする capability 自体が成果である。

   ただし本プランは `a12` と実行 site が未閉鎖なので、この反証条件を現在は満たさない。また `t139-pilot-collection-evidence/v1` を読む production consumer も 0 件であり、後続 receipt builder が名指しされていない。

   **成果物影響:** 本 wave では certified 選択・材料レポート・試行台帳は意図的に不変。将来の値を生むのは operational evidence を受領証へ昇格する別 consumer であり、現状は未実在。

6. **real — §10 の閉包 8 件はすべて「受領証 authority」として宙に浮く。**

   Q1/Q2 により record-items/schema/manifest を authority にしないため、8 件全体を canonical receipt 要件とは扱えない。

   - 閉包 1: S4(a) の判断自体はあるが、元の発火点だった受領証がない。解除 decisionで `[1..8]` を要求し、最初の qsub 前に単一 batch intentを durable化し、driverが各 slot membership、collectorが全8件のcoverageを再検査する必要がある。plan は intent を提案するが、解除 decision骨子には literal `[1..8]` の authority edgeがない。
   - 閉包 4: canonical TSV authority は未解決であり blocker。
   - 閉包 6: job ID・returncode・raw は operational qsub bindingへ置けるが、`t139-receipt/v1` fieldとは名乗れない。
   - 閉包 2・3・5・7・8: 今回の receipt/report/ledgerから完全に外し、値を生成したと主張しない。

   **成果物影響:** 閉包1の発火点がなければ結果を見た8 slot選択が可能になる。閉包4がなければschedule digestが実装依存になる。他6件を昇格すると未承認fieldが試行台帳・材料reportへ混入する。

7. **refuted — 現時点で D291 report が二重権威になっている。**

   report は `decision=D291`、`submission_authority=not_granted`、supersession scanを持ち、production consumerはない [report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/orchestrator/publication/report.py:216)。現在の受理集合を二つの consumer が競合して決めている事実はない。

   **成果物影響:** 現時点の certified 選択・レポート・台帳・pilot受理集合は変わらない。

8. **real — `report_scope` 追加は Q4 外の拡張で、将来誤読も機械的には防がない。**

   公開関数とCLIから将来 consumer が生まれる可能性はある [report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/orchestrator/publication/report.py:235)。しかし additive field は consumer が読むことを強制せず、F72/F143型の「宣言だけ・冗長gate」になる。active `submit_pilot` が report を authority として importしないことと、解除 decisionの優先関係を固定する方が実効的である。

   **成果物影響:** 追加すると D291 report JSONだけが変わり、exact consumerは未知keyで拒否し得る。一方、pilot受理集合・試行台帳・certified選択には何の防壁も増えない。

9. **real — P4(iii) の保証は「qsubを禁止」ではなく「valid runへの昇格を拒否」に限定すべきである。**

   repoには既に一般のqsub siteがある [dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/tools/pegasus/dispatch_compute.py:1475)。T-139 filenameだけのAST走査では、人間操作や汎用dispatcherを網羅できない。plan B4の修正方針は正しい。

   **成果物影響:** 直接qsubされたscheduler job自体は存在し得るが、driver preflightで止まり、valid run record・試行台帳・材料report・certified選択へ一切昇格しないことを保証境界とする。

nit はない。上記はいずれも成果物値・受理集合・参照経路へ影響する。

## blocker

- **B1:** `a12` producer・独立 verifier・実 pass artifactがなく、実正例を構成できない。
- **B2:** canonical TSV/157行のauthorityがなく、planのschedule bytes/hash契約を正当化できない。
- **B3:** operator-facing submit CLIとPegasus admission closureが未設計。特にlogin-only collectorは現行規律下で実行不能。
- **B4:** `[1..8]` のauthorityから、pre-qsub batch intent・driver・collectorまでの発火edgeが未閉鎖。
- **B5:** collection evidenceを読む後続consumerがなく、「将来のproof chainへ採用済み」とは言えない。D310もT-139の粗いprovenanceを認可する決定ではない。

## 裁定パッケージ候補

1. **a12 scope:** Q4の「投入の実務経路」にa12 producer・verifier・実pass artifactまで含むと解釈する（推奨）。含まないなら解除 decisionをlandできず、Q4/Q6との矛盾として停止する。
2. **a09 bytes:** 今回は承認済み規則から意味的scheduleを再導出・比較し、使用するserialization/hashを`operational-only`とする（推奨）。canonical `schedule_sha256`を名乗るなら閉包4の新裁定が必要で、Q1/Q2との整合を再確認する。
3. **slot固定:** 解除 decisionにpilot slot exact `[1..8]`を明記し、単一batch intentを最初のqsub前にdurable化する。これがS4(a)の発火点であり、禁止された「4入力の新decision」に当たらないかを明示裁定する。
4. **Pegasus site:** collectorをcompute-only経路へ置く（推奨）か、login-directに必要なcap・実測・registry更新を同一scopeへ入れる。未登録のまま「login-side only」としない。
5. **D291 report:** `report_scope`追加を本waveから落とす（推奨）。既存reportをcurrent authorityとして読まないことを解除decisionとsubmit側dependency検査で固定する。
6. **後続consumer:** `t139-pilot-collection-evidence/v1`は診断用と明記し、将来これをraw bytesから再検査してreceiptへ昇格するconsumer/taskを名指しする。Q1/Q2により本waveでは実装・採用済みと主張しない。

## 未読・未確認

- 必読のbrief、plan、D292/D308/D310/D316、指定§10、`report.py`全266行、`qsub_binding.py`全93行は読了した。
- `dispatch_compute.py`は指定どおり`qsub` hit前後30行だけを確認した。任意T-139 scriptを投入可能かまでは未確認。
- `grep -n "^## F" docs/failures.md` は、実見出しが `### F` のため0件だった。その後、見出しだけを`^### F`で引き、F72・F82・F143・F154・F204・F208の本文だけを読んだ。
- `record-items-v2.md`の本文精読は829〜844行だけ。ただしa12 hit確認のtargeted `rg`が同ファイル内の孤立した一致行を追加表示した。周辺節は読んでいない。
- pytest・build・qsub・simulationは実行していない。緑は確認していない。