---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-07
wave: dev-wave-t619-provenance-range
seq: 1
---

## {{D:provenance-uniform-epoch-predicate}}. provenance 既定監査の恒久形は選択集合と 4 層の適用述語を同じ 1 つの述語へ揃える形とし、実装は裁定へ返す

**決定:** `tools/check_ai_provenance.py` の既定監査について、選択集合の決定と 4 層 (base policy /
scope / implementation / Co-Authored-By 配置) の適用可否を、次の 1 つの述語へ揃える形を恒久形とする。
規則 R の seed 集合 `seeds(R)` は R の導入を内容検出した commit の集合 (base は `--diff-filter=A` の
hit、他 3 層は pickaxe hit)、権威 tip を `H`、`Anc(X)` を X 自身を含む祖先集合とする。

```text
applies_R(C) := C ∈ Anc(H) かつ
                ( (∃p ∈ seeds(R): p ∈ Anc(C))  または  (¬∃p ∈ seeds(R): C ∈ Anc(p)) )
```

- 権威ある既定監査 (`--range` なし) だけに適用する。明示 `--range` は一意な権威 tip を持たないため
  現行 lineage 述語を残し、`--message-file` 経路は 1 bit も変えない。
- `H` は起動時に一度だけ full SHA へ解決して全 query へ渡し、終了時の HEAD drift は rc=2 とする。
- shallow clone / graft / replace / 非一意な policy add は既定監査で rc=2 とする。
- `--reverse` と policy 前置は保存する。stale (rc=2) は新規違反 (rc=1) より優先する。
- **本 wave は実装しない。** 実装は次の 3 点がユーザー裁定を経てから行う — 契約本文
  (`docs/ai-provenance.md`) の非遡及規定の改訂、既知違反台帳への 1 件追加、forward correction の
  受理集合が strict 側へ変わることの受容。

**理由:**
- 既定監査の選択集合は `--ancestry-path` で「policy の子孫かつ HEAD の祖先」に限られており、
  policy より前で分岐して後日 merge された branch 上の commit を見ない。素の range には入る。
  現行 main では差 0 (1701 = 1701) だが、wave 側で local main を merge し main を wave tip へ
  ff-only する現行の land 手順は、この topology を毎回作っている。
- 同じ非対称は選択集合の中でも再出現する。実測で implementation 層に 2 件、CAB 層に 24 件、
  計 26 commit が「監査対象ではあるが、その規則の適用対象と判定されていない」状態にあった。
  base 層の穴が将来のものであるのに対し、こちらは現に開いている。
- 述語を統一したときの一回性コストは実測で新規違反ちょうど 1 件 (`333605d6…` の
  `missing-codex-author`) であり、その種別は既知違反台帳が受けられる 2 種の一方である。
  base / scope / CAB 層の新規違反は 0 件だった。CAB 層の 24 件は全件で raw と canonical の
  `Co-Authored-By` 認識数が一致している。
- seed を「集合」のまま扱うのは、Co-Authored-By 規則が branch ごとに独立した導入 commit を
  持ちうるためである。一意 root を要求する設計は、独立 lineage 上に 2 つの導入がある履歴で
  root が 0 件になり、fail-closed なら実行不能、片方を任意採用すれば他方の明示 range が緑へ緩む。
- `C = p` を第 1 項で真にすることで、規約が導入 commit 自身にも適用されるという契約を保つ。
- git だけでは「epoch 前に書かれて後日 merge された commit」と「epoch 後に古い base 上で書かれた
  commit」を区別できない。author/committer date は改変可能で信頼根拠にならず、reflog は commit
  object に束縛されない。ゆえに reachability は「HEAD へ取り込まれた時点で現行 policy 下として
  扱う」という保守的近似であり、真の legacy を拒否しうる代償は SHA ごとのユーザー裁定で受ける。

**却下した選択肢:**
- **lineage を据え置き、判定できない適用を診断として公開する** — rc を変えないので安全に見えるが、
  後から追加される規則ごとに同じ穴が再発する。診断の追加は D221 が定めた「既知 0 件のときの
  逐語出力は完全に不変」という receipt 契約も破り、消費側は stdout を捨てているので receipt にも残らない。
- **4 層の epoch resolver を共通化し単一 epoch へ畳む** — Co-Authored-By 規則の branch-local seed で
  成立しない (上記)。探索 tip を暗黙 `HEAD` にすると、明示 range で現在検出できている配置違反が
  検出されなくなる経路も生じる。
- **選択集合だけを素の range へ変え、適用述語は触らない** — 現に開いている 26 件の穴が残る。
  base 層は今日 no-op なので、この案は現行 main に対して何の効果も持たない。
- **commit の日時で epoch 拘束を決める** — date は改変可能で、正しさ防壁の根拠にできない。
- **merge 時 attestation の新 trailer を作る** — 真の legacy と規約違反を区別できる唯一の形だが、
  新しい trailer 種別と検証機構が要り、D205 のプロトタイプ基準では過剰である。
- **恒久形を本 wave で実装する** — 契約本文の改訂、既知違反台帳への追加、forward correction の
  受理集合変更の 3 つを伴い、いずれもユーザー裁定の領分である。台帳追加を wave 側で決めるのは
  防壁の恒久緩和を既成事実にすることであり、D221 が同じ理由で却下した経路と同型である。
