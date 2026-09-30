## 作った file と役割

すべて [md32-scratch](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-d/md32-scratch/README.md) 配下に作成した。所有外の file、tracked file、gitlink は変更していない。

| file | 役割 |
|---|---|
| [diag-counters.patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-d/md32-scratch/diag-counters.patch) | 再検査起点差、promotion の試行・積載、後続 update の素通りを計数し、commit した tx の起点差を出力 |
| [v-ronly-nopromo.patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-d/md32-scratch/v-ronly-nopromo.patch) | 読み取り専用 tx の promotion 抑止 |
| [v-uaf-reorder.patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-d/md32-scratch/v-uaf-reorder.patch) | INSERT abort の索引削除→clean→解放 |
| [v-update-keep.patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-d/md32-scratch/v-update-keep.patch) | promotion 由来の write に後続 update の body を移す |
| [launch_promo_diag.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-d/md32-scratch/launch_promo_diag.py) | BASE・bundle・patch hash・verifier・compile 定義・実行 flags を束縛する計算ノード用 job |

Y0 の patch 順は **BASE → trace → trace-tpcc → promotion `#error` 除去 → counters**。Y1 は `#error` 除去後に ronly、次に counters。TPC-C の T1～T3 はそれぞれ BASE に対照 patch を一本だけ重ねる。

## 数え上げと見積り

**8 build・27 走行**。内訳は YCSB 2 build・8 走行、TPC-C Debug／ASan 2 build・3 走行、TPC-C Release 4 build・16 走行。事前見積りは **約 0.26～0.44 node 時間**、投入 walltime は 01:30:00。性能値は取らない。

## login で行った検査と結果（未実走の明記）

- Python 構文検査と `--dry-run` は rc=0。dry-run は BASE、bundle、patch hash、verifier checkout を照合した。
- `git -C external/ccbench apply --check` は ronly と uaf が rc=0。update と counters は、子木 submodule の現 HEAD が指定 BASE／計装後の preimage と異なるため rc=1。4 patch とも `git apply --stat` では構文を読めた。**指定順での適用成功は未確認**。
- BASE の未計装 `transaction.cc` 一 TU は、指定 genome macro と手元の依存 header を与えた `g++ -fsyntax-only` で rc=0。診断 patch 適用後の TU、全 build、計算ノードの全走行は**実装済み・未実走**。

## 予測（結果を見る前）

Y0 の巡回 witness に再検査起点差で通った commit tx が入り、Y1 の観測巡回が 0 なら P1 と F1 を支持する。`update_skip` が正なら F2 の発火条件を支持する。TPC-C は gdb の送出点、土台 ASan の最初の報告、T0～T3 の異常終了率を合わせて帰属する。

## 総括

診断と一要因対照の job 本体を用意した。**原因の帰属は計算ノード実走前には確定していない。** 巡回 0 が得られても観測 cell の結果として扱い、上限は indeterminate とする。