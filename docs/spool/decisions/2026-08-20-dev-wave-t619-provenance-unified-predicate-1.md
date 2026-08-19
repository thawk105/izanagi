---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t619-provenance-unified-predicate
seq: 1
---

## {{D:t619-unified-predicate-implementation}}. D230 の統一述語を実装し、既定監査へ導入する

**決定:** D230 が設計した統一述語 (選択集合と scope/implementation/CAB 3層の epoch 適用述語を
同じ式へ揃える恒久形) を実装する。D230 自身の決定文は書き換えない — 「本 wave は実装しない」は
その決定が下った時点の正しい記録であり、実装は別の decision として追記する。

対象は既定監査 (`--range`/`--message-file` 未指定時) だけで、明示 `--range` の挙動は変えない。

- `_commit_range(None)`: `--ancestry-path` を削除し、`policy..HEAD` の plain range + policy 前置に
  する。選択集合と base 層の適用述語が同一式になる。
- scope/implementation 層: epoch 適用判定を単項 lineage から `authoritative` フラグで2項化する。
  既定監査でだけ「epoch の祖先でない commit にも適用する」第2項を有効化する。
- CAB 層: seed 集合の「どの seed の祖先でもない」判定を追加する。CAB seed が一度もこの履歴に
  導入されていない (空集合の) ときは、数式上の空虚な真を適用に読み替えず、常に非適用のままとする
  — scope/implementation の epoch が `None` のときも同様に非適用とする。規則が存在しない以上、
  規則が新たに適用対象を得ることはない。
- HEAD を起動時に一度だけ full SHA へ解決し、監査終了時に drift していれば rc=2 とする。
- shallow repository / git graft / git replace / `docs/ai-provenance.md` への非一意
  `--diff-filter=A` add を、既定監査で rc=2 とする (いずれも新規実装、既存に同種の検出は無かった)。
- 既知違反台帳へ `333605d680ec15f3f74b00e9e2746ae317b85dc5` を追加し、rc を新規違反だけで決める。
- `docs/ai-provenance.md` の非遡及規定 (別々に4箇所へ書かれていた) を1文へ統合し、family
  (`docs/ai-provenance.md` + `docs/provenance/**`) を net -168 bytes 縮約する。
  `docs/provenance/audit.md` の `PR-A02` も同じ意味へ更新する。

**理由:**
- 2026-08-07 の /rulings で、D230 が実装へ回した3点 (契約本文の改訂・既知違反台帳への追加・
  forward correction の受理集合変更) と、明示 `--range` の扱い・legacy 違反の受け皿の有無を
  含む5点が採用側で確定した。恒久形そのものの設計判断 (統一述語の式、却下した代案) は D230 が
  既に確定しており、本決定では再訪しない。
- 実装直前の再実測で、D230 が実測した「epoch 層26 commit の適用外・新規違反1件」という前提は
  12日後の HEAD でも完全に同一 (同じ26 commit、同じ1件) であり、時間経過による前提の陳腐化は
  無かった。

**却下した選択肢:**
- D230 の決定文自体を実装内容で書き換える — 当時「実装しない」と裁定した記録の意味が変わり、
  decision 台帳の履歴的正確性を壊す。
- CAB seed が空集合のとき第2項を数式どおり真とする (空虚な真の字義どおりの適用) — 一度も
  導入されていない規則が side-branch commit へ新たに適用されることになり、「規則の不在」と
  「規則の全面適用」を混同する。既存の `cab_policy_mask == 0` 早期 return と同じ結論 (非適用) を
  scope/implementation にも揃え、例外として明記した。
- `_normal_commit_audit(ancestry=None, authoritative=True)` の組み合わせに対応する独立 oracle
  実装を新設する — この組み合わせは production では発生しない (`_audit_history` は常に実
  ancestry を渡す) ため、fail-fast で拒否するに留めた (規律5、盛らない)。
