---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-26
wave: worktree-t2850-trial-run
seq: 1
title: [T-2850] 試走 block 1 の欠測 3 本の原因を確かめ、block 2・3 の投入を止めて、正しさを弱めずに費用を削る案を実測で比べた (docs のみ、branch worktree-t2850-trial-run)
---

## 本文

- 経過: 2026-09-23 の試走 wave は block 1 の 6 job (21512〜21517) を投入した後に session が消えた。2026-09-26 に再開し、rc=1 の 3 本の原因を一次資料で確かめた。
  random・sweep は系列開始 stock の bench 前の静定待ち (1 分 load ≤ 4.0 を最大 20 s) が時間切れで品質欠測 → `stock-unestablished`。llm は原提案 2 の親 session が
  週次上限の 429 で即終了し、2,702.7 s 待って `proposal-wait-timeout`。基盤設計 §4.6 項 1・§5.6 と事前登録 §5 により 3 本とも欠測で、再投入しない。
- ユーザー指示 (next-tasks session の中継、2026-09-26): block 2・3 を投入せず、費用を削る案を実測で比べ、確認を取ってから投入する。同種の B-5 本走の見積りへの発言は逐語で insight §0。
  試走の既承認 (write-heavy 42.4〜60.6 node 時間) は差し戻し扱い。block 2・3 は投入していない。
- 実測: 評価 1 回の約 91 % が正しさの検証。検証の trace 5 本を同じ node で同時に検査すると、判定を全件一致させたまま検査の wall が 0.24〜0.26 倍 (wh stock 177.8→42.8 s、
  rh stock 640.5→166.2 s、wh B0-L-W0 396.8→95.0 s)。同時検査の直後は load が 4.3〜11.1 に上がり、4.0 以下まで 3〜61 s かかるので、並列化は静定待ちの延長と組でしか使えない。
  測定は 4 job・0.75 node 時間 (2 node 時間未満のため確認不要の範囲)。B-5 側の依頼で rh B0-L-W0 の 1 job を同じ木から投げた (B-5 側の枠)。
- 図 1 枚 (1 手法の 3 系列) あたり: 今のまま 非 LLM 7.1・LLM 9.3〜26.6 node 時間、(b) 検証の同時化 2.6〜3.2・4.7〜22.7、(a)+(b) 2.6〜3.2。試走全体は 40.8〜58.2 → 16.3〜37.0 (b)・14.2〜17.5 (a+b)。
  記録は `output/insights/2026-09-26/t2850-trial-pause-cost-options/README.md`。
- near miss: 測定で「固定 8 µs の候補」を cmake define だけで指定し、stock と同じ build を測った (F707 の再発、fragment 同 wave)。取引数の一致で気づき、stock の再現として扱った。
- 工数: 親 1 (manager)、Codex author 1 + fix 1 (repo 外の測定 script)。計算は測定 4 job 0.75 node 時間。

## 次の一手差分

### 更新

- [T-2850] **P1 (VLDB 差分分析 P3: 探索の独立反復と費用・成果の曲線)**: 事前登録 v1 `docs/search-repetition-trial-preregistration.md` (D2231)・追補 1 で、試走を S1-wh × 5 手法 × 3 系列 +
  block job 3 に縮めて発効させた ({{D:t2850-trial-effect}}、実装は `7ea9aa09d` に固定)。block 1 の 6 job は終了 (7.28 node 時間。random・sweep・llm の 3 系列は欠測)。
  **block 2・3 はユーザー指示で投入を止めた (2026-09-26)。** 残りは 3 つ。(1) ユーザーの確認: 正しさの検査を弱めずに費用を削る案 — (a) LLM の待ちを node の外へ、
  (b) 検証の trace 5 本を同じ node で同時に検査 (実測で検査の wall 0.24〜0.26 倍、判定一致、静定待ちを 60 s 以上へ延ばすのと組)、(c) 系列数・B・N_eval の縮小 (事前登録の改訂) —
  を図 1 枚あたりの node 時間で示して選んでもらう (`output/insights/2026-09-26/t2850-trial-pause-cost-options/README.md` §4)。(b)・(a) を採るなら実装を変える wave と追補が要り、
  block 1 は予備走として新しい実装で 3 block を走らせ直す (経過時間の軸が変わるので混ぜない)。(2) 試走の後: 事前登録 §8 の規則で T_c・対差 SD・課題の集合・系列数を計算して追補に書き、
  本比較の上限をユーザー確認してから投入する。(3) MOCC (S2)・policy IR (S3) は、その空間の最初の生成より前の追補で足す。
  **生成・選択には [T-2851] の留保条件を使わない** (`docs/unseen-condition-transfer-preregistration.md` §2.3・§3、D2223)。一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P3。
  base: bbc0411a80b63064229046afc10ca5ef01cecc129c3f0ef8f734f4b4a7c10512
