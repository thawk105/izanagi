単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- 作業 root (read-only): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2`
- **親の段 1 brief (scope の正本)**: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/s1-brief.md`
- **契約の正本**: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md`
- 契約の追記訂正: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c2-derivation/contract-v3.1-erratum-1.md`
- 裁定 2 の原文: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c2-derivation/ruling-package.md`
- 直前単位 C2 の記録: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c2-derivation/README.md`
- **単位選択の相談結果 (既に済んだ検討。再導出しないこと)**: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/out-consult-unit.md`
- 6 単位分割の正本: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-01_t1946-t2107-registry-wiring-design/s4-adjudication-r2.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/CLAUDE.md`

# 段 2 — 単位 C3 の実装 plan を file:line 粒度で起草する

作業 root は read-only である。**書込み可能な tmp は無い。** したがって
**pytest 緑を要求しない。静的読解と grep による実測だけで結論を出す。**
テストの実走は親が行う。**走らせていないものを緑と書かないこと。**

**file を 1 つも作れない。** 成果物は**最終メッセージの本文へ全文を書く**こと。
「file へ書いた」と述べても親には届かない。

予算が尽きそうなら、**途中結論を下の出力形式どおりに書いて終わること** (無出力が最悪)。

## scope (段 1 brief が確定した 3 項)

1. campaign の直接計測経路を launcher の certified 入口 `launch_floor_attempt()` へ配線する。
2. production result を v4 (`RESULT_SCHEMA = LEGACY_RESULT_SCHEMA`) から既設 v5 契約
   (`RESULT_SCHEMA_V5`、attempt registry proof) へ切り替える。
3. 実 campaign 1 本で gate 入力の実値域を記録する。

## plan に必ず入れること

1. **file:line 粒度の変更計画。** 変更する各 file について、現状の該当行と、何をどう変えるかを書く。
   新設する symbol は名前・引数・戻り型まで決める。
2. **依存順。** 3 項の中で強制順序があるか。段 5 を 2 子へ割るときの素集合な所有 path 分割を提案する。
3. **pin 閉包 (DW-O09)。** この変更で bytes が変わりうる凍結成果物と、それを pin する台帳・test・
   trust root を**全列挙**する。path 検索だけでなく、role 名・xdist group 名・key 名・
   whole-file sha256・行番号で張る pin も探す。`test_frozen_artifacts.py` の `FROZEN_MANIFEST`、
   `test_official_perf_closure.py` の `_REVIEWED_PERF_FILES`、
   `test_reflux_formal_consumer.py` の AST 走査、`test_ccbench_spawn_sites.py` を必ず見る。
4. **producer write-path (DW-O10)。** 配線後の production 経路が書く file 種を棚卸しする。
5. **gate 入力の実在と値域 (DW-O13)。** `launch_floor_attempt()` が要求する各引数
   (`FloorAttemptReservation` / `FloorAttemptRegistryGenesis` / `FloorMeasurementCapture` /
   `post_probe` / `classified_at` / `terminal_builder`) を、campaign が実行時に持っている値から
   どう作るかを file:line で示す。**作れない引数があれば、それを名指しして止める。**
6. **変異候補。** 実装後に走らせる単独変異を 8-14 件、変異の内容と期待 kill node を対で挙げる。
   1 変異が 100 node 超を落とす過剰決定な候補は避ける。
7. **5 file 上限の判定。** 段 1 brief の (P1-2) は実装面 5 file 以内と仮定している。
   静的読解の結果が超えるなら、**超える file を名指しして、C3a (配線・v5 producer) と
   C3b (実 campaign・値域記録) への分割を推奨するかどうかを書く。**
8. **test 計画。** 新設・改修する test node を列挙する。正例と負例を分け、負例は
   「何を壊したら赤になるか」を 1 行で書く。既存 test の期待値は変えない。

## 禁止

- **実装しない。** patch も diff も出さない。file を作らない。
- 既存テストの期待値を変える計画を書かない。赤なら実装側が誤りとする。
- fake registry や injected `measure_fn` を「実値域の供給」と数える計画を書かない (契約 9 節)。
- launcher の perf 述語の新しい直接 call を作る計画を書かない (`_REVIEWED_PERF_FILES` の inventory が落ちる)。
- `attempt_registry_core.py` へ `aborted=False` keyword と `OriginSealed(False, ...)` を書く計画を書かない。
- `FORMULA_ID` を改版する計画を書かない (裁定 1 は未裁定)。
- 出力へ結合文字 U+0300〜U+036F を使わない。

## 出力形式

```
## 総括
(3-5 行)

## 変更計画 (file:line)

## 依存順と段 5 の所有分割

## pin 閉包の全列挙

## producer write-path

## gate 入力の実在と値域

## 変異候補 (内容 / 期待 kill node)

## 5 file 上限の判定

## test 計画 (正例 / 負例)

## 実装しないと判断したもの
```
