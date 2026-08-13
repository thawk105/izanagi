# [T-1062] 受入全走の実効 scheduler を receipt へ束縛する — 変異台帳と逐語

wave = `worktree-dev-wave-t1062-acceptance-scheduler`、base main = `48b2caab`。
裁定 = 2026-08-13 rulings 第 11 回 #3。

## 変異 matrix (最終: 15/15 KILLED、SURVIVED 0、MISMATCH 0)

runner 範囲ごとに spec を分けた。**期待 node は runner 範囲と対**であり、範囲が違う spec の
期待集合を流用してはならない。

| spec | runner 範囲 | 変異 | 結果 |
|---|---|---|---|
| `spec-a2.json` / `ledger-a2.json` | 4 file | MUT-A1 / A2b / A4 / A3 | 4 KILLED |
| `spec-a3.json` / `ledger-a3.json` | task_run + collection_config | MUT-A4b / A5b | 2 KILLED |
| `spec-b2.json` / `ledger-b2.json` | 4 file | MUT-B1〜B5 | 5 KILLED |
| `spec-c.json` / `ledger-c3.json` | land + task_run + collection_config | MUT-C1 / C2 | 2 KILLED |
| `spec-c4.json` / `ledger-c4.json` | land を `-k` で 2 test へ限定 | MUT-C3 | 1 KILLED |
| `spec-a4.json` / `ledger-a4.json` | failure_digest + task_run | MUT-A2c | 1 KILLED |

正例 (過剰拒否の検出) は 2 件ある。

- **MUT-A5b** — `_is_full_suite` を常に False にする。受入形 3 種と既存の full 分類テストが
  10 件赤になり、full 認定を過剰に狭める変更が検出できることを示す。
- **MUT-C3** — land の受理集合から `serial` を外す。`test_land_accepts_effective_scheduler[serial]`
  が赤になる。**受理集合を狭めていないことの証拠**であり、段 3 で対立した 2 レンズのうち
  「`loadgroup` のみ受理」を採らなかった裁定が実装に効いていることを示す。

## 初回走で起きたこと (probe → 再登録の記録)

- **MISMATCH 5 件はすべて「予測より検出力が高い」方向**だった。DW-M08 に従い初回を probe と
  して扱い、実測の完全集合へ再登録して再走した。初回 ledger は job dir に残している
  (`/work/1/SFC/tanab/dev-wave-jobs/t1062-acceptance-scheduler/mutation/ledger-a.json` /
  `ledger-b.json` / `ledger-c2.json`)。
- **SURVIVED 3 件の内訳。** 2 件は変異設計の誤りだった (marker を移さず二重に出す形になっていた、
  前段の分岐に先取りされる)。**1 件は本物のテスト欠落**で、exact 型判定を `isinstance` へ
  緩めても 1 件も落ちなかった。派生クラスを実効 scheduler にするテストを足して殺した。
- **MUT-C3 は 64 件を赤にし、failure digest が 48 KiB 予算で 52 件を省略した。** job stdout から
  完全集合を導けないため、runner 範囲を `-k` で当該契約 2 test へ絞って測り直した。
  `IZANAGI_FAILURE_DIGEST_ACCOUNT` の `omitted_failures` が 0 でない走行は、完全集合が
  採れていないと読む。

## 実機で観測した wire (relay 後の逐語)

Pegasus 計算ノードへ `--force-dispatch` で投入した走行の log に現れた marker 行。

```text
| IZANAGI_EFFECTIVE_SCHEDULER_V1 {"effective_scheduler":"loadgroup"}
```

行頭に `| ` が前置されるのは `tools/pegasus/dispatch_compute.py` の `_prefix_relay_lines` に
よる。成功時の relay は末尾 4 KiB (`DEFAULT_SUCCESS_RELAY_LIMIT_BYTES`)、失敗時は 64 KiB。
この literal は `orchestrator/tests/test_dev_wave_wait.py` の回帰テストへ pin してある。

marker の発行位置は `pytest_unconfigure` wrapper の中の **failure digest の直前**である。
`pytest_sessionfinish` で出すと digest (最大 48 KiB) より前になり失敗時の relay tail から
押し出されうる。逆に digest より後にすると、digest の END 行が stdout 末尾であることを要求する
`test_pytest_failure_digest.py` の e2e 契約を壊す (受入全走 1 回目で実測)。
前後どちらへも寄せられない位置が digest の直前だけである。

## 受入全走 (4 回)

| 走 | 結果 | 赤 | 帰属 |
|---|---|---|---|
| 1 | 10820 passed / 2 failed | digest e2e、signal 族 1 | digest e2e は本 wave 帰属の回帰。修正済み |
| 2 | 10819 passed / 3 failed | signal 族 1、t126 signal 2 | 3 件とも単独走で緑 = 非帰属 |
| 3 | 1 failed | t126 qualification driver 1 | 単独走 24 passed = 非帰属 |
| 4 | **10873 passed / 65 skipped / 0 failed (143.72 秒)** | なし | receipt 発行 |

4 回目の receipt (schema `dev-wave-acceptance-receipt/v3`) は
`effective_scheduler = loadgroup`、`verdict = child-green`、`child_rc = 0`、
`argv = ["python3", "tools/run_tests.py"]` を記録した。**本 wave の目的が実データで成立した
唯一の証拠である。**

赤が 1 件でもあると非帰属 checker が `probe worktree is not clean, including ignored files` で
rc=2 (判定不能) になり receipt が出ない。DW-O18 により rc=2 は非帰属の根拠にできないため、
完全緑になるまで再走した。新規作成した probe worktree 自体は clean であることを親が実測している。
