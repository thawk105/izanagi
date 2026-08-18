---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-19
wave: dev-wave-t1355-c04-c07-decider-bump
seq: 2
---

## {{D:c07-accept-trial-removal}}. 8c 条件7契約の `accept_trial` は exclusion pin でなく完全削除する

**決定:** 証拠契約 JSON の条件7 `reachable_from` から `accept_trial ->` prefix を削除し、
実在する consumer 関数だけを残す形にする。`MACHINE_CONTRACT_FUNCTION_EXCLUSIONS` へ
理由コード付きで pin する対処は採らない。

**理由:**
- `MACHINE_CONTRACT_FUNCTION_EXCLUSIONS` の既存3理由コード (`non-identifier-token`,
  `declared-unimplemented-token`, `different-module-token`) のいずれも `accept_trial` の実体に
  正しく当てはまらない。`accept_trial` は特定の未実装関数ではなく、契約書内の複数条件が共有する
  汎用的な「受理経路」を表す文字列であり、無理に理由コードを選べば虚偽の pin になる。
- 条件7の評価器 `_evaluate_c07` 自体は `reachable_from` の宣言済み chain を部分文字列一致で
  検査するだけであり、`accept_trial` prefix の実在を要求しない。削除しても評価器の判定ロジックは
  変わらない。
- 条件9 (`trial_registry.py` の `assert_trial_registry_acceptance`) が過去に踏んだ同種の是正
  (`accept_trial` を実在名へ改名) は、条件9の consumer file には実在する関数への改名だったから
  成立した。条件7の consumer (`s8c_result_judge.py`) には対応する実在関数が無いため、同じ
  改名パターンは適用できない。

**却下した選択肢:**
- `accept_trial` を `MACHINE_CONTRACT_FUNCTION_EXCLUSIONS` へ pin する — 3理由コードいずれにも
  正しく当てはまらず、機械的整合性のためだけの虚偽 pin になる。
- `accept_trial` を条件9と同様に実在関数名へ改名する — 条件7の consumer file に対応する実在
  関数が無く、存在しない名前を捏造することになる。

## {{D:s8c-p2-current-maintain}}. 8c 世代 record の裁定本文 digest・8b bytes 束縛は現状維持とする

**決定:** 8c condition-freeze record (schema v2) の構造的欠落2点 — (1) `ruling_reference` が
裁定"番号"の文字列のみで裁定本文の digest を持たない、(2) 8b (ratified freeze) の bytes を
束縛するフィールドが無い — のいずれも是正しない。次世代 record は既存 v2 schema のまま発行し、
`ruling_reference` には既に着地済みの D458 を用いる。

**理由:**
- D458 は「判定器・評価器・射影の bytes 全体を凍結範囲へ入れず、`DECIDER_VERSION` 1定数へ
  受理意味を代表させる」という coarse provenance 方針を明示的に採用している。裁定本文へ digest
  束縛を追加することは、決定文の bytes を新たに凍結対象へ加える動きであり、この既存方針と
  哲学的に衝突する。8b bytes 束縛も同型の bytes 級凍結である。
- 新世代 record が本 wave 自身の新規裁定を `ruling_reference` に持つことは構造的に不可能である。
  wave 内で新設する決定は land 時の fold で初めて `## D<N>.` 見出しを得るため、その番号は
  同じ wave の record 導入 commit からは参照できない (`_assert_rulings_exist` は commit 時点で
  実在する見出ししか検査できない)。したがって `ruling_reference` は既に着地済みの決定を指す
  必要があり、本 wave の変更が D458 の枠内で行う定型の bump + 発行である以上、D458 自身を
  指すのが最も正確である。

**却下した選択肢:**
- `ruling_reference_sha256` を additive field として追加する — D458 の coarse provenance 方針と
  衝突する。技術的には低結合な追加ができるとしても、方針との整合を優先した。
- `ratified_generation_sha256` (8b bytes 束縛) を追加する — 同上に加え、commit-pure な
  cross-module resolver の新設を要し、本 wave のスコープ (条件7の昇格) を大きく超える。
- 本 wave 自身の新規裁定を `ruling_reference` にする — fold 前の D 番号は record 導入 commit から
  構造的に参照できず、実現不能。
