---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-10
wave: dev-wave-t665-t662-launch-binding-impl
seq: 2
---

## {{D:launch-value-docs-binder}}. dev-wave の起動値は docs 権威から導出し、caller に指定させない

**決定:**

- dev-wave の codex 子は `tools/dev_wave_codex.py` 経由で起動する。`DW-O01` の規範行がこの経路を
  指定し、`tools/check_docs.py` が可視 top-level の full-match で pin する。
- **model は全段**、`DW-O01` の model 権威行から導出する。`--model` は launcher から削除し、
  既定値も置かない。
- **effort は段 6 の review / focus だけ**、`DW-S06-A` / `DW-S06-C` から導出する。
  それ以外の段は権威が存在しないので `effort_authority="unbound"` を receipt へ記録し、
  `--reasoning` を caller から取る。authority-bound な段では `--reasoning` の指定を禁止する
  (第二の権威を作らない)。
- **parse 対象は上記 3 節だけ。** `DW-S02` / `DW-S03` / `DW-S05-A` / `DW-S06-B` は parse しない。
  sandbox も導出しない。
- 権威は job ごとに snapshot する。`authority_commit` と対象節の sha256 を receipt へ固定し、
  working tree が当該 commit と 1 byte でも異なれば起動前に停止する。live HEAD とは照合しない。
- 規範位置は可視 top-level の full-match に限る。blockquote、list、link 例示、否定文、
  raw HTML block、Unicode 行分離は規範として受理しない。
- 実効値の照合は**全 `turn_context` の `payload.model` / `.effort` だけ**を見る。
  top-level への fallback を持たない。`collaboration_mode.settings.*` は読まない。
- 記録値は `recorded_*`、要求値は `requested_*` と別名で持ち、記録値を served identity の
  attest として扱わない。

**理由:**

- 起動値の権威 (docs) と実引数を突き合わせる層がどこにも無く、存在しない effort 値でも
  rc=0 で通ることが F56 で実測されていた。
- launcher は既に「caller が要求した値」対「実効値」を全 `turn_context` で照合していた。
  欠けていたのは「docs 権威」対「要求値」の一段だけだった。
- parse 対象を 3 節に限るのは、段 5 の機械 pin 拡大が見送り裁定の射程にあり、
  sandbox は docs に値そのものが存在しないためである。名指しされた範囲を超えて
  受理集合を変えない。
- authority を job ごとに snapshot するのは、権威行が時間変化し、wave が自分の land する契約を
  wave 内で dogfood する運用が実在するためである。

**却下した選択肢:**

- **caller の `--model` / `--reasoning` を assertion として残す** — 第二の権威になる。
- **段 5 の `DW-S05-A` も parse する** — 見送り裁定の射程を侵し、節の書式を事実上凍結する。
- **`DW-S06-A` / `DW-S06-C` へ sandbox 値を新設する** — 無裁定の受理集合変更である。
- **live HEAD を権威にする** — 過去 wave に偽の赤が出る。
- **契約文だけで raw `codex exec` を禁じる** — docs pin と同じ強度しかなく、
  本機構が解こうとしている問題の再演になる。

## {{D:derived-value-test-needs-independent-oracle}}. 派生値の検査は独立した oracle を持たせる

**決定:** docs から導出した値を検査するテストは、期待値を派生関数自身から取ってはならない。
docs を独立に読む最小の抽出をテスト側に置き、両者の一致を要求する。
期待値の literal をテストへ書くことは、これとは別に禁じる。

**理由:** 期待値を派生関数から取ると、その派生関数を変異させたとき期待値も一緒に動くため、
変異が検出できない。実際に本 wave では、対象テスト 623 全緑・敵対レビュー 4 本通過の状態で
派生関数の変異が生存し、束縛の中核主張が未証明であることが変異でだけ判明した。

**却下した選択肢:**

- **期待値を literal で書く** — 機械 pin を増やさないという既存の見送り裁定の実質的な再提案になる。
- **派生関数を呼ぶ既存テストを消す** — 循環していても回帰検出には効く。消さずに独立検査を足す。
