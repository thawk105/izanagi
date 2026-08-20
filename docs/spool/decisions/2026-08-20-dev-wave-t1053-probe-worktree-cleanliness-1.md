---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t1053-probe-worktree-cleanliness
seq: 1
---

## {{D:probe-cleanliness-bytecode-propagation-confirmed}}. probe worktree清浄性検査のPYTHONDONTWRITEBYTECODE伝播は現行コードで完結していると確認し、追加のロジック変更を見送る

**決定:** `tools/check_acceptance_reds.py` のprobe worktree清浄性検査が計算ノードdispatch由来の
bytecodeキャッシュ残骸で失敗する問題 (T-1053系) について、現行main HEAD上のコードには
PYTHONDONTWRITEBYTECODE伝播の欠陥が無いと3つの独立方法で確認し、追加のロジック変更は行わない。

**理由:**
- 親が現行HEAD上でcheck_acceptance_reds.pyの実dispatch経路
  (`_default_collection_runner`/`_default_node_runner`相当) を4回再現実験し、0/4で残骸を
  再現しなかった。うち1回はPegasus `gen_S` キュー同時34job走行という重負荷下でも再現しなかった。
- 段2 codex (read-only、reasoning=max) が `tools/check_acceptance_reds.py` から
  `tools/pegasus/dispatch_compute.py` までの伝播経路を全file:lineで再読し、欠陥なしと確認した。
- 段3敵対レンズの一つが独立に、実際にインストール済みのexecnet/xdistパッケージのソース
  (`execnet/gateway_io.py`、`xdist/workermanage.py`、`xdist/remote.py`) を直接readし、
  workerプロセス起動時にPYTHONDONTWRITEBYTECODEやbytecode cache設定を上書きする経路が
  無いことを確認した。
- 伝播を担う2つの修正 (env allowlistへの追加、dispatch子環境のsetdefault fallback追加) は、
  いずれもT-183由来の受入試行 (2026-08-20 10:27〜) より前にmainへ着地しており、
  「tested-mainが古かったため反映されていなかった」という説明は実測
  (`git merge-base --is-ancestor`) で棄却される。

**却下した選択肢:**
- 証拠なしに追加のenv伝播ロジックを実装する — 3独立方法が一致して欠陥なしと確認した状況で
  仮説だけに基づく変更を加えるのは過剰実装であり、実際の原因究明を妨げる。
- 診断改善を見送り再現待ちにする — 診断が無いままでは次回の再現時も同じ手動調査を
  繰り返すことになるため、診断改善 (どの汚染pathで失敗したかをメッセージへ含める) を
  優先して実装した。
