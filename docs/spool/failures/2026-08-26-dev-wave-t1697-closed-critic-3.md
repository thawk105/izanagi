---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1697-closed-critic
seq: 3
---

## 新規

### {{F:global-subprocess-patch-hijacks-production-git}}. test double の大域差し替えが、無関係な production の subprocess 呼び出しを横取りした [テスト代表性] [計測汚染]

- 事象: 新設 test が `unittest.mock.patch.object(C.subprocess, "run", fake_runner)` で
  **process 全体の `subprocess.run`** を差し替えた。`C.subprocess` は共有モジュール本体であり、
  patch は test の対象範囲を越える。結果、campaign 受理検査が内部で呼ぶ
  `orchestrator/campaign/contract_loader_binding.py` の `git rev-parse --show-toplevel` まで
  fake CLI の envelope JSON を返し、`contract-loader-root-error: Git top-level 出力が一意でない`
  で 8 件が赤になった。
- 根本原因: certified 判定を「`runner is subprocess.run` の同一性」で行う設計にしたため、
  certified 経路を試すには大域の `subprocess.run` を差し替えるしかない、と実装子が判断した。
  **狭い seam を用意しないまま同一性検査を課したこと**が原因である。
- **診断が難しい形をしている:** 赤の文言 (`Git top-level 出力が一意でない`) は git 側の
  環境異常に見え、login node では同じ関数が正常に解決する。**計算ノード固有の外乱に
  見えるが、実際は自分の test double が原因である。** 特定は `pytest --showlocals` で
  `raw_toplevel` の実値を採り、それが fake envelope JSON であることを直接見て確定した。
- 恒久対応: {{D:b4-certified-receipt-has-no-injection-seam}} — certified 経路から注入口を
  全廃し、注入は test-only 入口へ分離した。共有モジュール (`subprocess` / `shutil`) の
  属性差し替えを test から 0 箇所にした。
- 再発検知: 同 wave 内で **2 度発生した** (最初の実装と、その後の検出力補強)。
  2 度目は親が焦点走を実走して 1 件の赤で捕捉し、当該 test を取り下げた。
  検査は「変更した test file の焦点走を計算ノードで必ず実走する」ことに依存しており、
  静的レビュー 3 本はいずれも 1 度目を検出しなかった。
