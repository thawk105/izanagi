# [T-2228] A-2 経路で関門の 2 層目以降が発火することを実体で確かめた — 関門は通り、その先で 2 つの別の事実が出た

日付: 2026-09-04 / wave: `dev-wave-t2228-a2-gate-layers` / branch `worktree-dev-wave-t2228-a2-gate-layers`
基点 main: `396dc8988` (T-2226 着地後)。authority: none / default_effect: no-state-change (裁定パッケージは `ruling-package.md`)。

## 要点

1. **関門 (D1198 族) は A-2 経路で最後まで発火した。** production 入口 (`tools/pegasus/submit_paper_story_a2_certification.sh`) から
   attempt `t2228-20260904a` を投入し、rr5 / rr50 の両 workload で、旧経路では到達しなかった cell-1 (adopted) の両腕、
   family 判定、4 cell の admission、receipts、`run_campaign` (2 cell とも build → verify 6 回 → bench 5 回、anomaly 0) が実体で走った。
2. **関門の先で新しい層が出た。** `_raw_cell_from_wal` の canonical 判定が、patch 済みの木で評価された adopted cell を
   「WAL variant is not the canonical cell variant」で拒否し、driver は両 workload とも `driver_rc=2`。原因は identity の設計
   (adopted cell の src_token が `stock` 前提) であり、関門の欠陥ではない。受理集合に触るため裁定へ返す。
3. **既完走 4-cell (T-2022 attempt `t2022-20260828c`) の reject は、fixed backoff を測っていなかった。** 当時の driver は patch を
   当てていない共有木を `run_campaign` に渡し (pipeline は patch を当てない契約)、adopted cell の `BACKOFF_FIXED=10` は
   CMake に黙って無視され、`BACK_OFF=1` = CCBench 内蔵の指数 backoff 有効化だけが効いていた。F707 の型そのものの再発である。
   今回 patch 済みの木で測った adopted は stock より **速い** (rr5 +53.8%、rr50 +10.5%)。ただし今回の attempt は raw 化で失敗
   しているので、この数値は campaign log の観測値であり certified でも raw でもない。

## 実行 identity

- source commit (投入元 detached tree): `396dc89887b18477cfd665f88c5f93c95fcdae3f` (= local main、関門・driver ともこの commit)
- CCBench pin: `511c953` (full `511c9538e4e8efa54b45cda62e72389ed3b706ec`)
- policy: `orchestrator/campaign/paper_story_a2_certification.v2.json` (4 cell、`controlled_define_base` に `CCBENCH_BACKOFF_NOINLINE=0`)
- rr5 request `976127.nqsv` (Elapse 3140 s)、rr50 request `976128.nqsv` (Elapse 3156 s)、いずれも `driver_rc=2`
- durable authority: `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2228-20260904a/`
- receipts SHA-256: preregistration `0512fa85…6a2fe`、submission `d0a3eaba…280dd`、completion `a6d6fdb3…1ebe4`、acquisition `3f853efd…89763`
  (finish-group は両終端後に exact 1 回。raw manifest 無し = 失敗 attempt の閉じ方)

## 1. 関門が発火した証拠 (何を読んだか)

| 証拠 | rr5 | rr50 |
|---|---|---|
| campaign WAL の `build_start` (関門文脈が yield した後にしか書かれない) | 1 件 (`jobs/rr5/campaigns/…-285206c2/runs/wal.jsonl`) | 1 件 (`jobs/rr50/campaigns/…-bb1f5793/runs/wal.jsonl`) |
| job.stdout の `[campaign] evaluate` 行 | cell-0 (BF=-1) と cell-1 (BF=10) の 2 行 | cell-0 (BF=-1) と cell-1 (BF=5) の 2 行 |
| `[campaign] done` | 2 committed / 0 aborted / 0 skipped | 同じ |
| job.stderr の `condition gate rejected` | 0 件 | 0 件 |
| 前回 attempt `a2gate-20260902b` (T-2226 前) | cell-0 で両 macro とも `preprocess-root-dependent-builtin` 赤、cell-1 未到達 | 同じ拒否行 |

driver は cell ごとに両腕を評価して family 判定し、`admitted` でなければ即 `CertificationError` を投げる
(`paper_story_a2_certification.py:613-697`)。よって campaign が 2 cell とも走ったことは、cell-0 / cell-1 の 4 腕がすべて
family を通り (supply は緑、meaning は緑または unestablished)、receipts が 2 件作られ、context が yield した証拠である。

**限界:** 各 record の exact な reason code と admission payload は、driver が `run_campaign` 完了後に materialize する
`condition_gate_receipts` (job.stdout 末尾 JSON) にしか出ない。今回は driver がその前に落ちたため **record 単位の reason code は
残っていない**。静的予測 (段 2 plan、両腕 8 record の表) は insight の `verbatim/s2-plan.md` に凍結したが、実測値としては書かない。
campaign 前に receipts を保存する台帳の追加は、命令 (仮想リスク向けの台帳追加は scope 外) により本 wave では行わない。

