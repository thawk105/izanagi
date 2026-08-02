## BLOCKER

1. **[real] 推定しているのは arm 別の between-session 分散であり、RF 分母の「差の分散」ではない。**

   3 arm は同じ allocation/session 内で測るため paired design です。しかし案は `m[a,w,j]` の arm 別 CV を求め、`F_stock + F_degraded` を閾値にしています。[s2-plan.md:246–290](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:246) 現行 `between_run_noise_floor()` は「variant と baseline は別 session」という前提で、same-window CV は長期変動を含まない下限だと明記しています。[stability.py:102–115](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/calibrator/stability.py:102)

   この設計で noise と呼ばれるのは、fresh build・node・時刻・5-rep median 誤差を全部含む各 arm の周辺散布です。signal は arm 間の global median 差です。共通 session 外乱の covariance を無視し、`d_j=m_stock,j−m_degraded,j` の散布を測っていません。従来の within-run 誤用は解消していますが、差の floor への接続は未解決です。現行実装自身も、単独 arm の CV は独立二測定の差の標準偏差ではないと警告しています。[stability.py:238–244](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/calibrator/stability.py:238)

   **成果物影響:** `between_run_floor`、pairwise margin、`qualification/all_pass` の受理集合が未較正の式で変わり、同じ raw session から正例成立・不成立が反転しうる。

2. **[real。ただし「統計量・閾値が全く無い」は refuted] 識別可能性は記述的分離規則であって、統計的識別の規範になっていない。**

   閾値自体は明記されています。分母は `D > F_stock + F_degraded > 0` と周辺標本の完全非重複、X は中央値順序・完全非重複・gap>floor です。[s2-plan.md:269–290](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:269) したがって測定後に閾値を一から発明する案ではありません。

   しかし同時に p 値・信頼区間・多重比較 family を実装しないと明記し、5 rep に検定力根拠がないことも認めています。[s2-plan.md:292–294](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:292) 独立単位は240 processではなく8 sessionです。既存の8 session根拠も CV 推定の相対 SE 約27%に留まり、効果検出力ではありません。[between_run_floor.py:53–55](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/campaign/between_run_floor.py:53)

   さらに exact workload 値がプランに無く、「2 workload」とだけ書かれています。事前登録の正本を committed ancestorにして、arm・停止規則・成功判定・全件報告を結果から参照させる既決手順にも達していません。[decisions.md:5494–5501](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/docs/decisions.md:5494)

   **成果物影響:** `S`、`F`、ordering の値は残っても「識別可能」の意味と受理集合が測定者裁量を残し、材料レポートや台帳が参照できる規範的判定にはならない。

3. **[real。ただし「順序不成立時の規則が無い」は refuted] X の生死確認を、本格実装と9 allocationより前に置いていない。**

   順序不成立なら最終 artifact を生成せず、同 campaign 内で stripe 数を変えない規則は明記されています。[s2-plan.md:72–75](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:72) ここは固定済みです。

   問題は、二 stripe が実際に中間へ来るか未実測なのに、patch・contract・新 producer・PBS wrapper・約2,750行予定のテスト群を先に作る点です。[s2-plan.md:397–470](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:397) `DW-G01` は大型機構前に既存 driver または100行以内の使い捨てで生死確認するよう要求しています。[core.md:42–45](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/docs/dev-wave/core.md:42) 旧 wave には67行 patchによる先例もあります。[t139-silo-degradation-ladder-design.md:48–56](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/output/insights/2026-07-29_t139-silo-degradation-ladder-design.md:48)

   また四 stripe等を後続 wave で試せる一方、失敗した X を束ねる親 trial ledger・候補上限・全件報告規則がありません。「別 campaign ID」は履歴の区別にはなっても、成功するまで候補を変える選択性を塞ぎません。

   **成果物影響:** 二 stripe不成立なら正例 artifact はゼロのまま、失敗 raw は正式台帳・材料レポートから脱落し、後続の成功候補だけが受理集合へ残りうる。

4. **[real] 8 session＋collector は Pegasus の `single_process=True` 契約と衝突する。**

   現行契約の定義は「campaign を単一 process で完遂」で、Pegasus は `single_process=True / allow_resume=False` です。[env_contract.py:47–56](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/campaign/env_contract.py:47) [env_contract.py:180–185](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/campaign/env_contract.py:180) Runbookも単一 allocation/node/process完遂と解釈しています。[pegasus-runbook.md:432–434](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/docs/pegasus-runbook.md:432)

   案は1個の global schedule/campaign IDを8 performance jobとcollectorで共有します。「各job内ではsingle process」「collectorはresumeではない」という説明だけでは、campaign単位の契約をsession単位へ読み替えています。[s2-plan.md:316–336](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:316)

   **成果物影響:** 現契約どおりなら8-job artifactは不適格、読み替えるなら env contract の受理集合を無裁定で拡張するため、attestation・checkout参照鎖が規範不一致になる。

