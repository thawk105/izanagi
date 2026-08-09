---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-09
wave: dev-wave-t678-publication-wall-gate
seq: 1
---

## {{D:late-admission-gate-at-last-reversible-point}}. worker launcher の受理判定は最後の可逆点で確定する

**決定:** `tools/codex_worker_launch.py` の wall gate 再評価は、output publication・published output を
含む audit・**公開する exact bytes の temp write + fsync** をすべて終えた後、receipt final path の
可視化直前に置く。receipt は create-only 公開のままとし、公開後に受理を取り消す経路は作らない。
`_stage_receipt_write` が返した fsync 済み temp をそのまま公開して、gate の後に同じ bytes を
もう一度書く経路を無くす。receipt の `schema_version`・closed field 集合・`wall_clock_scope` の
literal・writer / checker の真理値表は変えない。`actuals.wall_clock_s` は receipt object 構築時点の
値であり、late gate の観測時刻とは別の量である。

**理由:**
- gate の目的は「実際に公開する bytes の write / fsync 費用を受理判断へ含める」ことである。
  gate の後に同じ bytes をもう一度書く構造では、その二度目の停滞が受理判断から漏れる。
- 「publication 完了後に再評価する」は create-only 公開の下では実装不能である。final path が
  可視化された瞬間に別 consumer が `accepted` を読めるため、その後の再評価は受理を取り消せない。
  取り消せない再評価で process rc だけを変えれば、receipt と rc が矛盾する。
- 受理集合は「publication I/O が成功した論理 job」について狭まるだけである。二度目の temp write が
  消えることで「一度目は成功し二度目だけが失敗する」冗長な失敗面は無くなるが、これは受理集合の
  拡大ではなく重複の解消である。
- 塞げない残余 (`os.link` / `os.replace`、親 directory の fsync、staged temp cleanup、lock 解放、
  return から process 終了まで) は 10〜20 秒に限定されず任意に長くなり得る。**この限界は
  記録・docstring で明示し、「publication 完了後に塞いだ」とは書かない。** 字義どおりの保証が
  必要なら commit protocol の再設計 (schema 世代更新 / 2 段 receipt / 可視化と admission の分離) が
  要り、それは別裁定とする。

**却下した選択肢:**
- **create 後に再評価して process rc だけを変える** — receipt が `accepted` のまま rc≠0 になり、
  receipt と rc の整合という既存不変条件を破る。
- **staging 後に gate を置くが temp は捨てて公開時に書き直す** — gate の後に残る write / fsync が
  そのまま新しい穴になる。段 2 の初案で、段 3 のレンズが具体的な回帰構成を示して倒した。
- **late gate の時刻を receipt bytes へ入れる** — bytes を変えると再 staging が要り、
  その費用がまた gate の外へ出る再帰になる。schema 世代を上げる別裁定が要る。
