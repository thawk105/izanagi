# 段 4 裁定 — [T-816] FN-2 trace v2 (手順 1・2)

親が段 3 の 2 レンズ (sol=A / luna=B) の所見を real / refuted、採用 / 不採用、scope 内 / 外に裁定する。
一次資料は `s3-lens-a.md` / `s3-lens-b.md` / `s2-plan.md` / `brief.md` / ruling-package.md。

## 0. 親が自分で裏取りした事実 (レンズの主張を鵜呑みにしない)

| 主張 | 裏取り | 判定 |
|---|---|---|
| A-3: 承認済み未統合 pin `c9c1a9c` がある | `docs/archive/worklog-phase3-0729-49-58.md:577` に「ccbench の新 pin `c9c1a9c` をユーザー承認 (D16)」。[T-167] は worklog 430 の次の一手にも carry。`output/insights/2026-07-29_t152-write-intent-shadow.md:3-5` に「ローカルのみ・push 待ち」 | **real** |
| A-3 続: 本 worktree から c9c1a9c に到達できるか | `git cat-file -t c9c1a9c` → `fatal: Not a valid object name`。本 worktree の submodule は origin からの fresh clone で、`git log --all` の最新 izanagi-trace 系は d706650 | **到達不能 (親の実測)** |
| A-10: `diff-tree --raw` に `-r` が要る | 028f34d→d706650 で実行。`-r` 無し = `cc` tree の M 1 行のみ。`-r` 有り = `cc/silo/transaction.cc` | **real** |
| A-5 / B-3: `g++-13` 不在 | `which g++-13` → 無し。`g++-11` (11.4.0) と `g++-12` が実在 | **real** |
| B-88: FN-1 と FN-2 は重複しない | worklog 428 の FN-1 = trace 外 `commit_counts_` による**個数**の裏取り。FN-2 = C 行の R/W 件数 + E による**txn 内構造**。機構が異なる | **重複なし (refuted = 重複の疑い)** |

## 1. 所見の裁定

### 採用 (must-fix、段 5 の実装契約に入れる)

- **R1 (A-10 real):** raw diff 列挙は `git diff-tree --raw -r -z --no-renames` とする。`-r` 無しは
  tree 単位しか返さず、exact-path gate が正例で必ず赤になる。
- **R2 (A-4 real、blocker):** include 行の**文字列比較だけでは条件付き include の false-green を塞げない**。
  必須 include を新側だけ `#if TRACE` の内側へ移すと、include 行集合は同一・include 除去後の
  TRACE=0 preprocess も同一なのに、実 TRACE=0 compile では header が入らない。
  **対策 (親の設計裁定):** preprocess 前に各 `#include` 行を**一意な marker token 行**へ置換し
  (`#include <x>` → `IZANAGI_INC_MARKER_<n>` のような、preprocess が消さない識別子行)、
  TRACE=0 で preprocess する。条件枝の中へ移した include は marker ごと消えるので差分に現れる。
  文字列比較 (順序込み) はこれに**加えて**残す (marker 化で表記差が潰れるため)。
- **R3 (A-5 / B-3 real、blocker):** `g++-13` 要求を撤回する。checker は `--cxx` を必須引数にし、
  **実走は g++-11 と g++-12 の両方**で行い、両方一致でなければ緑としない。
  レポートには compiler identity (path + `--version` 1 行目) を必ず載せ、
  「admission toolchain と同一である」とは**主張しない** (A-5 の過剰昇格を避ける)。
- **R4 (A-11 / B-4 real、blocker):** 変異事前登録を本裁定で行う (§3)。単一理由性を fixture で担保し、
  「非 0 終了」だけを kill 判定にしない — **期待 node と期待 message 断片の両方**を突き合わせる。
- **R5 (A-7 real、must-fix):** C tag の schema 権威を二重化しない。段 5 は silo の
  `emit_commit` 呼び出しを**削除して置換**する (残置による v1/v2 二重出力を禁じる)。
  `emit_commit` helper 自体は SI が使うので残す。
- **R6 (B-1 real、must-fix):** bundle は「作って verify」で終わらせず、**repo 外の一時 clone へ実際に
  取り込み、新 SHA を checkout し、checker をもう 1 度走らせる**ところまでを手順に含める。
  これが「worktree 撤去後に復元できる」ことの唯一の証拠である。
