---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2710-b5-wall-decomposition
seq: 1
title: [T-2710][T-2273] 受入 wall の律速 b5 群 (t080 e2e) の本体と固定費を replica shard-0 の同一 tip 反復で分解した — node 所要の約 9 割は共有 base の構築 (単独 98 秒 → 48 worker 下で 188〜257 秒) で本体 (verify) は 24 秒、pairing は replica で −52〜−69 秒の観測差 (事前登録の 3 対条件は未達)、最長 node 除外は wall を動かさず、分割 / 縮約は固定 duration model で利得 ≤ 7 秒 / 0、固定費 67 秒は warm bytecode cache の collection で cold replica は 129 秒 (docs のみ、probe は job dir、branch worktree-dev-wave-t2710-b5-wall-decomposition、変異 matrix 免除 = 実装面差分ゼロ)
---

## 本文

- ユーザー依頼は「[T-2710] [T-2273] (第 22 回 /rulings 項 3、ユーザー「推奨通りで」2026-09-18) 受入 wall の律速 b5 群 (t080 e2e、225〜500 秒) の本体と
  固定費を D357 の反復・対比較 (同一 tip・同一条件 3 走以上、中央値) で分解し、shard 内 pairing (上限 5.8%、[T-2766]) と e2e の分割 /
  parametrize 縮約の効果を実測で持つ — 成果は insight (実測値・分解表・次の諮り直しの裁定パッケージ案)。受理集合は変えず (D2068 / D2128)、
  保留検査は復帰させず、成分粒度は変えない (D2121)、8 条件の整備 wave は起こさない。実装はしない (実測と設計案まで、実装面差分ゼロ)。計測は
  計算ノードへ dispatch する。着手直前の local main から fresh worktree を作る。規律 2 を緩めない。本題の実測だけ。仮想リスク向けの gate・検査・
  台帳・一般化の追加は scope 外」。
- **閉じた (実測と分解表と裁定パッケージ案を insight に置いた。実装せず、段 4 → 5 (probe の author) → 6 → 7)。** 一次資料は
  `output/insights/2026-09-18/t2710-b5-wall-decomposition/README.md` (段 1〜4 の逐語、probe の逐語と sha256、集計の抜粋を同 dir に凍結)。
  decisions fragment 0 (裁定パッケージは提案であり採用済み判断ではない)、failures fragment 1 (F945 再発 2 件)。
- 主判定 (replica shard-0 = production allocator + conftest 順 + `-n 48 --dist loadgroup` を 1 計算ノードで、同一 tip `779b3ea3c`、条件 S1 / S / A / B / C
  各 3 走、Latin square 3 job 逐次): `[ccbench-current]` の call は単独走 (S1) で 125.7 秒 (中央値) = base 構築 98.3 + copytree 2.3 + verify 5 回
  23.0 + その他 2.1。replica A では 261〜287 秒で、増分はすべて base 構築 (builder の build 232〜236、待ち手の flock 待ち 188〜257) に入り、
  verify は 1 回 4.5〜5.3 秒で不変。発行なし key (g7) の build は 42.3 秒 → 発行 subprocess ≈ 60 秒 (別 key 比較の推定)。A の他成分を固定して verify 24 秒を引いても
  約 238〜263 秒が残る (算術)。pairing (B、T-2766 の形、49〜96 位を最小 cost の 48 unit に) は W 414.7 → 345.6 (中央値差 69.0 秒 = 16.6 %、有効な同 job 対は
  2 組で 52.0 / 65.1 秒、B 3 走はすべて A 3 走より短い、48 worker 全部で意図順が反映) だが、事前登録の「同 job 3 対」条件は未達で
  **採用効果は未確立** (段 6 レビュー B M1 を採用)、実受入での効果も未確認。最長 node 除外 (C) は
  W 417.8 で不変 (次点 `draft_finalize` が同じ床)。分割 (2+3 call) は固定 duration model で利得 ≤ 6.8 秒、縮約は 0 (実 wall 効果は未測定)、どちらも受理集合を縮める。
- **新事実 2 件。** (1) shard 固定費 (wall − 最大占有) の受入値 67 秒は「warm bytecode cache での collection + worker 起動 59 秒 + 終了 8 秒」で、
  fresh worktree (cold、計算ノードは `PYTHONDONTWRITEBYTECODE=1` で pyc を書かない) では 129 秒。login の `run_tests.py --collect-only`
  (24,934 件、47.9 秒、387 pyc) で温めた補助観測 (job 6、n=2、cold/warm の同 job 交互比較ではない) は F 66.4 / 66.4 で歴史受入の F と近く、cache 仮説を支持する
  (因果の確定ではない)。(2) 48 worker 下の
  base 構築の 2 倍化が律速の実体 (発行なし build 42 → 172〜198 秒なので主に実体化側と推定、内訳は未分離) で、D2068 の却下 3 案とは別の面
  (構築の並行度・順序、実体化 / 発行 / 待ちの内訳)。
