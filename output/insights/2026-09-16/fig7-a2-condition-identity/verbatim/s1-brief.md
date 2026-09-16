# 段 1 brief — 図 5 (A-2 certification reject) の identity 訂正

wave: `fig5-a2-identity-reissue` / branch `worktree-dev-wave-fig5-a2-identity-reissue` / 起点 main `9d52ef145`

## 研究前進

論文の A-2 節が使う図のうち、attempt `t2022-20260828c` を描く図の caption が「採用静的 backoff
(fixed 10 µs / 5 µs) が無 backoff 対照を下回った」と読める条件記述を持つ。実際に効いた条件差は
`BACK_OFF` の 0/1 (CCBench 内蔵の適応 backoff の有効/無効) だけである。図の**値と protocol status は
正しく、誤っているのは条件の記述だけ**である。完了判定は「同じ 4 cell の値を描く図 1 枚と caption が、
改訂稿 `docs/paper-story/results/2026-09-07-a2-certification-reject.md` の条件記述と一致し、
provenance が改訂稿を出所として記録し、受入全走が緑」。

## ユーザーが確定させた裁定 (command 引数)

図が支持する命題と caption を改訂稿の表現へ合わせる。provenance JSON の入力を改訂後の一次資料へ
差し替える。生成器は `tools/plotting/plot_a2_certification.py`、規約は
`tools/plotting/FIGURE_CONVENTIONS.md`。計測機の外で実行。実装面は Codex author (D95)。
**本題の図 1 枚と caption だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。**

## 段 1 の実測が出した新事実 (依頼の前提を更新する。逐語は `verbatim/` に射影済み)

1. **D1993 (2026-09-14) 決定 1** — D1645 の解除条件は attempt `t2364-20260907b` が満たす。
   A-2 の結論は既に論文素材として使ってよい。その図は `fig6_a2_certification_observed_positive`
   として 2026-09-07 に着地済み。依頼文の「正しい identity で取り直すまで外す」は現行状態ではない。
2. **D1936 項21 + D1993 決定 5** — 旧 fig5 の用途制限は**期限なし**。採用静的 backoff の結論・図として
   旧図を使わない。ただし「旧判定を歴史記録として説明すること」は禁じられていない。
3. **`docs/paper-story/figures/README.md` の追補 (D1936 項21 の実施)** — 「旧画像・PDF・provenance
   JSON・統計・凍結稿・キャプション正文と outer `reject` は保持する」と明記。
   append-only の results 2 稿が provenance JSON の SHA-256 `30113d50…` を記録している。
4. **機械的束縛 (決定的)** — `orchestrator/tests/test_plot_a2_certification.py::test_landed_fig5_repo_closure_and_caption_when_present`
   が `validate_repo_closure` 経由で `provenance["caption"] == _caption(provenance, prefix)` を要求し、
   さらに caption が `figures/README.md` に逐語で載ることも要求する。**生成器の legacy profile の
   caption 文言を直すと、fig5 を再生成しない限りテストが赤になる。** caption の訂正と凍結 bytes の
   保持は、現行の機構では両立しない。
5. **D1753** は「新しい図の filename を `fig5` 系にする」を凍結図との衝突を理由に却下済み。
   図番号は出力 prefix の `fig<N>_` から導出され、caller は caption 文字列を注入できない (D1753)。
6. **pin 表 `CANONICAL_SHA256`** (D1752) は certification の repo 相対 path を key に持ち、
   legacy (2026-08-24) と current-full (2026-09-07) の 2 entry が既に在る。新しい図を legacy 権威
   bytes から作ること自体は、表の追加なしで通る。

## 割れうる前提 (親の provisional 裁定。段 3 の攻撃対象)

- **(P1) 「作り直す」を in-place の上書きとして実施しない。** 新事実 3 の追補が bytes 保持を明記し、
  絶対規律 7 が訂正を追記に限るため、旧 fig5 の 3 file は 1 byte も触らない。
  代わりに**同じ legacy 権威 bytes から、訂正後の条件記述を持つ新しい番号の図を 1 枚作る**。
  これは D1645 自身が results 系列へ課した「旧稿を変えず新しい日付の稿で改める」と同型である。
  親は (P1) を暫定とし、レンズには「in-place こそ依頼に忠実で、追補は AI 起草の記述にすぎない」側の
  攻撃も明示的に求める。
- **(P2) 新図の番号と名前は `fig7_a2_builtin_backoff_onoff_reject` を暫定とする。** `fig6` は使用済み。
  番号は prefix から導出されるので、名前の決定がそのまま caption の図番号になる。
- **(P3) `tracked_inputs` の「差し替え」は、権威 bytes の置換ではなく出所記録の追加として実施する。**
  `validate_repo_closure` は tracked_inputs の各行の path と sha256 が現物と一致することと、
  `raw_manifest` がちょうど 1 行であることを要求する。certification.json / raw-manifest.json は
  改訂されておらず、改訂稿 `.md` は統制稿であって図のデータ入力ではない。よって 2 行は残し、
  改訂稿を別 kind の行として足す。**この読み方が誤りなら段 4 で覆す。**
- **(P4) caption の条件記述の訂正範囲は、cell を静的 backoff と述べる箇所に限る。** 値・status・
  限定・abort 率の扱いは改訂稿の表現に合わせる以上のことをしない。

## 不変条件 (破ってはならない)

- 旧 `fig5_a2_certification_reject.{png,pdf,provenance.json}` の bytes を変えない。
- 権威 bytes (`certification.json` / `raw-manifest.json`) と外部 WAL / raw cell の bytes を変えない。
- 図の値・median・効果・outer status を作り直さない。生成器は判定を再計算しない (既存契約)。
- caption へ caller 由来の任意文字列を注入する経路を作らない (D1753)。
- 図の作成は計測機の外 (login node) で行う (FIGURE_CONVENTIONS §7、絶対規律 4)。
- 新しい gate・検査層・台帳・一般化を足さない (ユーザーが scope 外と明示)。

## 成果物の形

1. 新しい図 3 file (`.png` / `.pdf` / `.provenance.json`)。
2. `docs/paper-story/figures/README.md` に新図の節と caption 逐語 (既存テストが逐語一致を要求)。
3. 生成器の最小変更 (実装面、Codex author)。
4. 記録 (worklog / insights fragment)。

## 分割方針

段 2 plan 1 本、段 3 敵対 2 レンズ (sol = 凍結・裁定整合、luna = 機構の実効性と caption 生成経路)、
段 5 実装子 1 本 (生成器)、段 6 レビュー 2 本 + fix。図の生成と README 編集は親が行う。
