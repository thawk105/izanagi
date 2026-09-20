---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-fig13-b10-waiting-grid
seq: 1
title: B-10 待ち方 grid 正式走 (report 978195.nqsv) の 3 族 Holm 判定と 36 cell の効果量・95% 区間・等価域 ±3.0% を 1 枚の forest 図 fig13 にし、新設生成器と着地 test・README の節・日本語キャプション正文と共に着地する (コード + docs、branch worktree-dev-wave-fig13-b10-waiting-grid)
---

## 本文

- ユーザー依頼 (2026-09-20、dev-wave 引数、台帳 ID 未起票。逐語は insight `verbatim/origin.md`) の範囲で 1 wave。fig11 wave (entry 1738) と同形の軽量版 (段 2・3 省略、段 6 review 2 本は残した)。
  一次資料は `output/insights/2026-09-20/fig13-b10-waiting-grid/README.md` (brief・裁定・review / fix / focus の逐語・変異台帳・走記録)。専用 handoff は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig13-b10-waiting-grid/HANDOFF.md`。
- 起点 local main `482f19b88`。開始 gate rc=0、編集面重複検査 hit 0 (47 worktree、unreadable 0)、pin 閉包 hit 0。一次資料 4 件 (report provenance JSON `a4390603…`、report .md `e237d17d…`、report 受領証 `93a1cd74…`、job 結果 `d5d4a0ee…`) の
  SHA-256 は稿 §4.1 / §4.2 と全一致、135 record からの再計算は cell_effects と bit 一致。
- **稿・report・既存 fig1〜12 の bytes は不変。** `docs/paper-story/README.md` の results 表は触っていない (ユーザー指示。同行の「図は無い」は起草時点の記述として残る)。
- 段 5 Codex author (gpt-6-astra / medium、18 分): 新設生成器 `tools/plotting/plot_b10_waiting_grid_forest.py` (判定は report から読み、135 record から同じ式で再計算して一致を要求するだけで判定を作らない。raw p の全 2^18 列挙は再計算せず分母の整数性と Holm の再計算だけ)
  と test 49 件 (実寸 fixture、着地 closure)。実データ CLI rc=0。親が login で図を生成 (PNG は author probe と bit 一致)、README 2 file を編集、焦点走 1 (計算ノード) 491 passed。
- 段 6 review 2 本: A (過剰・削除) must-fix 0 / GO、B (正しさ境界・限定) **must-fix 1 (B-1: FIGURE_CONVENTIONS §6 が必須とするレコード数 1,000,000 と Zipf skew 0.9 が図・caption・provenance に無い)** / NO-GO。
  裁定: B-1 / B-2 (等価域端点 test) を fix1 (Codex、5 分) で、A-1 / B-3 (README の照合範囲の文言)・A-5 (plotting README の重複) を親が直した。**A-2 (`outside-equivalence-range` の受理を拒否へ) は refuted** — 名前も等号の向きも report producer
  (`2a338449b` の `b10_backoff_shape_sweep.py` L1895〜1900) と同一で、拒否へ変えると producer と食い違う。A-3 / A-4 は不採用 (epoch 定数は repo 外を読まない閉包に要る。panel 題は可読)。
  焦点再レビュー: regressed 0 / partial 1 (変異 final 待ち) / GO、B-1 の実値 (records / threads / skew / rratio / rmw / max_ope / extime_s) を report JSON と照合して一致。焦点走 2 (fix1 後) 495 passed。
- 変異 matrix (登録 worktree `mut-fig13-b10-v2` @ tip、期待 node は login の self-run harness で観測した完全集合、本走は harness dispatch): anchor = tip `46e3c0a4d`、spec 20 件 (等価対照 m0 + 負例 19 = 段 4 の m1〜m12・m14、m13 を削除形 m13a / 境界形 m13b に分割、fix1 の条件検査 m15 records / m16 skew / m17 rratio / m18 threads)。本走 (dispatch、20:22〜21:19 JST) = **baseline PASSED・m0 SURVIVED・19 / 19 KILLED・期待 node 完全一致 20 / 20・MISMATCH 0**。単一 node で殺した変異 15 件、m1 は実データ系 4 node、m7 / m8 は 2 node。m4 (CI 係数、25 node) と m13b (曝露境界、33 node) は fixture 全般が先に赤になる過剰決定として単独変異の証拠から外した (DW-M03)。詳細は insight §6。
- 検査・受入: login self-run 49 → 53 passed (0 failed / 0 skipped)、焦点走 1 (計算ノード、11 file) 491 passed、焦点走 2 (fix1 後) 495 passed、check_docs 違反なし、diff --check 緑、provenance range 監査 (4 commit) 違反なし、full 監査は記録 commit 後に dispatch。 三軸語走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`、rc=1): hit は既知の凍結 holdout 系 file (`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/*`、`output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`、`docs/paper-story/figures/fig8b_b10_static_tail_cohort2.provenance.json`、`docs/paper-story/results/2026-09-16-b7-three-run-materials.md`) だけで、本 wave が足した file への hit は 0。受入: 記録 commit の tip で main を固定 SHA で取り込んだ後、待ち手経由の全走 (3 shard) を門番 loop から 1 回投入する。結果は本 fragment には書かず受領証 (`acceptance-receipt-final-<n>.json`、job dir) と land の記録が持つ。child-green でなければ land しない。
- 限界・言わないこと: 区間が ±3.0% の内側にあることは等価性の成立ではない (等価性検定はしていない)。36 cell の個別有意差は判定しない。静的右 tail の 2 cohort と合成しない (D2157)。機序を述べない。`official_certification` は `false` で採用根拠にしない。
  判定は D1678 で閉じており本図はそれを改めない。B-10 項目の閉鎖ではない。
- 事故: provenance 全史監査 (prov-1) を投入した後、queue 待ち中に fix1 を commit したため「HEAD が監査中に変化」で rc=2 (実行不能。全 commit 後に再走して閉じた)。旧 anchor の変異 probe は baseline dispatch が qsub 段で orphan hold を latch
  (request 13499 は scheduler 側で完走・終端。qdel せず) — anchor が fix1 で変わるため harness へ SIGTERM (signal 復元、clean) して新 anchor で作り直した。brief の「135 record」の単位誤記 (正しくは 135 record × 5 sample)。
- 裁定パッケージ候補 (実装せず記録): (1) results 表の当該行「図は無い」を fig13 着地に合わせて追補するか (fig11 wave は A-6 行を更新した先例)。(2) panel 題の raw p 二重表示と和の数値を本文幅では caption へ移すか (bytes が変わるので後継図の扱い)。
- 工数: codex 5 本 (author 1、review 2、fix 1、focus 1、全て gpt-6-astra / medium)、計算ノード job = 焦点走 2 + provenance 監査 2 + 変異 (final 1 + 中断 probe 1) + 受入。作図は login (計測機の外)。

## 次の一手差分
