---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-k2-loop-originals-lost-downstream
seq: 1
title: K2 loop 原本消失 (2026-09-20 19:25 JST) の下流影響 — 3 巡の主張ごとの対応表を実測で定め、round 3 の loop_state と round 2/3 の AO は repo 派生物から byte 一致で再構成でき WAL は内容同一まで、4 巡目の入力元の択 (round 3 派生物 / 別走 / pair 走) を裁定パッケージへ返した (docs のみ、実装差分ゼロ、branch worktree-dev-wave-k2-loop-originals-lost-downstream)
---

## 本文

- 起票は記録 wave `dev-wave-cleanup-backup-loss-record` の worklog fragment の新規 T「K2 loop 原本消失の下流影響」(本 wave 着手 20:52 JST〜land 時点で
  未 land、branch tip `f43322f8a`)。他 wave の placeholder は参照できないので本 entry は番号を書かない。**同 T が採番された後は、本 entry を根拠に完了へ置く**
  (残件なし: 対応表と裁定パッケージは `output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md` §2・§4 に着地)。
- ユーザー依頼 (dev-wave 引数) の範囲で 1 wave。起点 local main `7baf3f375` (fresh worktree、開始 gate rc=0)、記録前に `f94b61fc8` ([T-2792] の記録と fold) を固定 SHA で
  取り込み。軽量版 (DW-C00): 段 2・3 省略、実装面ゼロ、段 6 は一次資料から事実を再抽出する docs-only なので read-only レビュー 1 本。
- **ListAgents (20:55 JST): 稼働 17 session に [T-2795] wave は無い** (entry 1754 で着地済み、job dir の `submit-tree-pair` だけ残存)。編集面の重複:
  `docs/paper-story/README.md` は story 20260920b wave (`dev-wave-paper-story-20260920b`) が stale 注記の同じ節を編集中 (mtime 20:57 JST) だったので
  本 wave は README に触らず、積む文面を insight §5 に置いて peer へ事実を送った。`docs/phase3.md` は同 wave の版が main より古く未編集 → 項 4 に 1 行。
  記録 wave の編集面 (4 insight の erratum 節、新 insight、spool) とは重ならない。
- 実測 (login node、読み取りのみ、`materials/reconstruction-log.md`、生 stdout は `materials/reconstruction-stdout.txt`): (1) 3 巡稿
  `results/2026-09-20-k2-manual-loop-three-rounds.md` §5.1 が消失前の同日に 3 巡全原本の sha256 と bytes を再計算しており、記録 wave の結論「roundtrip は sha256 も無い
  (値までしか遡れない)」「round 2 の `campaign.lock` は照合不能」(いずれも insight に記載が無いことから導いたもの) を補正する: roundtrip は 5 file とも sha256 まで遡れる、
  t2746 job dir `scratch-campaign/` の `campaign.lock` は round 2 の記録値 `fc7acaca…` と byte 一致 (AO だけ別走)。記録 wave の file は所有外で書き換えない。
  (2) round 3 `loop_state.json` (`917ba3d3…`) は `materials/run-summary.json` から、round 2 / 3 の本走 AO (`804c62c7…` / `66d3e737…`) は `layer3_report.json` から、
  harness の writer 形式で byte 一致で再構成できる (round 2 の scratch 写しで手順を検算)。(3) round 2 / 3 の WAL は `layer3_report.json` の events と内容同一
  (canonical ref 5/5 = `materials/wal-refs.json`) だが payload の挿入順が戻らず bytes は再構成不能。digest は repo に逐語なし。(4) [T-2795] pair 走の原本 5 file は
  `submit-tree-pair` に無傷 (sha 5/5) だが worktree は unlocked・未追跡 `output/exploration/` あり = 撤去された候補 1 と同型 (16:26 の候補 list には無い)。
  (5) 4 巡目は harness の checkpoint 再開ではなく親の射影で前巡を運ぶ (round 3 の記録: round 2 の tree は `start_wall` 超過で入口停止 → fresh tree)。
  射影に要る入力は全部 repo 派生物か無傷の写しにある。(6) roundtrip 原本 5 file と round 3 の lock / digest / WAL の sha 一致 file は、K2 insight dir 4 つ + t2588 / t2746 の
  job dir root の 615 file を 21:23 JST に走査して受領証 1 件 (同一 bytes) だけ。(7) 21:24 JST に pair 走の原本 6 file (campaign 5 + claim) を T-2795 job dir
  `originals-copy-20260920/` へ byte 複製 (MANIFEST、6/6 一致)。worktree の lock は隔離 session の guard で打てず付随項へ。
- 対応表 (insight §2): B-6 (a) は round 3 = canonical 内容・roundtrip = 転記値まで、(b) 診断が届いたは原本非依存、(c) critic-3 の読取対象のうち digest の bytes は
  消失、(d) 同 job stock 未達は pair 原本現存。B-9 (c) は材料レポート自身は不変だが fresh rebuild 深い一致は原本 root 消失で再実行不能。fig12 は稿 + JSON 束縛で
  原本非依存、[T-2808] fig12b は影響なし。3 巡の値・判定・稿・図は変えない (規律 7)。