- **R7 (B-2 / A-9 real、must-fix):** 「gitlink 不変だから inert」は**新 HEAD checkout 中は偽**。
  正しい言明は「d706650 へ復元した後の、committed gitlink を読む既存成果物は不変」。
  復元 → clean 確認 → 受入、の順序を手順として固定する。worklog にもこの限定形で書く。
- **R8 (A-12 / B-6 real、must-fix):** 保証の名前を弱める。**「TU 同一」と呼ばず**
  「選定 context における TRACE=0 正規化 preprocess 出力の同一性 + include 活性の同一性」と
  報告する。checker 名も `check_trace0_preprocess_identity.py` とする。
- **R9 (A-1 / A-2 real、採用するが scope は広げない):** 件数は独立 witness ではない。
  **同時欠落 (write_set_ から要素が消えれば件数も W 行も同時に減る) は FN-2 v2 では検出できない。**
  これは [T-152] の write-intent shadow (独立 witness、`c9c1a9c`) の領分であり、
  [T-167] として**既にユーザー承認済み・未統合**である。したがって残余は新規課題ではなく既知項目へ
  帰属させる。段 7 で FN-2 の閉鎖範囲を「C が宣言した件数に対する R/W framing の欠落」に限定して
  記録し、同時欠落・X 中間欠落・内容置換・実行完了は**閉じないと明記**する。

### 採用 (scope 外、裁定パッケージで返す)

- **R10 (A-3 real、blocker → 裁定へ):** 新 commit の**親をどれにするか**は人間承認の対象が変わる
  設計択一である。d706650 を親にすると `c9c1a9c` と sibling になり、単一 pin で両方を得られない。
  本 wave は **d706650 を親とする** (理由: (i) 裁定パッケージ §3 手順 1 の文言どおり、
  (ii) 本 worktree から c9c1a9c へ到達できず、共有 checkout から fetch すると未監査 object を
  bundle へ載せることになる)。**最終 topology の決定はユーザー手番**として返す。
  checker は (old, new) の 2 commit を引数に取るので、topology を変えても**再走 1 回で済み、
  設計はやり直しにならない**ことを併記する。
- **R11 (A-8 real、blocker → 手順 4 の開始条件):** 手順 4 の「v1 拒否」を protocol 無差別に
  適用すると SI の trace が検証不能になる。SI の編集面 (`cc/si/transaction.cc`) は hook 管轄外
  なので本 wave では触れない。**手順 4 の前に「SI も v2 化するため編集面を広げる / verifier 入力へ
  protocol を束縛して Silo v1 だけ拒否する / v1 拒否を延期する」の三択を裁定へ返す**ことを
  手順 4 の hard block 条件として記録する。

### 採用 (規模を限定して採用)

- **R12 (A-7 後段 / B-5 real、must-fix、ただし best-effort):** emitter の実測が無いのは弱い。
  **新 commit の実 TRACE=1 ビルド 1 本を login node で試み、実 trace を 1 本取って
  「txn ごとに C はちょうど 1 本」「C の件数 == 実 R/W 行数」「E が最後に 1 本」を機械照合する。**
  ビルドが不可能なら (依存・メモリ・時間)、**skip を緑と数えず**「未実測」と worklog に書く。
  これは DW-C00 の「実測は省かない」に従う。scope は 1 binary・1 短時間 run に限る (規律 4)。

### 不採用 / 格下げ

- **A-6 (8 genome は -D 値空間全体ではない、must-fix):** **部分採用・格下げ (nit)。**
  非 genome option (KEY_SIZE 等) を変えた build が admission へ入る経路は本 wave の射程外であり、
  checker が全 `-D` 空間を保証すると主張しなければ嘘にならない。R8 の名前弱化で吸収する。
  `GLOBAL_VALUE_DEFINE` overlay が `transaction.cc` の実 TU 文脈に存在しないという指摘は
  **過剰拒否側**のリスクなので、両 commit へ同じ overlay を適用する限り比較の対称性は崩れない
  (片側だけに適用しない、を段 5 の契約に入れる)。
- **B-8 (run_tests の acceptance 形が曖昧、nit):** 採用。受入全走は既定 target のみで走らせ、
  余計な flag を足さない (既知の落とし穴)。targeted run を受入と記録しない。
- **A-2 の「E は各 W の実行完了 witness ではない」:** real だが、**FN-2 の定義がそもそも
  「trace 記録の欠落」であって「実行の完了」ではない**。R9 の限定記述で閉じる。scope 拡大しない。

## 2. プラン v2 (段 5 へ渡す確定形)