## 2. 関門の先で出た層 — canonical variant 判定

| | stock cell | adopted cell |
|---|---|---|
| WAL の `src_token` | `stock` | `955b452a332d3b33cab33ea19d784da79f29b0913de179e494f62fdffeb093c9` (rr5) |
| WAL の variant id | `960e57e1aeba` (rr5 / rr50 とも) | rr5 `1f2762881fcb`、rr50 `47e599584695` |
| driver の期待 (`variant_id(_genome_for_cell(policy, cell))` = src_token `stock` 前提、`:2810-2813`) | `960e57e1aeba` (一致) | `09a3e222ce49` (rr5) / T-2022 当時の id (不一致) |
| raw payload | `jobs/*/raw/*-stock.json` 書き出し済 | 書かれず、`CertificationError("WAL variant is not the canonical cell variant")` |

`source_digest.resolve_evidence` は genome の define で前処理した owner 文脈を pin の baseline と比べ、一致すれば `stock`、
違えば digest を src_token にする (`source_digest.py:2196-2200`)。patch 済みの木では BF=-1 は stock 枝が選ばれ baseline と一致するので
`stock`、BF=10 / 5 は合成枝が選ばれるので digest になる。**これは patch が効いている証拠そのもの**であり、driver 側の
「adopted も `stock` token」という前提 (T-2022 当時は patch 無しだったので成立していた) が現実と食い違った。

## 3. T-2022 (attempt c) が測っていたもの

| 一次資料 | 値 |
|---|---|
| T-2022 当時の driver (`639c1dbad`) | `run_campaign(…, ccbench_dir=str(source_root))` = patch 無しの共有木。`patchharness` 参照 0 件。関門配線なし |
| pipeline の契約 (`pipeline.py:916`) | 「呼び手が `patchharness.isolated()` で作った worktree を `ccbench_dir` に渡す」= pipeline は patch を当てない |
| attempt c の rr5 WAL `src_token` | 4 record すべて `stock` (adopted も) |
| attempt c の rr5-fixed10 raw payload の variant | `09a3e222ce49` = `variant_id(genome)` (src_token `stock`) |
| stock CCBench の `BACK_OFF` | `cc/silo/transaction.cc:42,719` の `#if BACK_OFF` = 内蔵の指数 backoff。CMake 既定 `CCBENCH_BACK_OFF=1` |
| patch (`patches/silo-backoff-fixed.patch`) | `BACKOFF_FIXED` は patch が供給する CMake cache 変数。無い木では CMake が黙って無視する (F707) |

つまり attempt c の「adopted」cell は **`BACK_OFF=1` (内蔵指数 backoff) と `BACK_OFF=0` (backoff なし)** の比較であり、
「fixed backoff 10 us / 5 us」は測られていない。3 秒 bench の commit / abort もこれと整合する (下表)。

| workload / cell | attempt c (patch 無し) | t2228-20260904a (patch 済み) |
|---|---:|---:|
| rr5 stock (BF=-1, BACK_OFF=0) | 2,527,542 tps、~2.39M commit / ~18.2M abort | 2,628,031 tps (CV 4.05%)、~2.41M commit / ~18.1M abort |
| rr5 adopted (BF=10, BACK_OFF=1) | 1,355,011 tps、~1.10M commit / ~1.05M abort | 4,041,833 tps (CV 0.27%)、~2.53M commit / ~8.35M abort |
| rr50 stock (BF=-1, BACK_OFF=0) | 3,662,448 tps | 3,895,043 tps (CV 2.86%)、~4.17M commit / ~16.4M abort |
| rr50 adopted (BF=5, BACK_OFF=1) | 1,248,603 tps | 4,303,497 tps (CV 1.24%)、~4.40M commit / ~10.5M abort |

stock cell は両 attempt で同じ variant id・同じ規模の値であり、変わったのは adopted cell だけである。

**規律 7 に照らした位置づけ.** attempt c の測定と reject は当時の事実として残す。ただしその reject が支持する命題は
「内蔵指数 backoff 有効 vs 無効」であって「fixed backoff vs stock」ではない。訂正は追記で行い、bytes は変えない。
今回の attempt は raw 化に失敗しているので、逆符号の数値は certified 主張に使えず、正しい identity で取り直した attempt だけが
現行の主張を支える。裁定は `ruling-package.md`。

素材: A-2 の「adopted は stock に劣る (reject)」という結論は、D1198 が守ろうとした型 (条件が供給されず別の条件を測った) の
実例だった。関門を driver 全体へ義務化した後で最初に関門を通した実走が、その関門の前に取られた結論を覆した。

