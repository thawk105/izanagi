# 段 6 敵対レビュー B (テスト検出力・変異帰属) — Claude 子 opus / read-only の逐語

親注記: pytest 未実走 (DW-O05)。判定は NO-GO (記録面)、変異 R1〜R6 は全件 kill 可能。

三ファイルとも読了。worktree の実体 (`tools/pegasus/test_dispatch.py`, `orchestrator/tests/test_pegasus_test_dispatch.py`) を patch と突き合わせて検証した。**pytest は一切走らせていない。以下はすべて静的検査であり、緑は主張しない。**

---

## 所見一覧

### [RB-1] R4 の実効位置 `validate_final_receipt_object` の accounting 再検証は**到達している** (blocking 条件クリア)
到達点は 3 つ、すべて `verify_files=True` かつ `accounting` 非 None。

- `tools/pegasus/test_dispatch.py:4400` `if final.get("accounting") is not None:` → `:4412-4416` `validate_nqsv_accounting(..., expected_group=bound_policy.account)`。この block は `:4298 if verify_files:` の内側。
- `accounting` 非 None は `:4161-4173` (CHILD_RESULT は `accounting is None` を拒否) により保証。
- `verify_files=True` の 3 経路:
  1. `PathMonitorFilesystem.stage_final` → `:4547-4551` (monitor の staging)
  2. `PathMonitorFilesystem.publish_final` → `:4542` → `_publish_final:4446-4450`
  3. `resume_dispatch:6479` (`filesystem` 省略 → `PathMonitorFilesystem`) → `:6490-6495` `verify_files=isinstance(fs, PathMonitorFilesystem)` = True
- test 側: `orchestrator/tests/test_pegasus_test_dispatch.py:2596-2611` が `filesystem=` を渡さずに `TD.monitor_job` を呼び、`:2626-2633` が `filesystem=` を渡さずに `TD.resume_dispatch` を呼ぶ。
- 実測裏付け: `grep PathMonitorFilesystem orchestrator/tests/test_pegasus_test_dispatch.py` の hit は新 test の docstring `:2571` **のみ**。既存 test は全件 `FakeFilesystem` で、`FakeFilesystem.publish_final:178-182` / `stage_final:190-194` はどちらも `verify_files=False`。**`:4412` が実装前に無被覆だったという B-5 の前提は静的に追認できる。**

成果物影響: 書けない (検出力の所在確認)。**blocking ではない (条件充足)**。

---

### [RB-2] R4 の red/positive の役割が事前登録表と**反転**している。要再照準
事前登録 R4 = 「`:4415` 束縛を `bound_policy.queue` に差替」。この変異下で:

- `test_resume_rejects_published_final_sealed_with_a_foreign_group` は封印済み group が `"OTHER"`、期待が `"gen_S"` → **依然 mismatch → 依然 raise → 緑のまま**。red 側はこの変異を殺さない。
- 殺すのは positive 側 `test_real_filesystem_final_receipt_rechecks_accounting_group_on_resume` (group `"SFC"` vs `"gen_S"` → `monitor_job` の stage_final 時点で DispatchError → `:2596` の `== 0` が落ちる)。

つまり red 側が殺すのは「`expected_group=` 引数そのものの削除」(TypeError) であって登録変異ではない。さらに positive が落ちるのは **monitor の publish 段**であり、test 名が謳う `on_resume` の leg には到達しない。表の R4 行を「positive が主 killer / red は引数削除の pin」と書き換えるべき。

file:line: `tools/pegasus/test_dispatch.py:4415`、`orchestrator/tests/test_pegasus_test_dispatch.py:2596-2611`, `:2706-2718`
成果物影響: 書けない。**nit (変異は殺せる。帰属記述の誤りのみ)**。

---

