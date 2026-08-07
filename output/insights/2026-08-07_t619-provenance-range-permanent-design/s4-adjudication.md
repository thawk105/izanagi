# 段 4 裁定 — [T-619] provenance 既定監査の範囲

基準 HEAD = `bb824d8b7fff427eb61d09cf3d9354359914c99c`。段 2 プラン + 段 3 レンズ A/B の全所見を
real/refuted、採用/不採用、scope 内/外で裁定する。

## 裁定表

| # | 出所 | severity | 判定 | 採否 | scope | 処置 |
|---|---|---|---|---|---|---|
| A1 | lens A | blocker | **real** | 採用 | 内 | 親の (P2)「epoch 述語は lineage 据え置き」を**撤回**する。将来 epoch でも同じ topology で違反が通る |
| A2 | lens A | blocker | **real** | 採用 | 内 | 不変条件 3 の「forward correction の受理集合を変えない」は**偽**。選択集合拡大は correction candidate を増やしうる。方向は strict 化 (rc 0→1) なので規律 2 には整合。裁定項目へ |
| A3 | lens A | must-fix | **real** | 採用 | 内 | 段 2 の「共通 epoch resolver」案は探索 tip が未定義で明示 range の CAB を fail-open にしうる。**resolver 統合案ごと却下**し B1/B2 と併せて seed 集合方式へ差し替え |
| A4 | lens A | must-fix | **real** | 採用 | 内 | HEAD race。恒久形は HEAD を**一度だけ full SHA へ解決**し、policy/range/epoch/ancestry の全 query へ同じ値を渡す。終了時 drift は rc=2 |
| A5 | lens A | must-fix | **real** | 採用 | 内 | gap 診断の stdout 追加は D221 の「既知 0 件のときの逐語出力は完全に不変」を破る。**恒久形 v2 では gap 診断を持たない**ので所見ごと解消する (下記) |
| A6 | lens A | nit | **real** | 採用 (nit) | 内 | stale の rc=2 が既存 rc=1 を飲む。受理集合は広がらないので意図した優先順位として設計へ明記するだけ |
| B1 | lens B | blocker | **real** | 採用 | 内 | CAB は branch-local seed が複数あり単一 epoch へ畳めない。**seed 集合を保つ統一述語**へ差し替える |
| B2 | lens B | blocker | **real** | 採用 | **外** | `-S "scope="` の最古 hit は意味的に一意でない。**T-619 が作る欠陥ではなく既存の潜在欠陥**。新規タスクへ起票 |
| B3 | lens B | blocker | **real** | 採用 | 内 | reachability は「非遡及」文書契約と両立しない。恒久形は**契約本文の改訂を必須**とし、family 余 6 bytes では等価縮約が要る。裁定項目へ |
| B4 | lens B | blocker | **real** | 採用 | **外** | `_build_ancestry` の pickaxe argv が 51,151 commit で ARG_MAX 超過。現行 1,702 なので約 49,000 commit の余裕。**既存の scale 限界**。新規タスクへ起票 |
| B5 | lens B | must-fix | **real** | 採用 | 内 | 真の legacy 違反のうち scope/CAB/形式 kind は D221 台帳にも correction にも載せられない。裁定項目へ。**ただし実測では現行 main の新規違反は台帳可能な kind 1 件だけ** |
| B6 | lens B | must-fix | **real** | 不採用 (不成立化) | 内 | gap が dev-wave receipt に残らない。A5 の帰結で恒久形 v2 に gap 出力が無いため前提が消える。receipt consumer 一般の欠落は [T-621] が既に持つ |
| B7 | lens B | nit | **real** | 採用 | 内 | 親の M6「順序非依存」は verdict にのみ成立。出力順は既存テストが固定。`--reverse` を保存する |

段 2 プラン由来で採用する項: policy 前置の保存、`--reverse` の保存、shallow / graft / replace /
非一意 policy add の既定監査 rc=2 fail-closed、`--message-file` と明示 `--range` の分離。

## 親の provisional 裁定の帰趨

- (P1) 選択集合 = 素の `policy..HEAD` — **維持**。段 2・レンズ双方が単調性を追認。
- (P2) epoch 述語は lineage 据え置き — **撤回** (A1)。実測 M13 でコストが 1 件と読み切れており、
  据え置きの根拠だった「コスト不明」が消えた。
- (P3) gap を診断として公開 — **撤回** (A5 + 統一述語)。統一述語を採ると lineage で決まらない
  適用が存在しなくなるため、公開すべき ambiguity 自体が消える。
- (P4) D221 台帳が受け皿 — **限定して維持**。台帳が受けられるのは `missing-ai-agent` と
  `missing-codex-author` の 2 種だけ (B5)。
- (P5) merge 時 attestation は過剰 — **維持**。段 2・レンズとも代案を出していない。