5. **[real] 全層のうち触るのは5/9層で、RFの producer/consumer は実在しない。**

   実効経路を次の9層に分けると明確です。

   | 層 | 計画 |
   |---|---|
   | 1. patch/source semantics | 触る |
   | 2. build activation・binary identity | 触る |
   | 3. correctness・liveness | 触る |
   | 4. schedule・provenance・raw measurement | 触る |
   | 5. artifact-local collector・qualification | 触る |
   | 6. RF計算・区間・帰属規則 | **触らない** |
   | 7. loop/campaign consumer | **触らない** |
   | 8. WAL試行台帳・certified選択 | **触らない** |
   | 9. 材料レポート・Layer3 proof chain | **触らない** |

   案自身がRF keyを禁止し、`pipeline_eligible=false` としています。[s2-plan.md:124–138](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:124) [s2-plan.md:292](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:292) `projection_guard`変更は3 loopへの漏洩を拒否するだけで、RF消費ではありません。現行Layer3はcampaign lock・WAL・既存calibration floorだけを読み、新 artifact pathやRFを読む入口がありません。[layer3_report.py:346–423](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/campaign/layer3_report.py:346)

   したがって brief の「新 artifact がRF入力として受理され、受理集合が変わる」は実効 consumerについて成立しません。[brief.md:65–70](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/brief.md:65)

   **成果物影響:** 新JSONとprojection拒否集合だけが増え、certified選択値・試行台帳・材料レポート・Layer3参照は全て不変。「gateを作ったが誰も呼ばない」状態になる。

6. **[real] Pegasus投入前条件と終了予算が閉じていない。**

   240はperformance process数としては正しいですが、certificationの少なくとも8 run、build、verifier、collectorは別です。[s2-plan.md:250–255](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:250) [s2-plan.md:311–323](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:311) 5–8時間は「queueが軽い場合」で、queue待ちは無制限に外出しされています。[s2-plan.md:367–375](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:367)

   §8との照合結果は次です。

   - `qstat -Q`: 未確認。今回のsandboxでは `EACCTAUTH Unknown user-id`。
   - `pegasusinfo`: 今回のread-only実測で `gen_S Run/All=51/56`。軽いqueueとは言えない。
   - walltime/node数: 2時間・1 node相当の案はあるが、新3-build/sessionとcertificationの実測なし。
   - §7.0メモリ分類: 新submitter/collectorとも未実施。既存submitterは外部3 repo cloneのため既に`unknown`分類です。[pegasus-runbook.md:347–359](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/docs/pegasus-runbook.md:347)
   - `/scr`退避: success publishはあるが、途中失敗時の退避契約が未記載。
   - quota: `check_quota`は今回余裕あり。ただし `rbudgetcheck` はsandbox制約で確認不能。
   - 投入環境と投入後3点確認: qstat/accountingは一部あるが、計算ノード側marker・資格情報失敗時停止を明記していない。[pegasus-runbook.md:552–566](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/docs/pegasus-runbook.md:552)
   - 全体wall-clock deadline・queue timeout: 無し。

   8 allocationは逐次なので8 node同時確保は不要ですが、1 nodeを9回得られる期限・保証はありません。

   **成果物影響:** queue・point・submitter実行場所・途中失敗次第で一部rawだけが残り、最終artifact参照が生成されないままwaveが無期限化しうる。

## MAJOR

1. **[real residual。ただし「F3手続きが無い」は refuted] 単独性確認は入っているが、証明面が不足する。**

   30 process全ての直前にsolo checkを置き、pgrep・load・前後receiptを取る案なので、F3の最低線は満たしています。[s2-plan.md:319–320](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:319) [s2-plan.md:340–351](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:340)

   ただし既存実装は開始前一瞬の `ycsb_.*\.exe` とload1だけです。[silo_ladder_rung1.py:1890–1924](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/campaign/silo_ladder_rung1.py:1890) PID可視性canaryは未実装であることがrunbookに明記され、run途中に開始した競合も連続検知しません。[pegasus-runbook.md:444–453](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/docs/pegasus-runbook.md:444)

   **成果物影響:** 見えない、またはrun途中からの競合がsession medianへ入り、ordering・floor・`all_pass`を誤って変えうる。