## 4. unit の正例・負例 (実体を名指し)

`orchestrator/tests/test_paper_story_a2_certification.py::test_condition_gate_family_real_records_positive_then_issued_red_negative`
(commit `b6a46f97c`、production 差分ゼロ)。既存テストは関門 4 関数をすべて stub していたため、driver から実体の
`require_condition_gate_family` を通す検査が 0 件だった。

- 正例: `_SUPPLIED` fixture (実 g++ / cmake) で monkeypatch **前**に実 record を作り、compiler を要する leaf 7 種だけを
  全引数 exact 検査付きで差し替え、production 相当 2 genome (BF=-1 / BF=10、NOINLINE=0) で receipts 2 件が
  record と実 family の admission の canonical JSON と完全一致することを固定する。
- 負例 (同じ test 関数): `_issue_arm_record` の赤 record (`configure-failed`) を実 family が `admitted=False` にし、driver が
  `CertificationError` に `macro:arm:reason_code:detail=` を載せることを固定する。family / wiring の負例であり実 configure 失敗の再現ではない。
- 実走: file 全件 114 passed / rc=0 (計算ノード、request `976243.nqsv`、5.90 s)。node 指定走 PASSED (request `976244.nqsv`、5.78 s)。

## 5. 開発検査

- 段 3 敵対相談 2 本 (`verbatim/s3-lensA.md` / `s3-lensB.md`) と段 6 敵対レビュー 2 本 (`verbatim/s6-reviewA.md` / `s6-reviewB.md`)。
  review B は must-fix 0。review A の must-fix 4 件はすべて変異登録の再照準 (既存テストでも落ちる変異を新規検出力に数えていた) で、
  コード fix はゼロ (`verbatim/s4-adjudication.md` 5a 節)。
- main 取り込み: T-2227 (main で着地、NOINLINE の meaning を枝選択 witness で宣言) が同じ test file と driver の関門文脈を変えていたため、
  clean な wave 木で Codex fix 子に「main 版 + 新 test」の最終形を書かせ、親が merge (固定 SHA `04576e521`) の中でそのまま採用した
  (merge commit `715480159`、codex `role=author` 併記)。新 test は NOINLINE=0 の meaning を
  `declared-compile-time-branch-selection-observed` (緑)、`unestablished_meaning_macros == ()` に追随した。
  merge 後の焦点走: 114 passed / rc=0、新 test PASSED (計算ノード、request `977700.nqsv`、6.19 s)。
- 変異 matrix (`mutation-spec.json`、sha256 `dd0b255b…`、DW-M08 の新旧両走):
  - 最終 tip `715480159` (新 test あり): baseline PASSED、**M1〜M7 の 7/7 KILLED**、SURVIVED 0、MISMATCH 0、TIMEOUT 0
    (`mutation-ledger-final.json`、計算ノード dispatch、8 走)。merge 前 tip `b6a46f97c` でも 7/7 KILLED (job dir に保全)。
  - 旧 HEAD `396dc8988` (main の test file、新 test なし、`mutation-oldhead-spec.json`): baseline PASSED、
    **M1〜M6 SURVIVED、M7 のみ既存 `test_condition_gate_prebuild_runs_once_for_multiple_cells` で KILLED**
    (`mutation-ledger-oldhead.json`、投入元 detached tree で実走)。したがって M1〜M6 は新 test だけが検出する差分であり、
    M7 は冗長 gate として新規検出力に数えない (段 4 裁定 5a 節)。
  - 段 4 の初回登録 (M2 / M4 / M5 / M7) は既存テストでも落ちる変異だった。段 6 review A が捕捉し、M2 / M4 / M5 を
    既存テストが生存する位置へ再照準した (erratum は `verbatim/s4-adjudication.md`)。probe は 3 回 queue 待ち (900 s 固定) で
    rc=16 になり、4 回目 (01:39 JST) で通った。
- 受入全走: 記録 commit を含む最終 tip に対して 1 回だけ走らせ、receipt は land が束縛する (値は本 README に書かない)。

## 既知限界と scope 外

- 他 3 driver (`backoff_sweep` / `backoff_repro` / `s1_direct_comparison`) の stock 比較は同じ `evaluate_define_supply_effectuation` の
  inert 経路を通る静的 consumer だが、driver 固有の root binding・到達・admission は本 wave では実測していない。
  本 wave の receipt はそれらの既存・将来成果物を追認しない。
- receipts の campaign 前保存、canonical variant 判定の修正、T-2022 への追記、A-2 の取り直しは本 wave では行わない (裁定へ)。

## 出所

- brief / plan / 相談 / 裁定 / 実装報告 / レビューの逐語: `verbatim/`
- 変異台帳: `mutation-ledger-final.json` / `mutation-ledger-oldhead.json`
