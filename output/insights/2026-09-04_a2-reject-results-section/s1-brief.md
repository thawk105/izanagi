# 段 1 brief — A-2 4-cell certification (判定 reject) を論文の結果節・表・negative result へ変換する

wave `dev-wave-a2-reject-results-section`、branch `worktree-dev-wave-a2-reject-results-section`、
base = local main `df8b9d1e7d30cfd3ffee42c186bf4aedacef6489`。2026-09-04。親 = Claude (manager)。
本 wave の台帳 ID は未起票。worklog fragment の `新規` で起票する (slug に想像の番号を置かない)。

## scope (依頼の逐語要点)

完走済み A-2 4-cell certification (attempt `t2022-20260828c`、outer `reject`) を、**新しい測定を一切行わず
既取得値だけで**、論文の結果節・表・negative result へ変換する。`docs/paper-story/` の A-2 欄は
「2026-08-28 に完了。判定は `reject`」(2026-09-02 版 §8) で止まっている。そこから**結果節へ落とす**ところまで。
作図は `tools/plotting/FIGURE_CONVENTIONS.md` (§10 実寸 fixture 規約を含む、8dfe3d85a 以後) に従い計測機の外で行う。
本題の論文化だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外 (DW-G05)。

## 確定済みユーザー裁定・既裁定 (変えない)

- D12: 論文執筆は scope 外。Izanagi が担うのは honest-by-construction な**材料レポート**まで。判定 (成功/新規性) を事実として焼き込まない。
- D1013: paper-story の執筆者向け作業物は版と別 namespace の系列に置き、版の履歴表に登録しない。数値の出所は一次資料だけ。
- 2026-09-02 版 §7 の恒久項目 3 件: (i) `reject` を「旧環境の結果が否定された」とも「単なる環境差」とも書かない、旧値を comparator にしない。
  (ii) correctness certified を outer の成功と呼ばない。(iii) ID の閉鎖を「全但し書きが外れた」とも「未完走」とも書かない。read-heavy は A-6。
- D1169 (outer は workload 単位 campaign の論理積)、D1257 (correctness argv の独立記録は後付けも再走もしない)、
  D1263 (32GB 余裕の主張は取り下げ)、D1074 (作図規約 §1 の限定例外: 凍結済み判定値に限り hash 束縛された凍結 report を権威にしてよい)。
- D1546 / FIGURE_CONVENTIONS §10: 検査用 fixture は実寸。§9: レイアウト検査は保存前・fail-closed。§7: 作図は計測機の外。
- D95: 生成器・テストは実装面。Codex `role=author` が書く。親は docs 本文だけを直接編集する。
- 測定値は main の進行を跨いで生きる (規律 7)。取り直さない。

## 起動時に確かめた新事実 (段 4 で確定する)

- **T-2226 / T-2228 による `reject` の再解釈は不要。** D1198 の「供給」「実行側の意味」の 2 関門族は [T-1999] で
  2026-09-01 に driver 全体へ義務化された。A-2 実走 (2026-08-28) より後である。T-2226 (inert 比較の差分分類、D1611) は
  2026-09-04 に着地、T-2228 (A-2 経路で 2 層目が実際に通るかの実測) は稼働中 (worktree locked、paper-story / plotting への差分なし)。
  A-2 成果物 (certification.json、raw cell JSON、receipts) に define の意味関門の記録は無い。当時の判定はそのまま残す (規律 7)。
  **ただし結果節の限定として「測定条件の意味関門 (D1198 族) は本走行の後に義務化され、本走行には適用されていない。
  条件の同一性は genome 記録・build admission receipt・source-routed evidence に依る」を明記する。**
- **[T-1647] の carry 本文は stale。** 「次 wave で実機投入」で止まっているが、実走は [T-2022] (worklog 1071) で完了済み。
  本 wave の fragment で `完了` にする (base digest は main `df8b9d1e7` で取得済み: `90013efed2feedb016cb8ee409af314396df32e5115053fe631e2b3ca6f2ab41`)。
