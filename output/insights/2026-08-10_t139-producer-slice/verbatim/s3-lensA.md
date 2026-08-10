結論は **NO-GO**。指定 8 文書はすべて全文読了した。pytest は実行していない。

親 brief §3 の実測値――`F`、core digest、T-139 API 0 件、pin 0 件、`FROZEN_MANIFEST` 未収載――は current HEAD `2169a06c` で再現した。しかし、その事実から引いた安全性の一般化は以下で崩れる。

### 所見 1 — N5 未裁定のまま schema digest を固定できない

- **深刻度** = `blocker`
- **根拠** = [s1-brief-addendum.md:94](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s1-brief-addendum.md:94)、[record-items.md:130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice/output/insights/2026-08-08_t139-addendum-a/record-items.md:130)、[addendum-a-reissue.md:266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:266)、[s2-plan.md:47](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:47)
- **失敗シナリオ** = preflight の最初の `a03` が不成立になる。marker も性能 run も存在しないため literal な record-items は row を拒否するが、追補 A は `post_performance_failure` を要求する。P8 を無断採用すれば受理集合を第三分岐へ拡大し、採用しなければ正当な attempt を記録不能にする。
- **成果物影響 1 行** = 固定 schema digest、`attempts[]`、適格 cluster 集合が実装選択で分岐する。

### 所見 2 — approval trust root が P5・P7・plan の三通りある

- **深刻度** = `blocker`
- **根拠** = [s1-brief.md:56](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s1-brief.md:56)、[s1-brief-addendum.md:75](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s1-brief-addendum.md:75)、[s1-brief-addendum.md:80](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s1-brief-addendum.md:80)、[s2-plan.md:15](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:15)
- **失敗シナリオ** = P7 に従い `approval_fold_commit=2169a06c` とした manifest は plan の新規 `F_e` 検査に拒否される。一方、developer が再掲した payload を新たな `F_e` とする manifest は plan では通るが、P7 が定めた承認 event を参照しない。
- **成果物影響 1 行** = 同じ承認済み四 blob に対する receipt の参照値と受理集合が resolver 実装ごとに変わる。

### 所見 3 — schema digest の固定が自己整合に退化している

- **深刻度** = `blocker`
- **根拠** = [s2-plan.md:25](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:25)、[s2-plan.md:151](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:151)、[s2-plan.md:285](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:285)、[preregistration.md:395](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:395)
- **失敗シナリオ** = `measurement_head` の子孫 commit で schema を緩め、同時に `T139_RECEIPT_SCHEMA_SHA256` を新 digest へ更新する。manifest の approved four blobs に schema は含まれないため、resolver・HEAD 照合・literal digest 照合はすべて通る。これは core §15 が明示的に否定した「caller 側の自己整合」と同型である。
- **成果物影響 1 行** = `accepted:true` 等を許す緩和 schema が新たに受理され、certified 選択とレポートの入力集合が拡大する。

### 所見 4 — binary 非同一性制約は循環置換で恒真化できる

- **深刻度** = `blocker`
- **根拠** = [s2-plan.md:184](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:184)、[s2-plan.md:215](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:215)、[s2-plan.md:239](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:239)、[artifacts.py:899](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice/orchestrator/qualification/artifacts.py:899)、[artifacts.py:931](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice/orchestrator/qualification/artifacts.py:931)
- **失敗シナリオ** = 性能 hash を `P_S,P_D,P_X` とし、correctness 側を `C_S=P_D,C_D=P_X,C_X=P_S` と記録する。各 arm の「同じ arm とは異なる」は成立するが、correctness binary 集合は性能 binary 集合と同一である。さらに `run_scope` には exec witness や scheduler-level allocation 束縛がなく、同じ PBS job に別 `allocation_id` を付けても非同一検査を通せる。
- **成果物影響 1 行** = trace-disabled run を correctness run と偽装した receipt が通り、壊れた variant が certified 入力へ到達しうる。