2. **[realは統計資格部分。旧rung受理・backoff転用を決めたという攻撃は refuted] 未裁定事項を部分的に先取りしている。**

   - 先取りしている: arm別CV floor、pairwise閾値、欠測/retry、完全非重複規則、および新manifestの `recovery_measurement_eligibility=true`。[s2-plan.md:244–294](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:244)
   - 先取りしていない: RF区間、`RF<0/>1`帰属、旧rungのloop baseline化、backoff loop転用。後二者は `pipeline_eligible=false` と非接続で保留されています。
   - 注意点: mode1は旧rungと同型なので、将来この新IDをbaseline consumerへ渡せば「旧identityを触らず同じ機構を受理する」迂回になります。

   **成果物影響:** 現時点の公式3成果物は不変だが、新artifact-local受理集合だけが未裁定の統計規則と`recovery_measurement_eligibility=true`で固定される。

3. **[real、段2で一部修復済み] 親briefの「実質差分4点」は実装・資源一般化として過小。**

   briefは既存artifactの表面field差を4点としていますが、新patch登録、裸マクロ防護、新qualification authority、8-job orchestration、collector、失敗台帳が別途必要です。[brief.md:27–28](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/brief.md:27) 段2自身もこの過小評価を認めています。[s2-plan.md:1–3](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:1)

   **成果物影響:** 段2案では多くを補ったため値の直接破壊はないが、briefだけを基準にするとproducer・qualification・試行失敗参照が成果物閉包から落ちる。

## nit

1. **[real] briefの要求数が自己矛盾している。**

   scopeは pin・attestation・schedule・3 arm・env tag・checkout・between-run floorの7要素ですが、「6要求のうち3つ」と数え、表からfloorを落としています。[brief.md:5–12](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/brief.md:5) 後段では不足4点へ戻るため実害は限定的です。

   **成果物影響:** 値・受理集合は変わらず、briefの要求件数参照だけが誤る。

2. **[real] C++概念コードの `key` は実CAS位置に存在しない。**

   `lockWriteSet()` の実体は `itr->key_` です。[transaction.cc:155–173](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/external/ccbench/cc/silo/transaction.cc:155) プランの `key.empty()/key.back()` はそのままではcompileしません。[s2-plan.md:62–69](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:62) 修正は局所的ですが、8-byte big-endian key末尾parityの負荷分布もprobeで確認すべきです。

   **成果物影響:** 未修正ならbuild失敗でartifact無し。修正後の受理集合への独立影響はない。

## 総括

**(a) 判定: NO-GO。** 段5の恒久実装・PBS本走へ進めません。許容できる次の一手は、100行以内の二stripe生死probeと、paired session差・事前登録・複数job契約・全件台帳を入れたplan v2です。

**(b) BLOCKER一覧**

- arm別between-session CVをpaired差のfloorへ使っている。
- 「識別可能」に誤差率・区間・committed preregistration・検定力根拠がない。
- 二stripeのDW-G01生死確認とcross-wave全件台帳がない。
- 8 job構成がPegasusのsingle-process campaign契約と衝突する。
- RF/WAL/選択/材料レポート/Layer3 consumerがなく、触るのは5/9層。
- queue・points・メモリ分類・投入後確認・全体deadlineが閉じていない。

**(c) provisional裁定と推奨案**

- **P1:** 概念には賛成、現実装順には反対。二stripeを恒久化する前にDW-G01 probe必須。
- **P2:** 旧ledger/evidence bytes不変と新identityには賛成。ただし独立manifestの `recovery_measurement_eligibility=true` を未裁定RF policyの代用にすることには反対。
- **P3:** within-runと分けて測る原則には賛成。現行のarm別CV加算・8×5・same-windowだけの実装には反対。
- **段2推奨案:** as-writtenでは反対。standalone candidate evidenceへ看板を縮めても、B-1/B-3/B-4/B-6を直すまでは本走不可。

**(d) 確認できなかった前提**

- 二stripeが両workloadで `degraded < X < stock` になること。
- 新patchのcompile、nm、verifier、t48 liveness、実walltime。
- exact workload値とその事前登録commit。
- `qstat`による現行job一覧・queue設定、`rbudgetcheck`の残ポイント。
- 異なるallocationのnode再利用・PID可視性・run中競合。
- 新submitter/collectorのcgroup peak memory。
- pytest・build・benchmarkは一切実行しておらず、緑とは報告しません。