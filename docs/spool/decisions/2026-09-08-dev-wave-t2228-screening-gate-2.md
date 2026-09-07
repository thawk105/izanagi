---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-t2228-screening-gate
seq: 2
---

## {{D:screening-gate-supply-route-proxy}}. screening 関門の FetchContent 供給は manifest の実在で切り替え、これを権限ではなく経路の代理として記録する

**決定:** D1733 が名指しした `screening_driver._run_condition_gate_for_genome` へ供給を入れるにあたり、
発火条件を **`expected_toolchain_manifest` が `None` でないこと**とする。同関数は
`backoff_sweep` だけでなく `s6_sort_sweep` と `s8a_trigger_sweep` からも到達する共有関数だが、
manifest を渡すのは `backoff_sweep` の 2 呼び出しだけなので、他 2 経路の挙動は 1 bit も変わらない。

**この述語は供給の権限を表さない。現行 call graph 上で backoff screening 経路を選ぶ代理である。**
将来 `s6_sort_sweep` か `s8a_trigger_sweep` が manifest を渡すようになれば、同じ分岐が自動で発火する。
`None` 経路の非発火 test は helper を直接呼ぶので、その変更を検出しない。
**したがって「この test があるので将来の水平展開はできない」とは記録しない。**
水平展開の可否は D1733 の再訪条件 (正規入口から関門へ到達したことの実測) で判断する。

**受理集合について。**判定式・既定値・stock 比較・meaning 腕・admission 条件は 1 行も変えていない。
一方で受理集合は「準備済み base の未供給だけを理由に前段の preprocess で赤になっていた呼び出し」が
判定へ進む分だけ**制御された拡張**になる (D1721 の形)。「緩めていない」とは書かない。
また変わるのは masstree の `config.h` だけではなく、masstree / mimalloc / googletest の
FetchContent population 全体である。「`config.h` 欠落だけが消える」とも書かない。

**本決定は screening 関門が緑になったことを主張しない。** 現行の正規入口から実 CCBench で関門を
通す生死確認は本 wave では行っていない。実装する wave と実測する wave を分ける D1666 の先例に従う。

**理由:**

- D1733 は関門を関数名で名指ししたが、その関数が共有であることには言及していない。
  未測の 2 経路へ発火させないのが `DW-G04` (条件付き機能は発火条件を満たす既存 artifact path か
  計測 ID を brief に書ける場合だけ実装する) に沿う。
- 新しい policy gate・driver-id 判定・boolean knob を足すと、依頼が明示的に scope 外とした
  「仮想リスク向けの gate の追加」になる。既にある引数の実在で切り替えるのが最小である。
- 段 3 の敵対相談 2 本が独立に「この述語は候補集合に含意された恒真ではない」と裏取りした。
  ただし対象である backoff 経路の内側では恒真であり、経路タグとして働いている。この二面性を
  記録しないと、後から「readiness 条件だ」と誤読される。

**却下した選択肢:**

- 3 呼び手すべてへ入れる — `s6_sort_sweep` と `s8a_trigger_sweep` は到達性が未測であり、
  発火経路の無い条件付き機能を main へ入れることになる。
- driver 名で分岐する — 経路名への依存を新設する。既にある引数で足りる。
- 関門を通すために preprocess を skip する — D1666 が偽の緑として却下済み。

## {{D:gate-prebuild-not-attributable-to-measurement-asymmetry}}. 関門前の依存 prebuild は計測の baseline/候補の非対称に帰属しない

**決定:** 条件関門の直前に依存の prebuild (約 20 秒) を足すことは、screening の baseline
(`do_settle=True`) と候補 (`do_settle=False`) の熱・cache 状態の非対称を**新たに作らない**と裁定する。
`do_settle` を候補側にも足す案は採らない。

**理由:**

- `pipeline.evaluate` は関門の後に `_prepare_evaluation_core` で variant の**完全 build** を行い、
  その後で `_bench_prepared` を走らせる。計測直前の機械状態を支配するのはこの build であって、
  関門より前の 20 秒ではない。build は baseline と候補の両方で起きる。
- `do_settle` の baseline / 候補の非対称は本変更以前から存在する設計であり、本変更に帰属しない。
- settle を足すと計測の意味論が変わり、既測値との比較可能性を落とす (絶対規律 7 の面)。

**却下した選択肢:**

- 候補にも `do_settle` を足す — 計測の意味論を動かす。本依頼の scope 外でもある。
- prebuild を関門の外へ出して 1 度だけにする — 検査する木と build する木の同一性を弱める。
