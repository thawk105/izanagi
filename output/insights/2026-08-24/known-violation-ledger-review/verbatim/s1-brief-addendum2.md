# 段 1 brief 追補 その 2 — 増加の実測と案 B の収量

`brief.md` および `brief-addendum.md` より新しい。矛盾する箇所は**この追補を優先**する。

## 1. 台帳は本当に増える一方か (growth.py)

`git log --first-parent main -- tools/check_ai_provenance.py` で main の本線だけを追い、
各時点の `KnownViolationSpec(` 出現数を数えた (現在値 53 は registry の 53 件と一致、方法は健全)。

**件数が変化した点: 増加 20 回、減少 2 回。** 意味のある減少は 1 回だけである。

- 2026-08-21T18:24 `5f1c0d6ccd` — 53 件 (このときの最大)
- 2026-08-21T22:49 `e0ac92775c` — **34 件 (−19)**。T-1479 の checker ロジック是正。
- 2026-08-22T08:50 `4c03b959a7` — 38 件 (−1)
- 2026-08-23T19:29 `bc927d03c4` — **53 件 (+7)**。元の水準へ復帰。

**−19 の是正は 44.7 時間で完全に食い潰された。** 34→53 は約 0.42 件/時 = **約 10 件/日**。
生成器を止めずに台帳だけ減らしても 2 日と持たない、という直接の実測である。

なお、`--first-parent` を付けないと merge topology のせいで ±21 の偽の増減が現れる。
本測定は `--first-parent` を使っている。

## 2. 案 B が実際に防げた件数 (prevented.py)

missing-codex-author 19 件について、その commit が変更した path 集合を調べ、
**変更 path が台帳 2 file (`tools/check_ai_provenance.py`,
`orchestrator/tests/test_check_ai_provenance.py`) だけに収まるもの**を数えた。
これらは「台帳を触ったこと以外に実装面の変更がない」commit であり、
台帳が 1 件 1 file のデータなら競合も実装面判定も発生しなかった。

**結果: 12 件 / 19 件。**
`a5b7045b12` `5823caf328` `8440a14850` `e39a8d4656` `3eaf2038ec` `387a1daab0`
`e86d363a87` `0c0f3e71b3` `bf92f327ca` `b9c07cc22d` `94815c5797` `3a5e5feb5f`

防げない 7 件のうち `311d463f89` は台帳 2 file に加えて `s8b_oracle_driver.py` を含むため
除外した (保守的な数え方)。残り 6 件は台帳と無関係の commit である。

12 件は台帳全体の 23%、かつ直近 4 日に増えた約 21 件の過半を占める。

## 3. 台帳データは 3 重化されている

親が現物を読んで確認した。同じ台帳内容が 3 箇所にある。

1. `tools/check_ai_provenance.py` の `KNOWN_PROVENANCE_VIOLATIONS` (正本)
2. `orchestrator/tests/test_check_ai_provenance.py:1861`
   `test_known_violation_ledger_matches_literal_entries` — `ruling` / `note` の**説明文まで**
   逐語複製 (約 430 行)
3. `orchestrator/tests/test_check_ai_provenance.py:2290`
   `test_known_violation_ledger_matches_real_commit_findings` — SHA と finding kind を再掲し、
   実 commit に対して `_audit_history()` を走らせて突き合わせる

3 は実際に受理集合を守る検査である (stale や取り違えを実 commit で捕える)。
2 が守っているものが 3 と別にあるかは、段 3 の sol レンズが判定する。
**3 箇所あることが、1 回の登録で複数 commit と複数の競合面を生む直接の原因である。**

## 4. 影響閉包 (親が全数検索で確認)

`KNOWN_PROVENANCE_VIOLATIONS` を参照する code は上記 1 と 2/3 の 2 file だけ。
checker CLI の呼び手 (`tools/dev_wave_land.py`, `tools/dev_wave_wait.py`,
`tools/pegasus/dispatch_compute.py`, `hooks/guard_bash.py`, `tools/task_run_check.py`,
`tools/codex_reasoning_ab.py`) は定数を触らない。

`_is_implementation_path()` を読んで確認した実装面の判定は
prefix (`orchestrator/ tools/ hooks/ .github/ .codex/ external/`)、
suffix (`.py .sh .bash .c .cc .cpp .cxx .h .hh .hpp .hxx .cmake .patch .diff`)、
basename (`CMakeLists.txt Makefile GNUmakefile pyproject.toml pytest.ini`) の 3 つ。
**`docs/` 配下の `.json` はどれにも当たらず、実装面ではない。**

## 5. 全数分類 (classify.py, classification.md)

53 件を生成器で分けた結果。
- G1 綴り誤り (2026-08-09 の単一事故、trailer literal 22 件同一): 22
- G2 role の綴り誤り (`role=fix`): 1
- G3 `--no-edit` merge で trailer ゼロ: 8
- G4 trailer 無し commit (revert / ユーザー直接 / 旧 docs): 2
- G5 台帳自身の競合を親が手解決した merge: 11
- G6 manager が実装面を直接 commit: 9

撤去可能は案 A の 4 件のみ。**49 件は履歴が不変である以上どの経路でも消せない。**

## 6. 実 commit 照合テストの被覆は部分的

`test_known_violation_ledger_matches_real_commit_findings` (test file 2290 行目、次の def は
2363 行目) が列挙する SHA は **31 件**であり、台帳 53 件の全部ではない。
残り 22 件を実 commit に対して検査しているのは、land 時に走る全史監査
(`check_ai_provenance.py` 本体、stale を rc=2 とする) だけである。
段 3 は「案 C で逐語ミラーを畳んだとき、この 22 件の被覆に穴が開くか」を判定すること。

## 7. 案 B と案 C は独立でない (親の分析。段 3 は反証を試みよ)

登録 1 回あたりの競合面は「registry tuple」と「逐語ミラー」の 2 つである
(実 commit 照合テストは 31 件で止まっており、最近の登録では更新されていないため競合面ではない)。

案 B は registry tuple を 1 件 1 file のデータへ移すが、**逐語ミラーが Python literal のまま残れば
登録のたびにそこを編集することになり、実装面の変更と競合が残る。** したがって
**案 B の効果は案 C (逐語ミラーを畳む) を伴って初めて出る。**
ミラーをデータから読む形へ書き換えても、それは同じデータを 2 度読むだけの恒真な検査になる。

⇒ 段 3 の中心的な問いは「案 C はゲートを緩めるか」である。緩めるなら案 B も成立しない。
