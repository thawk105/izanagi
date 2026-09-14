---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: dev-wave-t1643-has-include-pair
seq: 1
title: [T-1643] `__has_include` 族の実 pair を login と計算ノードで実測し、対照表を残した (docs のみ、branch worktree-dev-wave-t1643-has-include-pair、変異 matrix = 免除 (実装面差分ゼロ))
---

## 本文

- **成果物は対照表そのもの** = `output/insights/2026-09-14/t1643-has-include-real-pair/README.md`。
  子の逐語は同 `verbatim/`。raw JSON は 36 MB / 20 MB あるため repo へ入れず job dir
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1643-has-include-pair/` に保全した (entry 1483 の
  リポジトリ膨張の実測を踏まえた判断)。
- **依頼の前提が 1 つ覆り、段 1 brief に出して段 4 で再裁定した。** 依頼は
  「g++-13 と admission toolchain の実 pair」を求めたが、**`g++-13` は login `pegasus02` にも
  計算ノード `bnode009` にも存在しない** (今日 probe で両方を探索。台帳 `docs/failures.md:8023`
  と D293 の過去記録とも一致)。D293 は「固定要求のまま `g++-13` を Pegasus へ用意する」を
  却下済みなので、**不在そのものを対照表の 1 行として記録**し、実在する compiler で測った。
- **段 3 の敵対相談 2 本の所見は全件 real で、refuted はゼロだった。** 親 brief を 6 点訂正した。
  特に (a)「この食い違いは g++-12 で 1 式だけ実測済み」は過小で、既存 T-148 記録には literal
  間接形と `<atomic>` の preprocess error もある。(b)「g++-13 は compute にも無い」は
  **過去の台帳記録を今日の事実へ昇格させていた**ので撤回し、今日 probe で実測し直した。
- **compute 実測は F660 に当たらないと判明した。** 段 3 luna が既登録の
  `tools/pegasus/dispatch_compute.py --task generic` 経路を見つけ、親が runbook §「投げ先」(D895)
  と main 側 `admission_registry.json` (`class=local-ok`) の現物で検算した。probe は
  `tools/t1643_*.py` で `tools/pegasus/` 配下の新規実行体ではないため、登録も main 着地も要らない。
  **実際に rc=0 で通った** (request `997000.nqsv`、bnode009、Elapse 16S、child rc=0)。
  `--walltime` は **HH:MM:SS 形式**でないと rc=16 (setup-failure) になる。
- **login と compute で対照表・guard 件数が完全に一致した。** `g++` の実体は両所で
  SHA-256 `2360901d864c…` の同一 binary だった。`g++` と `g++-11` も同一実体なので、
  表の 3 名称は **2 実体**であり `DW-G03` の独立 2 例には数えない。
- **`g++-9` は測っていない** (「差が無かった」ではない)。checker の `BUILD_FLAGS` にある
  `-std=c++20` を認識せず (`did you mean '-std=c++2a'?`)、全 cell が失敗した。
  対照 820 件中 312 件の不成立はすべて `g++-9` と `g++-13` に局在する。
- **`controls_passed = false` / `conclusion = null` のまま閉じた。** 段 4 裁定が
  「対照が不成立なら結論を出さない」と定めたため、成立列 (`g++` / `g++-11` / `g++-12`) の
  限定観測は事実として記載し、**wave 全体の結論は保留**した。
- **段 6 レビューは sol が must-fix ゼロ、luna が成果物の文面に対する must-fix 7 件。** luna の
  7 件目 (compute 未測の書き方) は、luna 起動後に親が compute 実測を完了したため前提が変わり、
  「未測」ではなく「`generic` の compute 環境での観測であり本番 admission の呼出しには
  対応づけていない」という限定へ置き換えた。他の 6 件と nit 2 件はそのまま成果物へ反映した。
- **セッション異常:** 段 6 の投入で `--lane` を `--stage review` に付けて rc=2 即死した
  (`--lane は --stage consult でだけ指定できる`)。段 2・3・5 では `--dry-run` で argv を
  先に検査していたのに段 6 で省いたのが原因。`DW-O01` は「段別 flag 違反は rc=2 即死」と
  既に書いている。log path を変えて再投入し、以後は全段で `--dry-run` を先に通した。
- **エージェント工数:** codex 子 6 本 (段 2 plan 1、段 3 consult 2、段 5 author 1、段 6 review 2)。
  親は login probe 1 走、compute dispatch 2 回 (1 回目は walltime 形式で rc=16)。実装子は
  `tools/t1643_has_include_pair_probe.py` (475 行) だけを書き、親が実行後に repo 外へ退避した。
  **main へ入る実装面の差分はゼロ**なので `DW-S04` により変異 matrix を免除した (受入全走は実走)。

## 次の一手差分

### carry

- [T-1642]

### 完了

- [T-1643] `__has_include` 族の実 pair を login `pegasus02` と計算ノード `bnode009` で実測し、
  対照表を `output/insights/2026-09-14/t1643-has-include-real-pair/README.md` に残した。
  `g++-13` が両所で不在であることも実測結果として表に残した (D293 が用意を却下済み)。
  remaining: none
  base: 0a46bdf229f8e6e7d41652a7eba3e5a124a073c6f8cc93ef05e245e596b4b0e0

### 新規

- {{T:has-include-comment-vs-observation}} **P3・新規**: `source_digest.py:372-373` のコメントと
  guard の拒否診断本文は `__has_include` が `-nostdinc` で「常に 0 に倒れる / dead 枝になる」と
  説明するが、**angle 形式では preprocess error (rc=1) になる**ことを実測した
  (`output/insights/2026-09-14/t1643-has-include-real-pair/README.md` §2)。
  どちらも fails-closed 側なので受理集合は変わらない。記述を実測に合わせるかを裁定する。
- {{T:legacy-branch-compiler-asymmetry}} **P2・新規**: `pipeline.py:1790` が site 選択した
  compiler を checker へ渡す一方、`common is None` の legacy 分岐 (`:2002`、`buildcache.py:3140`)
  は `cc/cxx` を渡さず既定 `g++-13` を使う。静的に確認できる非対称であり、到達可能性と
  既存防壁との関係を評価するか裁定する。
- {{T:nonrecursive-scan-boundary-reachability}} **P2・新規**: `source_digest.py:85` / `:1895` /
  `:1662` の非再帰な走査境界 (`EVOLVE_BLOCK_SOURCES` の 3 file、`#include` 行は除去) から
  許可された variant が、実際に別挙動・stock identity 継承へ到達するかは未証明である。
  到達例を実測するか、限界の明記で閉じるかを裁定する。
