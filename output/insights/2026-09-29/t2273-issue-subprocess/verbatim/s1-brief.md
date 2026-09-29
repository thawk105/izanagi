# 段 1 brief — [T-2273][T-2560] 受入 shard-0 の律速 (b) 発行 subprocess の短縮

- 研究前進: 受入全走の 5 分上限 (全 dev wave の完了条件、test-time 規律) の回復。現状 B の W_max 中央値 317.2 秒 (D2271) > 300 秒。
  最遅 shard は 6 走とも shard-0、その律速の一つが共有発行 key builder 内の発行 child 約 87 秒 (D2253 項 4)。完了判定 = 事前登録の land 条件の成否 (5 分は別判定)。
- 実測 (段 1 前、`profile-summary.md`): 発行 child の CPU の 99 % が `s8b_holdout_freeze.search_repository` (1 回 ≈ 6.6 秒 × 約 13 回)。
  うち `_scan_one` 76 % — 正規表現 search 1 行 (s8b_holdout_freeze.py:564) 54 %、共通 literal の `in` 検査 (:559) 19 %、軸 literal の `in` (:562) 4 %。file 読込み 11 %。
- scope: `orchestrator/campaign/s8b_holdout_freeze.py` の `_scan_one` の係数削減 (D512 の枠内) と、その等価性・発火回数の test。
  変更 file は同 module と `orchestrator/tests/` の該当 test file を上限とする。t080_freeze_migration.py・発行 fixture・driver は変えない。
- 確定済み裁定: D512 (report の canonical bytes を 1 bit も変えない係数削減に限る、全 file の列挙・open・read・decode は維持、
  prefilter は既存 `_derive_required_literal` を 1 要素 mapping で呼ぶ形だけ、memo は 1 回の `search_repository` に閉じ texts identity に束縛)、
  D513 (出力等価な最適化は発火回数で番人、reference 実装への差し替えで三段分離)、D350 (literal は実際に compile する式から導出)、
  D351 (安全性は独立 slow 経路との全 report canonical bytes 一致、固定 fixture で)、D2253 項 4・D2271 項 3 ((b) の対象)、F264 (単軸経路を必ず 1 本)。
- 不変条件: 受領証・holdout 検査の受理集合と report bytes は不変 (規律 2)。`search_repository` の呼出し回数 (child 内 13 回) と観測点は変えない。
  呼出しを跨ぐ cache を作らない (D512)。production に最適化無効化 knob を足さない (D513)。仮想リスク向けの gate・台帳・一般化・環境変数は足さない。
- (P1) 親の provisional 裁定・攻撃対象: 走査回数を減らす案 (validate の内包重複・draft の verifier 走査の共有) は採らない — 観測点を減らすのは受領証の検査内容の変更に当たる。
- (P2) 親の provisional 裁定・攻撃対象: 主手段は「局所化 search」。軸 a の literal L_a (既存 helper の 1 要素 mapping 導出、非 None の時だけ) と、
  stdlib の幅解析 (`sre_parse.parse(expr).getwidth()`) による最大一致長 W (有限の時だけ) から、
  `compiled.search(text)` の真偽 = L_a の各出現 p について `compiled.search(text, max(0, p+len(L_a)-W), min(len(text), p+W))` のいずれかが真。
  根拠: helper が非 None を返す文法 (値側は `.` 以外のメタ文字なし・key は literal) では全 match が L_a を含み、長さ ≤ W、端依存の assertion が無い。
  L_a が None・W が無限・導出不能なら従来の全文 search に倒す。自作の regex 文法 parser は書かない (D512 却下案)。
- (P3) 親の provisional 裁定・攻撃対象: 共通 literal (:559) の `in` 検査を text ごとに 1 回へ (call 内 memo、D512 の枠内)。軸 literal の出現位置探索が (:562) を兼ねる。
- (P4) 親の provisional 裁定・攻撃対象: 効果見込み — `_scan_one` の約 65 秒のうち 50〜60 秒を削り child 86 → 25〜35 秒。共有発行 key builder が同程度縮めば W_0 に効く。
  shard-0 の W_0 がどれだけ縮むかは builder が L node の待ちに乗る割合次第で、実受入の隣接対でだけ判定する。
- (P5) pin 閉包 (DW-O09、子の網羅検索 `pin-closure.md` で確定): `s8b_holdout_freeze.py` の bytes 変更で壊れる凍結・再発行は無い — v1 の worktree 照合
  (`_verify_source`、s8b_holdout_freeze.py:945) は HELD (freeze_verification_hold.py:13) かつ記録値 1910fff… は既に現物と不一致、v2 g1 は frozen_at_head の blob で照合
  (s8b_ratified_freeze.py:1095 V1b)、t080 の METADATA_SPECS は v1 記録値の歴史 pin。FROZEN_MANIFEST は JSON 出力の pin。DW-O10 は非成立 (producer 出力 bytes 不変)。
- (P6) 親の provisional 裁定・攻撃対象: 既存の発火回数の番人 (test_s8b_holdout_freeze.py:427 の search 5 回、:985〜1097 の三段分離 0/5/9 回と reference 3 回) は
  局所化で search の呼出し回数が変わる。番人の意味 (prefilter を戻す変異・memo を外す変異を殺す) を保つ数え方へ改め、局所化層の有無も同じ fixture で分離する (D513)。
  期待値の変更は「数える単位の変更」として段 4 で個別に裁定する。
- (P7) 自己汚染: 新実装は軸 key と値を連続 literal で書かない (test_s8b_repo_scan_invariant.py の禁止)。同 test と test_s8c_preregistration_invariant.py:623 は growth hold 中
  (解除はユーザー指示のみ) なので迂回せず、段 6・7 で変更 file を `search_repository(root, files=...)` に渡して conjunction 0 件・陽性対照 > 0 を確かめる (F 台帳の先例)。
- 成果物: production 1 file の係数削減、等価性 test (reference 全文 search との per-text 真偽一致・全 report canonical bytes 一致、単軸・端・重なり・`.` 値・None/無限幅の fallback)、
  D513 型の発火回数 test、事前登録の隣接 3 対の実受入、insight・decision・worklog fragment。
- 受入・実測環境: Pegasus。焦点走・変異・実受入は計算ノード (dispatch)。land 条件は (a) と同形 (A = 測定準備時の local main、B = A + 実装、順序 A,B / B,A / A,B、
  shard-0 W_0 の対差が 3 対すべて正 ∧ 対率中央値 ≥ 10 %)、5 分上限は B の W_max 中央値で別判定、W_1・pre は補助量として報告。段 4 で事前登録。
- 計算量見積り (前 wave の実測単価: 受入 1 走 ≈ 879 秒・焦点走 ≈ 347 秒・変異 ≈ 668 秒・温め 111 秒): 計 約 2.2〜2.6 node 時間 → 系列投入前にユーザー確認。
- 分割方針: 実装子 1 本 (production + test を同じ子に持たせる、所有 path 2 file)。段 3 は 2 レンズ (A 正しさ・等価性・D512/D513 適合、B 過剰・効果・計測設計)。
