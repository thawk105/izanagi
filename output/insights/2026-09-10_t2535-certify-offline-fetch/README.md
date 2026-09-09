# [T-2535] 認定較正 job へ offline の FetchContent 供給を配線した — 非 silo の較正 record が初めて 1 件出た

wave `dev-wave-t2535-certify-offline-fetch`、branch `worktree-dev-wave-t2535-certify-offline-fetch`。
base `7f17e1c63`、main 取り込み後の tip は本 README を含む記録 commit。

## 1. 依頼と実施範囲

計算ノードから `github.com` を解決できず、CCBench の configure が masstree の FetchContent で
落ちるため、認定較正 record が 1 件も生産できていなかった (worklog entry 1405)。
この経路へ offline 供給を入れ、計算ノードの job で較正 record が 1 件出るところまでを実測した。

実施したのは次の 3 file だけである。

- `tools/pegasus/certify_calibration.sh` — staging root の構造検査、job-private への複製、
  pristine 検査、configure argv への 5 token 追加、verifier の interpreter 版数検査。
- `tools/pegasus/submit_certify.sh` — login 側の構造 precheck のみ。
- `orchestrator/tests/test_pegasus_calibration_workload.py` と
  `orchestrator/tests/test_pegasus_tools.py` — 契約テストと fixture。

条件関門の判定式・受理集合・既定値・stock 比較、walltime 式、`qsub` argv、receipt schema、
`tools/pegasus/admission_registry.json` は 1 bit も変えていない。

## 2. 結論 — 較正 record は出た

**request `989271.nqsv`、host `bnode020`、Elapse 302 秒、`calibrate_rc=0`、`failure.json` なし。**

| 項目 | 値 |
|---|---|
| protocol | `mocc` |
| genome | `mocc\|BACK_OFF=1,KEY_SORT=0,TEMPERATURE_RESET_OPT=1` |
| workload | `ycsb_zipf_skew=0.9, ycsb_rratio=50, ycsb_rmw=0` |
| threads | 48 |
| quality | `accepted` (reasons 空) |
| clocks_per_us | 2100 |
| records (飽和判定) | 1,000,000 — 下限基準を適用 (miss 率が単調上昇で飽和点なし、D15) |
| within-run noise floor | cv 0.0143、mean 818,327、`high_variance=false` |
| publish | `calibration-449d0ad22f13e366.json` (link-unlink) |
| CCBench head | `511c9538e4e8efa54b45cda62e72389ed3b706ec` |

acquisition receipt の `ccbench.build_argv` には 5 token が記録されている。

```
-DFETCHCONTENT_BASE_DIR=/scr/0_989271.nqsv/fetchcontent-base
-DFETCHCONTENT_FULLY_DISCONNECTED=ON
-DFETCHCONTENT_SOURCE_DIR_MASSTREE=/scr/0_989271.nqsv/fetchcontent-src/masstree-src
-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=/scr/0_989271.nqsv/fetchcontent-src/mimalloc-src
-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=/scr/0_989271.nqsv/fetchcontent-src/googletest-src
```

pristine verifier は無音で成功した (`third-party-source-verify.stderr` が 0 byte)。

## 3. 設計 — なぜこの形か

決定の本文は `docs/spool/decisions/2026-09-10-dev-wave-t2535-certify-offline-fetch-2.md`。要点は 3 つ。

1. **供給元は hydrate 済み staging であって永続 cache ではない。** masstree は
   `add_custom_command` の `WORKING_DIRECTORY` を source dir にして
   `bootstrap.sh` / `configure` / `make` / `ar` を実行し、`config.h` と archive を source dir へ書く。
   cache を直接指せば cache が汚れる。実際、永続 cache
   `/work/1/SFC/tanab/izanagi-thirdparty-cache` の masstree には ignored な生成物が **71 件**あった。
   `fetch_third_party.py verify` は既定で ignored を検査しないため rc=0 のまま見逃す。
   hydrate 済み staging は同じ検査で **0 件**だった。
2. **複製先 root と `FETCHCONTENT_BASE_DIR` を別 directory にする。** 同一にすると
   CMake の既定命名 `<BASE_DIR>/<name>-src` が複製を拾い、`SOURCE_DIR` override を 1 つ落としても
   configure が通る。テストは分離した実装と結合した対照を実 CMake で両方走らせ、
   前者だけが赤になることを確かめている。
3. **submit は hydrate も clone も git も起動しない。** login 側は staging root の構造検査だけを行う。
   これにより `submit_certify.sh` の admission 分類の根拠と実処理が食い違わず、
   `admission_registry.json` を変更する必要もない。

## 4. 実測 (親が取ったもの)

| 対象 | 値 | 取得場所 |
|---|---|---|
| login node の `github.com` 名前解決 | 成功 (20.27.177.113) | login |
| 永続 cache masstree の ignored artifact | 71 件 | login |
| hydrate 済み staging の ignored artifact | 0 件 | login |
| `cp -a` masstree | 21.3 秒 | login (宛先 NFS home) |
| `cp -a` 3 本合計 | 85 秒 | 同上 |
| hydrate 済み 3 依存の合計サイズ | 40 MiB | login |
| `_verify_pristine_floor_dependency_sources` 実コピーへの適用 | rc=0、22 秒 | login |
| 実 job の Elapse | 302 秒 | bnode020 |

