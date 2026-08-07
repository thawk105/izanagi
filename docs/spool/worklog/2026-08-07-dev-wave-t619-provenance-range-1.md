---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-07
wave: dev-wave-t619-provenance-range
seq: 1
title: [T-619] 既定監査の範囲の恒久形を設計し、実装は 3 点の裁定へ返した — 依頼が指した base 層は今日も no-op だが、同型の穴が epoch 層で現に 26 commit ぶん開いていた (docs のみ、実装差分なし、branch worktree-dev-wave-t619-provenance-range)
---

## 本文

- **依頼は「恒久形の設計まで」。本 wave は実装差分を持たない。** 段 4 で「実装しない」と裁定し
  段 5・6 を飛ばしたため、**変異 matrix と受入全走は対象外**である (`DW-S04`)。
  `tools/check_ai_provenance.py` の挙動は 1 bit も変えていない。完了・一部実装と読ませてはならない。
- 材料正本は `output/insights/2026-08-07_t619-provenance-range-permanent-design/README.md`、
  裁定表と恒久形の全文は同ディレクトリの `s4-adjudication.md`、逐語は `verbatim/` にある。
  設計判断は {{D:provenance-uniform-epoch-predicate}}。
- **依頼が指した穴 (base 層) は今日も no-op だった。** 起点 `bb824d8b` で
  `--ancestry-path 50c1ef4e..HEAD` = 1701、素の range = 1701 で差 0。起票時の 1659 = 1659 と同じ。
- **同型の穴が 1 つ下の層で現に開いていた。** 実装面 Codex author 契約の epoch (`8c6d3f3b`) で
  1238 対 1240 の差 2 件、Co-Authored-By 配置規約の epoch (`9b26b3bd`) で 1182 対 1206 の差 24 件。
  計 26 commit が「既定監査の対象ではあるが、その規則の適用対象と判定されていない」。
  scope epoch (`2f0245c1`) は 1579 対 1579 で差 0。
- **差を作るのは dev-wave の land 手順そのもの。** wave 側で local main を merge し main を wave tip へ
  ff-only する形は、「ある時点の main tip から見て子孫でない commit が後から main へ入る」状況を
  毎回作る。実 repo の anchor `f85e16e2` では 62 対 79 で差 17 件、中身は [T-503] wave branch だった。
  合成 repo を作らずに再現できたので、demo repo は作っていない。
- **一回性コストは実測で新規違反ちょうど 1 件。** 出荷済み `validate_implementation_author` に実
  message と実 path を渡して直接測り、`333605d680ec15f3f74b00e9e2746ae317b85dc5` の
  `missing-codex-author` 1 件だけが増えると確認した (insights 配下の `.py` 2 本を含むのに Codex
  author 行がない。Claude author・Codex researcher・Codex reviewer はある)。CAB 層の 24 件は全件で
  raw と canonical の認識数が一致し違反 0 件、base / scope 層も 0 件。
- **親の暫定裁定 2 つを敵対レビューで撤回した。** (P2)「epoch 述語は lineage 据え置き」は、
  後から追加される規則ごとに同じ穴が再発するため撤回。(P3)「判定できない適用を診断として公開」は、
  統一述語では判定不能が残らないうえ D221 の receipt 不変契約を破るため撤回。
- **段 2 のプランの中核も 1 つ却下した。** 「4 層の epoch resolver を共通化し単一 epoch へ畳む」案は、
  Co-Authored-By 規則が branch ごとに独立した導入 commit を持ちうるため成立しない。
  seed を集合のまま扱う統一述語へ差し替えた。
- **当初の不変条件が 1 つ偽だった。** 「forward correction の受理集合を変えない」は成立しない。
  選択集合が広がると `AI-Agent-Correction` の candidate が増えうるので、`PR-C01` の exact 1 件規則に
  当たって既定監査が赤になる経路がある。方向は strict 化なので規律 2 には整合するが、
  受理集合が変わること自体は裁定項目として返した。
- **恒久形は文書契約の改訂を必須にする。** 現行本文の「導入 commit 自身と以後」は lineage 読みで、
  統一述語は側枝 commit を拘束するため実装と食い違う。`docs/ai-provenance.md` +
  `docs/provenance/**` の family byte 余は 6 しかないので純増の加筆は物理的に不可能で、
  同一義務を 4 回書いている 348 bytes を 180 bytes へ統合する等価縮約案 (net −168) を裁定へ添えた。
- 段 3 の敵対レビューは blocker 6・must-fix 5・nit 2 で、**全件を real と裁定**した。refuted は 0 件。
  scope 外と裁定した 2 件は新規起票した。
- 工数: codex 子 3 本 (段 2 プランナ 1、段 3 敵対レンズ 2)、いずれも `gpt-5.6-sol` /
  `reasoning=max` / `sandbox=read-only` で rc=0。親の実測はすべてログインノードで行った。

## 次の一手差分

### 更新

- [T-619] **P1・ユーザー裁定待ち (恒久形の設計は完了、実装は裁定待ち)**: 恒久形は
  {{D:provenance-uniform-epoch-predicate}} の統一述語。裁定が要るのは 5 点 — (1) 統一述語を既定監査へ
  入れるか、入れるなら `333605d6` を既知違反台帳へ足して緑を保つか rc=1 のまま運用するか、
  (2) `docs/ai-provenance.md` の非遡及規定の改訂を許すか (family 余 6 bytes のため等価縮約
  net −168 bytes を伴う)、(3) forward correction の受理集合が strict 側へ変わることを受け入れるか、
  (4) scope / CAB / 形式 kind の legacy 違反に受け皿が無いことを受け入れるか、
  (5) 明示 `--range` を lineage のまま残す境界を採るか。成果物影響: 研究成果物の値は不変で、
  変わるのは commit gate の受理集合。放置すると epoch 層の 26 commit が規約適用外のまま残り、
  今後 epoch を追加するたびに同じ穴が増える。
  base: 97c80cdb6b275bddbfd7dfd0bf068ccb44c81ce81b67cb5027fbd99b8323d22e

### 新規

- {{T:provenance-scope-needle-ambiguity}} **P3・新規**: `_scope_policy_commit` の
  `-S "scope="` は意味的に一意でない。実 repo でも hit は既に 2 件あり、現在は最古が偶然
  正しい導入 commit になっているだけである。契約本文の非規範的な箇所に `scope=` が現れると
  そこが epoch と誤認され、本来 legacy の commit が scope 違反として拒否されうる。
  scope finding は既知違反台帳に登録できないため救済経路がない。成果物影響: 研究成果物の値は
  不変で、変わるのは commit gate の受理集合 (rc=0 で受けるべき履歴が rc=1 になる)。
  本 wave が作った欠陥ではなく既存の潜在欠陥である。
- {{T:provenance-audit-argmax-scale}} **P3・新規**: `_build_ancestry` の pickaxe は選択集合の
  全 SHA を positional argv へ展開するため、約 51,151 commit で `ARG_MAX` (この環境で
  2,097,152 bytes) を超え、既定監査が rc=2 で実行不能になる。現行 1,702 commit なので約 49,000
  commit の余裕がある。bitset のメモリも commit 数の二乗で伸び、4 GiB を初めて超えるのは約
  253,565 commit。成果物影響: 到達すると commit gate が違反の有無によらず実行不能になり、
  受理集合が事実上空になる。既存の scale 限界であり本 wave が作ったものではない。
