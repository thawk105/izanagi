# 段 1 brief — [T-813] 受入全走のノード横断シャーディング設計・実測評価

wave: dev-wave-t813-shard-eval / branch: worktree-dev-wave-t813-shard-eval / 2026-08-11

## scope

- **評価のみ。実装差分ゼロ。** 本番コード・受入 harness (`tools/run_tests.py` ほか) は 1 byte も編集しない。
- 成果物 = (1) 裁定パッケージ (repo 外 `ruling-package.md`)、(2) worklog fragment (spool)、
  (3) insights の実測逐語。probe・運転 script は repo 外 ([T-317] 裁定: repo へ入らない probe は親可)。
- **実装可否・機構案はユーザー裁定へ返して終端する** (受理集合の意味論に触るため)。

## 確定済みユーザー裁定 (前提)

- 受入窓は **(d) 直列維持 + 占有短縮**。(b) 楽観的並行 / (c) 独立 wave 同時受入 / (e) 窓 2 本化は不採用。
- 本 wave = (d3') の評価。飽和が見えたら (f) land train を別途裁定へ。
- 受入 lease は「受け入れる main に対して検査する」正しさの機構であり、直列の意味論は不変。

## 不変条件 (緩めない)

- I1. **受入の受理集合を保つ。** 分割後の合成結果が「既定 target を 1 回走らせた結果」と同じ受理判定を与えること。
- I2. 受入専用の事前検査 4 箇所 (`tools/run_tests.py` 594 / 632 / 705 / 1677) が、分割後も**全体として 1 回以上**発火すること。
- I3. 実 repo / 共有 submodule の相互排他 (D63/D258 の `real-repo` group) が分割後も成立すること。
- I4. 規律 2 — 性能のために正しさゲートを緩めない。「速いが受理集合が弱い」案は不採用。

## 成果物の形

裁定パッケージに次を必ず含める: (i) I1 の**定義**、(ii) 機構案 (argv 形状判定の置換案を含む) と各案の I1〜I4 充足、
(iii) 実測 (分割の決定性・rc 集約・ポイント・xdist 干渉・fail 帰属)、(iv) [T-810] 条件付き結論、(v) 未測定事項。

## 段 1 で実測した前提 (詳細は facts.md)

- **N1 (裁定パッケージの数値を更新):** 受入全走の wall は本日 15 本で **535.6〜566.4 秒** (中央値 ~546)。
  パッケージ §1 の「548〜1021 秒」は古い値の混在。占有 15〜25 分のうち全走は **約 9 分**であり、
  残りは main 取り込み・land・provenance 監査・待ち手の poll 粒度。**k 分割で縮むのは 9 分の部分だけ** (Amdahl)。
- **N2 (「ポイントほぼ不変」は未検証):** 1 job = 1 ノード全体 (affinity 全数 48 worker)。2026-08-09 実測の
  並列効率は 11.74 worker 相当 = **48 の 24.5%**。分割は確保コア数を k 倍にするので node×time は不変とは限らない。実測 arm で確かめる。
- **N3 (排他が割れる):** `real-repo` group は **13 file に跨る**。排他は「単一 runner invocation 内」(`run_tests.py` docstring 逐語) でしか成立しない。
- **N4 (形状判定):** 分割 9 形すべてが `_is_acceptance_run` = False。**xdist 多ホストの `--tx` / `--rsyncdir` も False**。
  一方 `--junitxml` / `-n` / `--dist loadgroup` は True のまま (= 非選択オプションは既に許容されている)。
- **N5 (最重要・分割の実害):** k=4 の実走で、**全走なら緑のテストが分割で赤になった** —
  `test_s8b_approved.py` の収集 ImportError (`No module named 'tests'`) と
  `test_profiler_directive.py::...role_policy_check` の `No module named 'codex_roles'`。
  suite は現状 **分割不変ではない**。I1 は機構ではなく suite 側の前提として成立していない。

## provisional 裁定 (P#: 攻撃対象)

- **(P1)** 分割単位は test file。nodeid 単位は argv 肥大と parametrize 再収集の不安定さで採らない。
- **(P2)** 排他 group を持つ file は group-atomic に 1 シャードへ束ねる (real-repo 13 file は不可分)。
- **(P3)** I1 の定義 = 「(a) シャードの collection の**和**が既定 target の collection と**集合として一致**し、
  (b) 各 nodeid がちょうど 1 シャードに属し、(c) 各シャードが受入専用 gate を通り、(d) 合成 rc = 全シャード rc の
  最大 (どれか非 0 なら非 0)、(e) 分割不変性 — 同じ nodeid の判定が分割の取り方に依存しない」。
  **(e) が現状破れている (N5)** ため、機構より先に suite 側の前提が要る。
- **(P4)** 形状判定の置換案は「argv 形状 → シャード集合の和が既定 target と一致する証明 (manifest)」。
  ただし N4 のとおり、**非選択オプションの allowlist 拡張 (`--tx` 等) なら受理集合を触らずに済む**代替がある。
- **(P5)** 本 wave は「実装しない」裁定で終端し、段 5・6 を飛ばす (4→7→8→9)。

## 並列分割方針 (子の使い方)

- 段 2 (plan) 1 本 / 段 3 (敵対) 2 本 = sol・luna。実装子は無し (実装差分ゼロ)。
- 親は実測 (probe arm base / k4count / 追加 arm) と裁定パッケージ執筆を担う。

## 成果物影響 (DW-G05)

本 wave を実装しない場合、成果物 (certified 選択・レポート・台帳) の値・受理集合・参照は**一切変わらない**。
変わるのは受入窓の待ち時間だけである。逆に、I1 を満たさないまま分割を実装すると
**「全走が緑」の意味が分割の取り方に依存する**ようになり、受理集合が壊れる (N5 が実例)。
