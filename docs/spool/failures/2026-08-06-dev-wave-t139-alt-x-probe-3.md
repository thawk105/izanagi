---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-06
wave: dev-wave-t139-alt-x-probe
seq: 3
---

## 新規

### {{F:probe-clean-tree-scheduler-droppings}}. scheduler が前 job の出力を repo root へ残し、次の job の clean-tree 検査が発火した [手順漏れ]

- 事象: probe job を再投入したところ、性能段の手前で `pre_performance_infra_failure` (rc=3、6 秒)
  になった。原因は、直前 job の標準出力・標準エラーが submit directory (= repo root) へ書かれ、
  untracked として残っていたことである。job 自身の clean-tree 検査が正しく fail-closed した。
- 根本原因: PBS は `-o` / `-e` を指定しないと submit directory へ出力する。probe が実走を
  commit へ束縛して clean-tree を要求する設計にした結果、**job の出力自体が次の job の前提を壊す**
  構造になった。scheduler 出力の置き場を投入手順が決めていなかった。
- 恒久対応: 投入時に `-o` / `-e` を repo 外の wave directory の**ファイル**へ向ける
  (directory を渡すと `NQScrereq: [BSV EINVAL] Not a regular file.` で受理されない)。
  script 内に絶対 path を書く案は採らない — 機体固有値を repo へ持ち込むため。
  手順は `docs/pegasus-runbook.md` の投入前チェックリストに従う。
- 再発検知: clean-tree 検査が発火した job は terminal state に
  `pre_performance_infra_failure` を残す。投入前に `git status --porcelain --untracked-files=all`
  が空であることを確認する。

### {{F:local-single-statement-dependency}}. `local` 一文内で先行代入を参照し `set -u` で実走が停止した [誤前提]

- 事象: probe job が投入 5 秒後に `destination: unbound variable` で停止した。
  該当は `local relative=$1 destination=$2 tmp="$destination.tmp"`。bash は `local` の全引数を
  builtin 実行**前**に展開するため、同じ文の中で先行する代入結果を参照できない。
  同型が driver 側にもう 1 件あった。
- 根本原因: 静的検査で検出できない形である。`bash -n` は通り、実装子は PBS を実走できず、
  親も機械防壁によりログインノードで probe を実行できないため、計算ノードで初めて表面化した。
  **「静的に緑」と「実走で緑」の差が構造的に残る面である。**
- 恒久対応: 両 script の `local` / `declare` / `readonly` / `export` を全走査し、同一文内依存を
  0 件にした。実装子の prompt に、`set -u` 下での最小再現 (修正前が落ち修正後が通ること) を
  実走して示すことを要求した。
- 再発検知: 実行時のみ表面化する形は、計算ノードでの実走が唯一の検査面である。probe の
  terminal state を必ず読み、`pre_performance_infra_failure` の detail から rc を特定する。

## 再発

### F132

- **再発: 2026-08-06** ([T-139] 代替 X probe wave、独立 2 例目)。使い捨て probe の driver が
  78 行から約 600 行へ、PBS が 55 行から約 330 行へ膨張した。**段 4 が規模上限を課しておらず、
  fix prompt へも継承されなかった**という根本原因が F132 と同一である。fix は所見を閉じる方向へ
  最大化し、規模の制約を知らないまま最も堅い実装を選んだ。本 wave では fix 巡数が上限に達しており、
  検査を落とす縮約は正しさ側を弱めるため実施していない。**独立 2 例が揃ったので、
  `DW-G03` により族全体への制度化を裁定へ返す。**
