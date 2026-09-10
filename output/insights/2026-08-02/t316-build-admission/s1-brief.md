# [T-316] role 出力の意味 gate — 段 1 brief (親)

## scope
coder role の出力が EVOLVE-BLOCK hole へ挿入され build/run される経路について、
「valid-schema な任意 C++ が意味 gate なしで通る」構造を閉じる**設計を裁定まで確定する**。
gate 本体の実装可否は段 4 で裁定する。auditor role を強くする方向は解にしない (下記 P3)。

## 確定済みユーザー裁定
- 対象タスクは T-316 (当初引数 T-276 は D122 で完了済み、ユーザーが T-316 へ切替)。
- T-316 自体の設計択一 ((a) boolean-expression AST/DSL / (b) credentialless・network 無し
  sandbox / (c) 両方) は**未裁定**。本 wave はこれを裁定パッケージとして返す対象とする。

## 段 1 前提実測 (すべて本 worktree 46b2b23 で実施、模擬でなく実モジュール呼出し)
1. `DiffQuarantine.validate()` は hole 内 1 行の `std::system("id > /tmp/o")` /
   `execl(...)` / `std::ofstream("/tmp/pwned")` / `while (true) {}` / `std::getenv` 経由の
   間接実行を**すべて passed=True** で通す (`diff_quarantine.py:256-`)。
2. `system` + URL 版が唯一赤になったのは `http://` の `//` がコメント delimiter 検査
   (`_LINE_COMMENT_DELIMITER`) に当たった**偶然**で、`//` を除くと通る。設計された防壁ではない。
3. `#` 指令拒否と `#include` HEAD 固定は本 vector に対して無効。`backoff.hh` が既に引く
   `util.hh` が `<stdlib.h>` (`system`/`getenv`)、`<unistd.h>` (`execl`/`fork`/`read`/`write`)、
   `<stdio.h>` (`popen`/`fopen`) を持ち込み、追加 include なしで POSIX 原始関数へ届く。
4. auditor gate は `diff_digest` を echo し `verdict="pass"` を返すだけで通過する
   (`auditor_gate.py:64-75` は「同じ diff を見たか」しか照合しない。実測済み)。
5. 既存テスト 38 本 (`test_diff_quarantine.py`) は構造・字句 vector のみ。意味注入の
   positive control は **0 本**。本 wave の純増検出力はこの 0 からの増分で測る。
6. DW-O09 pin 閉包: `FROZEN_MANIFEST` 23 件に `diff_quarantine`/`auditor_gate` 由来の
   producer 出力は**無い**。一方 `codex_roles/review_ledger.py` は role 名 key で
   `SOURCE_FILE_SHA256` / `ROLE_MANIFEST_SHA256` / `DESCRIPTION_SHA256` / `SCHEMA_SHA256`
   を pin し、人間レビュー時のみ更新と明記されている (F30 型の key 側 pin)。
7. DW-G04 発火条件: 実 artifact `output/campaigns/p3-s5-sort-loop-s5-sort-autonomous-3be89e0d/`
   と `p3-s4-loop-s4-autonomous-0b53a387/` が存在し、コード片軸ループは既に実走している。

## 親の provisional 裁定 (すべて攻撃対象)
- **(P1)** 本 wave では gate 本体 ((a)/(b)) を実装せず、裁定パッケージ + 現行受理境界を
  固定する test-only positive control までを実装面とする。
- **(P2)** (a) と (b) は代替でなく直交する 2 層。(a)「表現を狭める」は軸依存 (bool 述語軸には
  嵌るが comparator コード片軸には嵌らない) で、coder 出力 schema を変えるため実測 6 の
  role hash pin 閉包 4 台帳 + `manifest.json` + `.codex/role-adapters/*.json` を発火させる。
  (b)「影響を断つ」は軸非依存で role schema を一切触らない。**load-bearing は (b)、(a) は
  defense-in-depth** と置く。
- **(P3)** auditor は coder と同一 transport の非信頼出力であり、独立防壁として数えない
  (実測 4)。「auditor を強くする」提案は本 wave の解に採らない。
- **(P4)** 意味 gate を text 検査で「完全」に作る案は D33 の既決 (text gate に翻訳フェーズの
  完全再現を載せない) に反するため採らない。allowlist 型を出す場合も完全性を主張しない。

## 不変条件 (緩めない)
- 規律 2: 正しさゲートを緩める変更を採らない。受理集合を広げない。
- 実装面は Codex `role=author` が書く。親は brief・裁定・統合・全走・記録・commit のみ。
- role hash pin (実測 6) は本 wave で更新しない。更新が必要になる案は「実装しない」側へ倒す。
- 凍結成果物 23 件の bytes を変えない。

## 成果物影響 (DW-G05)
実装も裁定もしない場合: T-277 を開けて計測ノード上で loop を回した時点で、coder の 1 行が
計測機上で任意の POSIX 実行に到達しうる。その run に由来する certified 選択・材料レポート
median_tps・変異台帳の全数値が「非信頼コードの実行結果」に格下げされ、proof chain の
受理集合は「LLM が書いた任意の C++」のままになる。

## 成果物の形
1. 裁定パッケージ (択一・推奨・file:line 実装計画・pin 閉包の影響)。
2. (段 4 で採るなら) 現行受理境界を固定する positive control テスト群 (test-only)。
3. worklog エントリ、insights 逐語、必要なら decisions。

## 並列分割方針
段 2 = codex plan 1 本 (read-only)。段 3 = 3 レンズ並列 (親 brief と実測 1-7 の一般化も攻撃対象)。
段 5/6 は段 4 の裁定次第。