### [RB-3] `_bind_resumed_submit_identity` の第 2 連言項は**論理的に死んでいる**。変異で守られない
`tools/pegasus/test_dispatch.py:6458-6461`:
```python
    if (
        stdout_raw != qsub_request_id_raw
        or stdout_normalized != job_id_normalized
    ):
```
- `parse_qsub_id:662` は `return raw, normalize_job_id(raw)`。
- `_validate_submit_object:2620-2621` は resume 到達時点で `normalize_job_id(qsub_request_id_raw) == job_id_normalized` を既に強制済み (`:6653-6659` で呼ばれる)。

よって `stdout_raw == qsub_request_id_raw` ⟹ `stdout_normalized == job_id_normalized`。**第 2 項が単独で真になる入力は存在しない**。`or stdout_normalized != job_id_normalized` を削除する変異はどの test でも殺せない。R2 が守っているのは第 1 項 (raw 比較) だけであり、第 2 項は装飾。

成果物影響: 書けない (受理集合不変)。**nit だが「未被覆行」として §7 に必ず計上すること**。

---

### [RB-4] `except DispatchError: return` の escape hatch が無被覆。E1 の閉包は「qsub.stdout が parse できる場合」に限定される
`tools/pegasus/test_dispatch.py:6454-6457`:
```python
    try:
        stdout_raw, stdout_normalized = parse_qsub_id(stdout_text)
    except DispatchError:
        return
```
- 「submit-receipt.json 有り + `clean_return`(rc 0) + qsub.stdout が parse 不能」という状態で resume すると、**receipt の id は一切検証されない**。docstring `:6448-6451` が自認しているとおり、これは `_recover_submission_identity` を通った正規状態であり、実運用で到達しうる。
- resume は「その状態なら `submit-identified`(source=`scheduler-lookup`) と matched WAL が存在するはず」を**要求していない** (`:6685-6705` は不在なら黙って append する)。したがって偽 receipt はこの分岐で素通りする。
- この branch を `return` から `raise` に変える変異、あるいは `try/except` ごと削除する変異を殺す test は**新規 9 件のいずれにも無い**。`grep "def test_resume"` した 13 件を見ても、rc 0 かつ stdout 非 parse かつ submit receipt 有りの resume を作る test は存在しない。

成果物影響: **書ける** — 裁定 3 が事前登録した成果物影響 (「resume が qstat を経ずに他人の job へ qdel / final 封印」) のうち、**qsub.stdout が parse できない部分集合は閉じていない**。受入台帳に「E1 は R5 の 裁定 3 系列を全閉包する」と書くと過大主張になる。
**blocking (記録面)**。実装追加は要求しない。台帳の主張範囲を「qsub.stdout が clean parse する resume に限る」へ限定し、未閉部分を既知欠落として残すこと。

---

### [RB-5] `_append_matched_lookup_result` が**製品が絶対に書けない、かつ製品なら拒否する** WAL 行を作っている。R6 の純増検出力は装飾
`orchestrator/tests/test_pegasus_test_dispatch.py:1554-1579` の row の key 集合は
`{event, schema, attempt, argv, job_name, qsub_request_sha256, qsub_result_sha256, qsub_started_epoch_s, absolute_deadline_epoch_s, disposition, reason, candidates, monotonic_s}`。

`tools/pegasus/test_dispatch.py:3828-3836` が要求する `result_keys` は上記 + `{returncode, signal, timed_out, output_limited, completion_unknown, raw}`。→ `set(payload) != result_keys` で `"scheduler lookup result WAL is malformed"` (`:3849`)。

さらに `:3911-3914` は candidates を raw qstat から `parse_qstat_candidates(..., expected_group=policy.account)` (`:3887`) で再導出して逐語一致を要求する。**wrong-group candidate は再導出時に落ちる**。

fixture が緑になるのは `FakeFilesystem.publish_final:178-182` / `stage_final:190-194` が `verify_files=False` で publish するからだけ。docstring `:1548-1552` はこれを自認している。

結論: R6 の red は「製品が書けず、実 FS publish なら別の理由で拒否される入力」を検出する test。裁定 1 が既に「成果物影響 refuted」としており整合するが、**受入台帳では R6 を closure の証拠に数えてはならない** (R5 と同じ「診断 pin」扱い)。