- **単位 A (submodule):** 所有 = `external/ccbench/cc/silo/transaction.cc` のみ。
  d706650 を親に local branch `izanagi-trace-t816-fn2` を作り commit する。
  - v2 C 行: `C <txid> <thid> <epoch> <tid> <read_count> <write_count>` (7 token)。
    件数は `read_set_.size()` / `write_set_.size()`。
  - 終端: `E <txid>` (2 token) を、**entry X 検査・retention X 検査をすべて出し切った後**
    (`clear_shadow()` の直後、684 行付近の既存 `#if TRACE` ブロック内) に置く。
  - `emit_commit` 呼び出しは削除して置換 (R5)。`include/trace.hh` と `cc/si/transaction.cc` は不変。
  - すべて既存 `#if TRACE` の内側。`#ifdef` 禁止。
- **単位 B (checker):** 所有 = `tools/check_trace0_preprocess_identity.py` と
  `orchestrator/tests/test_check_trace0_preprocess_identity.py` のみ。R1〜R4、R8 を実装する。
- **統合段 (親、直列):** A の SHA 確定 → B の実走 (g++-11 / g++-12 の 2 本) → R12 の実ビルド試行 →
  bundle 作成 + 一時 clone への復元検証 (R6) → submodule を d706650 へ復元 (R7) → clean 確認 →
  変異 matrix → 受入全走 → 記録。

## 3. 変異事前登録 (DW-M01)

対象は単位 B の checker (`tools/check_trace0_preprocess_identity.py`)。
各変異は**受理判断を直接変える分岐**へ照準し、単一理由の fixture で kill を数える。
kill 判定は「期待 node の完全一致」+「期待 message 断片」の双方。

| # | 変異 (old 逐語 → new) | 期待 | 単一理由の担保 |
|---|---|---|---|
| M1 | raw diff 列挙から `-r` を落とす | KILLED | 正例 fixture (1 file 変更) が exact-path gate で赤になる。他の gate は発火しない |
| M2 | TRACE=0 出力比較を最初の context だけに縮める | KILLED | `#if TRACE` 内へ隠した差の fixture。include・diff・compiler gate は緑 |
| M3 | include marker 化を外し文字列比較だけにする | KILLED | 条件付き include fixture (include 行集合は同一)。他 gate は緑 |
| M4 | preprocess 失敗を `return pass` にする | KILLED | malformed 前処理 fixture。diff・include gate は緑 |
| M5 | diff status A/D/R を skip する | KILLED | ファイル追加 fixture。M 経路の比較は緑 |
| M6 | compiler 不在を skip/pass にする | KILLED | 存在しない `--cxx` fixture |
| M7 | 対象 0 件 (empty diff) を pass にする | KILLED | 同一 commit を 2 回渡す fixture |
| M8 | drift control: コメント・変数名のみ変更 (意味 no-op) | **SURVIVED 期待** | 注入実在を diff で確認する |

**wave 前の実コードの形の変異について:** 本 gate が禁じたい形 (`#if TRACE` の外への trace 漏れ、
条件付き include) を、wave 前の実コード (d706650) は使っていない。したがって
「wave 前の形と同型の変異 1 件」は該当なしであり、その旨を台帳へ明記する (省略ではない)。

**mask の事前確認:** M1〜M7 はいずれも「checker の受理判断」を変える。前段に同じ入力を拒否する層は
無い (checker は新規で、上流に同等の gate が存在しない)。後段の pipeline / campaign はこの checker を
呼んでいない (enforcement closure 外、承認前の独立ツール)。したがって赤理由は checker 自身に一意化される。

## 4. DW-G05 成果物影響 (must-fix ごとに 1 行)

- R2 を入れない → checker が緑のまま TRACE=0 binary が旧 pin と異なりうる = 報告 throughput 全値が規律 1 の保証外。
- R3 を入れない → 実走が不可能 (g++-13 不在) で承認証拠が 0 件、pin 前進が恒久的に未達。
- R5 を入れない → 同一 txn に v1/v2 の C が 2 本出て `dup_txids` / `trace-parse-error` となり、当該 variant の fitness/certified 行が成果物から消える。
- R6 を入れない → worktree 撤去で新 SHA が失われ、承認手番に渡すものが無くなる。
- R7 を入れない → 「既存値不変」という worklog 記載が偽になる。
- R9 を入れない → 台帳に「FN-2 closed」と誤記され、同時欠落型の偽陰性が閉じたと誤認される。
