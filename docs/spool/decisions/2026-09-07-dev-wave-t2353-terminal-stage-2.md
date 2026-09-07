---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-07
wave: dev-wave-t2353-terminal-stage
seq: 2
---

## {{D:formal-consumer-terminal-stage-shape}}. 8c formal consumer の FC07 は terminal record の `stage` を読み、旧 root `kind` 形状を拒否する — terminal の外枠は閉じない

**決定:** `orchestrator/campaign/reflux_formal_consumer.py` の `_validate_wal_outcomes()` は、
ordered WAL projection の末尾 record について `terminal.get("stage")` を
`orchestrator/campaign/model.py` の `STAGE_COMMIT` / `STAGE_ABORT` と比較する。旧形状の root `kind` は
受理しない。fixture (`orchestrator/tests/reflux_origin_fixture_builder.py`) の terminal record も
production の外枠 `{variant, stage, env_tag, ts, payload}` へ揃え、witness 系 field を payload 内へ移す。
`_wal_field()` の root→payload fallback、FC07 以外の判定式、reason code、他の gate は変えない。
**terminal record の外枠 key 集合・値の型・重複・root shadow を exact に閉じる gate は本決定では置かない。**

**理由:**
- production producer (`orchestrator/campaign/pipeline.py`) は commit / abort とも
  `stage` + `payload` 形状しか書かず、outer に `kind` を持たない。D1665 が trigger 側 (FC05C) を直した後も、
  本番 projection はこの 1 点で FC07 に落ちていた。
- `_wal_field()` は既に root→payload の順に読むので、`build_attempt_id` / `verify_configs` /
  witness 系は production 形状でも引ける。落ちていたのは root `kind` を直接読む 2 箇所だけだった。
- 定数を literal でなく production 正本から import することで、`model.py` 側が段名を変えたときに
  consumer の逐語 literal だけが取り残される経路を作らない。
- 外枠を閉じないのは、その緩さが**本決定で新たに生じたものではない**ためである。旧 `kind` 版でも
  production 形状でない flat record は同じだけ通っていた。閉じるかどうかは FC07 の受理集合を変える
  独立の判断であり、ユーザー裁定へ返す。変異 B-057-M5 (`terminal.get("stage")` を
  `_wal_field(terminal, "stage")` へ緩める) が焦点走 11 file で生存したことが、外枠が pin されていない
  ことの実測である。

**却下した選択肢:**
- 旧形状 (root `kind`) と production 形状の両受け — 受理集合が広がり、fixture 由来の形が本番へ紛れ込む
  経路を残す (規律 2、DW-G05)。D1665 が trigger 側で却下したのと同じ理由である。
- 同じ wave で terminal の exact outer-shape gate を新設する — 依頼の名指し外で、FC07 の受理集合まで
  変わる。段 3 の両レンズは拡張を推奨したが、scope 外として裁定パッケージへ送った。
- rejected 側 witness 系 field の producer を新設する — 同じく名指し外。別項として起票した。
- 段 2 / 段 3 が計算したと称する pin の hash 値をそのまま採用する — 別 context が計算した値であって
  実物ではない。実装子に変更後の実物から再計算させ、親が焦点走で検算した。

**限界 (DW-O13):** rejected 側が要求する `candidate_attributable` / `truncated` /
`witness_class_sha256s` には production producer が存在しない (`orchestrator/campaign/` 全走査で 0 件)。
`reflux_source_closure.py` の token 表は `wal.abort.payload.witnesses` という別名を挙げており、
consumer が読む名前とも一致しない。したがって本決定の後も、rejected の本番 projection は FC07 で止まる。
本決定が通すようにしたのは accepted 側だけである。また consumer は全検査通過後も `P6Unavailable` を返すため、
certified 選択集合は本決定では変わらない — 変わるのは report の reason と receipt / evidence-root 参照だけである。
