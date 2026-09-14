---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: dev-wave-t554-hook-wiring-skip-gate
seq: 1
title: [T-554] hook 配線テストの skip 撤去は裁定の 14 日前に済んでいた。hooks key 欠落時の赤を 2 経路で実測して閉じた (docs のみ、branch worktree-dev-wave-t554-hook-wiring-skip-gate)
---

## 本文

- **ユーザー直接起票の wave。** 依頼は D857 (2026-08-25 ユーザー裁定) の実施、すなわち
  「`.claude/settings.json` に `hooks` key が無いと skip するテストの skip 条件を撤去する」と
  「撤去後、hooks key を欠いた設定で実際に赤になることを確かめる」。
- **本題の撤去は 2026-08-11 の commit `d4d1e82c0` で既に済んでいた。** 同 commit が
  `orchestrator/tests/test_hooks.py` の `if "hooks" not in cfg: skip("hooks 未配線 ...")` を
  `assert "hooks" in cfg` へ置き換え、負例も同時に足している。
  `git merge-base --is-ancestor d4d1e82c0 refs/heads/main` は rc=0。
  **裁定 D857 は実装の 14 日後に出ている。** 起票は 2026-08-06
  (`docs/spool/FOLDED.md` の `T:hook-wiring-skip-gate`)、carry は archive の 300 番台から
  現行 worklog まで途切れず続いていた。**F35 の再発として記録した。**
- **撤去 commit の件名は carry の語を 1 つも含まないため、件名検索では出ない。**
  `git log --oneline -S'_assert_settings_json_wires_all_hooks' -- <file>` の pickaxe で初めて出た。
  済み carry を安く見つける手として記録する。
- **D857 の後半 (赤になることの確認) を 2 経路で実測した。** どちらも `.claude/settings.json` から
  `hooks` key だけを落とし、走らせた直後に `git checkout --` で戻す形で行った
  (`DW-O19`: 変異前 `--porcelain` 空、`git diff --stat` が対象 file 単独、復元後の sha256 照合)。
  - 経路 1 = テスト関数の直接呼び出し。`test_settings_json_wires_all_hooks` が
    `AssertionError: hooks 配線が消えている` で赤。
  - 経路 2 = pytest。`tools/run_tests.py` が計算ノードへ投げた走 (request 996918.nqsv、Elapse 10S) で
    `FAILED orchestrator/tests/test_hooks.py::test_settings_json_wires_all_hooks`、
    `1 failed, 1 passed in 4.11s`、失敗位置は `test_hooks.py:5066`。
  - 変異前の対照 (request 996885.nqsv) は `2 passed in 4.08s`。復元後の sha256 は変異前と一致し、
    `git diff --stat HEAD` は差分ゼロ。
- **経路 2 を足したのは段 3 の指摘による。** 親は当初「fixture を取らない関数なので pytest node と
  同じ経路」と書いたが、sol と luna が独立に「`conftest.py` に autouse fixture が複数あり、
  直接呼び出しの赤を pytest の赤と同一視できない」と指摘した。**採用して pytest でも実測した。**
- **段 3 の 2 レンズは、追加実装をしないという親の裁定を両方とも支持した。** 恒真性の所見はゼロ。
  luna は配線 helper の 8 個の assert を 1 つずつ当たり、どれも入力非依存に真になる式ではないことを
  表で示した。
- **親 brief の誤りを 3 件直した。** (1) 全数走査の hit を「2 件のみ」と書いたが、実際に数えると
  同じ検索は 11 件当たる。正しくは「hooks key を条件とする skip は 0 件、`test_hooks.py` に残る
  skip 呼び出しは submodule 未 init と template patch 未適用の 2 箇所」。
  (2) 上記の「pytest node と同じ経路」。(3) `orchestrator/tests/test_campaign.py:11362` の
  旧テスト名参照を「前提 gate」と書いたが、実際は docstring 内の「同形式」という比較で、
  そのテストを呼ぶ gate ではない。
- **scope 外と裁定した real 所見が 2 件ある。** どちらも両レンズが自ら scope 外と判定した。
  (1) 配線 helper は command 名と matcher の存在を別々に見るだけで対応関係を見ないため、
  Write と Bash の command を入れ替えても静的には全部通る。
  (2) 配線検査の緑は hook が実際に発火して拒否することの証明ではない。(2) は
  `hooks/README.md` が既知限界として自ら明記しているため、台帳へは移さない。
  (1) は D857 の射程外であり、依頼が「仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」と
  明示しているので実装しない。
- **luna が wave 中の main 前進を検出した。** 親が `7dc4ecc39` を記録した後に main が
  `0da89ce6e` へ、さらに `c2a28d67d` へ進んでいた。`--ff-only` で取り込んでから記録を書いた。
- **実装面の差分はゼロで、実装子を 1 本も起動していない。** 変異 matrix は `DW-S04` の
  「実装面の差分ゼロの wave だけ変異 matrix を免除する」に従って免除した。受入全走は免除せず実走した。
- **段 2 のプラン起草は省いた。** 実装が無く起草すべき plan が無いため。段 3 の敵対相談 2 本は
  省かずに回した。ユーザー裁定を「済」として閉じる判断だったので、独立の検査を残したかったため。
  `DW-C00` の軽量版より保守側の運用である。
- 子は段 3 の read-only codex 2 本 (sol / luna) だけ。実装子・fix 子・レビュー子はゼロ。
- **段 8 の改善候補は 3 件出たが、いずれも文書を変えないと裁定した。** (1) 済み carry を
  見つける pickaxe は F35 の再発記録へ入れた。`DW-S01` は既に「git / 成果物で済を照合」と
  命じていて F35 を指しているので、入口も reference も変えない。(2) login node で pytest を
  直に叩くと guard が拒否する件は、拒否文自身が `tools/run_tests.py` へ誘導するので
  手順の欠落ではない。(3) `tools/run_tests.py --help` が pytest の help を丸ごと出して
  runner 固有 option が埋もれる件は、実害が無いので候補どまりとする。

## 次の一手差分

### 完了

- [T-554] D857 の skip 撤去は 2026-08-11 の `d4d1e82c0` で済んでおり、hooks key を欠いた設定で
  `test_settings_json_wires_all_hooks` が赤になることを直接呼び出しと pytest の 2 経路で実測した。
  remaining: none
  base: adb15bc5a68b2e46a587f99a7ffccda44dacd09f2a74f19698ff9f9b80142c02

### 新規

- {{T:phase3-stale-hook-gate-name}} **P3・新規**: `docs/phase3.md` が hook 配線の前提 gate として
  `test_settings_json_wires_both_hooks` という現存しないテスト名を挙げている。現行名は
  `test_settings_json_wires_all_hooks`。名前で引くと空振りするので直す。成果物の値・受理集合・
  参照は変わらないため優先度は低い。`orchestrator/tests/test_campaign.py:11362` の同名参照は
  docstring 内の比較であって gate ではないので、対象に含めるかは着手時に判断する。
