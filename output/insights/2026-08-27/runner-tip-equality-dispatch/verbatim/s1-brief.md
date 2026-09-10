# 段 1 brief — 受入の runner 束縛から tip 等値要求だけを外す

## 依頼 (ユーザー)

受入 launcher の runner byte 一致要求を外す。実行元を tested main の blob に固定する保護は維持し、
tip との等値要求だけを落とす。D838 の代償 (当該 file を直す wave が受入を通せない) を解消する。

## 既存被覆 (純増の確認)

`docs/decisions.md` / `docs/worklog.md` / `docs/archive/worklog-*.md` を「実行器」「等値」
「D838」で検索した。D838 (2026-08-25 裁定) と実装 wave (archive worklog 960、T-1283) が唯一の
先行で、**等値を緩める方向の検討・実装は一度も無い**。本 wave は全部が純増。
関連する後続裁定 D987 (実行器を変える main 取り込みだけ受領証再利用を拒否) は**未実装**で、
本 wave の scope 外 (別機構、forward-main merge 経路)。

## 現物の実測 (親が読んで確定させた)

落とす対象の「tip 等値」は repo 全体でちょうど 2 か所。

1. `tools/acceptance_launcher.py` `_launch`: `source = blob_reader(repo, tested_main)`,
   `tip_source = blob_reader(repo, tested_tip)` の後、
   `if source != tip_source: raise LauncherFailure("tested-main and tested-tip runner blobs differ")`。
2. `tools/dev_wave_land.py` `_verify_acceptance_receipt`:
   `main_runner_entry[1] != tip_runner_entry[1]` を含む or 連鎖で `_acceptance_rejected()`。
   verdict (`child-green` / `non-attributable-only`) によらず共通に掛かる。

待ち手 `tools/dev_wave_wait.py` には runner 等値検査は**無い** (grep で確認)。

**先例:** launcher 自身 (`tools/acceptance_launcher.py`) は既に「tested main の blob から実行、
receipt の `launcher_executed_sha256` を tested main 側 blob の内容 SHA と照合」だけで、
main/tip 等値は要求していない (`dev_wave_land.py` の `launcher_source_revision` 分岐)。
つまり本 wave の到達点は、runner を launcher と同じ束縛形式へ揃えることである。

## scope (実装面)

- `tools/acceptance_launcher.py`: 等値比較 1 か所を落とす。tip blob の**読み取り自体は残す**
  (実在しない tip は従来どおり fail-closed)。
- `tools/dev_wave_land.py`: 等値比較 1 項を落とす。tip 側 entry の実在・`blob` type・SHA 形式の
  要求は残す。
- `orchestrator/tests/test_acceptance_launcher.py` /
  `orchestrator/tests/test_dev_wave_land.py`: 等値を固定していた test を、
  **main 束縛を殺す negative test** へ置き換える。
- docs (親が書く): `docs/pegasus-runbook.md` の受入節 2 か所、spool fragment
  (decisions = D838 の代償部分の改訂、worklog)。

## 不変条件 (変えてはならない)

- launcher は tested main の blob を exec し、実行後に main blob を**独立に読み直して**
  `runner_executed_sha256` と照合する (M3)。この 2 点は不変。
- land は `receipt["runner_executed_sha256"] == content_sha256(tested_main の runner blob)` を
  verdict によらず要求する。不変。
- 受領証 schema `dev-wave-acceptance-receipt/v5` の field 集合・意味は不変。
- 待ち手の tip 束縛 (`waiter_executed_sha256`)、launcher の main 束縛、checker
  (`tools/check_acceptance_reds.py`) の main/tip 等値は**触らない**。
- 受理集合は「tip 側 runner が tested main と異なる受領証」の分だけ**広がる**。
  狭める方向の変更を同じ wave に入れない。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 落とすのは launcher と land の**両方**。launcher だけでは land が拒否し続け、
  依頼の目的 (代償の解消) が達成されない。「launcher」と書いた依頼文より、
  「D838 の代償を解消する」という目的文を優先して読む。
- **(P2)** tip 側 runner の**実在**要求は残す。依頼は「等値要求だけを落とす」であり、
  実在要求の撤去は受理集合をさらに広げる別の変更。
- **(P3)** 既存の main 束縛 test の fixture は、現状 main と tip の runner が同一の木に
  建っている可能性がある。同一なら「main に束縛」と「tip に束縛」が観測上区別できず、
  等値を外した後の主要 gate が**恒真になりうる**。新旧どちらの test も
  **main と tip で runner が異なる fixture** の上に建てる。
- **(P4)** checker の等値 (受理経路 ii) は scope 外。別 file・別裁定系列で、
  依頼文も launcher と runner だけを指している。

## 成果物影響 (DW-G05)

実装しない場合: `tools/run_tests.py` を変更する wave は受入受領証を作れず land できない。
現に [T-1932] (受入既定 shard 数 2→3、実測 43.6% 短縮) がこの 1 点で塞がっている。
実装した場合: certified 成果物の着地根拠のうち「受入を実行した runner の bytes」は
tested main 側 blob に束縛されたままで**値は変わらない**。変わるのは land の受理集合で、
「tested tip の runner が tested main と異なる受領証」がちょうど 1 種類ぶん受理されるようになる。
既存の受領証・過去の判定結果は 1 件も変わらない (拒否が消える向きの変更のため)。

## 分割方針

実装は 1 単位 (2 tool + 2 test file、同一機構で所有を分ける利点が無い)。
段 3 の敵対相談 2 本、段 6 のレビュー 2 本は省かない (受理集合が変わる wave のため)。

## (P3) の実測結果 — 親が段 1 で確かめた

- `orchestrator/tests/test_dev_wave_land.py::test_land_accepts_child_green_matching_main_and_tip_runner_blobs`
  は fixture 自身が `assert <tested_main の runner blob> == <tip の runner blob>` を置いている。
  この木の上では「main 束縛」と「tip 束縛」は**観測上まったく区別できない**。
  さらに request helper の既定は `runner_executed_sha256 = <tested_tip の blob の内容 SHA>` で、
  main を基準にした照合は既定 fixture では発火していない。
- `orchestrator/tests/test_acceptance_launcher.py::test_matching_main_and_tip_runner_blobs_execute_tested_main_source`
  は main と tip に**同じ bytes の別オブジェクト**を渡し、`executed_sources[0] is main_source` という
  **同一性**で区別している。等値要求がある間はこれが唯一可能な書き方だった。
- したがって等値要求を外した後は、両 file とも **main と tip で bytes が異なる fixture**を用意でき、
  「実行したのは main 側の bytes」「照合先は main 側の blob」を**内容で**殺せるようになる。
  この機会に fixture を bytes 差のある形へ移すことを段 4 で裁定する予定 (段 2 は代案を出してよい)。
