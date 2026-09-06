# [T-2195] mocc trace policy の投入時束縛 — wave 記録

**wave:** `dev-wave-t2195-policy-binding` / branch `worktree-dev-wave-t2195-policy-binding`
**anchor commit:** `33d88a6b3` (段 5 実装)、`891136281` (段 6 fix 1)、`176ccb2ab` (段 6 fix 2)
**計測機:** Pegasus。テスト実走と変異走行は計算ノードへ dispatch。build / benchmark は行っていない。

---

## 1. この wave が主張できること

投入 script が policy を 1 回だけ読み、その bytes から出した raw SHA-256 と compiler mapping を、
投入受領証と scheduler 環境の両方へ束ねる。job 側の gate は **5 者の raw SHA** (post-clean の実体・
早期 parse 由来の shell 変数・pinned 受領証・qsub 環境変数・受領証に記録された qsub argv の `-v` 項) と
**3 者の mapping** (実体・shell 変数・受領証) の全一致を要求する。これにより次が新たに拒否される。

1. 「policy を書き換える → job に読ませる → source clean capture の前に戻す」経路。書き換えた bytes の
   SHA が投入時の値と食い違うため、clean capture を通っても `policy_binding` で落ちる。
2. 投入受領証の `policy.raw_sha256` や mapping を後から書き換えた走行 (環境変数・argv 側と食い違う)。
3. qsub の `-v` から `IZANAGI_MOCC_POLICY_RAW_SHA256` を落とした投入、値を差し替えた投入。
4. 早期 parse と post-clean の実体が食い違う走行 (投入側の再 hash と job 側の 5 者照合の両方で落ちる)。
5. policy を symlink・非 regular file に差し替えた走行、duplicate key を持つ policy / 受領証。
6. 未参照 field に `NaN` / `Infinity` を置いて SHA を合わせる細工 (権威的な全 `json.loads` が拒否する)。
7. gate を通った後に mapping や raw SHA が変わった走行 (finalization の独立 block が最終受領証を書かせない)。

## 2. この wave が主張してはいけないこと

- **policy の内容が正しいことは保証しない。** 保証するのは「投入時に読んだ bytes と、job が読んだ
  bytes と、記録された値が同じである」ことだけである。最初から誤った policy を置けば、三者は一致した
  まま通る。
- **投入する側と job が同じ主体である以上、意図的な弱体化への完全な防壁ではない** (規律 7、D387)。
  gate と検査を同じ主体が変更できるという限界はそのまま残る。
- **compiler の版ずれ検出そのものは拡張していない** (D1542 の射程)。本 wave は期待値の**出所**を
  束ねただけで、期待値の**中身**の妥当性には触れていない。
- 束縛は mocc trace の policy に限る。他の policy field や他の submitter への一般化は行っていない。

## 3. 変異走行が出した 2 つの実測

### 3.1 書き手のいない FIFO の負例は、赤にはなるが job を 1 時間止めた

段 6 fix 1 の時点で、gate の policy open から `O_NONBLOCK` だけを外す変異 (M18) を走らせた結果:

| 観測 | 値 |
| --- | --- |
| pytest の結果 | `1 failed, 144 passed in 14.28s` (writerless FIFO の負例が `TimeoutExpired` で赤) |
| batch job の Elapse | 3609 秒 (walltime 到達、request 979716) |
| 残った状態 | orphan hold + 変異が worktree に残留 |

`subprocess.run` の timeout は直接の子 (`bash`) しか kill しない。FIFO の open で block した**孫**
(heredoc の `python3`) が job の stdout / stderr を掴んだまま残るため、pytest が終わっても batch job が
終われない。**検出はできていたが、後始末ができていなかった。**

fix 2 で 3 つの wrapper (submit dry-run・POLICY BINDING GATE・POLICY FINALIZATION CHECK) の子起動を
`start_new_session=True` + `killpg` の回収経路へ替えた。同じ変異の再走で:

| | fix 1 | fix 2 |
| --- | --- | --- |
| M18 の所要 | 3609 秒 (job walltime) | 38 秒 (probe 2) / 206 秒 (本走) |
| 後始末 | orphan hold あり | なし |

**教訓:** 負例に timeout を付けても、block した孫が job の出力を掴んでいれば batch job は終われない。
`timeout` は「test が赤になること」しか保証せず、「走行が終わること」を保証しない。

### 3.2 gate の regular file 検査は、非 blocking 読みに隠れて単独では効かない

`S_ISREG` を落とす変異 (M10 = policy、M11b = receipt) はどちらも SURVIVED した。`O_NONBLOCK` 付きで
FIFO を読むと短絡読み取りになり、bytes が食い違って SHA 比較の側で先に落ちるためである。
**`S_ISREG` は冗長な歯**であり、単独変異の証拠から外す (DW-M03)。受理集合は変わらないので取り除きはしない。