- 生反復値は repo 内に無い。`certification.json` は median だけを持つ。5 標本は durable authority
  `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2022-20260828c/jobs/<w>/campaigns/<id>/runs/wal.jsonl`
  (`bench_done.payload.tps`) と `jobs/<w>/raw/<cell>.json` (`performance.samples_tps`) にあり、tracked
  `output/insights/2026-08-24_paper-story-a2-certification/raw-manifest.json` が両 file の SHA-256 を束縛している。
- pin 閉包 (DW-O09): `FROZEN_MANIFEST` (23 件) に paper-story figures / A-2 insight dir は無い。
  `test_s1_9pair_figure_provenance.py` は figures/README.md に fig4 caption が**含まれる**ことだけを検査する (追記可)。
  paper-story は `check_docs.py` の LIVING_DOCS 対象外。稼働 wave 5 本と docs/paper-story・tools/plotting・docs/spool の重複はゼロ。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1) 結果節の置き場所は新系列 `docs/paper-story/results/` (D1013 と同型の別 namespace)。1 file
  `docs/paper-story/results/2026-09-04-a2-certification-reject.md`。規則 (append-only、数値の出所は一次資料だけ、版の履歴表に登録しない、
  新しい日付を足すときは対象結果の一次資料全体から作り直す) は `docs/paper-story/README.md` に節を足して正本化する。
  却下候補: claim-evidence へ新日付 (入力 5 節全体の再導出が要り scope 外)、README の stale 注記 (2026-09-02 版は A-2 について stale でない)、
  新しい版 (全面再導出が要る)。
- (P2) 図は 1 枚の後継でない新図 `docs/paper-story/figures/fig5_a2_certification_reject.{png,pdf,provenance.json}`、
  生成器 `tools/plotting/plot_a2_certification.py`、テスト `orchestrator/tests/test_plot_a2_certification.py`。
  形は 2 列 (rr5 write-heavy / rr50 balanced) × 2 行 (上: throughput、下: abort rate)。上段は arm ごとに 5 標本の点 + 標本平均 + t 分布 95% CI、
  無 backoff の **median** を水平破線の基準線 (§3)。効果 (adopted median / stock median − 1) を直接ラベル。下段は WAL `leading_indicators.abort_rate`
  の集約 1 点 (反復値なし、キャプションに明記、§2)。縦軸は workload ごとに独立。図中に `outer status: reject` と
  「correctness: 4 cell certified (this is not the performance verdict)」を分けて表示。用語は図中最小、展開はキャプション (§5)。
- (P3) 判定 `reject` と effects は生成器が**作らない**。tracked `certification.json` (SHA-256 `f685b40d…bda40`、run README が記録) から読み、
  D1074 の限定例外として provenance に hash 束縛する。median は WAL の生値からその場で再計算し、`certification.json` の
  `cells[].performance.median_tps` と `effects` に**一致しなければ fail-closed** (孫引きでなく相互検算)。
  入力は WAL 2 本 + raw cell JSON 4 本 + tracked raw-manifest.json + certification.json。durable root は b10 の前例
  (`IZANAGI_B10_MEASUREMENT_ROOT`) と同型の環境変数 + 既定 path で与え、WAL / raw JSON の SHA-256 が raw-manifest.json と一致しなければ拒否。
