# [T-1027] 非帰属 checker — collect 打ち切りの是正と、実運用到達の残件

- wave: `dev-wave-t1027-acceptance-reds-checker` (2026-08-13)
- branch: `worktree-dev-wave-t1027-acceptance-reds-checker`
- 編集面: `tools/check_acceptance_reds.py` と `orchestrator/tests/test_check_acceptance_reds.py` のみ

## 何が真因だったか (実測)

`tools/pegasus/dispatch_compute.py` の `DEFAULT_SUCCESS_RELAY_LIMIT_BYTES = 4 * 1024` により、
child rc=0 の走行では子 stdout が末尾 4 KiB へ切り詰められる。

```text
[Pegasus dispatch] request 908840.nqsv child stdout begin (size=12098 bytes, omitted_bytes=8002)
| _docs_authority_alone_rejects_consistent_effort_mutation      <- 途中で切れた nodeid 片
| orchestrator/tests/test_codex_worker_launch.py::test_check_receipt_...
...
| 114 tests collected in 0.58s
```

`114 tests collected` に対し親へ届いた nodeid はおよそ 40 件。checker はこの部分集合を
完全な collection として扱い、exact selector を見つけられず rc=2 で止まっていた。

**完全な出力は disk に残っている。** `output/pegasus-dispatch/<nonce>/receipt.json` の
`scheduler_logs.stdout` は `omitted_bytes: 0` / `size: 12098` / 全文 `tail` を持ち、
欠けていた nodeid もそこに存在する。これが修正の足場になった。

**依頼が挙げたもう一方の候補 (xdist group suffix) は refuted。**
t907-t908-t910 wave の実 acceptance log の赤
`...::test_candidate_freeze_matches_contract_and_generation_chain@s8c-preregistration-candidate`
は、実 collect 出力に対して正しく match する。`| ` 行前置の除去も正常。
打ち切りは出力が relay 上限を超える file でだけ起きる。

## 何を変えたか

| # | 内容 |
|---|---|
| R1 | dispatch を伴う collect / rerun の timeout を 120 秒から 5100 秒へ。実測 211-213 秒の queue 待ちに負けていた。git 等は 120 秒のまま |
| R2 | collection の権威を dispatch receipt の `scheduler_logs.stdout.tail` へ。receipt は非 relay の一意な保存行から特定し、location / v2 schema / request args / child outcome / 完全性を検査 |
| R3 | footer 完全性 gate。selected 件数と unique nodeid 件数の一致を必須にし、欠落・複数・未知書式・重複・0 件を fail-closed |
| R4 | 検証済み nonce と fallback receipt を消したあと、exact dispatch root は**空のときだけ** `rmdir`。異物があれば保持して rc=2 |
| R5 | 単独 rerun の rc=1 だけで非帰属としない。当該 selector の FAILED/ERROR を rerun 自身の出力で裏取り |
| R6 | 選択に効く pytest 環境変数を collect / rerun の双方で除去し、選択集合を argv 決定にする |
| R7 | footer 欠落を production path のテストで固定 (seam 注入の恒真テストを検出力に数えない) |
| R8 | 権威 tail の U+FFFD を拒否。`errors="replace"` は byte 長を保つことがあり長さ一致は lossless の証明にならない |
| R9 | checker receipt に collection の出所 (nonce / request ID / stdout SHA-256) を記録 |

## 実運用到達は未達 — 残件と理由

赤を含む実 log での実走は、collect と selector 解決を越えた先で
**probe 指紋 gate と checker 自身の dispatch 残骸の衝突**により rc=2 で止まる。

```text
!! orchestrator/tests/__pycache__/    !! output/pegasus-dispatch/   ほか
status=invalid-input
reason=probe worktree is not clean, including ignored files
```

`output/pegasus-dispatch/` 側は R4 で閉じた。**`__pycache__` 側は scope 内で解けない** —
安全な解は producer の env allowlist へ `PYTHONDONTWRITEBYTECODE` を足すことだが、
`tools/pegasus/**` は本 wave の編集面の外である。裁定へ返した
(`rulings-inbox/2026-08-13-t1027-probe-fingerprint-vs-dispatch-residue.md`)。

一括削除案は段 6 レビューが正しく否定した。既存契約
`test_ignored_artifact_from_node_fails_closed` は rerun node が作った ignored な
`__pycache__/marker.pyc` を必ず拒否することを求めており、削除はこの防壁を壊す。

## 変異 (2 巡)

- **1 巡目 = probe。** KILLED 0 / MISMATCH 9 / SURVIVED 1 (`mutation-result-probe1.json`)。
  MISMATCH の原因は本 wave が入れた replay 回帰で、失敗 node の抽出結果に
  repo 非実在の `orchestrator/tests/test_example.py::...` が混入していた。
  SURVIVED 1 件は親の変異が等価だった (`PYTEST_ADDOPTS` は削除集合から差し引かれ別途上書きされる)。
- **2 巡目 = 本走。** baseline PASSED、**11/11 KILLED、SURVIVED 0 / MISMATCH 0**
  (`mutation-result.json`)。期待 node は完全集合へ再導出し、等価変異は実効 gate へ
  M8a / M8b の 2 件に分割した。M0 / M5 / M7 は wave 前の実コードそのものへの回帰変異である。

## この wave が示したこと

**gate を新設・改修する wave では、静的レビューは実環境欠陥を出せない。**
段 3・段 6 のレンズ計 4 本は production 経路の rc=0 漏れを 1 件も見つけられなかった
(それ自体は正しい結論だった) が、実環境の停止点は 1 つも出せなかった。
出したのは親の実データ実走 (5 件目の欠陥) と変異 matrix (本 wave 自身の回帰) である。
[T-1028] の「親が実データで 1 回通す」はこの型を捕まえるためにある。

**fail-closed の不変条件は、禁止する側の rc / status を明示して書く。**
親 brief は「不完全な collection から `attributable` を出すな」と書いたが、
危険なのは rc=0 (非帰属) 側であり、向きが逆だった。敵対レンズが blocker として是正した。