成果物影響: **書けない**。**blocking (記録面のみ)** — 台帳の R6 行に「成果物影響なし・fail-fast の対称性回復のみ」を明記。

---

### [RB-6] 偽の緑の罠は**無い**。`submit_and_monitor` 非経由を追認
- 新規 9 件はすべて `TD.resume_dispatch` / `TD.monitor_job` / `_monitor` を直接呼ぶ。`submit_and_monitor` の呼出は 1 件も無い。
- `except BaseException` は `tools/pegasus/test_dispatch.py:6226` の 1 箇所のみで、これは `submit_and_monitor` の内部 (`:6226-6260`)。新 test の呼出面には掛からない。`monitor_job:4963` / `resume_dispatch:6469` に broad handler は無い。
- `FakeScheduler.run:66-69` の sentinel は `AssertionError`。`pytest.raises(TD.DispatchError)` は捕捉しない → sentinel が偽の緑を作る組み合わせは無い。
- `FakeFilesystem.read_bytes:212` は `TD.DispatchError` を投げうるが、3 つの red はいずれも `match=` を持ち (`"differs from the qsub.stdout"` `:2407` `:2441`、`"candidate group is not the policy account"` `:2481`、`"accounting Group Name mismatch"` `:2709`)、これらの文字列は fake から出ない。偽陽性経路なし。

成果物影響: 書けない。**nit (肯定的所見)**。

---

### [RB-7] red 3 件は変異下で「別例外で赤くなる」。post-condition assert が到達不能
R1/R2/R6-red はいずれも `FakeScheduler([])` を渡す。対応変異を入れると検査は通り、resume は `monitor_job:6891` へ進んで `FakeScheduler.run:67` の `AssertionError` を投げる。`pytest.raises(DispatchError)` はこれを再送出するので **test は赤くなる (=変異は殺せる)** が、`:2417-2422` `assert scheduler.trace == []` / `assert not [...submit-identified...]` は**一度も評価されない**。

したがって「qdel/monitor へ進まないこと」「submit-identified が書かれないこと」は、**非変異 run でしか主張されていない**。裁定 3 が事前登録した成果物影響の核 (「qstat を経ずに qdel」) を直接 pin する test (cancel-intent 有りの resume + 偽 receipt) は無い。ただし検査位置が `:6662-6667` と分岐選択 (`:6787` cancel-intent / `:6848` unknown / `:6891` monitor) の**手前**にあることは静的に自明なので、実害は帰属の弱さのみ。

成果物影響: 書けない。**nit**。

---

### [RB-8] `monkeypatch` は正当。ただし「試験対象関数そのもの」への差替である
`orchestrator/tests/test_pegasus_test_dispatch.py:2664-2673` は `TD.validate_nqsv_accounting` を差し替える。
- no-touch 対象への monkeypatch ではない (対象は同 module 内の関数)。同 file の既存 test も `TD` 内部を差し替える (`:779` `:1265` `:1848` `:2296` `:2933` `:2968`) ので確立パターン。
- module global 経由の解決なので `:4412` と `:5303` の両方が差し替わる。`monkeypatch.undo()` (`:2695`) が resume 前に確実に戻す。
- 差替関数 `:2666-2669` は `bound(..., expected_group="OTHER")` を呼ぶ。返り値 dict (`:3231-3236` 相当) に group は含まれないので、封印される `final["accounting"]` は本来の実装と bit 同一。**期待値の焼き込み・現行値の差し込みは無い**。
- 揮発 payload の焼き込みも無い: `_accounting:400-418` は固定 epoch 文字列、user 名は `TD.scheduler_user_name()` で毎回計算 (`:405` 相当)。時刻・path・tree hash の直書きは無い。

成果物影響: 書けない。**nit**。

---

