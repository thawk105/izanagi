# 段 1 brief v2 (scope 拡大による巻き戻し) — dev-wave-suite-floor-recheck

**巻き戻しの理由.** 2026-08-09、ユーザーが「(a) の実装まで進めていい」と直接裁定した。
これにより `orchestrator/campaign/t080_freeze_migration.py` (freeze 族の中核) を編集することが確定し、
条件 `DW-O08` / `DW-O09` / `DW-O10` が新たに成立した。3 条件の最遅読了段は段 1 brief 前であるため、
入口の巻き戻し規則に従って段 1 へ戻す。**brief v1、段 2 プラン、段 3 レンズ 2 本、段 4 裁定は
本 brief の根拠として流用しない** (事実として引く実測値だけを、出典付きで再掲する)。
段 5 で作った probe は成果物として残るが、その採否は新しい段 2 プランが再評価する。

## scope

1. **(測定)** 受入全走 wall の内訳を計算ノードで実測し、D104 決定 (2) が現規模で成立するかを判定する。
2. **(実装)** [T-201] 択 (a) — 本番 `_history_touches_path` の走査置換。
   **受理集合が変わらないことを positive control で固定してから入れる** (2026-07-31 ユーザー裁定の受理条件)。
3. **(材料)** (b) `output/` tracked bytes 削減、(c)(d) の扱いは裁定材料として返すのみ。実装しない。

**scope 外**: (b)(c)(d) の実装、テスト分割、並列度引き上げ、受入全走への flag 追加。

## 確定済みユーザー裁定

- 2026-07-31: [T-201] は **(a)+(b) 採用 / (c)(d) 不採用**。(a) の受理条件は
  「正しさ防壁の中核に触るため、**受理集合不変を positive control で固定してから入れる**」
  (`docs/archive/worklog-phase3-0731-74.md` の (74) 項)。
- 2026-08-09 (本セッション): **(a) の実装まで進めてよい**。
- 2026-08-08 [T-656]/[T-653]: 受入既定 walltime 40 分、flag plumbing と受入分割は不採用。

## 段 1 の実測 (本 brief の前提。出典つき)

- **M1** `_any_history_touches_path` (`t080_freeze_migration.py:849`) は descendant commit を**全件**
  8-thread pool へ submit する。`any()` は戻り値の意味論だけで投入済みの仕事を打ち切らない。
  よって receipt 検証 1 回の `diff-tree` 発火数 = descendant commit 数。
- **M2** receipt 導入 commit `8bec195d` からの `--ancestry-path` descendant 数:
  2026-07-31 (D104 当時) **298** → 2026-08-09 **1529** (5.13 倍)。
  同期間の `output/` tracked は 3489 → 9435 ファイル、総 commit は 952 → 2183。
- **M3** 本番の唯一の呼び出し元は `t080_freeze_migration.py:1753` (`verify_receipt` 経路) の 1 箇所。
  他は test。`RECEIPT_REL` の pin は `t080_freeze_migration.py:34` と
  `orchestrator/tests/test_s8b_oracle_driver.py:1775`、`s8b_oracle_report.py:139` の 3 箇所
  (`DW-O09` の path 検索結果)。`FROZEN_MANIFEST` (23 entry) にこの receipt path は**入っていない**。
- **M4 (並行セッション提供、一次証拠にしない)** main checkout・ログインノード 1 回走行で
  現行方式 4.13 秒/commit、`--find-copies-harder` 除去で 0.03 秒/commit、
  逆引き `git log -- <path>` は全履歴 1 回 1.04 秒。**paired でも単独性確認済みでもない**ため、
  候補選定の材料としてのみ使い、こちらで計算ノードで測り直す。
