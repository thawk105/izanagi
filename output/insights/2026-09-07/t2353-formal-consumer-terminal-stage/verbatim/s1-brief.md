# 親 brief — [T-2353] 8c formal consumer の terminal 形状不整合

## scope (確定)

`orchestrator/campaign/reflux_formal_consumer.py` の `_validate_wal_outcomes()` が terminal record の
root `kind` を読む 2 箇所を、production が実際に書く `stage` を読む形へ直す。あわせて fixture の
terminal record を production の外枠へ揃える。**読み手の修理だけ。**

## 確定済みユーザー裁定 (command 引数)

- 実装は Codex author (D95)。
- 規律 2 を緩めない。
- 本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。

## 親が実測した事実 (すべて base main d19d2182f の worktree で確認)

1. production の commit record: `orchestrator/campaign/pipeline.py` が
   `emit(layout, v, STAGE_COMMIT, env_tag, payload)` で書き、payload に `verify_configs` と
   `build_attempt_id` を持つ (pipeline.py:1762-1785)。
2. production の abort record: `pipeline.py:1071-1075` と `pipeline.py:1215` が
   `STAGE_ABORT` + payload `{reason, error, build_attempt_id, ...}` で書く。
3. WAL の 1 行の外枠は `orchestrator/campaign/model.py` の `WalRecord` =
   `{variant, stage, env_tag, ts, payload}` (model.py:98-110)。`STAGE_COMMIT = "commit"`,
   `STAGE_ABORT = "abort"` (model.py:28-29)。outer に `kind` は無い。
4. consumer の `_wal_field()` (reflux_formal_consumer.py:821-825) は root→payload の順に読むので、
   `build_attempt_id` / `verify_configs` / abort の witness 系は production 形状でも引ける。
   **落ちているのは `terminal.get("kind")` の 2 行 (861, 867) だけ。**
5. fixture: `orchestrator/tests/reflux_origin_fixture_builder.py:360-379` の `_wal_records()` が
   terminal を root `{kind: "abort", build_attempt_id, candidate_attributable, truncated,
   witness_class_sha256s}` で作る。同 file の trigger record は既に production 形状
   (`{variant, stage, env_tag, ts, payload}`) で書かれている (T-2257 / D1665)。
   `orchestrator/tests/test_reflux_formal_consumer.py:861-866` にも root `kind: "commit"` の
   合成 terminal がある。
6. pin 閉包: 3 対象 file の bytes を pin する `FROZEN_MANIFEST`・golden sha256 は不在。
   path 検索と 64 桁 hex literal 検索の双方で 0 件。fixture 出力の hash は
   `build_ordered_wal_projection()` が自分で計算する (`source_wal_ref.sha256`) ので、
   record 形状を変えても内部整合する。
7. `orchestrator/campaign/reflux_result_evidence.py:594-598` の `_projection_attempt_id()` も
   root→payload の fallback を持つので、fixture の外枠変更で projection 検査は壊れない。

## 不変条件

- 旧形状 (root `kind`) の両受け・互換層は置かない (D1665 の先例、規律 2)。
- FC07 以外の reason code を新設しない。
- gate・検査・台帳・一般化を足さない。
- `_validate_wal_outcomes()` 以外の判定式・受理集合を変えない。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- **(P1)** production の abort payload には `candidate_attributable` / `truncated` /
  `witness_class_sha256s` を書く producer が存在しない (親の実測: `orchestrator/campaign/` 全走査で
  該当 0 件。`reflux_source_closure.py:85-87` の token 表は `wal.abort.payload.witnesses` という
  **別名**を挙げる)。よってこの修理後も rejected 側の本番 projection は FC07 で止まる。
  親の provisional 裁定: **producer 新設は依頼の名指し外なので scope 外**、限界として decisions へ記録する。
- **(P2)** `_wal_field()` の root fallback を残すか。fixture を production 形状へ揃えると terminal
  側で root fallback は使われなくなるが、fallback の撤去は受理集合を狭める変更であり本題外。
  親の provisional 裁定: **触らない**。
- **(P3)** `stage` を `model.STAGE_COMMIT` / `model.STAGE_ABORT` の定数で読むか literal で読むか。
  親の provisional 裁定: **production 正本の定数を import して使う** (逐語 literal の二重管理を避ける)。
- **(P4)** terminal record の外枠 key 集合・型を D1665 の `_wal_trigger()` と同じ exact で閉じるか。
  親の provisional 裁定: **閉じない** (gate 新設 = scope 外)。`stage` の読みだけ直す。

## 成果物の形

- `orchestrator/campaign/reflux_formal_consumer.py` の `_validate_wal_outcomes()` の 2 行修正。
- `orchestrator/tests/reflux_origin_fixture_builder.py` の `_wal_records()` terminal record を
  production 外枠へ。
- `orchestrator/tests/test_reflux_formal_consumer.py` の合成 terminal record を production 外枠へ。
  旧形状 (root `kind`) を拒否する負例テストを 1 本足す。
- docs は親が段 7 で書く。子は docs も commit も触らない。

## 分割方針

編集面が 3 file・数十行なので段 5 は実装子 1 本。段 3 の敵対相談は 2 レンズ並列。

## 成果物影響 (DW-G05)

放置すると 8c formal consumer の本番 projection が FC07 で止まり、certified 選択の proof chain が
本番入力で 1 度も通らない。修理すると accepted 側の本番 terminal record が FC07 を通る。
rejected 側は (P1) の限界により依然通らない。