- 段 2 plan (受理) が親 brief を訂正: B/C の変更は worker の `pytest_collection_finish` で xdist の送信前に置く (段 3 レンズ A が
  `tryfirst` 必須と指摘、採用)、verify 回数は 5/2/2/1、env 名は `IZANAGI_ACCEPTANCE_SHARD_PLUGIN_V1`、93 session の例外最長 node は
  `test_historical_oracle_nonadapter_reaches_current_semantics`、base key は 5 種、S1 も shared base 経路。段 3 レンズ A (must-fix 3) /
  B (must-fix 4) は全件 real・採用 (model は A にも同じ式、分割は連続検査を失う、pairing の判定規則を事前登録、固定費は 3 層で表記)。
  段 4 裁定と事前登録は `s4-ruling.md`。
- 失敗走 2 件 (事前登録どおり除外): job 4 の B (rc=16、t1259 の `git ls-files --others` 30 秒 timeout ×22 + real-repo flock deadline の
  worker internal error、同時刻に他 wave の受入 4 session) → job 5 で同条件 1 回置換 (344.4 秒、緑)。job 6 の warm A 3 走目 (rc=1、同型
  ×4) → 補助観測のため置換せず n=2。F945 の再発として failures fragment に追記。
- 段 6 レビュー B (事前登録・既裁定との整合と裁定パッケージ案の攻撃、must-fix 5 / should 4 / nit 3、解釈面 NO-GO) は全件 real・採用し
  README を是正した: pairing の判定を「採用効果は未確立」に (3 対条件未達)、「実体化・発行とも 2 倍」を撤回 (発行なし build の A 値
  172〜198 秒を提示し内訳は未分離)、cache の因果を仮説に限定 (n=2)、300 秒評価の cold/warm 混在と 210 秒 model の外挿を撤回 (算術例に降格)、
  分割 / 縮約の「効果なし」を「model 利得 ≤ 6.8 / 0、実 wall 未測定」に。レビュー A (数値再計算) は 1 本目が除外走の report.json
  不在で fail-closed 停止 (prompt の射影の誤り、親が是正して再投入)。再投入 (A2) は §3 shard 表の 86 セル全部と対差・model・B の配布・除外理由を
  生データから再現 (一致 49 / 不一致 12 / 未検証 1 の判定行)、must-fix 4 (pairing 判定 = B M1 と同じ、§5 の加算式が copytree を二重計上、固定費
  3 層の未閉 (5.2 秒の抜けと母数 95/97/97)、O percentile 25.8〜61.3 %) + should 5 (S の verify 23.1、範囲 187〜257 / 263〜290 / 344〜363、
  分割利得 6.3〜6.8 (warm 7.0)、除外 2 件、発行 ≈ 56 秒は推定) を全件採用して README を是正した。fix 子は起動していない (docs の是正のみ)。
- 段 8 (自己改善): 候補 3 件、いずれも記録のみ。(i) 段の flag 違反 (author に `--max-attempts 2`、review に `--reasoning`) で launcher を
  2 回作り直した — DW-C01 に既記 (「他段指定/必須段無指定はrc=2」)、dry-run を launcher 作成前に必ず通す (memory)。(ii) 時刻を推定で
  書きかけた (F1 型、memory 既存)。(iii) 計測中は wave worktree に 1 byte も書かない (fixture が可視 output を複製する) — README §2 に
  記載、docs 変更なし。
- 実走: 計算ノード generic dispatch 6 job (5522 / 5554 / 5601 / 5620 / 5650 / 5663.nqsv、bnode027 / 016 / 021 / 017 / 014、11:36〜13:56 JST、
  逐次、pytest 15 走 + 除外 2)、login: probe selftest 45/45、collect-only 1 回、三軸語走査 `s8b_holdout_freeze search` rc=0 (docs commit
  前後)、全史 provenance 監査 11,299 件 違反なし、`check_docs.py`、`spool_fold.py --dry-run`。受入全走は land 前に 1 回 (結果は land の受領証)。
- 工数: codex 子 6 本 (plan 1、consult 2、author 1、review 2、全段 `gpt-6-astra` / medium、rc=0・受理 6/6)。fix 0。親: 93〜95 session の
  集計 3 表 (inline)、xdist / conftest / acceptance_shards の現物読解、launcher 5 種、集計の検算、README。

- [T-2710] b5 群の本体 / 固定費を replica の同一 tip 反復で分解し、pairing (観測差、採用効果は未確立)・最長 node 除外 (効果なし)・分割 / 縮約 (model 値は下限、実 wall 未測定) の材料を持った。
  次の諮り直しの裁定パッケージ案は README §9 (択 (a) pairing は実受入 n≥3 の対比較を条件に採否、(b)(c) は採らない案として残す、(e) base
  構築の 2 倍化と cold cache を次の調査対象に)。
