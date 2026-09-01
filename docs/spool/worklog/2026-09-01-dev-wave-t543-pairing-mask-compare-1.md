---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t543-pairing-mask-compare
seq: 1
title: [T-543] 対比の要求を復元後の値同士で判定するようにした — 関門が実際には対比していない状態を閉じた (コード + テスト、branch worktree-dev-wave-t543-pairing-mask-compare、変異 6/6 KILLED)
---

## 本文

- D858 の実装。gate と ident の述語比較を生文字列から復元後の mask 同士へ変えた。
- **穴が現時点でも生きていることを、静的推論ではなく実発火で確かめてから着手した。** repo 外の
  使い捨て probe で、balanced の gate 側を ident と同じ mask 31 にし述語へ外側空白だけ足した
  偽造文書を作り、実 module に通した。`_validate_schema` (name-mask 束縛層) も
  `assert_s1b_pairing` (対比関門) も**受理**した。生文字列は別物・復元後の mask は同一。
  原因は正準述語言語が `text.strip()` で外側空白を明示的に受理することである。
- **裁定文の「measurement freeze の pairing 複製」は複製ではなかった。** 実体は known-axes への
  射影委譲であり、修正は自動で波及する。T-080 移行の pairing も同関数を既定に使う。
  よって consumer 側の編集は 1 file も要らなかった。波及先の編集ゼロで閉じている。
- **段 2 の計画子が親 brief の不変条件を 1 件反証した。** 親は「`build_document` の出力 bytes は
  不変」と書いていたが、`s1_known_axes_freeze.py` は自分自身の SHA-256 を出力の
  `generator.sha256` へ入れる自己ハッシュ generator なので、同 file を 1 byte でも変えれば
  既定引数の出力 bytes は必ず変わる。守れるのは「凍結 file を編集しない」と
  「`generator_sha` を明示注入した再構成で validator 以外を変えない」の 2 点だけである。
  親は段 3 の投入前に brief を訂正した。
- **generator hash の drift は本 wave 以前から存在する。** 着手時点の main で
  `python3 orchestrator/campaign/s1_known_axes_freeze.py verify` は既に rc=1
  (`recorded=1d4d45a3... actual=9cc9f877...`) で落ちていた。T-080 移行 receipt が同 pointer を
  metadata-only と分類している。本 wave はこの drift を直さず、隠しもしていない。
  凍結成果物を実検証する 2 テストは 2026-08-12 裁定で保留 (skip) されたままである。
- **段 3 のレンズ A が本 wave の分岐点になる所見を出した。** 「負例が balanced の mask 31 同士だけ
  だと、`workload == "balanced"` 限定や `mask == 31` 限定の誤実装が全テストを通る」。
  ユーザー依頼の「述語を読むだけでは恒真かどうか分からない」に直接触れるため採用し、
  負例を 3 workload すべてと mask 31 以外の同一 mask へ広げることを必須にした。
- **変異は 6 件登録し全件 KILLED、期待 node 完全一致、baseline PASSED。** 単なる有効・無効化
  (M1) と過剰拒否 (M2) に加え、生文字列比較への回帰 (M3)、workload 限定の誤実装 (M4)、
  mask 31 限定の誤実装 (M5)、例外変換の除去 (M6) を登録した。**M4 と M5 が別々の負例を殺した**
  ことが、関門が workload 値にも mask 値にも限定されず汎用に効いていることの機械的な証拠である。
  M2 は受理集合を縮小する wave に要求される「承認外の過剰拒否の正例」に当たり、正例が恒真で
  ないことを示す。probe は全件 SURVIVED 期待で走らせて観測 node を採取し、それから期待 node を
  確定した。
- **段 6 のレビュー B が NO-GO を出したが、コード欠陥ではなく親の手順不足だった。** 焦点走の
  対象集合から受入所要時間台帳の 90% 被覆検査が漏れていた。実走して緑を確認し閉じた。
  レビュー A は所見ゼロで GO。fix 子は起動していない。
- **consumer 焦点走で赤が出たが非帰属だった。** login node の局所走行がメモリ上限で OOM 中断
  (`scope-outcome-cap-oom`) したための赤で、runner が計算ノードへ自動 fallback した本走は
  240 passed / 17 skipped で緑だった (child rc=0)。
- 実装子 (Codex role=author) は計算ノードへ pytest を投げられず (sandbox が socket を拒否)、
  全試行が rc=16 だった。子は緑を主張せず「実装済み・未実走」と報告し、実測は親が行った。
- 実装 commit `f337df518`、main 取り込み merge `e36b05105`。push はしていない。

## 次の一手差分

### 完了

- [T-543] 対比の述語比較を復元後の mask 同士へ変え、consumer 波及を確認し、変異 6/6 KILLED で
  対比が実際に効いていることを正例・負例の両方から示した。
  remaining: none
  base: 3a87962798b9bb4ca0f2228fe577e96800c6ec320c1779b78e478b949d997251

### 新規

- {{T:pairing-mask-behavioral-equivalence}} **P3・新規・ユーザー裁定待ち**: 復元 mask の非同一は
  構成値の別性を保証するが、workload 上の観測可能な挙動差までは保証しない。段 3 のレンズ A が
  実測を挙げて指摘した — 一部の要因は全 workload で発火頻度 0 のため、異なる mask でも挙動が
  同一になる組合せが実在する ([T-543] が閉じた mask 同一の経路とは別)。本 wave は D858 が命じた
  「復元後の値同士の比較」までを実装し、挙動同値性の判定は別の性質として実装しなかった。
  **推奨**: 現行の 3 対 (mask 8 対 31、4 対 31、8 対 31) はいずれも挙動上も別物であることが
  実測で確かめられているため、当面は追加実装せず、対比の候補を増やすときに再検討する。
