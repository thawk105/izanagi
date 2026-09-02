## 検査した範囲

- 指定された handoff、段 5 自己申告、snapshot patch、D1374、D1377、D19 と、適用済みの関連実装・テストを静的検査した。pytest は実行していない。
- snapshot patch と `git diff --binary` は同一だった。
- 差分は 6 ファイルだけで、Pegasus の registered 2 件を含む凍結対象には差分がない。既存 assertion、skip、xfail、テスト関数の削除もない。
- 層 3 の受理集合は次のとおり。

  - v1 lock: 従来どおり `calibration/*.json` の直下だけ。
  - v2 lock: 直下集合と、ever-active contract が pin する 1 path の和集合。解決後 path で重複排除。
  - pin から新規受理されるのは within-run だけ。pin 由来の between-run は除外される。
  - `registered/` 全体は走査しないため、Pegasus g1 は pin により候補となるが、未 pin の g2 は候補にならない。
  - protocol、records、threads、workload の完全一致と、複数一致の fail-closed は維持される。

既知の `parents[3]` による入れ子 output_root の赤は、指示どおり所見に数えていない。

## real 所見

1. 根拠語の三分類が、match した非 legacy floor の成果物へ出力されない。

   `_floor_protocol_and_basis` は三分類を正しく返すが、match 後は `genome-absent-legacy-record` の場合だけ `protocol_match_basis` を report に追加している。[layer3_report.py:402](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/layer3_report.py:402) [layer3_report.py:531](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/layer3_report.py:531)

   したがって、match した `receipt-derived-build-argv` と `canonical-floor-genome` は最終 report ではどちらも field 不在となり、親の「表示を弱めて三分類を書き分ける」裁定を満たさない。追加テストも helper と mismatch 行だけを検査し、match した report を検査していない。[test_layer3_report.py:3191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/tests/test_layer3_report.py:3191) [test_layer3_report.py:3212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/tests/test_layer3_report.py:3212)

   さらに現行 schema は `protocol_match_basis` を legacy literal にしか許しておらず、親の「layer3_schema.json は変更しない」と三分類の成果物表示は両立しない。[layer3_schema.json:257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/layer3_schema.json:257)

   成果物影響: floor の値と受理集合は変わらないが、材料レポートと将来の certified report で receipt 由来と producer 管理 genome の参照根拠が区別不能になり、要求された provenance 表示が欠落する。

## refuted 所見

- pin-only 化はしていない。直下 glob と pin の和集合、および解決後 path の重複排除を確認した。[layer3_report.py:442](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/layer3_report.py:442)
- pin の contract/env 解決、repo・env directory 境界、通常 file、SHA-256 は実際の `build_report` 経路から到達する。複数一致も引き続き例外になる。[layer3_report.py:343](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/layer3_report.py:343) [layer3_report.py:391](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/layer3_report.py:391) [layer3_report.py:514](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/layer3_report.py:514)
- genome 導出は SPACES 在籍、全軸、TRACE 1 件かつ 0、重複、非整数、値なし、build 側 CCBENCH define、target と basename を検査する。binary SHA 照合後かつ benchmark 前に発火する。[cli.py:373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/cli.py:373) [cli.py:843](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/cli.py:843) [cli.py:978](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/cli.py:978)
- schema は legacy と genome 付きの二つの exact shape だけを受理する。canonical 順序、整数、重複、空 body、TRACE、再構成一致も検査し、import は stdlib のままである。[schema_v2.py:742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/schema_v2.py:742) [schema_v2.py:770](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/schema_v2.py:770)
- D1374 の legacy 一致と表示、および既存回帰は維持されている。[layer3_report.py:418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/layer3_report.py:418) [test_layer3_report.py:2977](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/tests/test_layer3_report.py:2977)
- `nm` 検査、records 決定、既定 sweep、CV 算出、正しさゲートには差分がない。
- M1、M3からM8、M10 は事前登録した機構を静的に捕捉する。揮発する時刻や絶対 path の固定値は追加されていない。

## nit

- M2 の mocc テストは、protocol を `silo` に固定すると期待文字列の不一致へ到達する前に、silo 軸不足で例外になる。[test_calibrator_certify.py:431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/tests/test_calibrator_certify.py:431) [cli.py:455](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/cli.py:455) 変異自体は赤になるが、事前登録した「`mocc|...` literal 不一致」という単一理由性には一致しない。
- 実装子の「rejected 全成果物へ同じ genome」という自己申告は広すぎる。result 未生成の早期失敗は従来形の `rejection.json` を書き、genome を含まない。[cli.py:763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/cli.py:763) [cli.py:1113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/cli.py:1113) calibration/v2 成果物の契約違反ではないが、自己申告は限定すべきである。

## 総括

real 所見は 1 件。直下 glob と pin の和集合、fail-closed、producer 導出、二形状 schema、D1374、不変条件は概ね裁定どおりである。一方、根拠語の三分類が最終 report へ届かず、M9 の追加テストもその欠落を見逃している。schema の許容値更新と、match した receipt 由来・canonical 由来の双方を最終 report で検査する回帰が必要である。