### [RB-9] positive control は「過剰拒否検出」として**十分**
| test | rc | drain | qdel 0 | 追加証拠 |
|---|---|---|---|---|
| `:2455 test_resume_accepts_submit_receipt_identity_equal_to_qsub_stdout` | `:2472 ==0` | `:2481` | `:2482` | final の raw/normalized `:2484-2485`、submit-identified 1 件 `:2486-2489` |
| `:990 test_monitor_accepts_accounting_group_equal_to_policy_account` | `:996 ==0` | `:998` | `:999` | `policy.queue != policy.account` gard `:993`、Group 行 1 本かつ `== policy.account` `:1002-1007` |
| `:2526 test_resume_accepts_lookup_wal_candidate_from_the_policy_group` | `:2545 ==0` | `:2554` | `trace == [("qstat","-f",JOB_ID)]` `:2555` (qdel 0 より強い) | source `scheduler-lookup` `:2561` |
| `:2564 test_real_filesystem_...` | monitor `:2596 ==0` / resume `:2626 ==0` | `:2612` | `resumed.trace == []` `:2634` | 実 FS の final を再 parse `:2613-2623` |

R5 (`:5306` を `policy.queue` へ差替) は `:990` の positive だけが殺す。R3-red (`:961`) はこの変異下でも緑のまま (`"OTHER" != "gen_S"` で依然拒否) — 事前登録どおり。**nit (肯定的所見)**。

---

### [RB-10] 新規 fixture の副作用は既存を壊さない
- `_accounting:400` の `*, group="SFC"` は keyword-only + 既定値。既存呼出 `:549` `:933` `:1022` はすべて位置引数 0〜1 個 → 無影響。
- `_reseal_submit_receipt:1524-1542` は `artifacts` dict を **in-place 更新** (`:1541`)。R1/R2 のみで使用され、更新後に `_append_pre_submit_and_qsub_intent`/`_append_qsub_return` が走る順序 (`:2395-2402`, `:2431-2439`) なので整合。`unlink()` (`:1532`) は `create_file:441` の `O_EXCL` 回避に必須。
- `_write_real_dispatch_files:1582-1585` は `TD.create_file` (O_EXCL) を使うので二重呼出で `FileExistsError`。新 2 test での 1 回ずつの使用のみ。`_qsub_artifacts` は `runner-result.json` を作らない (`:1427` は path のみ) ので衝突なし。
- `_append_matched_lookup_result` は RB-5 のとおり。既存 test は使わない。

成果物影響: 書けない。**nit**。

---

### [RB-11] 未被覆の残り (§7 の列挙)
1. `tools/pegasus/test_dispatch.py:6460` — 死んだ連言項 (RB-3)。殺せる変異が存在しない。
2. `tools/pegasus/test_dispatch.py:6456-6457` — `except DispatchError: return` の分岐 (RB-4)。到達 test なし。
3. `tools/pegasus/test_dispatch.py:6453` — `read_text(encoding="utf-8")` が無防備。非 UTF-8 の `qsub.stdout` は `UnicodeDecodeError` (非 `DispatchError`) を送出し、resume が fail-closed でなく異常終了する。既存 `:6712` と同型なので新規劣化ではないが未被覆。
4. `tools/pegasus/test_dispatch.py:5306` — 裁定 2 自身が「冗長 gate」と認定。positive `:990` の診断 pin のみ。closure に数えない。
5. `_policy_bound_lookup_candidate:4651` の group 検査は 2 呼出元 (`:4623` lookup replay / `:6678` resume) を持つが、新 test が突くのは resume 側のみ。lookup replay 側は既存 test 依存。
6. `:4412-4424` を被覆するのは新 2 test **だけ**。この 2 件が無関係な理由で赤くなると `:4412` は静かに無被覆へ戻る (単一障害点)。

**nit だが台帳へ逐語計上を要求する**。

---

## 変異判定表

