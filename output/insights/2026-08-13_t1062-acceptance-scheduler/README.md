# [T-1062] 受入全走の実効 scheduler を receipt へ束縛する — 変異台帳と逐語

wave = `worktree-dev-wave-t1062-acceptance-scheduler`、base main = `48b2caab`。
裁定 = 2026-08-13 rulings 第 11 回 #3。

## 変異 matrix (最終: 14/14 KILLED、SURVIVED 0、MISMATCH 0)

runner 範囲ごとに spec を分けた。**期待 node は runner 範囲と対**であり、範囲が違う spec の
期待集合を流用してはならない。

| spec | runner 範囲 | 変異 | 結果 |
|---|---|---|---|
| `spec-a2.json` / `ledger-a2.json` | 4 file | MUT-A1 / A2b / A4 / A3 | 4 KILLED |
| `spec-a3.json` / `ledger-a3.json` | task_run + collection_config | MUT-A4b / A5b | 2 KILLED |
| `spec-b2.json` / `ledger-b2.json` | 4 file | MUT-B1〜B5 | 5 KILLED |
| `spec-c.json` / `ledger-c3.json` | land + task_run + collection_config | MUT-C1 / C2 | 2 KILLED |
| `spec-c4.json` / `ledger-c4.json` | land を `-k` で 2 test へ限定 | MUT-C3 | 1 KILLED |

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

marker の発行位置は `pytest_unconfigure` wrapper の最後である。conftest 自身が failure digest を
最大 48 KiB、この位置より前に出すため、`pytest_sessionfinish` で出すと失敗時の relay tail から
押し出されうる。
