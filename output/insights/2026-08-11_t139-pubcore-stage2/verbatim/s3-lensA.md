## 所見

### 1. [nit] 既存 pin は「現行 path の bytes」を監視していない

プラン上、凍結 core・追補 A・旧 publication core・旧 B を変更する操作はなく、新 path への複製だけなので、直接の凍結侵犯は見つからなかった。digest・`study_label`・`document_kind`・role/key 側も検索したが、Python の pin は [test_t139_preregistration_binding.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/orchestrator/tests/test_t139_preregistration_binding.py:35) の core/A だけで、B/publication core の隠れ pin は無かった。

ただし `read_pinned_blob` は明示的に worktree path を開かず過去 commit の object を読むため、現行凍結 path を編集しても当該テストは落ちない（[blobref.py:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/orchestrator/preregistration/blobref.py:89)）。[プラン:481](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-pubcore-stage2/s2-plan.md:481) の現行 bytes SHA-256 検査が唯一の直接防壁である。

**成果物影響:** 誤編集が混入すると certified triple は過去 blob を読み続ける一方、現行 canonical path を読む材料レポート・人間レビューだけが別 bytes を参照し、pytest は緑のまま分岐する。

### 2. [blocker] 固定 root literal だけでは、累積台帳のリセットを防げない

source core は `b03` に「累積台帳を束縛する正規の根の同定方法」を要求する（[preregistration.md:339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:339)）。現 B は固定 literal に加え、caller 非選択の canonical 外部台帳・原子予約・一意性を要求していた（[addendum-b.md:165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-09_t139-addendum-b/addendum-b.md:165)、[同:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-09_t139-addendum-b/addendum-b.md:177)、[同:198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-09_t139-addendum-b/addendum-b.md:198))。プランは後二者を削除し、`(fold_commit, ledger_kind)` と caller 入力除外だけを残す（[プラン:262](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-pubcore-stage2/s2-plan.md:262)）。

具体的な破り方は次である。

1. 呼出し A は固定 root `R=(88d68f91…, individual_publication)` を導出するが、空の台帳実体 `L1` を使い ordinal 1 を確保する。
2. 呼出し B は別 checkout・別 path・別 repository の空台帳 `L2` を使う。root は同じ固定 literal `R` のままで、再び ordinal 1 を確保する。
3. どちらも caller が root 値を選んでおらず、受領証・親系列 ID も root 入力にしていないため、提案 `b03` の全文を満たす。

これは「ID を変えず、ID が束縛される台帳実体を取り替える」reset である。追補 P の `p03` は clone-local を非権威化するが、P6 は B が P を参照せず単独で義務を果たすと主張し、public core 自身も source admission が P に依存することを禁止している（[publication-core.md:641](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-10_t139-publication-core/publication-core.md:641)）。

**成果物影響:** 試行台帳が同じ `(root, individual_publication, 1)` を複数受理し、各公表表が `α_pub,1=0.025` を再取得するため、ordinal・spending・追補参照が非一意になる。

### 3. [blocker] 予約規定の移設は「一本化」ではなく、二重定義と admission の孤児化を同時に作る

再発行 B は `b01` を逐語保存するため（[プラン:247](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-pubcore-stage2/s2-plan.md:247)）、次の予約規範が B に残る。

- `reservation_mode: create_only`
- `release_on_failure: false`
- canonical 予約 entry で候補を数える
- 失敗後も ordinal を解放・再利用しない
- ordinal 2 以降は `submit_main` 前に deny

実体は [addendum-b.md:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-09_t139-addendum-b/addendum-b.md:65)〜80 である。同じ create-only・非解放・canonical 予約は新 core §8.2 にも残る（[publication-core.md:573](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-10_t139-publication-core/publication-core.md:573)）。したがって「予約規定は core + P のみ」という brief の不変条件（[brief:46](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-pubcore-stage2/s1-brief.md:46)）は成立しない。プラン内だけで「b01 は会計」と読み替えても、凍結される B 本文の規範は変わらない。

一方、旧 `b03` にあった「本 study は ordinal 1 を占め、その一意性が成立しないまま本走を投入しない」という時相規定は削除される。新 core §8 は欠落・重複時に「公表表を生成しない」としか定めず、source `submit_main` を止められない。`p01` は ordinal 1 を許容し、`p02` は `k=1` とするだけで、「本 study が entry 1 をいつまでに予約するか」を定めない。land 1 §S7 項7も `b03` への未凍結要件ポインタだけである（[package.md:155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1/output/insights/2026-08-11_t139-manifest-land1/package.md:155)）。

**成果物影響:** B v2 の exact-key 解決だけで `main_admission` が閉じ、canonical 公表 entry が欠落・重複した本走も source 試行台帳と certified primary 選択を生成できる一方、公表表は欠落または参照不能になる。

### 4. [blocker] `core_ref.commit` は approval fold から pre-approval content commit へ意味が変わっている

