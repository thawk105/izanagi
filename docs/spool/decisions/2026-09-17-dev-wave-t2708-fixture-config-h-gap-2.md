---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2708-fixture-config-h-gap
seq: 2
---

## {{D:t080-fixture-config-h-force-add}}. t080 fixture の config.h 取り込み漏れは、実 repo の ignore 一致集合を写す一般解では直さず、直すなら path 名指しの force-add と membership 検査 1 本に限る (採否はユーザー裁定)

**決定:** t080 e2e fixture (`_build_t080_stub_free_e2e_repo`) が `sort_swo_masstree/.gitignore` の `/config.h` により
tracked の `config.h` を取り込めていない件について、

1. 実 repo で `git ls-files -ci --exclude-standard` した集合を fixture で `git add -f` する**一般解は採らない**。
2. 直す場合は、`git add -A` の直後に対象 path を名指しした `git add -f` 1 行と、実 builder の未発行 fixture でその path が
   index と `enumerate_repository_files` の双方に含まれ source と bytes 一致することを検査する新規 test 1 本に**限る**
   (取り込み行を削除する変異でその test が赤になることを事前登録する)。
3. 直すか現状維持かは**ユーザー裁定**とする。放置しても certified 選択・レポート・台帳は変わらない。
4. 費用許容値は既存裁定に無いので、「fixture 構築の critical path への追加は 1 秒以内」を提案値として置く。
   D2086 の「−10% なら採らない」は高速化の採用基準であり、忠実性向上の費用許容値には転用しない。

**理由:**

- 計算ノード (bnode028) の実測で、一般解は実 repo 側の列挙 (`ls-files -ci`、419 path、tracked 27,022 件への ignore 照合)
  だけで反復中央値 4.8 秒、一連 5.0 秒かかる。fixture 構築は key ごとに走るので shard あたり約 25 秒の追加になり、
  提案許容値 1 秒を桁で超える。path 名指しの `add -f` は 28.7 ms。
- 一般解は「fixture に実際に複製された集合」ではなく実 repo の集合を入力にするため、複製から除外される path
  (receipt / draft、`*.pyc`) が将来 tracked かつ ignore 一致になると存在しない path を force-add しうる。存在しない path を
  黙って捨てる形にすると意図的除外と複製失敗を区別できず、既存の output 複製が持つ fail-closed の姿勢に逆行する。
- 同型の穴は現時点で config.h の 1 件だけである (実 repo の tracked かつ ignore 一致 419 件のうち 418 件は root
  `.gitignore` 由来で fixture に複製されない。期待集合 25,182 件との差はちょうど 1 件で、取り込むと差 0)。件数非依存の
  一般化に独立 2 例目が無い。
- 取り込んでも判定は変わらない (config.h に三軸 key 0 件、`_live_scan_sha256` は `search` を含まない、22 対の scan で
  semantic report と hash が一致)。fixture の検出力が実 repo の scan より 1 file 狭いだけで、成果物影響はゼロなので、
  親の一存で実装せずユーザー裁定に返す。
- 既存の可視性検査 (`test_s8b_oracle_driver.py` 1633〜1705 行付近) は output の複製までを見て、再 index 化後の欠落を
  検査しないので、採用時は新規 test が要る (既存 test は取り込み行の削除を殺さない)。
- path 名指し案は D2086 の proto 化 (branch 保存) と独立で、構築時 snapshot の集合を追加で持つ必要が無い。

**却下した選択肢:**

- 一般解を採る — 上記の列挙費用と成立条件の欠落。
- fixture 側の `.gitignore` を書き換える / 複製から外す — fixture 内の `.gitignore` は実 repo の tracked file の複製であり、
  改変すると別のずれを作る。
- scan 増分を根拠に採否を決める — 計算ノードでも 1 scan 18.4 秒に対し A/B 対差は中央値 −70 ms、IQR 558 ms で、
  1 file (10 KB) の増分は順序効果 (±数百 ms) に埋もれて分離できなかった。統計上限 (+157 ms/scan) と per-file 換算の
  期待値 (0.72 ms/scan) は桁が違い、どちらか一方を根拠にしない。
- 解除 env (`IZANAGI_RUN_GROWTH_HELD_TESTS`) で held module を probe から import する — ユーザー明示専用であり使わない。
  probe は enforcing な pytest session (`--collect-only` + `-k` 不一致名) の内側で import した。
