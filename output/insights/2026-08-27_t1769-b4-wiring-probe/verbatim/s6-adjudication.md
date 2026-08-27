# 段 6 レビュー所見の裁定 (親)

レビュー A (`s6-review-sol.md`) = must-fix 8 件、レビュー B (`s6-review-luna.md`) = must-fix 9 件 + nit 1 件。
重複を統合して 12 件の fix 項目にした。**所見ゼロではない。**

親が実測で確定した赤 1 件を先に記す。

## 実測で確定した赤 (RB9)

```
python3 tools/run_tests.py orchestrator/tests/test_plain_runner_coverage.py
→ 1 failed, 2 passed in 3.80s
  test_every_test_file_is_self_runnable_or_allowlisted
  assert not ['test_p3_b4_wiring_probe.py']
```

新規 test file に自走 harness (`_run()` / `__main__`) が無い。**受入全走で必ず赤になる。**
親の段 6 焦点走はこの consumer を漏らしていた (レビュー B が発見)。

## 実装子へ差し戻す fix (12 項目)

|#|由来|内容|
|---|---|---|
|F1|RA1 + RB4|multi-path audit event (`rename` / `replace` / `link` / `symlink`) の **source と destination を個別に realpath 解決**し、片方でも protected root に重なれば拒否する。`dir_fd` と pre-opened fd も解決対象に含める。destination 側の負例を operation ごとに置く|
|F2|RA2 + RB2|逆閉包の**射程を証拠で正直に固定する** — 解析した module 集合を exact に列挙し hash を残す。visitor が記録した unresolved issue を目録構築が**検査する**。証明経路上の aliased dynamic import・`sys.modules` alias・非 literal `getattr`・未解決 local assignment を `StaticInventoryError` にする。「module 限定なしの包含」を主張する文言を削る|
|F3|RA3 + RB3|import 副作用の検査を **runtime import より前**に行う。走査対象を runtime が実際に import する推移閉包へ広げる。decorator 内の call も走査する。**fresh single-thread process を起動条件として機械強制**し、seal 前から存在する非 main thread があれば拒否する|
|F4|RB1|`sys.setprofile` / `threading.setprofile` と code 生成系 audit event を遮断する。負例を **swap → 実 writer 呼出し → restore** の順に置き換え、restore 後の publish が拒否されることを示す|
|F5|RB5|`admission_reads.sha256` を**承認が実際に読んだ bytes 由来**にする。事後の再読 hash は照合にだけ使う|
|F6|RB6|preimage hash に **versioned domain prefix + NUL** を前置し、実 campaign ID の先頭 8 桁と一致しないようにする。trigger は**実 site resolver と同じ cfg 構築経路**を通す|
|F7|RA8 + RB7|publish 窓の boolean を **実 write / link の直前直後で観測**して構成する。静的経路上の**全 edge** の guard を逐語記録する (`main → drive_iteration` の `if a.run_iteration` を含む)。検査名を runtime 通過と誤読されない名前へ狭め、top-level にも非主張を置く|
|F8|RB8|`main(argv)` が one-way guard を残す以上、**fresh 専用 process 以外での実行を機械拒否**する。同一 interpreter での 2 回目の呼出しを拒否する|
|F9|RB9|**新 test file に自走 harness を足す** (`_run()` / `__main__`)。allowlist へは追加しない|
|F10|RA7|M-06 の負例が**実 protected root を対象にしない**ようにする。環境指定の protected root を `tmp_path` 配下に置き、before/after manifest を固定する|
|F11|RB9 後半|consumer 表を**参照関係から再生成**する。レビュー B が挙げた漏れ (`test_plain_runner_coverage.py`、`test_login_headroom.py`、`test_p3_s4_loop.py:1107`、`test_reflux_ir.py:274`、`test_t1286_commit_receipt.py:657`、`test_s8b_oracle_report.py:5488`、`test_t338_submission_gate_unit5.py:490`) を含める|
|F12|RB10 (nit)|cleanup 失敗が元の例外を隠さないようにする。primary exception を保持する|

## 親が引き受ける — 変異 matrix の再設計 (RA4 / RA5 / RA6)

`DW-M01` は「単一理由性を確認できなければ登録せず実効 gate へ再照準する」と定める。
レビュー A が静的に指摘した問題は**親の事前登録側の不備**であり、実装子へ差し戻さない。

|旧 ID|問題|再照準|
|---|---|---|
|M-01|過剰決定 (実 main 負例 + 3 driver 正例が同時に落ちる)|正例を落とさない位置へ移す。装着の**報告**でなく**装着そのもの**を 1 site だけ外す|
|M-03〜M-05|過剰決定 (seed 専用検査 + producer 負例 + 正例)|seed ごとの専用検査だけが落ちる位置へ移す|
|M-08 / M-09|過剰決定 (3 driver 正例が全部落ちる)|共有関数でなく**probe 側の照合**を 1 site 変異する|
|M-10|driver 未指定|base に固定する|
|M-11|生存 (temp parent 条件と issued path 条件の二重拒否)|**両条件を同時に外す 1 変異**に作り替えるか、片方の条件だけを持つ実効 gate へ再照準|
|M-12|生存 (publish 経路の呼出しを外しても直接呼びの test が通る)|F4 の新負例 (restore 後 publish 拒否) を期待 node にする|
|M-14|生存 (check-loop gate と schema gate の二重拒否)|schema gate が拒否しない入力を作り、publish gate 1 点へ再照準|
|M-15|過剰決定|sort の `conditional_edges` 検査 1 node へ絞る|

**再登録は fix 完了後、実装を読んでから確定する** (F7 が edge 記録を変えるため M-15 の位置が動く)。

## fix の分割 (DW-S06-B)

**一枚岩とする。理由:** 12 項目すべてが新規 2 file の中に閉じており、
F2 (静的解析) と F7 (証拠の edge 記録)、F3 (import 前検査) と F8 (process 契約) が
同じ関数群を触るため、所有を素集合に切れない。Codex fix 子 1 本へ寄せる。
