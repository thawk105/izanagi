# [T-1687] 繰越義務述語の段 6 前提関門 adapter — 変異 matrix の逐語

- wave: `dev-wave-t1687-carry-obligation-caller`
- 本走 spec: `2026-08-26_t1687-carry-obligation-caller-mutation-spec.json`
  (sha256 `190e19c0b96d994136c71ab4bd42d2db9c63f7941e3ec2e011daa3970394c815`)
- 本走 repo_head: `2d49db399e1079196590e550a3a2d292b0f9eada`
- 本走 raw 台帳: `2026-08-26_t1687-carry-obligation-caller-mutation-ledger.json`
- runner: `python3 tools/run_tests.py --force-dispatch -n 0
  orchestrator/tests/test_calibration_freeze_stage6_candidate_gate.py
  orchestrator/tests/test_calibration_freeze_authority_contract.py -q -rf`
- 本走結果: **baseline PASSED、KILLED 13 / 13、SURVIVED 0、MISMATCH 0、
  TIMEOUT 0、PARSE_ERROR 0**

`-n 0` は F95 の回避である (下記 erratum)。

## 本走の内訳

段 4 裁定 §4 が登録した A1〜A8 / B1〜B3 / C1 と正例 1 件の全 13 ID を実走した。

| ID | 登録 ID | 撃つ不変条件 | 変異 |
|---|---|---|---|
| `t1687.m01` | A1 | adapter は義務述語を実際に呼ぶ | 呼出し行を削除する |
| `t1687.m02` | A2 | 義務未解消は必ず拒否側の終端へ落ちる | `ContractError` を握り潰し policy 終端へ進める |
| `t1687.m03` | A3 | **呼んだふりでは通らない** | 述語を呼ばず、同じ診断文の `ContractError` を adapter 内で自作する |
| `t1687.m04` | A4 | 義務が通っても受理経路は無い | policy 終端の送出を `return None` に置換する |
| `t1687.m05` | A5 | 呼び手が渡した path を素通しする | 受け取った path を捨てて既定を渡す |
| `t1687.m12` | A6 | 義務述語はちょうど 1 回だけ呼ばれる | 義務述語を 2 回呼ぶ |
| `t1687.m06` | A7 | 述語由来でない例外を関門の結果に化かさない | 捕捉を `except Exception` へ広げる |
| `t1687.m13` | A8 | 2 つの終端は別の型である | policy 終端で義務拒否側の型を送出する |
| `t1687.m07` | B1 | 呼び手の棚卸しの母集合が縮まない | 母集合から `orchestrator/campaign/` を外す |
| `t1687.m08` | B2 | 集合の exact 判定が恒真化しない | 判定器の比較を `if False:` にする |
| `t1687.m09` | B3 | **台帳の記載だけを書き換える抜け道が無い** | 前提条件表の `unmet` を `met` に書き換える |
| `t1687.m10` | C1 | 設計正本と契約 module の逐語が片側だけ動かない | 契約 module の pin 末尾を旧文へ戻す |
| `t1687.m11` | 正例 | 合格終端は恒偽でない | 義務述語を恒偽にして常に拒否させる |

期待 node は probe 相の実測を完全集合として固定し、本走で完全一致だけを KILLED とした
(`DW-M08`)。逐語は raw 台帳の `expected_nodes` / `failed_nodes` にある。

## 帰属の注記

`t1687.m01` と `t1687.m03` は 4 node、`t1687.m04` と `t1687.m13` は 2 node、
`t1687.m10` は 25 node が同時に赤になる。いずれも単一の変更に起因する単一理由であり、
期待 node を完全集合として登録している。

**呼出しの実在を独立に示すのは return-spy
(`..._executes_obligation_predicate_with_forwarded_paths`) だけである。**
実 repository の終端テストと policy 終端テストは終端 oracle であって wiring oracle ではない。
段 6 の敵対レビューがこの区別を指摘し、テストの docstring へ明記した。

段 4 で登録した B2 は当初「実 repository 側の `0 件ちょうど` を `0 件以上` へ緩める」変異だったが、
段 6 レビューが「負の対照が別経路を見るため生存する」と実測したため、`DW-M01` / F28 に従って
判定器そのものの恒真化へ再照準した。

## 撃っていない面 (焦点再レビューの実測)

- **実 repository 側の判定呼出しそのものを削る変異は撃っていない。** テスト自身の assertion を
  削る変異はどのテストでも同型に成立し、本 wave 固有の穴ではない。判定の論理は共有純関数へ
  集約済みで、その恒真化は `t1687.m08` が殺す。
- module を跨ぐ alias の再 export は 1 file の AST では解決できない。この限界は
  `_caller_inventory()` の docstring に明記した。同 file 内の辞書経由・引数束縛経由・
  変数束縛経由は「曖昧な caller」として fail-closed になる。
- 段 0 の 7 算出値は変異の対象ではない。既存の exact-summary テストと、差分がそこへ到達しない
  ことが別証拠である。

## erratum

`DW-M02` に従い、初回結果を消さずに残す。

### 1 回目 — 未追跡ファイルで中断

親が変異走行中に台帳 fragment を repo へ書き、harness が
`runner/test 実行前に untracked file を検出` で中止した。fragment を commit してから再投入した。
`DW-O19` は「変異前は `--porcelain` 空確認」を求めるが、**走行中に tree へ書かない**ことは
書いていない。段 8 の改善候補とした。

### 2 回目 — F95 の 3 例目

段 6 の fix で `REAL_REPO_SERIAL_NODES` へ登録した
`test_stage6_candidate_gate_caller_inventory_matches_repository_and_docs` が kill 集合に入るため、
F95 と同じ二重拘束に当たった。素の node id で登録すると実測側が `@real-repo` 接尾辞付きで
`MISMATCH` になり、接尾辞を付けて登録すると preflight が
`期待 node が pytest collection に実在しない` で停止する。

F95 の恒久対応は `_normalize_node` への接尾辞正規化で、別タスクとして未着手である。
本 wave は**再照準せずに済む迂回**を実測で見つけた — runner argv へ `-n 0` を足して
並列を切ると、実測側の node id にも接尾辞が付かず、preflight と突き合わせの表記が一致する。
1 変異だけの probe (`result-serialprobe.json`) で確認してから本走した。
これにより、**台帳の記載だけを書き換える抜け道を塞ぐ変異 (B3) を落とさずに済んだ**。

### 3 回目 — queue 混雑による rc=16

本走の 6 件目で `receipt scheduler_logs.stdout.path がない` / rc=16 になった。
`docs/pegasus-runbook.md` が明記するとおり dispatch の infra 失敗であって変異判定の結果ではない。
`IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=1800` を与えて `--resume` し、残りを完走した。

### 4 回目 — 登録 ID の欠落

焦点再レビューが、段 4 裁定の登録 12 ID に対して親が組んだ変異が 11 件であり、
A6 と A8 が除外理由の記録なく落ちていたことを指摘した。両者を追加し、13 件で組み直して
本走をやり直した。上表がその全件である。
