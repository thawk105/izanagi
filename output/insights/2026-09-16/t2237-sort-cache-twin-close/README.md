---
authority: none
default_effect: no-state-change
---

# [T-2237] sort 軸の文法版 cache 束縛 (D1548) — 双子 [T-2253] で着地済みの確認と段 1・段 4 の記録

wave `worktree-dev-wave-t2237-sort-cache-twin-close` (2026-09-16) の段 1 brief と段 4 裁定の凍結スナップショット。
可変状態の正本ではない。状態は worklog 末尾を見ること。

## 結論

D1548 の sort 軸局所束縛は [T-2253] (`8f54a601c`、2026-09-04 commit・2026-09-05 land) と s1 への波及 [T-2327] (`50cfcb683`) で
main に着地済みである。[T-2237] は同じ作業を指す重複の持ち越しで、独立した手番は残らない。実装子は起動していない。

## 段 1 brief (2026-09-16、基準 main 0c292eff6)

- 研究前進: 束縛は着地済み。本 wave は同一作業の重複 active 項 [T-2237] を終端させ、次タスク提案が済んだ実装を
  再提案して wave を空転させる経路 (本 wave 自身がその 1 本) を止める。完了判定 = land 後の fold で現行 worklog の
  次の一手から [T-2237] が消える。
- 覆した前提: 依頼と carry は「実装待ち」。実測は着地済み (下の P1)。承認済み裁定 D1548 は変えない — 裁定の実体は既に満たされている。
- scope: [T-2237] を `完了` (remaining none) で閉じる worklog fragment 1、F428 再発 1 項の failures fragment 1。コード差分ゼロ。
- scope 外: [T-2326] (契約 ID の checker hash 閉包。D1548 の外で [T-2253] 段 4 が別 ID 化)、任意軸一般化 (D1548 が却下)、
  重複 active 項を機械検出する lint (依頼の「検査・台帳の追加は scope 外」)。
- 確定裁定: D1548 (sort 局所適用)、D1411 (campaign 由来の明示引数・既定 None で非対象の bytes 不変)、
  D1997 (重複項目は本文書き換えで残さず 完了 で終端を構造宣言)。
- 不変条件: 規律 2 不変 (verifier・受理集合・gate に触れない)。実装面ゼロなので D95 の Codex author は発火しない。
- 模擬/実の差: 取り残し照合は静的読解 (git grep)、挙動はテスト実走。コード編集はしない。
- 成果物影響 (DW-G05): 放置すると台帳 (worklog 次の一手) の active 集合に済んだ作業が残り、提案経路が同じ実装 wave を
  再起動する。certified 選択・レポートの値と受理集合は変わらない。
- 分割: 子ゼロ (DW-C00 docs-only)。段 2・3・5・6 を省き 4→7→8→9。

## 段 4 裁定

### 裁定 inbox 再走査

wave 開始後に main へ入った差分 (0c292eff6..a48d0a07a) のうち [T-2237] / [T-2253] / D1548 に触れる行は carry 番号の更新 1 行だけ。
sort 束縛の実装面 (`p3_s4_loop_sort` / `loop` / `pipeline` / `source_digest` / `buildcache`) への変更なし。
記録前に e667c8c13 まで `--ff-only` で取り込んだ時点でも同じ。

### (P1) [T-2237] は [T-2253] と同一作業で残件なし — real (確定)

- 経緯 (一次資料):
  - 2026-09-02 エントリ 1214: t2145 の fold が [T-2237] を採番 (起草時推奨 = backoff 限定維持)。
    fold 割当は `docs/spool/FOLDED.md` の `T:d901-grammar-version-cache-binding`。
  - 2026-09-03 エントリ 1221: [T-2253] を採番し「t2145 branch が同じ主題の項を登録したら同一作業として land 時に統合」と注記。
  - 2026-09-04 エントリ 1246 (/rulings 第 6 回): [T-2237] を「裁定済み (D1548) → 実装待ち」へ更新したが [T-2253] との重複に触れず。
  - 2026-09-05 エントリ 1266: [T-2253] を実装・land して 完了。同エントリの次の一手で [T-2237] は carry のまま。
- 実装: `8f54a601c` (loop → pipeline → source_digest `sort-src-token/v1` → buildcache legacy / v2)。s1 sort_best cell は [T-2327] `50cfcb683`。
  どちらも main の祖先 (`git merge-base --is-ancestor`)。
- 取り残しの全数照合: `git grep '"sort_swo_oracle"'` で campaign identity に sort 契約を宣言する producer は
  `p3_s4_loop_sort` と `s1_direct_comparison` の 2 本だけで、両方とも契約 ID を cache 経路へ渡す。
  `s8b_floor_campaign` と `s8b_oracle_driver` も `sort_oracle_contract_id` を evidence・build へ渡す。
  残りの参照 (`s8b_sort_swo_receipt`、`s8b_binary_admission`、`critic/digest` ほか) は受領証の検査や読み手で build しない。
  `s6_sort_sweep` は契約を宣言せず identity・WAL にも版を持たない (docstring「s6 sweep からは呼ばれない」) ので、
  D1548 が直した分断 (identity・WAL には届き cache には届かない) が無く、D1411 に従い鍵を動かさないのが正しい。
- [T-2253] 段 4 が scope 外にした契約 ID の閉包改善は [T-2326] として別に生きており、D1548 の実体ではない。

### 採否

- **実装しない。** 段 5・6 を飛ばし 4→7→8→9。
- 実装面差分ゼロのため変異 matrix 免除 (DW-S04)。受入全走は免除しない。
- 子ゼロ (DW-C00: 設計択一なし・正しさ防壁に触れない・受理集合不変、docs-only)。
- 記録: worklog fragment で [T-2237] を `完了` + `remaining: none`。failures fragment で F428 へ再発 1 項
  (新しい面 = 対象 carry 本文が双子の T 番号を名指さず、両項を結ぶ鍵は共有の D 番号だけだった)。

## 実測

- `orchestrator/tests/test_p3_s4_loop_sort.py` 単独走 (木 = main 0c292eff6、`python3 tools/run_tests.py <file> -q`、
  login の bounded local が上限に当たり計算ノード 1510.nqsv へ自動 dispatch) = rc=0、58 passed・赤 0。
  受入形の走行ではない。