### 所見 5 — correctness verifier が存在せず、後段 validator に先送りされている

- **深刻度** = `blocker`
- **根拠** = [s2-plan.md:244](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:244)、[s2-plan.md:299](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:299)、[s2-plan.md:310](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:310)、[preregistration.md:239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:239)
- **失敗シナリオ** = trace-enabled run が G2 anomaly を出すが、driver は output pointer を保存するだけで trusted verifier の構造化結果を検査しない。そのまま次の性能 allocation を導出できる。P1 は eligibility validator の後置と correctness verifier の即時 gate を混同している。
- **成果物影響 1 行** = 終端 reject すべき候補に性能 attempt・費用・raw receipt が追加され、台帳とレポートの候補状態が誤る。

### 所見 6 — `a12` と N3 を無視して実 `--submit` できる

- **深刻度** = `blocker`
- **根拠** = [addendum-a-reissue.md:825](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:825)、[addendum-a-reissue.md:889](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:889)、[s1-brief-addendum.md:27](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s1-brief-addendum.md:27)、[s2-plan.md:258](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:258)、[s2-plan.md:283](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:283)
- **失敗シナリオ** = `a12` simulation が未完了または digest 不一致で、core §7 の第 2 erratum も存在しない。それでも submission 手順には simulation の再計算・pass 必須化がなく、承認済み一件の erratum だけで resolver が成功して `--submit` に進める。
- **成果物影響 1 行** = 未較正の pilot raw が生成され、後続の `J`・`q`・型 I 誤りに関する台帳／レポート記述が偽になる。

### 所見 7 — `a03` 恒真化 mutant を予定テストは kill しない

- **深刻度** = `blocker`
- **根拠** = [s2-plan.md:337](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:337)、[s2-plan.md:365](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:365)、[s2-plan.md:369](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:369)、[t139_r4_env_probe.py:508](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice/tools/pegasus/probes/t139_r4_env_probe.py:508)、[addendum-a-reissue.md:206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:206)
- **失敗シナリオ** = producer は reader を二回呼び raw snapshot も正しく保存するが、判定だけ `allowed=True` に固定する。reader call 検査は通り、別 helper に failure を直接渡す写像テストも通る。busy が `1.0` 超でも completed となる。`load1` を誤って判定に使う mutant も consumer guard の四 pointer に含まれない。
- **成果物影響 1 行** = 親 brief §8 の「否定検査 8 を新規 kill」は偽となり、不適格 cluster が receipt と certified 集合へ混入する。

### 所見 8 — binding-required sink を generic writer で迂回できる

- **深刻度** = `blocker`
- **根拠** = [s2-plan.md:138](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:138)、[s2-plan.md:329](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:329)、[artifacts.py:227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice/orchestrator/qualification/artifacts.py:227)、[artifacts.py:258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice/orchestrator/qualification/artifacts.py:258)、[artifacts.py:507](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice/orchestrator/qualification/artifacts.py:507)
- **失敗シナリオ** = caller が T-139 用 `QualificationRoot` から capability を発行し、公開 `create_json(capability, canonical_receipt_path, forged_receipt)` を直接呼ぶ。`publish_raw_receipt` の keyword-only signature テストは緑でも、実 bytes は binding なしで永続化できる。
- **成果物影響 1 行** = 未束縛 receipt が canonical raw 名前空間に入り、台帳・validator・レポートの参照先を奪う。

### 所見 9 —固定 Git ref は canonical alpha 台帳ではない

- **深刻度** = `blocker`
- **根拠** = [s2-plan.md:269](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:269)、[s2-plan.md:277](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:277)、[s2-plan.md:279](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:279)、[addendum-a-reissue.md:925](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:925)
- **失敗シナリオ** = clone A と clone B で固定 ref が未作成の状態から、それぞれ CAS に成功して `(F,1)` を予約する。push しないため互いを観測せず、各 local validator は重複なしと判定する。
- **成果物影響 1 行** = alpha 台帳が二重化し、primary 系列の familywise error と certified 選択の有意水準が変わる。

