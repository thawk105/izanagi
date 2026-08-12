---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-13
wave: dev-wave-t953-oracle-residue
seq: 3
---

## 新規

### {{F:brief-search-truncated}}. 段 1 brief の「存在しない」実測を head で切った検索から書いた [誤前提]

- 事象: 親が段 1 brief に「finding の `observations` を生成する箇所は 0 件」と書いた。実際は
  producer に 3 箇所ある。この誤った前提の上に消費側 schema の設計を組み立てていた。
- 根本原因: 完全性を要する検索を `grep -rn observations ... | head -20` で切っており、
  campaign 側の hit が truncate されて表示に出ていなかった。**「無い」ことの実測は全件を見ないと
  成立しない**が、親は truncate された出力を根拠にした。
- 検出経路: 段 3 の敵対レンズ 2 本が独立に同じ誤りを指摘した (レンズ A と B が別の攻撃面から
  到達)。親はその後に自分で測り直して是正し、schema を実 producer の emit 形から作り直した。
  実害には至っていない (near miss)。
- 恒久対応: memory `complete-search-not-truncated-for-absence` (「無い」の実測は全件検索でだけ
  成立し、`head` 等で切った出力を根拠にしない)。**`DW-S01` への統合は予算で入らなかった** —
  本文を 1 文足すと `docs/dev-wave/**` の L1 unique footprint が 10,731 bytes となり
  予算 10,625 bytes を超えて `check_docs.py` が赤になる (実測)。予算引き上げは自己改善の範囲外
  なので入口・reference は変更せず、機構は memory に置いた。
- 再発検知: 段 3 の敵対レンズが「親自身の実測値とその一般化」を攻撃対象に含める既存契約
  (`DW-S03`) が検出経路として実際に働いた。この経路を弱めない。
- 型の区別: F30 の 4 度目の再発 (2026-08-07) も `head` で切った検索が原因だが、あちらの型は
  **凍結 pin の閉包漏れ**であり、その恒久対応 (pin 元の全列挙) では本件は防げない。
  本件は pin と無関係な段 1 の一般の実測であるため別エントリにした。

## 再発

### F30

- **再発: 2026-08-13** — 五度目。**編集面 source を bytes で pin している側**を段 1 で数え落とした
  (2026-08-04 の再発と同じ向き)。[T-953] の項目 (d) が
  `orchestrator/campaign/s1_direct_comparison.py` を編集したが、この path は
  `orchestrator/campaign/s8b_oracle_manifest.py` の `_GENERATOR_SOURCES` が `materializer` として
  束縛しており、`validate_reviewed_spec` が spec 内の `generator_versions.materializer.sha256` を
  実ファイルの byte hash と突き合わせる。テストの golden literal は旧 hash を焼いていたため、
  **受入全走で 2 件が赤になって初めて判明した** (段 1・段 3・段 6 のいずれも検出できていない)。
  親は段 1 で `ORACLE_CONTRACT_ID` を pin する側は全列挙したが、**編集対象ファイル自身を
  pin する側**を列挙しなかった。決定的証拠は golden の `dc67d934...` が
  `git show main:orchestrator/campaign/s1_direct_comparison.py | sha256sum` と完全一致すること。
  実害は受入 1 走 (134 秒) と fix 1 巡の手戻りで、誤った land には至っていない。
  恒久対応は `DW-O09` から変更しない (本文は既に両向きの列挙を要求している)。
  **今回効かなかったのは規約ではなく遵守であり、pin の向きを両方数える義務が
  4 度目・5 度目と続けて破られている事実を顕在化させる。**
