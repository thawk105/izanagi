---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-17
wave: dev-wave-t2228-screening-liveness
seq: 3
---

## 新規

### {{F:child-required-input-absent-from-launch-env}}. 親が子 (launcher) の必須入力を、起動経路が実際に渡す env 集合と突き合わせずに仕様化した [誤前提] [手順漏れ]

- 事象: 計算ノードで正規 CLI を起動する job dir の launcher の author 仕様で、親が `PBS_JOBID` を
  必須入力 (未設定なら rc=2) にした。起動経路 `tools/pegasus/dispatch_compute.py --task generic` は
  clean env (`HOME LANG LANGUAGE LC_ALL LC_CTYPE LOGNAME PATH TZ USER` だけ) で子を起動し、
  `PBS_JOBID` を渡さない。そのまま投入していれば launcher は前提検査で必ず rc=2 になり、
  本題 (screening 関門) は 1 度も走らなかった。
- 根本原因: 親は段 1 brief に generic dispatch の clean env の鍵集合を書いていながら、段 5 の
  author 仕様を書くときに「子が要求する入力 × 起動経路が実際に渡す env」を突き合わせなかった。
  `DW-O13` (gate 入力の実在 — 設計前に入力が実成果物のどの field に存在するか確認する) を
  gate の述語にだけ適用し、一回限りの実行体の入力には適用しなかった。
- 検出経路: 段 6 の敵対レビュー 2 本が独立に `dispatch_compute.py` の `_CLEAN_CHILD_ENV_KEYS` /
  `_child_environment` を読んで must-fix にした。fix 1 巡 (`mktemp -d` で scratch を確保し job の帰属は
  dispatcher の receipt に委ねる) で閉じ、実害なし (near miss)。
- 恒久対応: `DW-O13` の適用対象に「子・launcher が要求する env 入力」を含めて読む。memory
  `child-required-inputs-must-match-launch-env` (子の必須入力は起動経路の実 env 集合 — clean env なら
  その allowlist — と段 5 仕様の前に突き合わせる。dispatch 経由なら `_CLEAN_CHILD_ENV_KEYS` と task の
  `env_allowlist` を実測して brief と仕様の両方に書く)。
- 再発検知: `DW-S06-A` の敵対レビュー 2 本が「dispatch 環境との整合」を攻撃面に持つこと。
  本件はその契約が働いた。

## 再発

### F287

- **再発: 2026-09-17** — [T-2228] wave で、official output root を job dir 配下に置くにあたり
  「`/work/1/SFC/tanab/dev-wave-jobs/` 配下に `.git` 祖先が無い」を `ls -la | head -5` で切った出力から
  段 1 brief に書いた。実際は `/work/1/SFC/tanab/dev-wave-jobs/.git` (空 directory) があり、
  `layout._has_git_ancestor` が official root を拒否して attempt a (`2319.nqsv`) が screening 関門に
  到達する前に赤になった。段 3・段 6 のレンズはいずれも「親確認済み」を前提にしており、検出したのは
  実走そのものだった (計算ノード job 1 本、46 秒を消費)。**「無い」の実測は全件を見ないと成立しない**型の
  再発で、是正は各祖先を 1 段ずつ `ls -ld` で実測してから別 root へ回避した。
