# 段 6 裁定補遺 — レビュー 2 本の所見と変異事前登録の訂正

親が段 6 の敵対レビュー 2 本 (`s6-reviewA.md` / `s6-reviewB.md`) を real / refuted へ裁定し、
本走前に変異事前登録を訂正する。訂正の理由をここへ残す (DW-M02 / DW-O12 の erratum)。

## 1. 所見の裁定

### A-1 (停止級) — real・**P では閉じない構造的残余として確定**

`tools/acceptance_shards.py:1201, 1243-1255` は `multiprocessing.get_context("fork")` で worker を
起動する。**fork は `close_fds` / `FD_CLOEXEC` と無関係に開いている fd を複製する**ので、
shard worker (tip 側 `acceptance_shards.py` のコード) は申告用 write-fd を継承する。

**裁定: real。ただし段階 P の制約下では閉じられない。**

- 実行器 `tools/run_tests.py` と `tools/acceptance_shards.py` はどちらも編集できない
  (前者は D838、後者は稼働 wave の所有)。
- そもそも **dispatcher はその fork worker から呼ばれる**。申告 channel は
  fork worker から到達可能でなければ機能しない。よって「runner の fork 子孫から隠す」は
  段階 P では原理的に不可能である。
- **それでも fd 案は file 案より厳密に強い。** file 案では `exec` された任意の子孫
  (login collect-only の pytest、bounded local の pytest、計算ノードの pytest = **被検査テスト
  コードそのもの**) が申告を偽造できた。fd 案ではそれらは `close_fds=True` で fd を失うため
  偽造できない。残るのは runner から fork された login 側 infra
  (`tools/acceptance_shards.py`、`tools/pegasus/dispatch_compute.py`) だけである。
- **記録する残余の正確な形:** 「`tools/pegasus/dispatch_compute.py` または
  `tools/acceptance_shards.py` を編集した wave は段階 P では捕まらない」。
  段階 R が外側 dispatcher import を main 側へ束縛して閉じる。

**採用する fix:** A-1 が指摘した**別 fd への誤書き込み**経路だけは塞ぐ。
dispatcher は書き込み前に `stat.S_ISFIFO(os.fstat(fd).st_mode)` で pipe であることを確かめ、
違えば fail-closed にする。環境の fd 番号が exec 後に再利用された fd を指す事故を防ぐ。

### A-3 (must-fix) — real・採用 (**正常経路を壊す実バグ**)

`tools/pegasus/dispatch_compute.py:487-492` の `_canonical_json_text` は `indent=2` の複数行
JSON を返し、それを申告 channel へ書いている (`:927-928`)。一方 launcher
(`tools/acceptance_launcher.py:115-125, 293-307`) は空白なし 1 行 JSON を canonical として
1 行ずつ parse する。**post-P の正常な dispatch が全部 land 不能になる。**

**裁定: real・最優先で fix。** dispatcher の申告書き込みを launcher と同じ canonical 形式
(空白なし・`sort_keys`・1 行 + 改行) にし、**dispatcher の writer が出した bytes を
launcher の parser へ直結する seam テスト**を置く。片側の serializer だけを使うテストは
この不一致を検出できない。

### A-2 / B-5 (停止級) — real・採用 (scope 拡大)

`orchestrator/tests/test_resume_gate_acceptance_boundary.py::test_resume_gate_then_postclaim_merge_runs_runner_once`
は実 launcher を copy し、K なし・申告なしで受領証成功を要求する。新契約で確実に赤になり、
**受入全走が緑にならないので本 wave が着地できない。**

**裁定: `orchestrator/tests/test_resume_gate_acceptance_boundary.py` を編集面へ加える。**
`test_dev_wave_wait.py` と同じ扱い — 明示 K=1 を設定し、synthetic runner に継承 fd へ
正規申告を書かせて成功期待を維持する。期待を失敗へ倒さない。

### B-4 (must-fix) — real・採用