追補 A reissue と B はともに、`core_ref.commit=88d68f91…` を「限定例外の決定を canonical 台帳へ fold した commit `F`」と逐語で定義する（[addendum-a-reissue.md:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:43)、[addendum-b.md:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-09_t139-addendum-b/addendum-b.md:20)）。source resolver 契約も `core_ref.commit` を `F` またはその子孫に限定する（[preregistration.md:395](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:395)）。

実測では `88d68f91…` の tree に core blob が存在し、SHA-256 は `ac939af4…` だった。ただし同 commit の差分は canonical docs の fold だけで、core bytes 自体は祖先から継承している。すなわち「blob locator としても使える」ことは確認できたが、承認 fold という意味は消えない。

プランは P の同じ key に、将来の `F_approval` より前の `C_core` を書き、「承認 fold commit ではない」と明記する（[プラン:123](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-pubcore-stage2/s2-plan.md:123)）。引用された D262 は approval payload を先に fold し、その子孫へ manifest を置く二段構成であり（[decisions.md:12140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/docs/decisions.md:12140)）、pre-approval commit を `core_ref.commit` と呼ぶ先例ではない。

**成果物影響:** 既存意味の resolver では P が永続的に解決失敗して公表表を生成できず、内容 commit 意味へ緩める resolver では approval 前 commit を受理する集合が新たに開く。

### 5. [nit] B v2 の envelope 説明と実 parser が逆

B は fenced block 内の `##` / `###` も grammar が数えると説明する（[addendum-b.md:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-09_t139-addendum-b/addendum-b.md:36)）。実装は `_outside_fences` で fenced 行を不可視にし、field 抽出時にも明示的に skip する（[addendum_envelope.py:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/orchestrator/preregistration/addendum_envelope.py:83)、[同:140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/orchestrator/preregistration/addendum_envelope.py:140)）。プラン自身も差を認識しているが（[プラン:121](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-pubcore-stage2/s2-plan.md:121)）、B v2 の preamble を直す操作を持たない。

**成果物影響:** fenced `### b99` を含む blob は文書 grammar では余剰 key、utility では無視されて受理となる。ただし今回予定する exact bytes には該当 heading が無いため、現候補の値は変わらない。

### 6. [must-fix] C-1 の基礎値は再現したが、丸め値を論理境界として使っている

project 実装を使わず、`F(2,ν)` の閉形式、中心 `t` の不完全 beta 表現、ならびに

```text
T = (Z + δ) / sqrt(V/ν),  Z~N(0,1), V~χ²_ν
```

の直接数値積分から検算した結果は次だった。

```text
q(13,0.025)        = 3.449997401748…
power(d=1.0)       = 0.576279948558…
d for power 0.80   = 1.220995636198…
d for power 29/30  = 1.562340730078…
α*                  = 0.014415014982840…
```

したがって `q`・`0.57628`・非心度 `√J·d`・自由度 `J−1`・片側方向・`L_J ≤ inf P` の向きは正しい。しかし「`d⁻ < 1.2210` なら確実に infeasible」は区間 `[1.220995636…,1.2210)` で強すぎ、「`d ≥ 1.5623` は十分」は `[1.5623,1.562340730…)` で偽である（[package.md:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-10_t139-publication-core/package.md:100)、[プラン:343](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-pubcore-stage2/s2-plan.md:343)）。

**成果物影響:** 境界帯の pilot では a10 の certified `J` が存在するのに材料レポートが「確実に infeasible」と説明する、または `L_J<0.80` なのに十分条件成立と記録する不整合が生じる。

### 7. [nit] `α*` の境界は `>` ではなく `≥`

`α_pub=α*` では `c_B=q` である。primary pass は厳密不等号 `T_k>q` なので、その場合も

```text
T_k > c_B
L_k > 0
p_k^unadj < α*/6
```

となり、Holm は全件棄却して同時下限も全て正になる。したがって §5.3 の「非整合が起こらない」条件は `α_pub ≥ α*` であり、`α_pub > α*` だけではない（[publication-core.md:277](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-pubcore-stage2/output/insights/2026-08-10_t139-publication-core/publication-core.md:277)）。

**成果物影響:** `p02` が厳密に `α*` を選ぶ場合だけ、公表表へ不要な「primary pass でも下限が 0 を含みうる」警告が付く。今回の `0.025` には影響しない。

## 総括

**NO-GO。blocker 3 件。**  
最大の穴は、B v2 が固定 root と一意な canonical 台帳を切断し、fresh ledger による ordinal 1 の再取得と、予約なし `main_admission` を許すこと。  
さらに `core_ref.commit` の意味変更により、追補 P は既存 resolver では解決不能、緩和 resolver では未承認 commit を受理しうる。  
`b03` の authority・予約時相と `core_ref` の意味を文書上で一意に閉じるまで、Q-FREEZE を提示してはならない。