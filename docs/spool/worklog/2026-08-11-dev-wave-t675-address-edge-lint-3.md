---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t675-address-edge-lint
seq: 3
title: cleanup-branches command の住所 (address edge) を構造 lint で塞いだ — 事前登録した変異 2 件が「殺せない負例」で不成立だと親とレンズが独立に見つけた (コード + docs、変異 8/8 KILLED、branch worktree-dev-wave-t675-address-edge-lint)
---

## 本文

- **ユーザー裁定 R1〜R4 (archive worklog 381) をそのまま実装した。**正本は
  `output/insights/2026-08-10_t675-pin-semantic-gap/package.md`。R1 = 呼称を
  「住所 (address edge) の構造 lint」へ ({{D:address-edge-structural-lint}})、R2 =
  `docs/skill-self-improvement.md` の既存 2 行の精密化置換 (5997 → 5996 bytes、上限 6000)、
  R3 = `.claude/commands/cleanup-branches.md` の `F26` × `` `docs/failures.md` `` 同一可視行
  共起 1 件だけ、R4 = `DW-G05` 上 backlog。
- **`DW-G05`: 実装しなくても certified 選択・レポート・試行台帳のどの値も受理集合も参照も
  変わらない。変わるのは `check_docs` と AI 作業手順の受理集合だけである。**したがって
  backlog であり、本 wave はユーザー指示による単独 wave として実行した。
- **事前登録した変異 2 件が「殺せない負例」のせいで不成立だった。**段 4 で登録した M2
  (ID の隣接判定を単純部分文字列へ緩める) と M3 (path の backtick 要求を外す) は、当初の負例が
  `F260` と `archive/docs/failures.md.bak` を**同時に**使う二重欠陥だったため、片方の guard を
  壊しても他方が拒否し続けて 1 件も赤にならない。**親の検算と段 6 の敵対レンズが独立に同じ結論へ
  達した。**負例を guard ごとに独立させて初めて、2 つの guard に positive control が付いた。
  変異表を書いた時点では「2 本とも KILLED」と読めていた。
- **段 3 と段 6 の敵対レンズは 4 本すべて NO-GO を返し、すべて実在の欠陥だった。**段 3 は
  単純部分文字列一致が `F260` / 別 path / link definition / 表セル横断で偽 edge を作れることを
  示し、親案の (P1) を破棄させた。段 6 は finding の対象 path が未検証であること (対象 command を
  差し替える変異が負例をすり抜ける) と、frontmatter の `description:` に偽 edge を置ける迂回を
  見つけた。所見ゼロは 1 本も出ていない。
- **親 brief の主張 3 件が反証され、訂正した。**(i)「repo の `*.py` 全体で sha256 定数は 2 本だけ」
  は誤りで、正しい主張は「`docs/skill-self-improvement.md` を pin する sha256 定数は無い」だけ。
  (ii)「2 literal の同一可視行共起を要求する検査は repo に 0 件」は誤りで、dispatch inventory が
  既に同一可視行から typed edge を構成して期待集合と比較している。**純増は検査パターンではなく
  「cleanup command の F26 edge という対象」だけである。**(iii)「受理集合は変わらない」は
  無限定に書いてはならない。
- **scope 外の real 所見 2 件を実装せず裁定候補として返した。**(s1) `check_docs` は hooks・CI・
  pre-commit のいずれからも呼ばれず、land も fold 経路でしか呼ばない。**新 lint が効くのは
  `python3 tools/check_docs.py` を明示的に走らせた層だけである。**(s2) inline の hidden HTML、
  4-space indented code block、link definition の quoted title、打ち消し線、否定形の prose では
  偽 edge を作れる。いずれも Markdown の意味解釈が要り `DW-G03` の族一般化にあたる。
  → {{T:address-edge-lint-layer-coverage}}
- **F173 の恒久対応にある「機械化は `docs/dev-wave/**` の byte 予算に阻まれており」は誤りだった。**
  実装面は `tools/check_docs.py` (Python) にあり `TextLimit` の対象外である。当初は
  「追記のみの台帳なので訂正できない」と裁定して F1 の再発だけを記録したが、**wave 中に別 wave が
  land した `supersede 追記` 節でこの前提が消えた**ため、F173 へ supersede 行を追記して古い記述を
  明示した。誤記の型そのものは F1 の再発として残す。
- **codex 子は 2 回とも pytest を実走できなかった。**login の headroom 不足 (約 1.73 GB /
  user slice 約 12.5 GiB 使用) と sandbox 内の `qstat` 不通で rc=16。子は正直に
  「実装済み・未実走」と申告し、親が `--force-dispatch` で計算ノードへ投げて実測した。
