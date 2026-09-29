# 段 4 裁定 — [T-2853] R2 fig8b

- 裁定時刻: 2026-09-28 JST (段 3 の 2 本受理後)。入力: s1-brief.md、codex/s2-plan.md (受理 rc=0)、codex/s3-a.md・s3-b.md (受理 rc=0)。
- 裁定 inbox 再走査: rulings-inbox の 2026-09-27〜28 (full37〜39) に T-2853 / fig8 / R2 の新裁定なし。

## 所見の裁定

| ID | 所見 | 判定 | 採否 | 処置 |
|---|---|---|---|---|
| s3-a F1 | 生成器の provenance 検査は役割枠 (1, primary)/(2, reproduction) を固定要求 (plot:544)。役割を変えると検査不合格、残すと図中で R2 が主結果/独立再現に見える | real | 採用 | wrapper は内部の役割枠と検査を保ち、図中の block 見出しと caption の役割語だけを R2 用 (R2-a / R2-b、別 attempt) にする。出力後に生成器の既存 closure 検査 (validate_external_sources / _validate_repo_closure_v2 相当) を通す。測定値の受理条件 (verdict・gate_passed・failures・repo_stock_pin・SHA・DAT) は一切変えない |
| s3-a F2 | source commit・nonce は completion.json に無く reservation.json にある | real | 採用 | 完走照合は request ID・workload・run kind・status を completion と receipt、source commit・gitlink・nonce・script SHA を reservation と receipt で照合 |
| s3-a F3 | 両 group を 8737 で走らせると cohort 1 の厳密な再実行でない | real | 採用 (s3-b F1 で解消) | A′ 採用。対照表に group ごとの source commit・事前登録 commit・文書 blob SHA・spec SHA を別欄で載せる |
| s3-b F1 | P2 (A) では cohort 1 を測り直したことにならない。A′ は同費用で driver 改修不要 | real (旧依存元 /work/SFC/tanab/github/{gflags,glog} は現存し HEAD = policy pin・clean を親が実測) | 採用 | P2 を A′ に改める: R2-a = submit-tree at `0600887d92538b3f34d894f9674d202d0a29a578` + 事前登録 `cad6f46d8` (40 桁は投入時に rev-parse)、R2-b = submit-tree at `8737cacb4bd286eb3e0784d16dba6eb85e5d6eab` + 事前登録 `8737cacb4` |
| s3-b F2 | 対照表の必須項目が過大 | real | 採用 | 表は 4 group × 3 workload: group・source/事前登録・verdict、8 点の throughput / abort rate の平均と 95% CI、6 区間の state と L の範囲、1250→9999 µs の throughput 比、正しさ件数。反復値・全境界は report / DAT / provenance の path と sha256 で辿る |
| s3-b F3 | 図が出ない場合の成果物を結果前に明記 | real | 採用 | insight §0 項 7 に「完走・invalid・未完走・描画拒否のいずれも掲載、図が出ないときは group ごとの report・値・拒否理由を表で並記」を明記 (投入前 commit に含める) |
| s3-b F4 | wrapper の陽性対照・細かな記録は追加検査 | real (nit) | 部分採用 | 陽性対照は最小に絞る: 原 metadata で wrapper を通した artist_series が既存 fig8b provenance の artist_series と一致すること 1 点だけ (wrapper が値を変えないことの確認)。記録は wrapper の sha256・実行 argv・入力 sha256・出力 provenance |
| s2 P4 注 | CLAIM_BOUNDARY_V2 は import 時に元 COHORTS から作られる | real | 採用 | wrapper は COHORTS 差し替え後に CLAIM_BOUNDARY_V2 を作り直す |

## プラン v2 (確定)

1. P1 維持: 元の driver = `tools/pegasus/submit_b10_backoff_grid.sh --run-kind t2500-tail-formal` (依頼の shape.sh は fig13 の driver で誤記)。driver 変更なし。
2. P2 → A′。submit-tree-a を 0600887d9 に移し (detached checkout + submodule update)、precheck (HEAD・clean・事前登録 cad6f46d8 の bytes 一致・gitlink 511c953・job script sha・凍結 digest・旧依存元) を通す。
3. P3 維持: trace 保全 opt-in は使わない (driver の qsub -v が渡さず、両 commit とも D2233 以前)。理由を insight に記録。
4. P5: insight §0 (A′ と s3-b F3 を反映) を投入前に commit (docs-only)。その commit 後に投入。
5. 2 group を同時投入 (6 job = 6 node)。出力親 `/work/1/SFC/tanab/b10-backoff-grid-t2853-r2-20260928/`。探索走 campaign は cohort 2 と同じ path。
6. 待ち手 1 本で 6 root の completion.json / failure.json を待つ。起動時検査で測定前に落ちた job は原因を直せるなら直し、新しい nonce・新 group で投げ直す (元 request ID を記録)。
   R2-a が旧 commit 固有の環境要因で起動できないと判明した場合は、R2-a を 8737cacb4 で投げ直し、その旨と理由を記録する (結果を見る前のこの規則で決める)。
7. 集団報告は group ごとに、その group の submit-tree で手順書 §4 の argv (事前登録 commit は投入時と同じ) を実行し、出力を出力親の `group-report-r2-a` / `group-report-r2-b` へ。
8. 描画・対照表の wrapper は Codex author 1 本 (repo の worktree 内 scratch に書かせ、親が実行後 repo 外へ退避、repo には入れない)。
9. 段 6: 一次資料から値を書き起こすので read-only review 1 本 (+ 必要なら焦点再レビュー)。受入全走は DW-S04 により免除しない (約 0.25 node 時間)。
10. 見積り: 測定 1.40 + 受入 0.25 = 1.65 node 時間 (< 2)。起動失敗の再投入は測定前の数秒で線に影響しない。実測で 2 を超える見込みになったら止めて見積りを示す。

## 変異の事前登録

repo の実装面 (D95 決定 2) の差分はゼロ (wrapper は repo 外の使い捨て)。DW-S04 により変異 matrix は免除。受入全走は行う。
