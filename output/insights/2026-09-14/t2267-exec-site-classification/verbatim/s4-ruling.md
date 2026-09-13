# 段 4 裁定 — [T-2267] 実行場所分類

基準 commit: `75bea8e5fe918e7ec9fd18c10cd0dadcf474c51a`。裁定 inbox 再走査済み (`docs/handoff/` の
残 1 件は別 wave の T-1998 precheck、本 wave と無関係)。local main は wave 開始後も 75bea8e5f のまま。

## 1. 親の (P1) — 限定して採用

**refuted (無限定形) / real (限定形)。** レンズ A 所見 1・2・3 とプラン §1 が独立に同じ限定を出した。

- 採用する形: **認可済みの login bounded scope は存在する** (`tools/run_tests.py` の pytest 経路と
  `tools/check_ai_provenance.py` の履歴監査経路)。**しかし T-2216 model の凍結入力・本走 argv を
  受け取れる認可済み login dedicated-scope 経路は、調査した現行実装には無い。**
- 親の brief の「存在しない」という無限定の書き方は誤り。記録では限定形だけを使う。
- `script_path` (`tools/run_tests.py:1897`) の内部 seam、`mutation_fanout` の `run` command 引数、
  compute の `generic`、namespace 隔離は、いずれも**認可済み経路に数えない**。
- 親の hook 拒否記述も訂正する。「無条件拒否」ではなく
  「LOGIN/SUSPECT で解析された head が `systemd-run` のとき拒否。非実行の command-reader は例外
  (`hooks/guard_bash.py:1191`-`:1192`)」と書く。
- 静的検索を全実行面の不在証明にしない、と明記する。

## 2. 親の実測値の射程 — must-fix 採用

**real。** レンズ A 所見 4・5、レンズ B 所見 1・2。

- 今回の観測は **§7.0 手順による実測ではない**。sampler は scope 起動後に開始し
  (`tools/run_tests.py:2014`→`:2027`)、ループ待機は 5 ms (`:152`, `:1958`)。§7.0 は先行 sampler と
  間隔 ≪1 ms を要求する (`verbatim/runbook-7.0.md:53`, `:63`)。下振れ量は未評価で、
  25% / 128 MiB の margin で吸収できることも確認していない。
- したがって **certified peak を計算しない。欄を作らない。** class を変更しない。
- 3 走は cap が同一でない (rep1 の提示値 3,940,686,240、rep2/rep3 は 1,073,741,824)。
  §7.0 は cap 変更時の再測定を要求する (`verbatim/runbook-7.0.md:90`-`:95`) ので、
  **「3 反復」と書かない**。cap 別に 1 走 / 2 走として記録する。
- 提示された cap は runner の**付与予算**であり、実効 `memory.max` の逐語観測ではない
  (`tools/run_tests.py:1754`, `:1818`, `:1832`。3,940,686,240 は 4096 の倍数でない)。
  実効値は **未取得**と書く。
- 見出しは「既存 pytest scope の参考観測 (正式分類には不使用)」とし、本走欄は「未実測・unknown」。
  レンズ B が提案した断り書きを逐語で採用する。
- pytest の入力欄に model の 5 files / 297,814 bytes を転記しない。`-n 0` と 32 worker は別行。

## 3. 凍結入力 — 親の「不在」を訂正

**refuted。** 親の走査は 2 repo に限定されており、範囲外を不在の証明に使った誤り。
段 2 が参照鎖 (`output/insights/2026-09-07/t2313-13pt-audit/README.md:35`-`:36` →
外部 model 出力の `provenance.measured_input`) から 2 本を発見し、親とレンズ A・B が
それぞれ独立に sha256 を再計算して pin `f46cebdd…` との一致を確認した (各 269,108 bytes)。

- 記録は「指定範囲の走査では一致 0 件」「範囲外に完全一致 2 本を発見・照合」の両方を残す。
- **repo へ複製しない。** 引用・原文 path・完全 digest・bytes・照合日を insight に書く。
  一律禁止でないことはレンズ B が示したが、複製先の provenance 規約を新設せずに置くと
  由来不明の凍結 bytes を増やす。保全先の裁定は裁定パッケージへ 1 項目として回す
  (job ディレクトリは使い捨てで、消えれば path と hash から bytes は復元できない)。
- 入力の発見は**実行環境までの再現成功を意味しない**と明記する。

## 4. 不足経路の仕様 — 成立条件だけ書き、裁定へ返す

**real。** レンズ A 所見 8、レンズ B 所見 6。

- 本 wave で完了できるのは「不足の特定・成立条件の仕様・証拠の記録」まで。
- 仕様は段 2 の 5 条件を採る。既存内部関数の転用案は書かない。
- **裁定衝突を明示する。** D180 (`verbatim/d180.md`) は測定専用 bounded surface の即時新設を却下し
  族再設計へ同梱と定めた。D210 (`verbatim/d210.md`) は上限付き実行を entry point の内側に閉じ、
  汎用 launcher を作らないと定めた。D1938 は実行担当の変更であって、これらの実装変更を
  一括承認したものとは読めない。**親の裁量では実装しない。**
- scope 外の層を表で列挙する (hook admission / admission registry 正本 / runbook 投影表 /
  `check_docs.py` の集合完全一致検査 / 新経路の受入全走)。
  docs-only の受入成功を「対象本走が認可済み bounded 経路で動く」と読み替えない。

## 5. 成果物の配置・形式

- insight: **`output/insights/2026-09-14/t2267-exec-site-classification/README.md`**
  (`output/README.md:82`-`:85` の日付ディレクトリ規約。親 brief が指定した旧形式は採らない)。
  冒頭に `authority: none` / `default_effect: no-state-change`。
- spool fragment 2 本 (worklog 1・decisions 1)。`base` は **land 先 local main を cwd として**
  `python3 tools/spool_fold.py --base-digest '[T-2267]'` で取得する
  (`docs/spool/worklog/README.md:83`-`:91`)。worktree や carry stub の文字列を直接 hash しない。
- T-2267 は **`更新`**。本 wave の終了を T-2267 の `完了` に転記しない。
- decisions 見出しに日付を付けない。`title` は worklog fragment のみ。

## 6. 段の進め方

- **実装しない**と裁定したので段 5・6 を飛ばし `4→7→8→9` とする。
- 実装面の差分ゼロなので変異 matrix は免除 (DW-S04)。**受入全走は免除しない** — 段 7・8 の
  commit 完了後、land 対象 tip に対して実走し、結果を worklog へ書く (DW-O12)。
- 記録に使う file:line は段 3 の訂正を反映する
  (`--force-dispatch` は `tools/check_ai_provenance.py:2978`、runner の引数処理は
  `tools/run_tests.py:2397`)。

## 7. 裁定パッケージ (ユーザーへ返す項目)

1. 対象限定の測定実行経路を作ってよいか — D180 の「即時新設は却下・族再設計へ同梱」と
   D210 の「entry point 内に閉じる・汎用 launcher を作らない」に触れる。触れる理由を添える。
2. 非 `tools/pegasus/` path の `local-ok` 登録が loader と hook の双方で拒否される制約の下で、
   対象を測っても class をどう扱うか。
3. 凍結入力 bytes の保全先 (使い捨て job ディレクトリ外へ置くか、置くならどの provenance 規約で)。
