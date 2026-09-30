# 段 6 追補裁定: local main 17995a4fe の取り込み (merge2)

- wave HEAD: bd6284c427a819e0864631e3ba627f06095c2e1f
- local main: 17995a4fea1243b1bd1c97f12f02c111821ffb66 (VHash hot block (md_23、`orchestrator/campaign/vhash_cicada_hot_block.py`) などが着地)
- merge-base: /work/SFC/tanab/tmp/vhash-ro-gc-publish-2026-09-29/merge2/base.txt
- 受入全走の終端 merge が 7 file の衝突で rc=70。合成は親の手作業でなく Codex author の fix 子が書く (T-2228 型)。

## 事実
- 衝突 7 file (13 箇所) はすべて「両 wave が同じ登録簿の同じ位置へ別の項目を足した」型:
  condition_meaning_gate.py (macro 登録 3+3)、materializer_admission.py (build 関数 1+1)、orchestrator/tests/README.md (pytest 専用 allowlist 1+1)、
  test_ccbench_spawn_sites.py (spawn site 3+4、wave の sink 分類 test 1 本)、test_condition_meaning_gate.py (macro 集合 4 箇所)、
  test_p3_build_authority_cli.py (2 箇所)、test_screening_driver.py (2 箇所)。
- **自動合成の罠:** 両 wave が同じ件数 pin を同じ値へ書き換えたため (例: 55→58、51→54、52→55、45→48、65→68、69→72)、
  git は衝突なしで 1 回分だけ残す。本来は両 wave の追加の合算が要る。screening_driver.py は両側の既定値 3+3 が残っている (自動合成で正しい)。

## 裁定 (FM-1〜FM-3)
- **FM-1 (和集合):** 衝突箇所はすべて main 側と wave 側の項目を両方残す。どちらも削らない・書き換えない・重複させない。並び順は周辺の慣行に従う。
- **FM-2 (件数 pin の再導出):** 7 file と screening_driver.py の中で、macro 集合・build sink 集合・spawn site 集合・define 交差表の分類件数に依存する
  全ての件数 pin と exact 集合 (自動合成された箇所を含む、wave 側の `test_ro_gc_publish_build_sink_uses_complete_condition_gate_family` と
  main 側の hot block 関連 test を含む) を列挙し、**合成後のコードから値を導出して**書く。「+3 を足す」と機械的に決めない
  (例: 新 macro が交差表でどの sink に対して covered / proven-unreachable / deferred になるかは sink ごとに違う)。導出根拠を報告に書く。
- **FM-3 (受理集合を動かさない):** gate の受理・拒否の意味、既存 test の期待のうち件数・集合以外の部分、driver・patch・model は変えない。
  main 側・wave 側いずれの登録も落とさない。

## 検査
- 子は login で pytest を走らせられない。親が合成後の tip で計算ノードの焦点走を回す (test_ccbench_spawn_sites・test_condition_meaning_gate・
  test_p3_build_authority_cli・test_screening_driver・test_p3_s4_loop・test_vhash_ro_gc_publish・main 側の hot block test)。
- merge commit には Codex author 行と claude integrator 行の 2 trailer を付ける。