### 所見 10 — `attempts[]` exact coverage は publish との間で競合する

- **深刻度** = `blocker`
- **根拠** = [s2-plan.md:85](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:85)、[s2-plan.md:236](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:236)、[s2-plan.md:283](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:283)、[s2-plan.md:314](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:314)
- **失敗シナリオ** = collector が intent 集合 `L0` を読み receipt と exact 一致させる。その検査後・publish 前に別 `submit_pilot` が intent `I9` を追加する。receipt は `L0` のまま create-only publish され、canonical ledger は `L0∪{I9}` になる。series close CAS、ledger-head digest、共有 lock のいずれも計画にない。
- **成果物影響 1 行** = 永続 receipt が attempt を欠いたまま修復不能となり、台帳と validator の受理集合が分岐する。

### 所見 11 — nested closure の保証対象が `$defs` に限定されている

- **深刻度** = `must-fix`
- **根拠** = [s2-plan.md:166](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:166)、[s2-plan.md:184](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:184)、[s2-plan.md:229](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:229)、[record-items.md:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice/output/insights/2026-08-08_t139-addendum-a/record-items.md:50)
- **失敗シナリオ** = `run_scope`、`outputs[]`、`preflight_evidence`、conditional `then/else` などを inline object として実装し、そこだけ `additionalProperties:false` を落とす。`accepted:true` をその open object に追加した receipt が通る。`$defs` だけの静的確認では検出できない。
- **成果物影響 1 行** = producer の適格性自己申告が raw receipt に入り、consumer が参照できる受理入力が増える。

### 所見 12 — mutation の単一理由帰属が再び成立していない

- **深刻度** = `must-fix`
- **根拠** = [s2-plan.md:356](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:356)、[s2-plan.md:363](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:363)、[s2-plan.md:365](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:365)、[s2-plan.md:367](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:367)、[s4-adjudication.md:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice/output/insights/2026-08-08_t139-producer-adjudication/s4-adjudication.md:45)
- **失敗シナリオ** = 「ledger と receipt の双方から削除」は二境界同時変異、「raw を捨て boolean を追加」は欠落と余剰の二変異である。余剰 boolean の schema reject だけで赤になれば、raw 必須制約が欠けても kill と誤記録される。missing/extra/duplicate envelope を parser 直テストだけでまとめると、public resolver の `except → R13` fallback も生存できる。
- **成果物影響 1 行** = mutation ledger が検出力を過大計上し、親 brief §8 と受入レポートの kill 数が誤る。

### 所見 13 — e2e が production driver を通らず、半実装 land を再導入する

- **深刻度** = `blocker`
- **根拠** = [s2-plan.md:400](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:400)、[s2-plan.md:402](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:402)、[s2-plan.md:416](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s2-plan.md:416)、[s1-brief.md:73](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s1-brief.md:73)、[erratum-core-s15.md:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice/output/insights/2026-08-08_t139-addendum-a/erratum-core-s15.md:111)
- **失敗シナリオ** = stub driver が完成 JSON を返す一方、production `t139_driver` は schedule、correctness binary、environment observation のいずれかを欠く。正例は通るまま A+B が先に land し、schema digest と public resolver が固定される。これは erratum の `∅→R13` 拡大を実装しながら、実 producer 正例をまだ持たない分割である。
- **成果物影響 1 行** = 「producer 実装済み」台帳だけが先行し、後続 C が schema-valid receipt を生成できないまま受理仕様だけが凍結される。

## 総括

**NO-GO**  
N5、approval root、schema の外部 pin、global alpha 台帳が未確定で、correctness／`a03`／`a12` の前置 gate と binding sink も迂回可能である。  
現プランでは receipt の受理集合と mutation 検出力を一意に固定できない。