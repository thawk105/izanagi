---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2236-ledger-refresh
seq: 1
---

## {{D:acceptance-ledger-refresh-mode}}. 受入所要時間台帳の再生成は「凍結 8 suite 据え置き・それ以外を 1 走の JUnit から全再生成する」refresh mode で行い、効果は観測値としてだけ記録する

**決定:** `tools/update_acceptance_duration_ledger.py` に `--refresh` を足す (`--add-only` と排他)。
凍結 8 prefix (`_ADD_ONLY_FROZEN_SUITE_PREFIXES`) に一致する既存 entry は値ごと保持し (再量子化しない、JUnit に無くても残す)、
それ以外の entry は入力 JUnit から全再生成する (値の置換・旧名の削除・新名の追加)。凍結 prefix に一致する JUnit testcase は
採用しない。failed / error の testcase は既存どおり除外し、その非凍結 entry は残さない (consumer の未登録 1.0 秒 fallback に任せる)。
描画は全再生成と同じ canonical 形。閾値 0.90・凍結 prefix・除外集合・consumer・既存 mode の挙動と stdout は変えない。

入力は受入 1 走 (3 shard) の JUnit だけとし、複数走を結合しない (生成器が入力間の重複 nodeid を拒否する)。選ぶ走は「最新で、
collection が再生成先の main と一致する緑走」とし、性能代表性ではなく入力の整合性で選ぶ。

land で main 側の台帳が進んでいたら、main の現物を base に同じ JUnit で `--refresh` を再走する (決定的)。main が add-only で
足した非凍結 node のうち入力 JUnit に無いものは落ちる (次の add-only wave が再登録する) ので、落ちた node は名前と件数を insight に
記録する。refresh を F902 の add-only 和集合 merge へ流用しない (add-only = 既存値保持、refresh = 非凍結の置換で、別契約)。

再生成の効果 (shard 別 wall) は受入 1 走の観測値としてだけ記録し、改善・退行・300 秒達成を主張しない (D357)。

**理由:**

- 台帳の予測負荷は 3 shard で均等 (5701 / 5700 / 5700 秒) なのに実測の直列和は 8852 / 4433 / 4519 秒で、乖離の主因は凍結 8 suite
  の外にある既存 node の値の陳腐化 (`test_s8b_oracle_driver.py` +2126 秒、`test_s8b_floor_campaign.py` +1289 秒、どちらも
  shard-0)。既知 node の差 2932 秒に対し未登録 node の差は 219 秒で、`--add-only` (既存値を byte 保持) では主因を直せない。
- 全再生成は D1152 が却下している (凍結 pin を壊す)。凍結 8 suite を据え置けば T-1574 の 8 suite identity・12 値・removed 5 件の
  不在が 1 byte も動かず、規律 2 の pin を緩めない。凍結 426 entry は json 往復で text 差 0 (親の実測)。
- 4 走の結合は生成器が拒否する。同じ node の time は走ごとに 2 倍程度動く (`test_t316_sandbox_probe` の 8〜9 秒 対 18〜19 秒) ので、
  1 走入力は割付の頑健性を保証しない。これは限界として記録する。
- D357 は受入 wall の主張に同一 tip 3 走の中央値を要求する。before の 4 走は投入元が異なり反復比較にならない。

**却下した選択肢:**

- 全再生成 — D1152 が却下済み。T-1574 の node 集合 hash (121 / 42 / 69 に対し実体は 138 / 46 / 81) と 12 値が全部食い違う。
- `--add-only` だけ — 既存 node の陳腐化した値を直せず、主因に届かない。
- 台帳の手編集・凍結 prefix / 閾値 / 除外集合の変更 — F902 が禁じ、規律 2 に触れる。
- T-1903 (所要値の述語化) を同時に行う — D205 で active から外れており、本 wave の scope 外。
- failed / error の非凍結 entry を旧値のまま残す — 「今回の JUnit か凍結旧値」という出所契約に反し、旧値を実測更新済みと誤読させる。
- 新しい生成器 script の新設 — 既存生成器の mode 追加で足り、依頼が新設を禁じる。