- 裁定パッケージ (insight §4、ユーザー): 4 巡目の入力元 = **択 A (推奨) round 3 の派生物から射影を組む** (系列を切らない、loop_state / AO は sha 一致の再構成物を
  再構成と明記して置き harness には load させない) / 択 B 別走 (新系列、critic-3 の還流を捨てる) / 択 C pair 走を直前巡にする (診断と実測の出所が混ざる)。
  付随: `submit-tree-pair` の `git worktree lock` を次の非隔離 session が打つ (本 wave の隔離 session では guard が他 worktree への git 操作を拒否)。
  やらない理由の最も強い形は各択に併記。
- 言わないこと: 原本を復元した、WAL を再構成できる、digest を再描画できる (未実測)、provenance は消失前と同じ強さ、4 巡目の認可・予算・投入時期。
- 段 6 read-only レビュー 1 本 (gpt-6-astra、12 call、180 秒): NO-GO → must-fix 7 件 (roundtrip 不在断定の走査根拠、B-6 (c) の限定に WAL / lock を含める、B-6 (d) の 3 巡と pair の
  分離、択 A / B の provenance 比較の過大、次巡記録文の裁定先取り、実測 log の「逐語」表記、記録 wave との相違を「補正」と書く) + nit 2 件 (出所の誤記、whiteboard ≠ current_perf)。
  全件 real・採用、親が docs を直した。焦点再レビュー 1 巡目は NO-GO (残 must-fix 4: 走査件数の誤記 23→24 と値の不在の根拠、README 冒頭の「逐語」表記、fragment が再レビュー結果を
  先取り、受領証を除外しない限定文) → 追加実測 (`start_wall` 値の内訳、走査 (b) の条件込み採り直し) と fix → 2 巡目の結果は `reviews/s6-focus-2.md` (本 entry の記録時点の判定は
  insight §6)。「択 A を棄却する技術的根拠は無い」「択 B は次系列の依存範囲を減らす利点があり研究目的次第で合理」「付随項は scope 外に当たらない」「A 推奨と B / C の合理性は矛盾しない」
  はレビューの判定。
- 事故: なし。工数: codex 3 本 (段 6 レビュー 1 + 焦点再レビュー 2、実測値は insight §8)、計算ノード job 0。

## 次の一手差分

### 更新

- [T-2795] **P1・裁定済み (D2172 項 3、択 (i) + (iv)) → launcher 実装済み (D2183) → pair 初投入 (2026-09-20、`13339.nqsv`) で stock が one-shot claim leaf に
  拒否され pair 不成立 → launcher と claim の整合を直す修復 wave (AI、Codex author + 敵対検証子、D2187) → 修復後の pair 再投入 (1 job) と
  4 巡目 (1 job) は D2172 項 3 の予算の再提示 (ユーザー)。4 巡目の入力元 (round 3 派生物 / 別走 / pair 走) はユーザー裁定**:
  候補 10 の再評価は certified (811,956 tps、campaign `b24749ae`) だが、同 job・同 campaign の stock driver (2 起動目) は `campaign_claim.acquire_claim` の
  `O_EXCL` で認可前に停止 (`src_token == STOCK` 未確認)。修復方向 = 1 回の認可・claim の所有期間で候補と stock を両評価する driver 設計 (claim leaf は不変、
  `run_campaign` の認可契約または stock 評価の呼出し形を変える。D553 の sink-local `single_process` と D2183 の CLI 排他への影響を段 1 で明示)。却下候補 =
  同 identity path の DEAD 再取得 (one-shot の受理集合変更)、claim の rename (防壁を外す)、別 out_root (同 WAL を破る)。保留も択。修復 wave は
  同 durable root・Pegasus 契約での候補→stock 連続起動の結合検査 (F1019 再発の恒久対応) を必ず含める。B-5 (β、[T-2797]) の job body 設計も同じ制約を受ける。
  記録: `output/insights/2026-09-20/t2795-k2-pair-attempt/README.md`、3 巡目 README の追記節。(ii) 単独・(iii) 単独は不採用のまま。
  **2026-09-20 追記 (原本消失の下流):** round 3 の campaign 原本は 19:25 JST に消失 (記録 wave の F)。4 巡目の射影入力 (whiteboard・current_perf・critic-3 逐語・
  knowledge-input・受領証・identity の lock) は全部 repo 派生物か無傷の写しにあり、入力元の択 A (推奨、round 3 派生物から組む) / B (別走) / C (pair 走を直前巡) と
  やらない理由は `output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md` §4。修復 wave の段 1 で `dev-wave-jobs/dev-wave-t2795-k2-pair/submit-tree-pair`
  (pair 走の原本 5 file + claim、unlocked。byte 複製は同 job dir `originals-copy-20260920/` に 2026-09-20 21:24 JST 作成済み) を `git worktree lock` する。
  4 巡目の記録には、択 A なら「round 3 の原本 bytes は消失、入力は派生物から組んだ」を、択 B / C なら実際に選んだ入力元とその原本の所在を書く。
  base: cff0f011dd4e23e4e0c3b1077379b76f5e8da27f8005045f754ed5638fe6bd8e

### 新規

- {{T:k2-originals-lost-readme-stale-note}} **P3・新規**: `docs/paper-story/README.md` の stale 注記に「K2 手動 loop 3 巡の campaign 原本の消失 (2026-09-20 19:25 JST)」の
  1 段落を積む (文面 = `output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md` §5、記録 wave の F 番号を実番号で)。story 20260920b 版の land 後に
  同版の注記へ足す (同 wave は「未着地 wave の内容は書かない」規律で書かないと返答、2026-09-20 21:2x JST)。稿・図の bytes は変えない。