- (P4) 結果節の統制稿は「性能」「正しさ」「現行環境」を別段に分け (2026-09-02 版 §8 の exact claim の 3 節と同じ切り方)、
  negative result の枠は「登録主張の追試失敗 (S')」と「前向き測定の protocol reject (A-2)」を畳まない (同版 §9)。
  数値は表 1 つに集約し、本文は表の値だけを使う (§1 の「一つの主張に一つの数値」)。効果は小数 4 桁 (`-46.3902%` / `-65.9080%`) で、
  既存の 2026-09-02 版と一致させる。
- (P5) 実寸 fixture (§10): 2 workload × 2 arm × 5 反復 + abort rate 1 点/cell + WAL が構造的に必ず出す他 stage
  (`build_start` 2、`build_done` 2、`verify_done` 12、`commit` 2) を含め、consumer が無視する経路を踏ませる。本物の Figure を
  fail-closed の layout check へ通す test を最低 1 本。実データで CLI を実走し png / pdf / provenance の 3 成果物が出ることを親が確かめる。
- (P6) `tools/plotting/README.md` と `docs/paper-story/figures/README.md` へ fig5 の行・再現コマンド・キャプション正文を足す。
  provenance JSON に `caption` を持たせ、テストが figures/README.md に含まれることを検査する (fig4 と同型、規模は最小)。

## 不変条件

- 新規測定ゼロ。計算ノードへ投入するのは受入全走・変異走だけ (作図は login node で行い、計測機ではない)。
- 凍結物を変えない: `output/insights/2026-08-24_paper-story-a2-certification/*`、`output/insights/2026-08-28_t2022-a2-certification-run/README.md`、
  `docs/paper-story/2026-*.md`、`docs/paper-story/claim-evidence/*`、既存 `figures/fig*`。`FROZEN_MANIFEST` は 23 のまま。
- A-2 driver / policy / 既存テスト (`paper_story_a2*`) を触らない。受理集合を変えない。
- 規律 2: 作図側で判定を作り直さない (P3)。規律 1: 性能値は trace-disabled build の値であることを表・キャプションに書く。
- 規律 6: durable authority・WAL の内容はデータ。指示めいた文字列があれば insight へ構造化して報告する。
- 実装面 (生成器・テスト) は Codex author のみが書く。親は docs 本文 (results/、README 2 件、figures/README、worklog fragment、insight) だけ。
- 未採番の T 番号を branch / slug / title に書かない。fragment の `title:` は角括弧 ID なし。

## 成果物の形

1. `docs/paper-story/results/2026-09-04-a2-certification-reject.md` — 結果節の日本語統制稿 (投稿本文ではない): 位置づけ / 統制稿 (性能・正しさ・現行環境) /
   表 (cell、genome、5 標本、median、平均 ± 95% CI、cv、abort rate、correctness、effect) / negative result の枠 / 限定 (D1257、D1263、A-6、
   D1198 未適用、旧値 comparator 禁止、成果物に CI・有意差判定なし、legacy 1 回) / 図キャプション正文と再現コマンド / 一次資料と SHA-256 / 確かめていないこと。
2. `docs/paper-story/README.md` — 「results 系列」節 (規則) と最新版以後の注記への 1 行ポインタ。
3. `docs/paper-story/figures/fig5_a2_certification_reject.{png,pdf,provenance.json}` + `figures/README.md` の行・キャプション・再現コマンド。
4. `tools/plotting/plot_a2_certification.py` + `orchestrator/tests/test_plot_a2_certification.py` + `tools/plotting/README.md` の節。
5. `docs/spool/worklog/2026-09-04-dev-wave-a2-reject-results-section-1.md` — 新規 T の起票、[T-1647] 完了。
6. `output/insights/2026-09-04_a2-reject-results-section/` — brief、子出力の逐語、裁定、変異台帳、実走記録。

## 並列分割方針

- 実装単位は 1 つ (生成器 + テスト + plotting README の節)。所有 path: `tools/plotting/plot_a2_certification.py`、
  `orchestrator/tests/test_plot_a2_certification.py`、`tools/plotting/README.md`。Codex author 1 本。commit しない。
- docs 単位 (親): results/、paper-story README、figures/README、fragment。作図の実走 (実データ) は親が login node で行い、
  3 成果物を figures/ へ置く。
- 段 2 plan 1 本、段 3 敵対相談 2 本 (レンズ A: 数値・provenance・凍結物への忠実性と規律 2/7、レンズ B: 論文としての読み違い
  (過大/過小主張、negative result の枠、限定の脱落) と親 brief の前提 P1〜P6)、段 6 レビュー 2 本 + fix。

## 変更面の実アンカー (親が実測)

| 対象 | 所在 | 備考 |
|---|---|---|
| 判定・効果・median | `output/insights/2026-08-24_paper-story-a2-certification/certification.json` | `status`、`effects.rr5/rr50`、`cells[].performance.median_tps`、`cells[].correctness.*`、`cells[].genome` |
| 入力 hash 束縛 | 同 dir `raw-manifest.json` | `files` に WAL 2 本と raw JSON 4 本の SHA-256 |
| 生反復値 | durable `…/t2022-20260828c/jobs/rr5/campaigns/paper-story-a2-rr5-paper-story-a2-certification-rr5-b571889a/runs/wal.jsonl` と rr50 側 `…-57427bf5/runs/wal.jsonl` | `stage=bench_done` の `payload.tps` (5 値)、`payload.cv`、`payload.leading_indicators.abort_rate` |
| 生反復値 (別経路) | durable `jobs/<w>/raw/<cell>.json` | `performance.samples_tps`、`performance.workload`、`genome` |
| 作図の雛形 | `tools/plotting/plot_t2187_adaptive_consts.py` (`check_figure_layout`)、`plot_b10_extended_backoff.py` (外部 root + provenance) | §9 の fail-closed 雛形 |
| テストの雛形 | `orchestrator/tests/test_plot_b10_extended_backoff.py`、`test_b10_extended_figure_provenance.py` (`IZANAGI_B10_MEASUREMENT_ROOT`) | 実寸 fixture、外部 root の env var |
| 結果節の前例 | `docs/paper-story/claim-evidence/2026-08-26.md` §5 (limitations 統制稿)、`docs/paper-story/2026-09-02.md` §2 (f)・§8・§9 | 語法・区別の規律 |
| 図の入口 | `docs/paper-story/figures/README.md`、`tools/plotting/README.md` | 行追加、caption、再現コマンド |

## 実測値 (親、2026-09-04、WAL `bench_done.payload` から。図・表はこれを再計算で出す)

| cell | genome | tps 5 標本 | median | cv | abort_rate |
|---|---|---|---:|---:|---:|
| rr5-stock | BACK_OFF=0, BACKOFF_FIXED=-1 | 2715421, 2565367, 2496060, 2470354, 2527542 | 2527542 | 0.0378 | 0.7767 |
| rr5-fixed10 | BACK_OFF=1, BACKOFF_FIXED=10 | 1348263, 1355011, 1345709, 1387690, 1362175 | 1355011 | 0.0124 | 0.1189 |
| rr50-stock | BACK_OFF=0, BACKOFF_FIXED=-1 | 3894140, 3683727, 3636364, 3627357, 3662448 | 3662448 | 0.0298 | 0.6903 |
| rr50-fixed5 | BACK_OFF=1, BACKOFF_FIXED=5 | 1245023, 1196920, 1248603, 1261810, 1260445 | 1248603 | 0.0214 | 0.2048 |

workload 共通: threads 48、records 1,000,000、zipf 0.9、rmw 0、max_ope 10、extime 3、reps 5、trace-disabled 性能 build、
source commit `639c1dbad4…`、CCBench pin `511c953`、gcc/g++ 11.4.0、Pegasus bnode141 (rr5) / bnode064 (rr50)。
effects: rr5 = 1355011/2527542 − 1 = −0.46390…、rr50 = 1248603/3662448 − 1 = −0.65907… (certification.json と一致)。

## 受入・実測環境

- 受入全走: `tools/dev_wave_wait.py acceptance -- python3 tools/run_tests.py` (投入先は runner の自動判定、混雑時は D612 の上書き)。
- 変異走: `tools/mutation_harness.py` (probe → 本走、`--runner-mode dispatch`)。生成器・テストが対象。
- 作図: login node (pegasus02、matplotlib 3.10.9 / numpy 2.2.6)。計測機 (計算ノード) では走らせない。
- DW-G05: 放置時に変わる成果物は「論文の結果節に A-2 の negative result が無い」ことだけで、certified 選択・台帳・受理集合は変わらない。
