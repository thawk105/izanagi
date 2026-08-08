結論: **NO-GO**。指定5ファイルは読了し、コード・成果物は変更していません。`python3 tools/check_docs.py` は rc=0 でした。

### B-01 — D125 と R-B2 の identity 境界が未確定

種別: real。  
根拠: D125(2) は「Pegasus contract のときだけ `search_config` へ `measurement_env` を足し、campaign_id を別空間にする。OTHER の campaign_id は 1 bit も変えない」と決定している。[D125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/docs/decisions.md:6098) 一方、R-B2 は H を `search_config` から外し D13 の env 非identity を回復するとする。[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:150) `measurement_env` を残すのか、D125(2) を supersede するのかが書かれていない。T530 側も supersede 表記を scope 外にしている。[s4-adjudication.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s4-adjudication.md:43)

成果物影響: Pegasus と OTHER の campaign root が衝突または意図せず分離し、certified 成果物の帰属を誤る。  
判定: **must-fix**。保持か supersede かを明示し、後者なら新裁定を要する。

### B-02 — 実際の producer では authority 境界が layout より後ろ

種別: real。  
根拠: R-B2 は `layout.ensure()`、repair、recovery、WAL より前に停止するとしている。[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:155) しかし `p3_s4_loop` は `layout.ensure()` と `ensure_resumable_attempts()` を先に実行し、`env_contract.authorize()` は後の `run_campaign` 呼出し時である。[p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/p3_s4_loop.py:878) 現行 `run_campaign` 内だけを直してもこの caller は覆えない。

成果物影響: 世代不一致でも新 directory、lock、reject、recovery/WAL が先に作られ、「書込み前停止」の主張が破れる。  
判定: **must-fix**。全 certified caller の最初の durable boundary を明示的に統一すること。

### B-03 — loader source と enforcement source の authority が混同されている

種別: real。  
根拠: v2 lock の `loader_source` は `env_contract.py` と `env_contract_activation.py` の2ファイルだけである。[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:48) しかし実際に強制する `execution_guard`、`loop`、`pipeline`、`wal` は別の実行閉包である。D75 も宣言した source closure が実体より狭くなりうると明記している。[D75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/docs/decisions.md:3027) さらに `source_commit` の取得方法は既存 preflight では receipt に依存するが、generic path には同等の authority が定義されていない。[certified_writer_preflight.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/certified_writer_preflight.py:40)

成果物影響: loader 2本だけが一致していても、実際に検査を発火させた enforcement 経路や commit の帰属が不明な certified artifact になりうる。  
判定: **must-fix**。検査対象を2 loaderに限定するなら主張も限定し、authority全体を名乗るなら source closure と commit provenance を定義すること。

### B-04 — v1 legacy resume と v2 authority の移行動作が矛盾

種別: real。  
根拠: 現行 resume は `campaign.lock` の top-level 5 key を要求する。[ident.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/ident.py:176) R-A1 は nested v2 envelope を導入する一方、既存30 campaign は H なしの v1 historical として「不変」としている。[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:168) v1 を再開可能にすれば source/authority gate を迂回し、拒否するなら「v1 unchanged」と衝突する。

成果物影響: 旧 campaign が g2 で無束縛のまま追記されるか、正当な legacy replay が一律不能になる。  
判定: **must-fix**。v1 は read-only historical なのか、どの条件で再開可能なのかを durable write 前の動作として固定すること。

### B-05 — DW-G03 の一般化条件を満たしていない

種別: real。  
根拠: DW-G03 は同型欠陥が異なる producer/consumer で独立に2件再現した場合だけ族一般化を許す。[core.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/docs/dev-wave/core.md:55) 親が示す silo と qualification は「既に binding を持つ2実装」であり、generic certified 経路の同型欠陥を2件再現したものではない。[s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s1-brief.md:37) プラン自身も generic integration measurement は未存在と認めている。[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:233)

成果物影響: generic certified writer 全体へ機構を広げても、実際の全producerで検査が発火する保証がなく、未保護の成果物を受理しうる。  
判定: **must-fix**。現段階では設計メモに限定するか、対象 generic producer/consumer 2組の独立測定を追加すること。

### B-06 — t530 の旧設計を land する race が順序記述にない