## 4. 変異 matrix

runner = `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_mocc_trace_job_contract.py -q -rf`
(dispatch)。本走 tip `176ccb2ab`、spec sha256 `aabfcd1d1ab444ab1125b97674ffc781e333819dc0454a6bec9496a1d42627ad`。
**22 変異すべてが期待どおり (KILLED 19 / SURVIVED 3、期待外れ 0)、baseline 緑。**

| id | 変異 | 結果 | 赤になった test |
|---|---|---|---|
| M1 | 受領証 payload の `raw_sha256` を再 serialize hash へ | KILLED | `submit_dry_run_contract` |
| M2 | clean 後の再 hash 比較を落とす | KILLED | `submit_rejects_policy_change_between_parse_and_clean_gate` |
| M3 | 受領証から `raw_sha256` field を落とす | KILLED | `submit_dry_run_contract` |
| M4 | qsub `-v` の raw SHA export を落とす | KILLED | `submit_dry_run_contract` |
| M5 | gate: 実体 vs 受領証 SHA の比較を落とす | KILLED | `rejects_submit_raw_sha_mismatch` |
| M6 | gate: 実体 vs shell mapping の比較を落とす | KILLED | `rejects_parse_restore_clean_attack` |
| M7 | gate: 実体 vs 受領証 mapping の比較を落とす | KILLED | `rejects_submit_mapping_tamper` |
| M8 | gate: 実体 vs 環境変数 SHA の比較を落とす | KILLED | `rejects_env_binding_mismatch` |
| M9 | gate policy open の `O_NOFOLLOW` を落とす | KILLED | `rejects_symlink_policy` |
| M10 | gate policy の `S_ISREG` を落とす | SURVIVED (登録どおり) | — (冗長 gate、§3.2) |
| M11a | gate receipt open の `O_NOFOLLOW` を落とす | KILLED | `rejects_symlink_or_non_regular_receipt_after_pin[symlink]` |
| M11b | gate receipt の `S_ISREG` を落とす | SURVIVED (登録どおり) | — (冗長 gate、§3.2) |
| M13a | finalization の mapping 再確認を落とす | KILLED | `finalization_rejects_mapping_changed_after_gate` |
| M13b | finalization の raw SHA 再確認を落とす | KILLED | `finalization_rejects_raw_sha_changed_after_gate` |
| M14 | 最終受領証の `policy` payload を落とす | KILLED | `finalization_records_bound_policy` |
| M15 | gate: 実体 vs 早期 parse SHA の比較を落とす | KILLED | `rejects_parse_restore_clean_attack_raw` |
| M16 | gate: policy の repo 相対 path 検査を落とす | KILLED | `rejects_noncanonical_policy_repo_path` |
| M17 | gate: 受領証 argv の `-v` 項検査を落とす | KILLED | `rejects_submit_raw_sha_export_tamper` |
| M18 | gate policy open の `O_NONBLOCK` を落とす | KILLED | `rejects_writerless_fifo_without_blocking[writerless_fifo-regular]` |
| M19 | gate の `parse_constant` を落とす | KILLED | `rejects_non_finite_json[policy]` と `[receipt]` |
| P1 (過剰拒否) | mapping 比較を `==` から反転させ、正しい入力も拒否する | KILLED | `accepts_unchanged_policy` ほか 3 件 |
| E1 (等価) | `raise SystemExit(str(exc)) from exc` の `from exc` を落とす | SURVIVED (登録どおり) | — |

M12 (gate の順序) は実行時変異から除外し、静的 test で所有する。理由: 170 行の block の移動は置換で
表せず、marker の削除は診断文字列だけの赤になる (DW-M03)。M3 / M4 の owner は dry-run contract test の
みである。

## 5. 一次資料

| 何 | 所在 |
| --- | --- |
| 変異 spec / 台帳 | 本 dir の 6 file (`mutation-spec-*.json` と `mutation-ledger-*.json`) |
| codex 子の成果物と受領証 | job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2195-policy-binding/codex/t2195-policy-binding/` |
| 段 4 / 段 6 の裁定 | 同 job dir の `stage4-ruling.md`、`stage6-ruling.md`、`stage6-ruling-2.md` |
| M18 の hang の現物 | request 979716 の job stdout (Elapse 3609S)、probe 台帳の中断記録 |
| 受入全走 1 回目 | 同 job dir の `acceptance-receipt-1.json` (tested_main `9194bfef8`、tested_tip `4d49eee6f`、`20937 passed, 68 skipped`) |