実装の `timeout 120` は、この実測 max (21.3 秒) の約 5.7 倍である。

## 5. 変異走行

`mutation-spec-final.json` / `mutation-final-report.json`。
spec sha256 `eb14f70d1fe22ac059c822d7968fc76144adc946bff29cc1fda09051ae87c9e4`。

**baseline PASSED、9/9 KILLED、SURVIVED 0、MISMATCH 0、期待 node は probe 走で観測した完全集合。**
probe 走 (`mutation-spec-probe.json` / `mutation-probe-report.json`、
spec sha256 `4ddfdf8a267483ff46093ef37833010d486b09599fd206826a034d4dd75e528c`) は
全件 SURVIVED 登録で観測 node を集める用途で、9 件とも MISMATCH になっている。

登録した変異は M1〜M4・M6〜M10 の 9 件。
**M5 (5 token を `configure_argv` の先頭 5 要素へ移す) は登録から外した。** cmake が argv[0] でなくなり
コマンド自体が壊れるため赤の理由が一意にならない (DW-M01)。同じ境界を突く M8 (条件関門の
`${configure_argv[@]:5}` の幅を変える) へ照準し直した。

M8 は `test_pegasus_tools.py::test_certify_cmake_paths_derive_from_colon_free_job_tmpdir` も
巻き込む過剰決定がある。冗長 gate として記録し、単独変異の証拠としては
`test_certify_condition_gate_receives_the_same_fetchcontent_tokens` を採る。

## 6. 段 3・段 6 が実際に変えたもの

- **段 1 brief の (P1) は誤りだった。** 「cache は `verify` rc=0 だから pristine」は成り立たない。
  段 2 と段 3 の両方が独立に指摘し、親が ignored artifact 71 件を実測して撤回した。
- **段 3 レンズ A が「SOURCE_DIR を 1 つ落とす負例」の設計欠陥を出した。** 段 2 の案では
  複製先が `<BASE_DIR>/<name>-src` だったため、この負例は baseline から緑になる。§3 の 2 はこの是正である。
- **段 6 レンズ B が blocker を出した。** 新設の verifier 呼出しが裸の `python3` で、
  計算ノードの既定 3.9 では import 自体が失敗する構成だった。投入前に閉じた。F500 の再発として記録した。
- **段 6 レンズ A が「テストが production の関数を実行していない」を出した。** 条件関門への
  転送検査と configure の使用箇所の検査を、production の実体を走らせる形へ直した。
  これにより M8・M9 が殺せるようになった。

## 7. 名乗らないこと

- **「offline 供給を入れたので silo の認定が通る」とは言わない。** 本 wave が実測したのは
  `mocc` の 1 本だけである。silo は条件関門を通り、その関門は別課題がユーザー裁定待ちで所有している。
  さらに pristine copy には masstree の `config.h` が無く、D1666 が driver 段へ入れた
  関門前 prebuild は認定経路に無い。この層は未実測のまま残る。
- **「acquisition receipt が第三者 build 入力を束縛する」とは言わない。** receipt が記録するのは
  一時 path を含む argv だけで、masstree / mimalloc / googletest の pin は 1 つも入っていない。
  `pinned_clean=True` は CCBench checkout について述べたものである。
- **「条件関門への 5 token 転送を実機で確かめた」とは言わない。** mocc の job は関門を 1 度も呼ばない。
  転送は shell の実 fragment を走らせた検査であり、`condition_meaning_gate` 側の消費は未実走である。
- **「受理集合を緩めていない」とだけは書かない。** 判定へ到達する呼出し集合は、
  base 未供給だけを理由に前段で赤になっていた分だけ**制御された拡張**になる (D1721 / D1784 と同じ形)。
- 1 job・1 ノード・1 protocol の観測であり、計算ノード全体への一般化ではない。

## 8. 運用で踏んだこと

- **1 回目の投入 (`989232.nqsv`) は `source_identity` で止まった。** 親が投入後に
  `docs/spool/` の fragment を書いたため、job 冒頭の clean 再照合に掛かった。
  job の検査は `output/` を除外するので、投入中に書いてよいのは `output/` 配下だけである。
  実装の問題ではない。証拠は `measurement/first-attempt-failure.json`。
- **provenance の全史監査に短い timeout を掛けて orphan hold を作った。** 監査は計算ノードへ
  dispatch するため 300 秒では足りない。hold は `output/pegasus-dispatch/orphan-hold.json` と
  `orphan-holds/<request>.json` の **2 箇所**にあり、`qstat` の行頭照合で対象の終端を確認してから
  両方を消す必要がある。

## 9. 凍結した一次資料

- `measurement/` — 実 job の `job-result.json`、`acquisition-receipt.json`、`calibration.json`、
  `publish.json`、および 1 回目の `failure.json`。
- `mutation-spec-final.json` / `mutation-final-report.json` — 変異本走。
- `mutation-spec-probe.json` / `mutation-probe-report.json` — 観測 node を集めた probe 走。
- `verbatim/` — 段 1 brief、段 2 プラン、段 3 レンズ 2 本、段 4 裁定、段 5 実装子、
  段 6 レビュー 2 本と fix 子、親の実走結果。
