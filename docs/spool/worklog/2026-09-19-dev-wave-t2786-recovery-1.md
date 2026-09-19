---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-19
wave: dev-wave-t2786-recovery
seq: 1
title: [T-2786] 中断測定を回収しt080共有base構築の実体化・発行・待ちを3ブロックで観測した (docs-only、branch worktree-dev-wave-t2786-recovery)
---

## 本文

- ユーザー依頼「中断測定の回収」で 1 wave。block1 (9492.nqsv) の 3 走却下を原本で判別し、2 件とも probe 欠陥
  (analyzer が marker 単位 group_to_workers を 1 群 1 worker と誤想定、plugin の P 配線検査が execnet 別名前空間の class に
  `isinstance` で必ず失敗) と確定。測定の実態ではないので隔離 Codex author (fix2、`2277c8236`) で修正し、事前登録の置換
  1 ブロックを block1 → block4 (ALP) に使った。詳細と数値は
  `output/insights/2026-09-19/t2786-base-decomposition-recovery/README.md`。
- 記録用 wave 木は main `a99425b66` からの fresh worktree。測定木 `7975385b5` は resume gate NG (main が 41 commit 先、
  T-2724 の shared-base key 5 要素化を含む) のため事前登録の固定 source として据え置き、記録だけ wave 木へ書いた。
- 段 2/3 は前 wave の plan/consult を流用 (骨格同一)。段 6 レビュー 2 本: A は fix2 に must 0、親の P smoke 案に must 1
  (事前登録外の 13 走目、`_one` 直呼びは 1200 秒制限と process group 回収を通らない) → real・採用し smoke を撤回。B は GO。
- 検証: probe test 20 本は計算ノード (10725) で 20 passed。変異 (10748) は baseline 緑、M1〜M6 完全一致 KILLED、
  M7 は KILLED だが失敗 node が期待 1 に対し 4 (同 fixture 族の負例が先に marker 拒否へ当たる) で DW-M08 の MISMATCH。
  初回結果を erratum として残し期待集合 4 node で再登録・再走 (11218) し、M1〜M7 の 7 件が完全一致 KILLED。fix2 の analyzer は
  block1 A/L 原本を受理し、注入した runtime 単位分割を拒否 (実データ照合)。
- 測定: block4 ALP (10758)、block2 LPA (10866)、block3 PAL (10958) の 9 走全部 valid。Wtotal 中央値は A 395.7 秒、
  L 709.4 秒 (3/3 とも A より 287〜329 秒遅い = 観測差)、P 405.4 秒 (3/3 とも 10% 未満 = 変化なし)。改善は成立しない。
  内訳は発行 subprocess 約 65 秒・直下 git 約 11 秒が一定で、伸びるのは copy 配置 (他 test と同時なら 80〜112 秒、
  それ以外は 28〜35 秒)。
- 計器欠陥の型は F649 の再発 (合成 fixture だけで緑、実体を通さず)。failures fragment に再発追記。新規 D なし。
- 他 wave の同時 job は各走の activity に記録。各 block の開始時 node loadavg (1 分) は 0.2〜1.1、他 user の活動 process 0。
- push・remote 操作なし。probe は job dir と bundle に置き repo へ入れない。mutation2 (10742) は scratch dir 未作成で
  rc=125 (5 秒) の空振り 1 回。dev-wave 改善候補は段 8 で 1 件を docs へ統合せず候補記録に留めた (詳細は本文末尾)。
- 段 8: 候補「probe の validity 述語は本番の検証コードと実データ 1 走で照合する」は F649 の恒久対応 (DW-S05-C の実体名指し)
  と段 6 レンズの既存節で意味が覆われるため新節を足さず、再発追記だけにした。

## 次の一手差分

### 完了

- [T-2786] t080 共有 base 構築の内訳・並行度・順序を 7975385b5 の replica で 3 ブロック (9 走) 実測した。発行 subprocess
  約 65 秒と git 約 11 秒は一定、伸びるのは copy 配置 (他 test と同時で 80〜112 秒、それ以外 28〜35 秒)。builder 同時 1 本 (L) は
  3/3 で悪化、collection 前の先行構築 (P) は 3/3 で変化なし。採用候補なし。残る余地と再測定条件は insight §7 に提案として置く。
  remaining: none
  base: 570fb57e15db11ba21e691c70ec9af5d58719f949ca84c986a80336b449c139f
