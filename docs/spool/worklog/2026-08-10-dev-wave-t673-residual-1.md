---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-10
wave: dev-wave-t673-residual
seq: 1
title: [T-673] §56 の残余 3 項を消化した — (5) は起票、(6) は insights の逐語凍結で既に充足、(7) は既存 L2 節への統合 1 件と台帳 1 件へ振り分けた (docs のみ、branch worktree-dev-wave-t673-residual)
---

## 本文

- **裁定の一次資料。** rulings-inbox §56 (2026-08-10、発話「推奨通りで」) の [T-673] 7 項のうち、
  (5) G 起票可 / (6) 再生成 / (7) [T-700] (b) 規範下で L2 か台帳、の 3 項が対象。台帳側の本文は
  `docs/archive/worklog-phase3-0810-358.md`、選択肢の逐語は
  `output/insights/2026-08-09_t673-transition-quantifier-ruling/RULING-PACKAGE.md`。
  起動時に worklog 末尾 (367) まで消化状況を確認し、[T-673] が carry stub のままで 3 項とも
  未消化であることを実測してから着手した。
- **(5) の起票。** G = loader / issuer への integration pin。量化縮退の候補検査はすべて private
  gate を直接叩いており、gate が実際に効く 2 層 (production loader、発行 tool) を通っていない。
  {{T:loader-issuer-integration-pin}} として起票した。
- **(6) は追加作業なしで既に充足していた。** 裁定が前提にした「逐語は insights へ凍結する」を
  実測で確認した — `verbatim-probes-and-instruments.md` が候補テスト 5 本を行数と SHA-256 付きで
  1170 行にわたり保持している。よって将来採用時の再生成は成立する。
  **side branch `worktree-dev-wave-t673-probe` (probe commit `3912c7fc`) は現存する。** 裁定文は
  「side branch は保持しない」だが削除の実行指示とまでは読めないため、branch 削除はユーザー指示が
  あるときだけという規律に従って削除していない。可否はユーザーへ返す。
- **(7) の振り分けと、その根拠。** 段 8 候補 2 件を次のように分けた。
  - 候補 1 のうち使い捨て worktree 経路 (`tools/mutation_worktree.py`、`--scratch-root` は既存
    directory 必須で全 registered worktree の外) は `DW-O19`「tracked file の一時変異」へ統合した。
    主 tree を変異させない代替経路であり、発火時点 (一時変異の直前) も一致するため意味を保つ。
    追記後 861 bytes / 単節予算 1000 bytes。
  - 候補 1 の `estimated_run_seconds` の単位と、候補 2 の spec 使い回し不可は、意味を保って入る
    既存 L2 節が無い。台帳 ({{F:mutation-spec-field-contract-unwritten}}) と memory で担った。
  - **[T-700] (b) の 3 条件検査は発火しない。** 同規範が課されるのは新規 L2 節の admission だが、
    本 wave は既存 L2 節へ統合しただけで新規節を作っていない。新規節を作れば
    `tools/check_docs.py` の受理集合が変わって実装面になり、かつ並行 wave
    `dev-wave-t700-t695-l2-admission` (作業中) がその所有者である。なお同規範自体は
    `docs/decisions.md` へ未記録であることを実測した (`T-700` の grep hit 0 件)。
- **候補 2 は実害ゼロの near miss である。** [T-673] wave の変異台帳 7 本はいずれも `MISMATCH` 0 で、
  同 wave は候補ごとに spec を分けて制約を回避していた (`s4-adjudication.md` の matrix 2 / matrix 3)。
  仮想的懸念だけで台帳を変えない契約に触れるため、F の事象欄へ実害ゼロと回避の実測を明記した。
- **軽量版・子ゼロで実施した。** docs-only で実装面ゼロ、正しさ防壁に触れず受理集合も変えないため、
  段 2 / 3 / 5 / 6 の子を省いた。変異 matrix はコードとテストの差分がゼロのため免除。

## 次の一手差分

### 更新

- [T-673] **P2・§56 の (5)(6)(7) は消化済み → 残余は (3) と (4)**: (5) は
  {{T:loader-issuer-integration-pin}} として起票、(6) は insights の逐語凍結で充足 (side branch
  `worktree-dev-wave-t673-probe` の削除可否だけユーザーへ)、(7) は `DW-O19` への統合 1 件と
  {{F:mutation-spec-field-contract-unwritten}} 1 件へ振り分け済み。残るのは (3) 本番編集禁止の下で
  D (走査完全性 guard) を測る別 wave の起票と、(4) E (変異 spec の恒久登録) を関連 wave の段 4 で
  再登録させる運用義務の所在。正本 =
  `output/insights/2026-08-09_t673-transition-quantifier-ruling/RULING-PACKAGE.md`
  base: 44b6101322c46e015fb6ae97fa59bd5ef61c3aa60b24b6910c7ad7ae11a5b3d2

### 新規

- {{T:loader-issuer-integration-pin}} **P2・新規 (§56 の [T-673] (5) で起票可)**: 量化縮退の候補検査は
  すべて private gate を直接叩いており、gate が実際に効く 2 層 (production loader、発行 tool) を
  通っていない。M > N の合成 registry で両経路を通す integration pin を追加する。放置すると、
  private gate は緑なのに loader / issuer 経由では縮退が素通りする経路が受理集合に残り、
  certified 選択の証拠側が「gate を通った」と名乗れない。正本は同 RULING-PACKAGE の選択肢 G。