種別: real。  
根拠: T657 の既裁定 prerequisites は silo historical resolution と floor protocol 再発行であり、T627 は既に活性化前に land 済み。[ruling](/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-04-rulings-session-5rulings.md:392) 一方、t530 は旧 H-in-identity 設計の未land commit 3本を抱えている。[handoff](/work/1/SFC/tanab/dev-wave-jobs/handoff/dev-wave-t657-t660-g2-activation.md:31) R-B2 統合前に t530 が再開・land されないことが明示されていない。[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:248)

成果物影響: g2 活性化と旧 t530 実装の間に H-in-id campaign が生成され、split 条件と再移植リスクが再発する。  
判定: **must-fix**。T657 は止めず、t530 の実行・land だけを B2/B3 統合完了まで保持する順序を明記すること。

### B-07 — D75 に反する report field 名の曖昧さ

種別: real。  
根拠: D75 は gate と metadata の型分離を要求する。[D75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/docs/decisions.md:3014) 後続裁定も同名識別子による二義化を理由に、新 producer を名前確定前に land しないとしている。[docs/decisions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/docs/decisions.md:8057) しかし計画は `meta.certified_authority_sha256` と「authority source ref」としか書かず、既存 `source_ref` / `source_refs` との型・意味の分離が未確定である。[layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/layer3_report.py:477)

成果物影響: loader provenance と WAL/genome provenance が同じ参照として解釈され、report の証拠帰属を誤る。  
判定: **must-fix**。非衝突の exact field 名、型、参照対象を先に確定すること。

### B-08 — 親の「実測で確定」は反実仮想を含む

種別: real（測定事実と推測の混在）。  
根拠: 30 campaign が H/`build_admission` 無し、activation serial 1、ambient lookup/authorize 36件という静的事実は再現できる。一方、generic integration measurement は未存在で、brief の g2後の成果物影響は将来経路の推測である。[s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s1-brief.md:49) 「唯一の loader 検査」も generic loop に限定して記述すべきで、silo/qualification の既存検査まで否定しないこと。

成果物影響: insight package が未観測の failure を実測済みとして記録し、後続裁定の証拠強度を誤らせる。  
判定: **nit**。実測・反実仮想・一般化を節単位で分離すること。

### B-09 — docs予算は現状緑だが、残余がほぼゼロ

種別: real。  
根拠: `check_docs.py` の cap は core 9,600、workers 5,000、mutation 3,750、operations 8,400、aggregate 25,200 bytes。[check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/tools/check_docs.py:168) 実測は順に 8,655 / 4,526 / 3,689 / 8,329、aggregate **25,199/25,200**、`dev-wave.md` 9,457/9,500、skill 5,997/6,000。T-664 の予算捻出を先に置く必要がある。[worklog.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/docs/worklog.md:2505) なお `output/insights` と worklog は checker の living-doc対象外。[check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/tools/check_docs.py:29)

成果物影響: normative docs を追加する場合は即座に check_docs 違反となり、設計記録の更新順序を誤る。  
判定: **nit**。output package の推定 10–15KB と fragment 1–3KB は予測値として扱い、`docs/dev-wave/**` を触る場合だけ T-664 先行と明記すること。

### B-10 — D205に対する実装量の切り分け不足

種別: real。  
根拠: D205 は研究前進を優先し、測定・検証・台帳の正しさに直接効く最小堅牢化だけを採る。[D205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/docs/decisions.md:9842) A1 は約500–750 production行、B2 は約350–550行で、さらに report v4、historical reader、15 caller 閉包まで束ねている。[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:76) loader authority と resume boundary の核は科学的正しさに直接効くが、generic integration measurement が無い状態で周辺 hardening まで同時に正当化できない。

成果物影響: 初回の有意な generic certified measurement より先に大規模な周辺実装へ研究時間を消費する。  
判定: **nit**。核となる vertical slice と、実 artifact が出るまで延期する部分を分離すること。

なお、T-665型の「契約文や docs pin を追加するだけ」の案は、プラン自身が明示的に却下しており、この点は問題ない。

## 総括

**NO-GO。must-fix は7件（B-01〜B-07）、nit は3件（B-08〜B-10）。**

must-fix は、D125の明示的整合、全callerでの書込み前停止、source authority の境界、v1/v2移行、DW-G03再現条件、t530 land race、D75のfield命名を閉じるまでである。