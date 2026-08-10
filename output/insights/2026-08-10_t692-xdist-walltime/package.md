# 裁定パッケージ — 受入全走の walltime 恒久策 ([T-692] R3 の実装 wave から)

wave: `dev-wave-t692-r3-xdist-walltime` / 2026-08-09〜08-10
一次資料: 同 job dir の `s1-measurement.md` / `analyze-out.md` / `s2-plan.md` /
`s3-lensA.md` / `s3-lensB.md` / `s4-ruling.md` / `s6-revA.md` / `s6-revB.md` / `s6-re.md` /
`mutation2-ledger.json` / `junit-baseline.xml`

---

## 1. 依頼と、実測が返した答え

依頼は「walltime 逼迫への**恒久策**として、並列化の可否・分離が必要なテスト群・所要短縮の実測を
伴う実装または択一パッケージを返す」だった。

**まず前提を 1 つ訂正する。** 受入 suite は**すでに pytest-xdist で並列実行されている**。
`tools/run_tests.py` が `--dist loadgroup` を既定付与し、計算ノードでは
`site_policy.default_test_jobs` が cap 無しで affinity 全数 = **48 worker** を使う。
したがって「並列化の可否」は導入の可否ではなく、現行分配の改善余地の問題だった。

**実測 (bnode055、7685 passed / 20 skipped、wall 1407.97 秒):**

| 指標 | 値 |
|---|---|
| testcase の直列総和 | 16534.55 秒 |
| 実測 wall | 1407.97 秒 |
| 実効並列度 | **11.74 worker 相当 = 48 の 24.5%** |
| `real-repo` group の直列和 | **1388.80 秒 / 43 node** |
| critical path 下界 max(最大 group, 総和/48) | **1388.80 秒** |

**wall は `real-repo` group の直列和でほぼ完全に説明できる** (差 19.17 秒)。
そしてその 96.0% はたった 2 node である。

- 680.23 秒 `test_s8b_binding_driftguards::test_run_block_broken_binding_manifest_refuses_and_writes_nothing`
- 653.50 秒 `test_s8b_oracle_driver::test_cli_subprocess_returns_rc_2_on_gate_refused`
- 残り 41 node の合計は 55.07 秒しかない

**worker は余っている。** 並列度を上げても下界は動かない (下界は最大 group が決める)。
2026-07-30 の `-n 48` = 205 秒 / `-n 32` = 207 秒という実測とも整合する。

## 2. 恒久策になるか — ならない

両者の正体は実 repo の **T-080 receipt 解決** である。`orchestrator/tests/real_repo_receipt_memo.py`
は「1 回 22.4 秒 = git subprocess 1845 本、**commit 数に比例**」と記録しているが、
commit と output が増えた現在は数百秒規模に膨らんでいる。

**1 走で解決は構造的に 2 回要る。**

1. 共有 memo 側 1 回 — flock + xdist run ID + HEAD で 1 セッション 1 回に畳まれる。
   ほかの worker はその完了を待つ (670 秒帯に約 16 node が並ぶのはこれと整合)。
2. production CLI 子プロセス 1 回 — `test_cli_subprocess_returns_rc_2_on_gate_refused` は
   CLI を別 interpreter で起動するため、`mock.patch` によるプロセス内 memo が伝播しない。
   **これは production の受理経路そのものなので、test 側 cache を注入して速くすることは
   規律 2 (正しさゲートを緩めない) に反する。**

したがって wall ≈ `2q + tail` (`q` = 解決 1 回のコスト、`q = Θ(commit 数 + output ファイル数)`)。
**xdist の分配をどう変えても `2q` は消えない。** 分配側の変更は一度きりの定数削減であり、
増加の傾きを変えない。段 3 のレンズ B も独立に同じ結論に達した
(「恒久策ではない。案 1 は増加率を変えない」)。

上限 2400 秒への到達は、tail 固定の楽観仮定でも `r ≒ 3.27` 倍、全項目が同率で増えるなら
`r ≒ 2.74` 倍で起きる。

## 3. 本 wave が実装したもの (裁定不要な部分)

正しさが明確に改善し、設計択一が割れない部分だけを実装した。

1. **[T-438] の閉鎖** — `test_ruleops.py` の実 checkout reader が
   `xdist_group(name="real_repo")` と表記ゆれで canonical `real-repo` と**別 group**になっており、
   実 submodule を patch する writer との相互排他が効いていなかった (2026-08-04 起票、未了)。
   canonical へ移した。**wall は実測 +69.45 秒。速さのために見送らない (規律 2)。**
2. **収集監査の強化** — 従来は marker の positional 引数しか見ておらず、kwargs 形・
   非 canonical 名・二重 marker・canonical node への手書き marker をすべて見逃していた。
   全 collected item を対象に形・個数・group 名集合・provenance を検査し、
   各々に合成負例の positive control を付けた。
3. **group 内順序の固定** — 独立解決を行う CLI node を先頭、共有 cache barrier をその次へ。
   `pytest_collection_finish` で並べ替え、pytest 本体の `--ff` / `--nf` の後でも効かせる。
   **順序は wall の性質であって D63 の排他ではない** (同一 group = 単一 worker で逐次実行)。