計算ノード側の `_job_run` が bound request を検証して `runner_report` を result payload へ
載せるまでを通すテストが無い。helper 直呼びと `subprocess.run` 全面 mock では、
`_validated_runner_binding` / `_runner_binding_report` / optional field のどれを壊しても
検出できない。

**裁定: `_job_run` を通す E2E を 1 本足す。** site / envelope 以外の差し替えを最小限にする。

### A-4 (nit) — real・不採用 (残置)

`len(reports) != expected_k` が先に拒否するため、index 検査到達時の長さ条件は恒真。
削除しても受理集合は変わらない。防御的重複として残すが、**発火する保証として数えない**。

### B-1 / B-2 / B-3 (must-fix) — real・採用 (変異事前登録を訂正)

下記 §2 で M4 / M7 / M9 / M11 を訂正する。

## 2. 変異事前登録の訂正 (本走前・erratum)

**訂正の理由:** 段 4 で登録した 4 件は、実装が確定した後に見ると
(a) 同値変異である、(b) 構成できない、(c) 受理集合を変えず診断だけを変える、のいずれかだった。
DW-M03 と DW-M04 に従い、**本走前に**実効 gate へ再照準する。初回登録は消さずここに残す。

| # | 旧登録 (段 4) | 問題 | 新登録 |
|---|---|---|---|
| M4 | index multiset を `set` 比較へ緩める | **同値変異。** 件数が exact K で固定されているため、`set(idx) == set(range(K))` は multiset 一致と同値になる。`[0,0,2]` は `set` 化後も `{0,2} != {0,1,2}` で同じ例外を送る | **index 検査を丸ごと削除する。** `[0,0,2]` (件数 K・digest/nonce 正常) が受理されるようになるので受理集合が広がる。単一理由: 件数検査は通り、index 検査だけが唯一の拒否層 |
| M7 | 未設定・空の fail-closed を落とす | **診断だけの赤。** guard を消すと `int(None)` の `TypeError` になり runner は起動しない。受理集合は広がらない | **未設定時に既定 K=2 を返す。** runner が起動して受理集合が実際に広がる。単一理由: 未設定入力で runner 起動に到達するか否かだけが変わる |
| M9 | 申告 digest を manifest 期待値の転記にする | **構成不能。** 裁定どおり manifest に期待 digest を載せていないので、転記元が存在しない | **hash 対象を pathname から読み直した bytes にする** (stdin へ渡す buffer は main blob のまま)。main と tip の bytes が異なる実 repo でのみ差が出る。単一理由: 同一 buffer 束縛だけが破れる |
| M11 | manifest 一部欠落の fail-closed を落とす | **診断だけの赤。** guard を消すと欠落 key の添字参照が `KeyError` になり、scheduler へ到達しない | **部分 manifest を unbound として通す。** 1 key だけ設定した走行が現行 pathname 起動で dispatch されるようになり受理集合が広がる。単一理由: 部分 manifest の走行が scheduler へ到達するか否かだけが変わる |

M1 / M2 / M3 / M5 / M6 / M8 / M10 / M12 は登録どおり据え置く。
新設する A-3 の seam に対する変異を 1 件足す。

| # | 位置 | 変異 | 単一理由 | 期待 KILLED node |
|---|---|---|---|---|
| M13 | dispatcher の申告 writer | canonical 形式を `indent=2` へ戻す | writer の bytes を launcher の parser へ直結する seam テストだけが赤になる | `test_binding_report_writer_output_parses_in_launcher` |

**正例は P1 / P2 のまま据え置く。**

## 3. fix の scope

編集面に `orchestrator/tests/test_resume_gate_acceptance_boundary.py` を追加する。
それ以外の禁止事項は段 4 と同じ。`tools/run_tests.py`、`tools/acceptance_shards.py`、
`tools/dev_wave_land.py`、`tools/dev_wave_wait.py`、受領証 schema は不変のまま。