| ID | 判定 | 理由 (1 行) |
|---|---|---|
| **R1** | **殺せる** | `:2395-2400` の再封印 receipt は `_validate_submit_object:2620` を通るので、`:6662-6667` を削ると `:2407` の `match="differs from the qsub.stdout"` が満たされず赤 (実体は `FakeScheduler` sentinel の escape)。 |
| **R2** | **殺せる (ただし守られるのは `:6459` の raw 項のみ)** | `raw="123.nqsv"` / `normalized="123.nqsv"` は `_NQSV_ID_RE:274` で内部整合なので、normalized だけ比較する変異は素通り → `:2441` が赤。`:6460` 側は RB-3 により永久に無被覆。 |
| **R3** | **殺せる** | `_qstat:424` の既定 group が `SFC` で per-job gate `:5107` を通過するため、`_accounting(group="OTHER")` を拒否できるのは `:3247-3250` だけ。削除でも `!=`→`==` 反転でも `:967` の rc 125 か `:971` の `ACCOUNTING_INCOMPLETE` が落ちる。 |
| **R4** | **要再照準 (変異自体は殺せる)** | `bound_policy.queue` 差替を殺すのは positive `:2596` のみで、red `:2637` は緑のまま。しかも positive が落ちるのは resume ではなく monitor の `stage_final:4547` 段。表の red/positive 役割を入れ替えて記録すべき。 |
| **R5** | **殺せる (診断 pin)** | `policy.queue` 差替は positive `:990` (`assert policy.queue != policy.account` `:993` が分離を保証) が rc 125 で落ちる。裁定 2 どおり closure には数えない。 |
| **R6** | **殺せる (ただし純増検出力ゼロ)** | `:4664-4669` の group 検査削除で `:2481` の `match` が外れて赤。だが入力行は `_validate_scheduler_lookup_chain:3828-3849` を通れない非製品 WAL であり (`FakeFilesystem` の `verify_files=False` でのみ緑)、成果物影響は書けない。 |

**殺せない変異: なし。** 事前登録 R1〜R6 は全件 kill 可能。ただし R2 は登録より狭い範囲しか守らず、R4 は照準が反転、R5/R6 は診断 pin。

---

## 判定

**NO-GO (条件付き・記録面のみ)**。変異 R1〜R6 は全件殺せ、R4 の実効位置 `test_dispatch.py:4412` への到達も 3 経路で追認できたので、実装・test の差戻しは要求しない。
NO-GO の根拠は 2 点: (1) RB-4 — `:6456` の escape hatch により E1 は「qsub.stdout が parse できる resume」しか閉じていないのに、裁定 3 の成果物影響が全閉包として記録されようとしている。(2) RB-5 — R6 の入力は製品が書けず実 FS なら別理由で拒否される行なので、closure の証拠に数えられない。
台帳に (a) E1 の閉包範囲の限定、(b) R6/R5 を診断 pin として除外、(c) RB-2 の R4 照準訂正、(d) RB-11 の未被覆 6 件を明記すれば **GO**。

---

## 総括

R4 は事前登録の必須条件を満たしている — `verify_files=True` かつ `accounting` 非 None の組に、`monitor_job` の stage/publish と resume の 3 経路で実到達しており、既存 test が 1 件も `PathMonitorFilesystem` を使っていないことも grep で追認した。
偽の緑の罠は無い。`submit_and_monitor` の `except BaseException:6226` は新 test の呼出面に掛からず、`FakeScheduler` sentinel は `AssertionError` なので `pytest.raises(DispatchError)` に吸われない。fixture への現行値差し込み・揮発 payload の焼き込みも無い。
弱点は検出力ではなく**帰属と主張範囲**にある。R4 は red/positive の役割が反転し、R2 は連言の半分が論理的に死に、R6 は製品が書けない WAL 行を突いている。
最も実質的なのは `:6456` の `except DispatchError: return` で、ここは無被覆かつ E1 の閉包に穴を残す — 実装追加ではなく受入記録の限定で処理すべき。
pytest は未実行。この報告のいかなる部分も「緑」を意味しない。実測は計算ノード上の親の責任。