- **M5** D104 の材料 (`output/insights/2026-07-30_t200-suite-floor/s7-negative-result.md:186-205`) は
  **同一コードの baseline がノード間で 116.25 / 200.72 / 214.34 秒 = 1.8 倍**開くこと、
  および当時の「207.42 秒」が**後に棄却された共有 cache 実装ありの arm** の値であることを記録している。
  よってユーザー brief の「D104 測定時の 207 秒」も同じ arm の値であり、
  **日付跨ぎ・ノード跨ぎの wall 比を因果推定に使わない**。

## 判断が割れうる前提 (親の provisional 裁定。段 3 の攻撃対象)

- **(P1)** 走査の意味論は「descendant commit のいずれかが RECEIPT_REL を M/D/R/C/T のいずれかで
  触ったか」である。**同じ検証経路の直前に、全 descendant に対する blob OID 一致検査
  (`t080_freeze_migration.py:1744-1752`) が既にある**。したがって走査が追加で捕らえているのは
  主に (i) rename/copy の**source 側**としての出現、(ii) descendant 集合外の親を持つ merge 境界、
  である。置換候補はこの 2 つを落としてはならない。
- **(P2)** 受理集合不変の positive control は、**実 repo の全 commit に対する新旧の判定値の全件一致**を
  一次証拠にする。合成 repo だけの control は根拠にしない (自己 hash / pin 対象では模擬を裁定根拠に
  しない、F29)。48 並列なら全史でも数分で回る見込み。
- **(P3)** 候補は最低 3 つ測る: (i) `--find-copies-harder` 除去、(ii) 逆引き `git log -- <path>`、
  (iii) `commit-graph --changed-paths` 併用。**判定が 1 件でも変わる候補は速度に関係なく棄却**。
- **(P4)** 測定 (scope 1) は実装前に走らせ、実装後の受入全走と合わせて before/after を同一ノードで取る。

## 不変条件 (違反したら停止)

- **検出力を下げない (規律 2)。** 置換後も改竄検出の受理集合は完全に同一でなければならない。
  速度を理由に skip / 期待値緩和 / 検査除去を採らない。**判定が変わる候補は棄却**であり、
  「実用上問題ない」という理由で通さない。
- 受入全走に flag を足さない。計測は別走行。
- 一次証拠は duration にしない (D104 決定 4)。同一 allocation・同一ノードの paired 比較と
  機構の実発火回数の直接観測を使う。
- 測定は単独性を確認した計算ノードで行う。ノードを跨いだ wall 比較をしない (M5)。
- probe と microbench は repo 外。tracked file の一時変異は `DW-O19` に従う。

## 成果物

1. 受入全走 wall の内訳 (発火回数・累計 CPU・worker critical path・CPU 稼働率、方法と生値つき)
2. D104 決定 (2) が現規模で成立するかの 3 値判定 (支持 / 反証 / 判定不能)
3. (a) の実装 + **全史 positive control による受理集合不変の固定**
4. 実装前後の受入全走 (同一ノード) と、下限がどれだけ動いたかの実測
5. (b)(c)(d) の裁定材料

## 成果物影響 (DW-G05)

(a) を実装しない場合、受入全走の wall は commit が増えるたびに線形に伸び続ける
(M1 + M2: 発火数 = descendant 数)。実装を誤ると **freeze receipt の改竄検出が緩む** —
certified 選択そのものは変わらないが、proof chain の根拠である receipt 不変性の検証が
偽陰性を返しうる。これが本 wave で最も重い失敗様式であり、全史 positive control はその防壁である。

## 分割方針

段 2 プラン (codex read-only / max) → 段 3 敵対 2 本 (sol / luna) → 段 4 裁定 + 変異事前登録 →
段 5 実装 (Codex `role=author`。production 1 単位 + positive control テスト 1 単位) →
段 6 敵対レビュー 2 本 + fix + 変異 matrix + 受入全走 → 段 7 記録 → 段 8 → 段 9 land。

測定 job (計算ノード 1 allocation) は段 2/3 と並行して投入する — 実装候補の選定に必要な
前提実測だからである。
