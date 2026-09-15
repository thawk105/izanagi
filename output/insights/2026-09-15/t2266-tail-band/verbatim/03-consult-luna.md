## 投入 argv の確定

- **`--preregistration-commit`**
  ```text
  cad6f46d86ae4dc31edadfbdfad39c65ed73d70a
  ```
  `git log --follow` で特定した、2026-09-10追補を追加した commit。HEAD の祖先で、現在の文書 bytes と一致する。SHA-256 は `8084be04dc1fc6a78b0fa1ac4a16986add796945d8c4ecace86ed2df4c44a45a`。
  
  基点の完全長 `0600887d92538b3f34d894f9674d202d0a29a578` も祖先性・bytes一致・marker/spec の条件を満たす。**受理される commit は一意ではない**が、文書更新の来歴を示す値として上記を選べる。短縮形 `0600887d9` は submitter の40桁検査に落ちる。

- **`--explore-campaign`**
  ```text
  /work/1/SFC/tanab/b10-backoff-grid-t2418-explore/b10-backoff-grid-20260908T193601Z-2540578-write-heavy/campaigns/t2418-backoff-static-explore-v1-silo-write-heavy-sweep-c9cea61a
  ```
  実在を確認。WAL の5件の `verify_done.payload.workload.tag` はすべて `legacy`。driver は admission を経て lock の `run_kind=t2418-explore` と WAL の mode を読む。探索の性能値は使わない。今回、admission 自体の実行確認はしていない。

- **`--output-parent`**
  
  **新規 formal 専用親の現存値は確定できない。** 過去の作法に沿う作成予定値は：
  ```text
  /work/1/SFC/tanab/b10-backoff-grid-t2500-formal
  ```
  この directory は現在存在しない。親が投入前に作成しなければ submitter は拒否する。`/work` の repo 外に専用親を置くことは、runbook と探索・1000 µs走の先例に合う。

- **cwd**
  ```text
  /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-tail-band
  ```
  job は `PBS_O_WORKDIR` を `pwd -P` で解決する。隔離 worktree を拒否する条件はない。`external/ccbench` とその `.git` file は実在する。ただし計算ノードでの全起動条件の充足を実走確認したわけではない。

## 所見

### 1. 事前登録追補による binding 不成立は否定できる

**refuted / must-fix相当の疑義**  
**file:line:** `orchestrator/campaign/b10_backoff_static_tail_formal.py:232`、`docs/b10-backoff-static-tail-preregistration.md:1081`

祖先検査・blob照合に通る commit は特定できた。文書から抽出した現行 parser と静的制約を使った照合でも、marker、JSON、shape、格子再生成、測定順に不一致はなかった。これは driver 全経路のテストではない。

**成果物への影響:** 初版 commit を安易に渡すと追補分の bytes 不一致で停止するが、上記 commit ならこの停止理由は除ける。

### 2. 出力親が未作成で、argv はまだ投入可能な状態ではない

**real / must-fix**  
**file:line:** `tools/pegasus/submit_b10_backoff_grid.sh:85`、`docs/pegasus-runbook.md:298`、`output/insights/2026-09-09_t2418-backoff-static-explore/README.md:188`

出力親は**既存**の絶対 directory が必要。repo内、repoの祖先、`.git` を持つ祖先の下も拒否する。新規専用親の作成は投入前に済ませる。

**成果物への影響:** 放置すると qsub 前に終了し、3 jobも標本も生成されない。

### 3. 「約20分」は再計算しても妥当な見積りだが、実測扱いはできない

**real / must-fix（時間の表記）**  
**file:line:** `docs/b10-backoff-static-tail-preregistration.md:218`、`output/insights/2026-09-04/t2266-backoff-static-tail/README.md:213`、`orchestrator/campaign/pipeline.py:147`

8 genome・正しさ各1回の先例は **629〜632秒**。探索3 campaign の保存WALで、同一variantの `build_done→verify_done` は **6.68〜16.92秒**だった。この差分は検査純時間そのものではなく、間の処理も含む。

- 40回の正しさ検査：同じ時間帯を仮定すると **約267〜677秒**。
- 既存8回から追加する32回を最長値で見積もると、`632 + 32×16.92 ≈ 1174秒`、**約19.6分/job**。

正しさ workload は性能測定の48 threadsではなく、既存の **4 threads・200 records・extime 1秒**を使う。48-thread認証の長時間実績をそのまま掛けるのは誤り。今回の資料から11700秒超過を積極的に予測する根拠は得られない。ただし現行 build・gate込みのformal完走時間は未測である。

**成果物への影響:** 約20分を保証として扱うと、遅延を失敗と誤認したり回収を早期終了したりする。

### 4. 締切時に「invalid報告まで必ず残る」とは限らない

**real / must-fix**  
**file:line:** `tools/pegasus/b10_backoff_grid.sh:626`、`orchestrator/campaign/b10_backoff_static_tail_formal.py:750`、`docs/b10-backoff-static-tail-preregistration.md:997`

外側の `timeout 11700` は、driver内のタイマー開始より先に動く。したがって外側が先に終了させ、内側の `report_sweep_timeout()` に届かない経路がある。PBS killでも報告生成は保証されない。

残存WAL・stdout・failure receiptを回収し、欠測と理由を記述的に報告する必要がある。`completion.json`、完全なexecution report、登録済み飽和／域内非飽和の主張を失う。格子・repを削って救済しない。

**成果物への影響:** 完走成果物だけを待つと、部分観測と失敗理由が最終報告から脱落する。

### 5. F936の運用規律は必要だが、同じ関門がこのjobにあるという説明は誤り

