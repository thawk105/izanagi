# [T-2146] 段 1 brief — 発行主体 subtree を hooks の書込み防護対象へ足す

## scope

`/work/1/SFC/tanab/dev-wave-authority/` (以下「発行主体 root」) を、hooks の 2 つの書込み防壁
(`guard_write` = Write/Edit/MultiEdit/NotebookEdit/apply_patch、`guard_bash` = 書込み・削除・移動)
の拒否対象へ加える。判定は path 要素の境界で行い、単なる部分文字列一致にしない (兄弟 directory を
巻き込まないため)。合わせて `hooks/README.md` に、閉じた面と閉じない残余を書く。

**scope 外 (実装しない):** 読取り防護の新設、鍵の運用手順、issuer の production 配線 ([T-1984])、
承認 record の発行、防護対象一般への拡張、新しい台帳・検査・gate。

## 実測した前提 (すべて成立)

- 発行主体 root は 0700 で実在し、鍵 2 本・issuer 運用複製・説明 file の 4 件が置かれている。
- 参照側は `tools/acceptance_receipt_signature.py:47-49` (公開鍵) と
  `tools/acceptance_issuer_reference.py:92-94` (秘密鍵)。どちらも argv / 環境変数で上書きできない
  module 定数で、依頼の記載と一致する。
- 発行主体 root を防護する既存判定は repo 内に 1 件も無い (`git grep` 全件が tools の 2 定数、
  archive worklog、[T-1984] の plan だけ)。**純増**である。
- 編集面 (`hooks/` の 4 file と `orchestrator/tests/test_hooks.py`) を触っている稼働 wave は
  無い — 104 branch の三点 diff で 0 件、95 worktree の未 commit 差分も 0 件 (HEAD blob 照合)。

## 覆した / 補った前提 (段 4 で確認する新事実)

- **N1.** 依頼が引く「guard を未 commit で変えている間は子を起動できない」は、より詳しい手順が
  **D374** に既裁定として存在する。実装子は (1) 防護対象外の file を先に書く、(2) `guard_bash` を
  先に patch する、(3) `guard_write` は完成形を防護対象外の作業 dir で `py_compile` と `decide()`
  実測まで通してから **最後に 1 回だけ** apply_patch で入れる、(4) 親が次の子の前に統合 commit、
  (5) 直しが要れば有効化前の commit から作り直す。本 wave はこの 5 手順に従う。
- **N2.** 批准台帳 `hooks/enforcement-source-closure-ratifications.v1.jsonl` に production の
  消費経路は無い (docs/decisions.md の当該裁定)。したがって hooks の bytes を変えても批准 gate は
  発火しない。凍結 pin 閉包は `tools/check_codex_hooks.py` の HEAD blob 束縛 1 件だけである。
- **N3.** `guard_read` は fail-open の「コンテキスト衛生」層であって正しさ防壁ではない。よって
  秘密鍵の**読取り**を塞ぐには新しい機構が要る。これは scope 外だが、書込みだけを閉じても
  「AI が署名を偽造できない」とは言えないので、**README には残余として明記**し、機構の新設可否は
  ユーザー裁定へ回す (本 wave では作らない)。

## 不変条件

- 規律 2 を緩めない。本変更は拒否だけを増やし、既存の受理を 1 件も増やさない。
- 受入 (acceptance) の受理集合を変えない。発行主体 root へ書く production 経路は現時点で無く、
  公開鍵の**読取り**は Python 内で行われるため hook の観測面の外にある。
- 一時的な無効化 flag・環境変数・argv 上書きを作らない (D374 の却下選択肢、[T-1984] plan の条件)。
- 親は実装面 (`hooks/*`、`orchestrator/tests/*`) を直接編集しない。Codex `role=author` が書く。
- 「完全ロック」と書かない。script 経由・変数展開・persistent shell・同一 uid・別 process は
  依然として開いたままであることを README に残す。

## 成果物

1. `hooks/guard_write.py` — 発行主体 root の subtree 判定を deny union へ追加。
2. `hooks/guard_bash.py` — fast-path trigger、tree 判定、引数照合、redirect 先照合へ追加。
3. `orchestrator/tests/test_hooks.py` — 正例 (発行主体 root 配下の Write / Bash 書込みが拒否)、
   負例 (兄弟 directory・接頭辞が同じだけの path・読取りコマンドは通る)。
4. `hooks/README.md` — 閉じた exact surface と残余 (N3 を含む)。
5. worklog / decisions / failures の fragment (`docs/spool/`)。

## 分割方針

実装単位は 1 つ (unit-A)。guard_write と guard_bash と test は互いに依存し、D374 の順序を 1 人の子が
守る必要があるため分割しない。段 3 の敵対相談は 2 レンズ (境界判定の抜け / 受理集合の非意図的変化)。

## (P1) 親の provisional 裁定 — 攻撃対象

- **(P1-a)** 発行主体 root は module 定数の絶対 path として書く。`tools/` の 2 参照と同じ形であり、
  argv / 環境変数で上書きできる設計にしない。
- **(P1-b)** 判定は lexical path と canonical path (realpath) の両側で行い、`_inside` と同じ
  path 要素境界を使う。inode alias 走査 (`_HooksInodeIndex` 相当) は**張らない** — 発行主体 root は
  0700 の repo 外 subtree で、hooks subtree のような hardlink alias の実例が無い。
- **(P1-c)** guard_bash では既存の `_hooks_tree_violation` と同じ 4 箇所 (tree 判定・引数照合・
  redirect 先・fast-path trigger) に足すだけで足りる。
- **(P1-d)** 段 6 の変異 matrix は、追加した 4 箇所それぞれを個別に無効化する変異で歯を立てる。

## DW-G05 成果物影響

放置すると、AI が編集できる領域に「AI が書けないはずの鍵と発行主体」が置かれたままになる。
D906 が要求する「署名鍵と発行権限は AI が書ける領域の外」が、書込み側で機械的に成立しない。
その結果 [T-1984] の署名必須化を有効にしても、着地受領証の真正性は「そう書けば通る」経路を
残したままになり、certified な選択結果の着地判定が恒真な関門になりうる。

## 実測環境

login node での単体テストのみ。build・計算ノード投入・性能計測は行わない。