- **段 8 の改善候補 1 件は byte 予算に阻まれ、裁定へ返した。**候補は `DW-M08` への 1 文
  「期待 node と記録 node は集合の完全一致で判定するので、runner の test 集合を変異の影響範囲へ
  絞る」。実測すると `docs/dev-wave/**` の L1.5 unique footprint が 9688 bytes となり予算 9566 を
  122 bytes 超える (追記は 134 bytes、超過前の実測余白は 12 bytes)。**byte を捻出するために
  既存の義務を削るのは F173 そのものなので行わず、追記を撤回した。**この規律は本 wave が
  塞いだ穴の当事者そのものである。→ {{T:mutation-expected-node-scope-doc}}
- **land が 1 度 provenance 全履歴監査で拒否された (rc=29)。**原因は親が peer の land 通知を受けて
  手動で作った merge commit で、両親がともに `tools/check_docs.py` と
  `orchestrator/tests/test_check_docs.py` を変更していたため merge 結果がどちらの親とも異なり、
  `DW-O17` の Codex `role=author` を要する。親は `role=integrator` だけを書いた。
  **merge 直後に `check_ai_provenance` を回さず `check_docs` しか見ていなかったのが漏れである。**
  退避 branch を作って merge 前へ戻し、Codex の merge 監査 (両親の意図の欠落・重複を
  実コードと AST で照合、結果は修正不要) を通した merge commit へ作り直し、docs 2 commit を
  cherry-pick で復元した。作り直し後の provenance は 2307 件・新規違反なし。
- **同じ穴を塞ぐ runbook 修正が、本 wave の land 拒否と独立に別 wave から main へ入っていた**
  (受入待ち手の merge に実装面 overlap 判定を足す)。取り込んだうえで本 wave の待ち手 script にも
  同じ判定を入れた。overlap が非空なら待ち手では merge せず親へ戻す。
- 受入全走は 2 走した。1 走目は作り直し前の tip で **8285 passed / 20 skipped / 521.07 秒 /
  rc=0**。その tip は provenance 拒否で捨てたので、下の値が最終 tip の本走である。
  変異 matrix も最終 tip で再走し、作り直し前と同じく 8/8 KILLED (baseline rc=0) を得た。
  **再走時に 1 走目の ledger を上書きしてしまい、凍結する台帳は最終 tip の 1 本だけである。**
- 受入全走: **8397 passed / 20 skipped / 502.53 秒 / rc=0** (tip `c22610d1`)。本 fragment へこの値を書き込む commit は
  docs のみで、受入を再走していない。

## 次の一手差分

### 完了

- [T-675] 住所 (address edge) の構造 lint を裁定 R1〜R4 のとおり実装し、変異 8/8 KILLED を得た。
  scope 外の 2 件は {{T:address-edge-lint-layer-coverage}} へ分離した。
  remaining: none
  base: ff79fbfd967299e827b6fdaab2e6f63db9c4b4cbcd7eae818f5cba9461096d67

### 新規

- {{T:address-edge-lint-layer-coverage}} **P3・新規 (本エントリ、段 3 / 段 6 の scope 外 real 所見)**:
  住所 (address edge) の構造 lint が効く層を裁定する。現状 `check_docs` は hooks・CI・pre-commit の
  いずれからも呼ばれず、land も fold 経路でしか呼ばない。あわせて、Markdown の意味解釈を要する
  偽 edge (inline hidden HTML、4-space indented code block、link definition の quoted title、
  打ち消し線、否定形 prose) を塞ぐかどうかも裁定する。`DW-G03` の独立 2 例が揃うまでは却下が既定。
- {{T:mutation-expected-node-scope-doc}} **P3・新規 (本エントリ、段 8 自己改善)**:
  `DW-M08` へ「期待 node と記録 node は集合の完全一致で判定するので、runner の test 集合を変異の
  影響範囲へ絞る」を足すかを裁定する。134 bytes の追記に対し `docs/dev-wave/**` の L1.5 余白は
  12 bytes しかない。予算のために既存の義務を削る道は取らない。予算値の引き上げは
  `docs/skill-self-improvement.md` により独立審査対象である。

### 見送り追記

- [T-059] 2026-08-11 に**再発火** (述語 `validator_or_rejection_gate_changed` = 住所 (address edge) の構造 lint 新設)。既裁定の範囲内なので追加裁定はせず記録のみ — 同 wave が変異 8 件を実装前に事前登録し 8/8 KILLED を記録したため真時 action は履行済み。ただし事前登録のうち 2 件は当初「殺せない負例」で不成立であり、実装前の検算で是正した。
