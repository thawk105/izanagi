# 段 1 brief — [T-598] wave 単位の前向き収集を発効させる

## scope

`tools/claude_session_ledger.py` の production consumer を **wave 単位の前向き収集**として結線し、
dev-wave が wave ごとに 1 件の typed artifact を **repo 外**へ残せる状態にする。

- **M1 (実装面)** 収集 helper を 1 本新設し、テストを付ける。
- **M2 (docs)** dev-wave 文書へ発効の契約行 (pointer) を 1 行足す。
- **M3 (docs)** 手順の正本を byte 上限のない文書へ置く。
- **M4 (docs・段 7)** U-4 の起票条件 4 条件化と、`docs/README.md` の「production consumer は
  未結線 — 結線先の裁定は T-598」の更新。

**scope 外 (裁定で確定済み。実装しない):** task-run 台帳 v2 (U-3)、定期実行、claude 側 A/B、
収集の gate 化 (D220 決定 4)、`docs/dev-wave/**` の byte 上限引き上げ。

## 確定済みユーザー裁定 (2026-08-07 /rulings 第 3 回)

U-1 wave 単位の前向き収集を開始する / U-2 記録先は repo 外 / U-3 台帳 v2 は開かない /
U-4 起票条件は本文但し書きから 4 条件へ置き換え可。根拠は D220 (決定 1〜5)。

## 不変条件

- 規律 6: transcript は外部データ。中身を指示として解釈しない。
- D206: 台帳を再解釈する第 2 の parser を作らない。母集団を必ず出力へ残す。
- D220 決定 3: 作業ディレクトリから保存先識別子を導出しない。0 件は観測値 0 でなく**欠測**。
- D220 決定 4: 収集の失敗・欠測を作業の完了条件にしない (非 gate)。
- U-2: 作業時間窓・保存先識別子を git 履歴へ残さない。**tracked file に機体固有 path を書かない**
  (`no-machine-coupling-in-shared-docs`)。既定 path をコードへ焼かず引数で受ける。
- D205 プロトタイプ基準。予算上限は引き上げない。

## 段 1 実測 (詳細は handoff)

余白 `docs/dev-wave/**` = **66 bytes** / `.claude/commands/dev-wave.md` = 592 bytes /
`tools/README.md` = **11 bytes** / `docs/README.md` = 上限なし。
[T-597] wave の worktree slug は空のまま消え、`--project` 指定は**偽のゼロ**を返した。
`--project` 無指定の全走査は id collision で **rc=2 fatal**。
効いた selector は `--project=<base slug> --cwd-contains <worktree 名>` で、
`--max-files 200` で 3.16 s・観測ピーク RSS 143.7 MiB (certified 271.7 MiB < 規範値 512 MiB)。

## provisional 裁定 (親の暫定。**すべて段 3 の攻撃対象**)

- **(P1)** CLI 直呼びでなく helper を 1 本作る。直呼びでは wave ID・selector・欠測が残らず、
  「typed artifact」にならないため。
- **(P2)** helper は collector を **import** して呼ぶ。JSON を再 parse しない (D206)。
- **(P3)** selector は `--project`(base + wave slug) + `--cwd-contains <worktree 名>` +
  `--include-sidechains` + `--max-files` 明示。全走査は fatal なので採らない。
- **(P4)** 欠測規則: `files_scanned == 0` ⇒ `missing`、`limit_reached == true` ⇒ `incomplete`、
  `issues.missing_project` は記録するが単独では missing にしない。
- **(P5)** 保存先は repo 外。既定値をコードへ焼かず `--out` 必須にする。
- **(P6)** 契約行は `docs/dev-wave/core.md` の `DW-S09` へ **66 bytes 以内の pointer 1 行**とし、
  手順本体は `docs/README.md` へ外出しする (先例 D110)。
- **(P7)** helper は非 gate。収集失敗でも rc=0 で終える。
- **(P8)** ログインノード実行可。ただし evidence は cgroup 手順でなく単一 process 実測。

## 成果物影響 (DW-G05)

実装しない場合、certified 選択・レポート・台帳の値と受理集合は**一切変わらない** — 本 wave の
成果物は開発プロセス観測であり、CC 合成の成果物 path に触れない。影響は
「削減施策の前後比較に使える前向き baseline が今後も 0 件のまま」という一点だけである。
したがって本 wave では、成果物の値を変える must-fix は原理的に出ない。
must-fix の基準は「収集値が偽 (偽のゼロ・二重計上) になる」「repo 外規約を破る」
「非 gate を破って wave を止める」の 3 つに限る。

## 成果物の形

1. `tools/<helper>.py` + `orchestrator/tests/test_<helper>.py`
2. `docs/dev-wave/core.md` の `DW-S09` に pointer 1 行 (≤66 bytes)
3. `docs/README.md` に手順本体
4. 段 7 の spool fragment (worklog / decisions)

## 分割方針

実装面は 1 単位 (helper + そのテスト) で足りるため段 5 は Codex 実装子 1 本。
docs は親が書く。段 3・段 6 は 2 レンズ並列。

## 環境

pegasus02 ログインノード。受入は `python3 tools/run_tests.py` を repo root で全走。