## 恒久形 v2 (本 wave の設計成果物。実装はしない)

### 統一述語

4 層すべてを 1 つの述語へ揃える。規則 R の **seed 集合** `seeds(R)` を、R を導入した commit の
検出結果 (base は `--diff-filter=A` の hit、他 3 層は pickaxe hit) の集合とし、権威 tip を `H` とする。

```
applies_R(C) := C ∈ Anc(H) かつ ( (∃p ∈ seeds(R): p ∈ Anc(C)) または (¬∃p ∈ seeds(R): C ∈ Anc(p)) )
```

`Anc(X)` は `X` 自身を含む祖先集合。

- 第 1 項が現行の lineage 述語 `L_R`。第 2 項が今回足す「どの seed の祖先でもない」= 側枝分。
- `C = p` は第 1 項で真になり、導入 commit 自身にも規約が適用される (契約 6 行目)。
- seed が複数でも一意 root を要求しないので B1 が解消する。`commits[0]` / 「全 hit の祖先」を
  選ぶ必要が無くなり A3 も解消する。
- base 層へ当てると `{policy} ∪ (Anc(H) \ Anc(policy))` = 素の `policy..HEAD` + policy 前置に一致する。
  **選択集合と適用述語が同一の式になる**のが本設計の要点である。
- lineage で決まらない commit は第 2 項で「適用する」に確定するので、公開すべき ambiguity が残らない
  (P3 撤回の根拠)。

### 適用境界

- **権威ある既定監査 (`--range` 無し) だけ**に適用する。明示 `--range` は一意な権威 tip を持たないため
  現行 lineage 述語を残す (段 2 の境界を採用)。
- `--message-file` 経路は 1 bit も変えない。
- `H` は起動時に一度だけ full SHA へ解決し、全 query へ同じ値を渡す。終了時に HEAD が動いていれば rc=2 (A4)。
- shallow / graft / replace / 非一意 policy add は既定監査で rc=2 (段 2)。
- stale (rc=2) は新規違反 (rc=1) より優先する。受理集合は広がらない (A6)。

### 現行 main での効果 (すべて実測)

| 層 | ancestry | plain | 差 | 新規違反 |
|---|---:|---:|---:|---:|
| base `50c1ef4e` | 1701 | 1701 | 0 | 0 |
| scope `2f0245c1` | 1579 | 1579 | 0 | 0 |
| implementation `8c6d3f3b` | 1238 | 1240 | 2 | **1** |
| CAB `9b26b3bd` | 1182 | 1206 | 24 | 0 |

新規違反 1 件 = `333605d680ec15f3f74b00e9e2746ae317b85dc5` の `missing-codex-author`
(`output/insights/2026-07-28_t142-review-verbatim/count_abort_reasons.py` と `count_frontier.py`)。
種別は D221 台帳が受けられる 2 種の一方である。

## 実装しない裁定 (`DW-S04`)

本 wave は段 5・6 を飛ばし `4→7→8→9` とする。理由は 3 つで、どれも単独で十分である。

1. ユーザーが scope を「恒久形の設計まで」と指定した。
2. 恒久形は**契約本文の改訂を要する** (B3)。文書契約の変更は裁定の領分であり、
   family 余 6 bytes では等価縮約 (−168 bytes 案) の採否も裁定が要る。
3. 恒久形は `333605d6` を新規違反にする。緑を保つには D221 台帳へ 1 件足す必要があり、
   台帳追加は防壁の恒久緩和としてユーザー裁定の領分である (D221 の却下項と同じ理由)。

実装差分がないため**変異 matrix と受入全走は対象外**である (`DW-S04`)。
`DW-M01` の変異事前登録も対象外。

## ユーザー裁定へ返す項目

1. **統一述語を既定監査へ入れるか。** 入れるなら `333605d6` を D221 台帳へ足して緑を保つか、
   既定監査を rc=1 のまま運用するか。
2. **契約本文 (`docs/ai-provenance.md`) の改訂を許すか。** 非遡及の定義を lineage から
   「seed の祖先でないこと」へ書き換える必要がある。family 予算のため等価縮約 (−168 bytes) を伴う。
3. **forward correction の受理集合が変わることを受け入れるか** (A2)。方向は strict 化。
4. **scope / CAB / 形式 kind の legacy 違反に受け皿が無いことを受け入れるか** (B5)。
   現行 main では 0 件だが、将来の pre-policy fork の land を恒久的に止めうる。
5. 明示 `--range` を lineage のまま残す境界を採るか。

## 新規起票 (scope 外の real 所見)

- **B2**: `_scope_policy_commit` の `-S "scope="` は意味的に一意でない。既存の潜在欠陥。
- **B4**: `_build_ancestry` の pickaxe argv が約 51,151 commit で ARG_MAX を超え、既定監査が rc=2 で
  実行不能になる。現行 1,702 commit。
