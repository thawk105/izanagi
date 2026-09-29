# 段 1 brief — [T-2853] R2 fig6 単位 (A-2 の測り直し、現行 policy 5 node)

- 研究前進: 再現パッケージ R2 の図単位の 2 本目 (fig8b に続く)。論文 A-2 の値 (fig6、ComSys では表) の測定設計 (stock `BACK_OFF=0` 対 fixed 10 µs (rr5) / 5 µs (rr50)、48 thread・100 万 record・Zipf 0.9・5 反復、legacy 1 + performance 5 の正しさ検査) を、現行 repo の driver `tools/pegasus/submit_paper_story_a2_certification.sh` と現行 policy (`scheduler.nodes = 5`、CCBench pin `6810666`) で 1 回測り直す。完了判定 = 2 job が完走し finish-group・collect の結果 (certification、正しさ、効果) と原 attempt `t2364-20260907b` の値の対照表・R2 の図が insight に載る (失敗・拒否でもそのまま載る)。
- scope: (1) 投入前の地位の固定 (insight §0 を投入前に commit)、(2) 投入 (ユーザー確認後)、(3) finish-group と collect (repo 外の一時 root へ)、(4) 同じ生成器 `tools/plotting/plot_a2_certification.py` (bytes 不変) で R2 の図と対照表を repo 外 wrapper から描く、(5) insight と worklog fragment。gate・検査・台帳・一般化・driver/生成器の変更は scope 外。
- 確定済みユーザー裁定: 依頼 (投入単位は図 1 本、原と合成しない別 attempt、同じ生成器の図に並べる、2 node 時間以上ならユーザー確認後に投入、trace 保全口は渡せるなら使う、成果は insight のみ、規律 1・2 不変、本題だけ)。計算確認の線 = 1 タスクの job 合計 2 node 時間 (開発の検査を含む、/rulings 第 31 回 項 1)。
- 実測した前提:
  - 見積り ((a) Elapse): 同じ A-2・同じ 5 node 形の probe `t2489-20260918a` (request 4978 / 4979) が 680 + 728 s × 5 node = 7,040 node 秒 = **1.96 node 時間**。受入全走 1 回 ≈ 0.25 (DW-S04 は受入を免除しない、見積り) を足すと **≈ 2.21 → 確認が要る**。repro-rest の 1.70 は B-7 の Elapse を当てた試算で、同形の実測 t2489 の方が直接。
  - trace 保全口: driver の `qsub -v` は env を固定列挙し `IZANAGI_TRACE_ARCHIVE_ROOT` を渡す口が無い → 使わない (driver 変更が要るため)。正しさ検査は従来どおり job 内の trace 有効 build。
  - 生成器は新しい attempt の pin を CLI から受けないが、`main(argv, expected_hashes=...)` の Python seam がある → repo 外 wrapper で R2 の sha256 を渡す。
  - collect は `--repo-root/<tracked_destination>` に fresh leaf でしか書かない (既存なら拒否) → repo 外の一時 root を渡す (原 `output/insights/2026-09-07_t2364-…` は触れない)。
- 不変条件: 規律 1 (検証は trace 有効、計測は trace 無効の別 build・別走、driver の既存経路)・規律 2 (anomaly は即 reject、検査を緩めて描かない)・規律 7 (原 attempt・fig6・結果稿は bytes 不変、R2 で上書きしない)。R2 は原 attempt の置換でも合成対象でもない。
- (P1) 投入元は現行 main `035fc11fa` の detached checkout (repo 外 `/work/1/SFC/tanab/tmp/t2853-r2-fig6-20260929/submit-tree`)。wave 側の commit で job の HEAD 検査を壊さないため。親の provisional 裁定。
- (P2) 図の caption は生成器の既定文 (attempt ID・request・host・効果を記録から組む) のまま差し替えない。R2 の地位は insight §0 と図のファイル名 (`fig6_r2_…`) で示す。親の provisional 裁定。
- 成果物: `output/insights/2026-09-29/t2853-r2-fig6/README.md` (+ verbatim、figures)。測定原本は durable base `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/<attempt>`。wrapper は repo 外 (Codex author)。
- 分割: 段 2・3 省略の軽量版 (設計択一なし、正しさ防壁・受理集合を変えない)。実装面は repo 外 wrapper だけで段 5 Codex author 1 本、段 6 read-only レビュー 1 本 (一次資料から事実を書き起こす docs のため)。受入は 1 回。
- 実測環境: login (pegasus02) で投入・集計・描画、計算は gen_S 5 node × 2 job。
