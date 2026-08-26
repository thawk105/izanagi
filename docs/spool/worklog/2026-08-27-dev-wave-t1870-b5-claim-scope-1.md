---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t1870-b5-claim-scope
seq: 1
title: [T-1870] B-5 の主張を D1067 の条件付き優越へ揃え、届け方は版の追加でなく README の stale 注記を選んだ (docs のみ、branch worktree-dev-wave-t1870-b5-claim-scope、実装面差分ゼロにつき変異 matrix は DW-S04 の免除、受入全走は実施)
---

## 本文

- **届け方の選択 (依頼が明示的に二択で渡したもの)。** D1067 の「論文素材 §8 の B-5 欄の文言も
  同じ範囲へ揃える」を、**`docs/paper-story/README.md` の「最新スナップショット以後に確定した
  こと（stale 注記）」への追記**で満たした。`claim-evidence/` へ新しい日付を足す案は採らなかった。
  理由は `docs/paper-story/README.md` 自身の 2 つの規則である。(a)「このディレクトリの位置づけ」が
  「一項目の決着を届けたいだけなら、版を足さずに本 README の『最新スナップショット以後に確定した
  こと』で指す」と定めており、今回はまさに B-5 1 項目の決着である。(b)「claim-evidence 系列の規則」が
  新しい日付を入力 5 節 (最新版の §3 / §6 / §7 / §8 / §9) 全体からの再導出に限り、一項目の差分改訂を
  新日付として置くことを「更新しなかった項目の stale が『その日付時点でそう主張した』という新しい嘘に
  変わる」として名指しで禁じている。B-5 だけを直した全面再導出は、残る数十項目の現在地を同日の
  一次資料で取り直す作業を伴い、取り直さなければその嘘を作る。凍結物である `2026-08-26.md` と
  `claim-evidence/2026-08-26.md` は 1 byte も触っていない。
- **注記が覆す先は 4 か所で、うち 1 か所は着手前の想定になかった。** 版 §8 の B-5 欄に加えて、
  `claim-evidence/2026-08-26.md` の §4.3 (B 群) の B-5 行、§2.4 (いま書けない主張) が
  「LLM でなければできない」に付けた回復条件 `後続別主張: B-5`、そして §5.3 (合成能力についての限界)
  の limitations 統制稿にある「LLM でなければ到達できないとも書けない」の**理由**である。
  最後の 1 つは文自体は正しいままだが、添えた理由 (対照が未取得) が D1067 の後では足りない —
  対照を取っても必要性は言えない、が正しい理由になる。**証拠の現在地 (未取得) はどの欄でも動かない。**
- **一次資料だけを出所にした。** 主張範囲・理由・D52 案の不採用はすべて `docs/decisions.md` の
  D1067 本文から取り、版の記述を出所にしていない。roadmap が別の場所で「LLM の因果的必要性は未実証」
  と書いていることとは矛盾しない (非証明の陳述であって主張ではない) ので、roadmap は触っていない。
- **凍結 bytes の pin 閉包 (DW-O09) を docs path でも取った。** repo 全体の Python 走査で
  `docs/paper-story/` を bytes pin するのは `figures/*.provenance.json` の 2 test だけで
  (`orchestrator/tests/test_backoff_figure_provenance.py`、`test_s1_9pair_figure_provenance.py`)、
  README・版本文・claim-evidence を pin する台帳・test・trust root は 0 件だった。今回の編集面は
  この閉包の外にある。
- **子は起動していない。** docs-only・実装面差分ゼロ・正しさ防壁と受理集合に変化なしのため
  `DW-C00` の既定の軽量版とし、段 2・3 と段 6 の review 子を省いた。設計択一 (届け方の二択) は
  README が正本として決着させているので「割れる」に当たらないと裁定した。
- 焦点走 `orchestrator/tests/test_check_docs.py` = 567 passed / 3 skipped、
  `python3 tools/check_docs.py` = 違反なし。

## 次の一手差分

### 完了

- [T-1870] B-5 の主張範囲を D1067 の条件付き優越へ揃え、README の stale 注記として届けた。
  remaining: none
  base: eba1b750db3a2913e78380b475314797298cb9fb07ba30ce334e476fa5fcd16a