- [T-2273] 律速を再同定: 最遅 shard の wall ≈ 共有 base 構築 (48 worker 下 188〜257 秒) + verify 24 + copy 4 + 相方 20 + 固定費 60 (warm)。
  本体側・分割・縮約では model 上届かず、pairing は replica で −52〜−69 秒の観測差 (採用効果は未確立)。

## 次の一手差分

### 更新

- [T-2710] **P1・裁定パッケージ提示済み → ユーザー裁定待ち**: t080 e2e 群 (b5) の本体 / 固定費の分解を replica shard-0 の同一 tip 反復で持った
  (`output/insights/2026-09-18/t2710-b5-wall-decomposition/README.md`)。node 所要の約 9 割は共有 base の構築 (単独 98 秒 → 48 worker 下で
  188〜257 秒、主に実体化側と推定)、本体 (verify) は 24 秒で不変、最長 node 除外は wall を動かさず、分割 / 縮約は固定 duration model で
  利得 ≤ 7 秒 / 0 かつ受理集合を縮める。pairing は replica で −52〜−69 秒の観測差 (事前登録の 3 対条件は未達、実受入は未確認)。固定費 67 秒は warm bytecode cache の collection (cold なら 129 秒)。裁定パッケージ案 (README §9) は
  (a) pairing の採否 = 実受入 n≥3 の対比較を条件、(b)(c) 分割 / 縮約は採らない案として残す、(e) base 構築の 2 倍化の内訳と構築の並行度・順序を
  次の調査対象にする。D2068 の却下 3 案は再提示しない。
  base: 5582c52c5e4a700c7efe570b3a1836321bb5cb711f039594acc5b9cfc7acfc3c
- [T-2273] **P1・律速を再同定 (第 2 回)、300 秒目標は本体側・分割・縮約では届かない**: 最遅 shard の wall ≈ 共有 base 構築 (48 worker 下
  188〜257 秒、単独 98 秒) + verify 24 + copy 4 + 相方 20 + 固定費 60 (warm) / 129 (cold)。pairing は replica で −52〜−69 秒の観測差 (cold replica の B は 344〜363 秒で 300 秒未達、warm 実受入は未測定)。
  次の候補は {{T:t080-base-build-contention}} (base 構築の 2 倍化の内訳と並行度・順序) と [T-2766] (実受入での効果確認)。
  base: fe54b5d8d2859be4ecfec884b06483388adfe786606b491b10862a3c7d571f42
- [T-2766] **P3 → P2・replica で観測差あり (採用効果は未確立)、実受入での確認待ち**: 49〜96 位を最小 cost の 48 unit にする pairing は
  replica shard-0 で W 414.7 → 345.6 (中央値差 69.0 秒、有効な同 job 対 2 組で 52.0 / 65.1 秒、B 3 走はすべて A 3 走より短い、48 worker
  全部で意図順が反映、3 個目の unit なし)。事前登録の「同 job 3 対」条件は未達。相方 20 秒の除去は確認済み、最長 node 自身の 30〜45 秒短縮は
  原因未同定 (builder の担当移動は観測、同時実行負荷の変化は説明仮説)。採否は D104 決定 3 に従い同一 tip の実受入 n≥3 の
  対比較 (A/B 交互) を条件に諮る。実装は conftest の並べ替え関数の後段 1 関数 (Codex author、変異登録要)。
  base: 48aade1fc994c3c041eec56216ce8028609755be129bac303210fec45902cc7b

### 新規

- {{T:t080-base-build-contention}} **P2・新規**: t080 e2e の共有 base 構築が 48 worker 下で単独の約 2 倍 (98 → 188〜257 秒) になる内訳
  (repo 実体化 42 秒 / 発行 subprocess 60 秒のどちらがどれだけ伸びるか、同時に走る cost 2 位以下の unit との干渉) と、構築の並行度・順序
  (5 key の base を先に build してから他 unit を流す、builder を 1 worker に固定する等) の効果を replica で実測する。D2068 の却下 3 案
  (whitelist / alternates / 独立 index) は再提示しない。受理集合不変。probe は job dir、Codex author。
- {{T:acceptance-cold-bytecode-cache}} **P3・新規**: fresh worktree (login で pytest を 1 度も走らせていない wave) の受入は test module の
  bytecode cache が無く shard 固定費が +60 秒 (129 vs 67 秒、計算ノードは `PYTHONDONTWRITEBYTECODE=1` で pyc を書かない)。受入投入前に
  login で `run_tests.py --collect-only -q` (48 秒) を走らせる手順を runbook / DW-O18 側に置くか、受入 launcher が warm を確認する案の
  採否。docs-only wave で発火する。
