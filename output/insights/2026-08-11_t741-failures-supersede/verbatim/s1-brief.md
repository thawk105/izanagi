# 段 1 brief — dev-wave-t741-failures-supersede

- wave: `dev-wave-t741-failures-supersede`
- worktree (試験対象 checkout): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede`
- base main: `c0460ef5`
- 対象タスク: [T-741]

## 確定済みユーザー裁定

[T-741] = (a)。failures fragment へ `supersede 追記` 節を足す (`見送り追記` と同型の 1 行挿入)。
F196 ほか stale 化した既存記述の是正に使う。目的は規律 6 の監査レンズ設計 (攻撃面リスト) の鮮度維持。
一次控え = `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-04-rulings-session-5rulings.md` §61、
worklog エントリ 374。

## 裁定前提の実測 (brief 前に親が実施)

1. 「failures fragment は `新規` / `再発` しか表現できない」= 真。
   `tools/spool_fold.py:676 _failure_symbols` は H2 を `新規`/`再発` に限定し、
   `tools/spool_fold.py:1547 _failure_parts` は `^## (?P<title>新規|再発)$` しか読まない。
2. 「`見送り追記` と同型の 1 行挿入」= 真。`tools/spool_fold.py:1487 _insert_deferred_appends`
   は `- [T-NNN] <suffix>` の 1 物理行を、対象 item の**先頭行の行末**へ挿入する。
   parse は `tools/spool_fold.py:540` 以降。
3. 「F196 ほか stale 化した記述が実在」= 真。`docs/failures.md:4819` の F196 恒久対応末尾は
   「runbook §7.3 の待ち手契約自体の改訂は本 wave の scope 外であり、裁定へ返す」だが、
   直後の F197 恒久対応は「`docs/pegasus-runbook.md` 7.3 を是正し」と実施済みを記す。
   裁定を覆す新事実はない。
4. 凍結 bytes の pin 閉包 = 不成立。`grep -rn "spool_fold\|spool/README\|spool/failures/README"
   --include=*.py` の hit は `orchestrator/tests/test_spool_fold.py` と
   `orchestrator/tests/test_dev_wave_land.py` の実行経路だけで、SHA-256 pin・FROZEN_MANIFEST は無い。
5. gate 入力の実在 (DW-O13) = 確認済み。target 識別子は `docs/failures.md` の
   `### F<n>.` 見出しであり、`tools/spool_fold.py:56 FAILURE_ID_RE` が正本。
   実 canonical は 202 件すべてこの形。`再発` と同じ selector を使い、同名識別子を二義化しない。

## 既存被覆の性質検索と純増検出力

「既存エントリ本文へ 1 行挿入し、対象の実在・重複・同一内容の再挿入を拒否する」性質は
既に 2 経路が持つ。

- 見送り台帳 (`docs/phase3.md`) 向け: `deferred-append-shape` / `-empty` / `-missing` /
  `-duplicate` / `-duplicate-suffix`
- failures `再発` 向け: `failure-recurrence-empty` / `failure-recurrence-shape` /
  `failure-missing` / `failure-duplicate`

**純増検出力は 3 点だけ**。(i) failures 台帳に対する「1 物理行 shape」の強制、
(ii) 同一行の再挿入拒否 (`再発` は複数行 payload を許し重複 payload を検査しない)、
(iii) `再発` と区別された節として表現できること。

## 成果物影響 (DW-G05)

実装しない場合、failures 台帳の stale 記述を是正する手段が fragment 文法に無いままとなり、
規律 6 の監査レンズ設計 (攻撃面リスト) が古い前提で組まれる。具体的には F196 を読む後続 reviewer が
「runbook §7.3 は未改訂」と判断して再訪を起票する。台帳の受理集合そのものは変わらないが、
監査の対象集合が誤る。

## 発火 gate (DW-G04)

発火条件を満たす既存 artifact = `docs/failures.md:4819` の F196 (supersede 根拠は F197 恒久対応)。
本 wave 内で実際に 1 件使う。

## scope

- `tools/spool_fold.py` — fragment 文法・fold 適用・検査の拡張
- `orchestrator/tests/test_spool_fold.py` — テスト
- `docs/spool/failures/README.md`、`docs/spool/README.md` — 正本更新 (親が書く)
- 本 wave の failures fragment 1 件 (F196 への supersede 追記、親が書く)

## provisional 裁定 (親の暫定であり攻撃対象)

- **(P1)** H2 節名 = `supersede 追記`。許可順序 = `新規` → `再発` → `supersede 追記`。
  使う節だけを置く (supersede 単独の fragment も有効)。
- **(P2)** item 形 = `- Fnn <本文>` の 1 物理行のみ。H3・`base:`・継続行は付けない。
  本文は空白以外を含むことを要求する。
- **(P3)** 挿入位置 = 対象 F エントリの**末尾** (次の `### F` 見出しの直前)。`再発` と同じ位置。
  同一 fold で同じ F に `再発` と supersede が来たら **再発 → supersede** の順で挿入する。
- **(P4)** fold は接頭辞・日付を補わない。書き手が `- **supersede: 日付** — ...` を本文に書く
  (`見送り追記` の「日付は書き手が書く。fold は補わない」と同じ)。
- **(P5)** target は literal `Fnn` のみ。`{{F:slug}}` を target にはできない
  (同 fold で採番した新規 F を supersede するのは無意味)。本文中の placeholder は従来どおり解決する。
- **(P6)** 拒否条件 = 空節 / 複数行 item / 空白のみ本文 / target 不存在 / canonical F 重複 /
  対象エントリに同一行が既存 / 同一 fold 内の同一 (target, 本文) 重複。
- **(P7)** docs 更新は `docs/spool/README.md` の「fold が行うこと」3 と「不変条件」の
  既存 bytes 書き換え列挙にも及ぶ (現状は再発挿入と見送り追記の 2 つだけを列挙)。
- **(P8)** 本 wave の failures fragment に F196 への supersede 追記を 1 件入れ、
  `python3 tools/spool_fold.py --dry-run` で land 前に実 canonical に対して確かめる。

## 不変条件

- canonical の既存 bytes は不変 — 挿入のみで削除・並べ替えをしない。
- fold は決定的かつ冪等。時刻・mtime・ディレクトリ列挙順を出力に使わない。
- 既存の `新規` / `再発` / worklog / decisions の受理集合と出力 bytes は不変 (回帰なし)。
- 実装子は `tools/spool_fold.py` と `orchestrator/tests/test_spool_fold.py` だけを編集し、
  docs 編集と commit をしない。親が統合 commit・記録・land を行う。

## 成果物の形

上記 2 コード file の差分、docs 2 file の更新、failures fragment 1 件、worklog fragment 1 件。
受入は Pegasus login node で `python3 tools/run_tests.py` の受入全走 (runbook §7.3 の lease 経由)。

## 並列分割方針

実装面は 1 file + 1 test file で分割しない (段 5 は codex author 1 本)。
段 2 プラン 1 本、段 3 敵対 2 本 (sol / luna)、段 6 レビュー 2 本。docs は親が書く。