**real / must-fix（順序と説明）**  
**file:line:** `docs/failures.md:24669`、`tools/pegasus/b10_backoff_grid.sh:372`、同`:472`、`02-plan.md:72`

F936の発火元は `certify_calibration.sh`。今回のjobに見えるclean検査はCCBench detached worktreeと依存sourceの検査であり、同じrepo全体の検査とは限らない。**汚したら必ず止まって守られる、と期待してはいけない。**

順序は以下。

1. scopeのinsight草稿と、投入前に必要なspool fragmentを確定。
2. 必要な文書変更をcommitしてから投入。
3. 待機中はread-only調査・監視と、許された`output/`内の記録。
4. 全job終端後、insightを完成し、結果のspool fragmentを書いてcommit。

結果fragmentを投入前に完成させることはできないので、未測の結果は書かない。待機中にsource・patch・事前登録・spoolを編集せず、commit／merge／checkout／変異走／書込みを行う子を起動しない。

**成果物への影響:** 放置すると起動失敗だけでなく、job間で異なるworking bytesを測る可能性が残る。

### 6. 別ノードというだけで集団がinvalidになる欠陥は確認できなかった

**refuted / must-fix相当の疑義**  
**file:line:** `orchestrator/campaign/b10_backoff_static_tail_formal.py:262`、同`:295`、同`:577`、`orchestrator/campaign/env_contract.py:168`、`orchestrator/campaign/buildcache.py:1176`

比較するのは、source digest、toolchain、環境契約hash、較正path/hash、事前登録commit・文書hash・spec hash、records・threads・extime・性能rep数・正しさrep数。

T-2566 §2(a)のsource tokenは、追跡source bytesのdigestへ変更済み。環境契約は登録値でありhostnameやjob IDを含まない。toolchainはrequested名・実体path・version情報で、hostnameを含まない。

**成果物への影響:** 同じ登録環境とtoolchainの別ノード走を、ノード名だけで拒否する構造ではない。実際にtoolchain等が異なれば登録どおりinvalidとなる。

### 7. 3 jobの並行投入は作法に反しない

**refuted / must-fix相当の疑義**  
**file:line:** `docs/pegasus-runbook.md:1318`、`tools/pegasus/submit_b10_backoff_grid.sh:235`、`tools/pegasus/b10_backoff_grid.sh:280`

別workloadの独立jobは並行投入の典型として明示されている。各jobの出力root・scratch・build cache・CCBench作業木は分離される。共有repoを変更しないことが前提。

**成果物への影響:** 直列化は登録標本を改善せず、queue待ちを追加する。現在のqueue状況は今回未確認。

### 8. 部分失敗の復旧手順はplanだけでは完結していない

**real / must-fix**  
**file:line:** `02-plan.md:49`、`tools/pegasus/submit_b10_backoff_grid.sh:253`、`docs/pegasus-runbook.md:1450`、`docs/b10-backoff-static-tail-preregistration.md:1012`

まずreceiptの成功済みrequestと終端状態を照合する。起動前のoutput root欠如は失敗としない。終端後の`completion.json`欠如はformal未完として扱い、観測を保存する。

再投入は新nonce・新requestとし、成功jobを巻き添えで再実行しない。ただし現submitterには失敗workloadだけの再投入引数がなく、formal CLIにも専用resume引数はない。**全submit再実行を復旧手順として提示してはいけない。** 同一性を維持した復旧経路を親が具体化できなければ、不完全cohortを失敗として報告して止める。別campaignのcellを継ぎ合わせない。

**成果物への影響:** 放置すると成功分の重複測定、異なる集団の混入、または永久に3完走を待つ状態になる。

### 9. 追補の数値・参照に小さな誤りがある

**real / nit**  
**file:line:** `01b-brief-addendum.md` §2、`output/insights/2026-09-04/t2266-backoff-static-tail/README.md:56`

12個のtps値は一致。ただし700→800のbalancedは **−5.64%**であり、−5.63%ではない。他の8変化率は表示精度で一致する。

700／800／900の正しい行は **56／58／59**。追補の57／59／60はずれ、60行は無効な旧1000の行を指す。新1000の数値行は9月10日資料の90〜92。planの主要コードアンカーは実在し、新規README`:1`は作成予定として明示されている。

**成果物への影響:** 趨勢の結論は変わらないが、引用先が別点・無効値になり追跡性が落ちる。

### 10. planはF-2を確認済み事実として使用していない

**refuted / nit**  
**file:line:** `02-plan.md`「親 brief の検査」F-2、同「計画」重複確認

planはqstatゼロ行を裏取り不能と明記し、投入直前のqueue・receipt・完了成果物確認を要求している。F-9についても現在の未投入を未確認と区別している。

**成果物への影響:** この確認を省略しなければ、親の古いqstat観測だけによる重複投入判断にはならない。

## 採るべき O

**O-C。** 指定レンズで攻撃した範囲では、事前登録binding、探索mode、worktreeからの投入、別ノード間identityに、本走を必ず不成立にする条件は見つからなかった。時間も保存実績から約20分という見積りを再構成できる。ただし出力親の作成、投入前の書込み確定、部分失敗時の回収・報告手順は具体化が必要である。O-Cは901〜998 µsを測らないため、その帯やT-2266の完了として記録してはならない。

## 総括

事前登録commitと探索campaignは具体値まで特定できた。  
約20分は保存実績に基づく見積りであり、formal本走の実測ではない。  
最大の運用上の穴は、部分失敗時に完走待ちから失敗報告へ移る手順である。  
別ノードidentityによる必然的invalidは確認できなかった。  
静的読解・保存資料照合のみ実施し、編集・commit・投入・pytest実走は行っていない。