変異 matrix: 8 変異すべて検出、**SURVIVED 0** (KILLED 3 / MISMATCH 5)。
MISMATCH はいずれも「事前登録した node は落ちたうえで、もう 1 node も同時に落ちた」= 過剰決定で、
生存ではない。期待値を結果に合わせて書き換えることはしていない (DW-M03)。

## 4. 要裁定 (R-a 〜 R-e)

### R-a — 実 repo を読む ungrouped payer を D63 の競合閉包へ入れるか (最重要)

段 3 レンズ A と段 6 レビュー B が独立に Critical と判定した**既存の穴**である
(本 wave の変更が作ったものではない)。

`test_s8b_oracle_driver.py` の `_run()` 系 node は `root=ROOT` で
`verify_receipt` に到達し、`enumerate_repository_files` が
**untracked (`git ls-files --others`) と ccbench submodule を実際に列挙・読取する**
(`orchestrator/campaign/s8b_holdout_freeze.py:197-212`)。
memo が hit すれば読まないが、**miss した最初の 1 本は必ず読む**。
どの node がそれになるかは実行ごとに変わる。したがってこれらは D63 の閉包に入るべきだが、
現在は canonical group の外にいる。memo は cache path 不明・lock 失敗・store 失敗で
`_resolve_now()` へ **fail-open** する。

- **(a) 閉包へ寄せる** — R3 原案 (案 F) の文字どおりの実施。約 50 node を
  `real-repo` group へ入れる。同一プロセスになるので 2 本目以降は cache hit (2〜3 秒) になる。
  wall は概ね中立〜微増と予想されるが**未実測**。
- **(b) prewarm + fail-closed** — worker 起動前に runner が 1 回解決して cache を作り、
  session 中の miss を**赤にする** (fail-open を廃止)。session 中に実 repo を読む node が
  無くなるので閉包に入れずに済む。ただし prewarm 分 (`q`) が直列で critical path に乗る。
- **(c) reader/writer flock 化** — 理論下界は最良 (約 691 秒) だが **D63 の保証機構そのものの
  置換**であり、分類漏れ 1 件で偽緑を作る。段 2 の子も段 4 の親も落とした。
- **(d) 何もしない** — 穴を既知として残す。

**親の推奨: (b)。** 閉包を広げずに fail-open を消せる唯一の案であり、
`q` の短縮 (下記 R-c) と効果が合成できる。ただし wall は縮まない。

### R-b — s8c candidate 3 node を canonical group へ寄せるか

R3 の射程内。本 wave では並行 wave `dev-wave-t553-git-budget` が同ファイルを編集所有中だったため
外した。**その wave は 2026-08-10 に land し、所有は解けている。**

- 値段は実測 **+58.35 秒**。
- ただし t553 の git 時間予算の定数は**現行の group 構成下での並行度を前提に実測**されている。
  group を移すと前提が変わるため、同時に動かすべきではないと親は判断した。

### R-c — `q` (T-080 receipt 解決) の短縮をどう位置づけるか

**これが唯一の恒久策である。** 並行 wave `dev-wave-suite-floor-recheck` が
`_any_history_touches_path` の短縮を所有しており、descendant 数が
2026-07-31 の 298 → 2026-08-09 の 1529 (5.13 倍) に増えたことを実測している。

`C' = C - ΔC`、`M' = M - ΔM` として wall ≈ `max(C', M') + tail`。
**片方だけ短縮しても支配項が入れ替わるだけで効果が出ない。** 両方に効く短縮が要る。

### R-d — `DEFAULT_WALLTIME` (00:40:00) を上げるか

`tools/pegasus/dispatch_compute.py:28` の固定値で、`run_tests.py` は `--walltime` を渡さないため
**呼び出し側から上げられない**。上げても消費 1408 秒は縮まず、期限が延びるだけである。
根治ではないが、R-c が効くまでの**時間稼ぎ**としては有効。

### R-e — 2 回目の解決 (production CLI 子プロセス) を無くす設計変更を認めるか

wall の下界を `2q` から `q` へ落とす唯一の道。ただし
`test_cli_subprocess_returns_rc_2_on_gate_refused` は production CLI の受理経路を
実プロセスで検査する positive control であり、ここに test 側 cache を注入するのは
**規律 2 に反する**。認めるとすれば「production 側に正当な cache を持たせる」設計変更であり、
受理集合と proof chain に触るため単独の裁定が要る。

## 5. 主張しないこと

- 本 wave の変更で wall が縮むこと。**縮まない見込みである** ([T-438] の +69.45 秒があるため)。
  実測値は worklog に記録する。
- 段 2 が出した「約 876 秒」という期待値。段 3 の両レンズが「同時開始を仮定した条件値」と
  判定し、非重複なら 1529.17 秒になると計算した。採用根拠にしていない。
- ログインノードで測った 427.58 秒を計算ノードの値として使うこと (段 3 レンズ A が指摘、撤回済み)。
- 670 秒帯が共有解決の待ちであると**確定**したこと。開始時刻と lock owner が記録されていないため、
  帰属は整合するが確定していない。
