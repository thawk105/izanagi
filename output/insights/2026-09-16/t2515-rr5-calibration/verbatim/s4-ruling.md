# [T-2515] 段 4 裁定 — rr5 の accepted 較正取得

親が段 2 プランと段 3 の 2 レンズを real / refuted に裁定し、プラン v2 を確定する。

## 1. 親 brief の (P1)〜(P3)

| 前提 | 裁定 | 根拠 |
|---|---|---|
| (P1) 依頼の「未着地 6 commit の回収」はすでに main で完了 | **real。回収作業は行わない** | `35a740cd4` が 5 commit の必要差分を合成、2026-09-15 の `worktree-dev-wave-t2515-record-recovery` (main の祖先) が残る 17 file を byte 一致で回収、`559bcbc29` の conftest 部分は T-2579 が実装。`3dbf7ea1d` の関門 argv 修正は `run_condition_gate` ごと撤去され対象が消滅 |
| (P2) 再走で accepted になる見込みが高い | **real、ただし射程を狭める** | レンズ A [1] を採用。probe が示したのは「旧系列なら選択警告が解消する」までである。旧 CV=0.013535 は **1,000,000 件**の反復値で、新しい選択点 2,000,000 件の CV を裏づけない (`sweep.py` は選択後の N で雑音反復を取り直す)。「他の却下理由は 0 件」も旧 run の事実であって新 run の予測ではない |
| (P3) 実装面の差分ゼロ | **維持。段 2 と レンズ B [3] を不採用** | 親が実走で測定した。`test_probe_output_v1_corpus_is_exact_and_replays_all_physical_copies` は `orchestrator/tests/growth_test_holds.py:300` に登録済みで、実走は `IZANAGI_GROWTH_HOLD_SUMMARY_V1 {"collected_hold_functions":1,"opted_in":false}` を出して **skip** した (1 skipped)。新しい attempt を 1 件足しても赤にならない。段 2 と レンズ B は本文の静的読解だけで判定しており、両者とも pytest 未実走だと自ら明記している |

## 2. 段 3 所見の裁定

| # | 所見 | 裁定 | 対応 |
|---|---|---|---|
| A[1] | 旧 CV は 1M の値で新選択点 2M を裏づけない | **real・採用** | insight で「選択器の再評価」と「今回の測定」を別表に分ける。CV は今回の実測値だけを書く |
| A[2] | hold の skip はコーパス整合性の証明ではない | **real・採用** | 「対応不要・整合性確認済み」とは書かない。既存不一致 6 件・今回の増分 1 件・検査が走らなかった事実を insight に残す。hold の解除はユーザー指示専用なので触らない |
| A[3] | 「rr5 取得済み」だけの更新は旧却下を見えなくする | **real・採用** | `docs/phase3.md` の T-2515 行と insight から 2026-09-14 の却下 (`0_995806.nqsv`) と T-2534 の記録へ辿れる形にする |
| A[4] | D2026 の正本収録 commit は `3c87bafdc` で実装 commit `632754bbc` と別 | **real・採用** | 親が実測で追認した。`3c87bafdc` = 2026-09-15 18:35「Fold landed documentation fragments」、main の祖先。両方を区別して記録する |
| B[1] | 先行と同一 script bytes という前提は失効 | **real・採用** | 現 `certify_calibration.sh` = `3fc75c03fb66b4c284b70d6558b7fbe6eb081a2d02b3f10c07a1c99bb570e110`。親が独立に実測した。改訂 `f5ba28378` は予約式のコメントと receipt の文面だけで、`frozen_required_s` と timeout は不変。所要 184/177/238 秒は参考値に留め、保証として書かない |
| B[2] | job の出力で tree が dirty になり、収録前に受入・land へ進むと止まる | **real・採用** | `output/env/pegasus/calibration/attempts/` (tracked 418 file) と同 `job-staging/` (tracked 934 file) はいずれも gitignore 対象ではない。job 終端後に生成物を収録してから受入・land へ進む |
| B[3] | 実装面が必要 | **refuted** | §1 (P3) のとおり実走で反証 |
| B[4] | hydrate だけでは準備完了でない | **real・採用** | gflags `/work/SFC/tanab/github/gflags`、glog 同 `glog` は実在・clean、CCBench pin `511c9538` clean を投入直前に再確認する |
| B[5] | 停止経路一覧 | **real・参考採用** | 投入前に踏めるものは §3 のチェックリストへ畳む。踏めない (計算ノード側) ものは失敗時の読み方として使う |
| B[6] | CCBench worktree の競合 | **推定・不採用 (scope 外)** | wave の submodule common dir は主 checkout と別であることを子が確認済み。同 wave の submodule を走行中に触らないことで足りる |
| B[7] | 単一 file の存在で成功と読むと誤る | **real・採用** | §4 の証拠集合を「accepted を取得した」と書くための最小条件とする |
| B[8] | compute 待ちは使えるが rc=0 は終端判定であって成功判定でない | **real・採用** | `tools/dev_wave_wait.py compute` を 1 本だけ張る。`--done-file` は不在の request 固有 path、`--accounting-file` は今回の nonce の scheduler stderr。周期 qstat を足さない |
| B[9] | silo 1 本の scope を覆す根拠なし | **real・採用** | scope 据え置き。mocc/rr5・tictoc/rr5 は T-2224 の残件として持ち越す |

## 3. プラン v2 (投入前チェックリスト)

1. `PEGASUS_EFFECTIVE_CLOCK_TOLERANCE_PCT` が未定義であること。
2. wave worktree が `output/` を除いて clean であること (untracked を含む)。
3. staging root と masstree / mimalloc / googletest が実ディレクトリであること (hydrate 済み)。
4. gflags / glog / CCBench の pin と clean を再確認。
5. queue が `DIS` / `INA` でないことを `qstat -Q` の本文で確認。
6. 投入は wave root を明示した既定 launcher 1 回だけ:
   `bash <wave>/tools/pegasus/submit_certify.sh --repo-root <wave> --protocol silo --rratio 5`
   `--attempts-root` と `--job-script` は変えない。
7. 投入後に request 可視性を 1 度だけ確認し、nonce / request / receipt を照合する。
   launcher が失敗しても、投入済みでないと確かめるまで再投入しない。
8. 待ち手は compute 1 本。約 240 秒は進捗の目安であって打ち切り期限ではない。
9. 終端後に §4 の証拠を照合し、生成物を収録してから受入・land へ進む。

## 4. 「accepted を取得した」と書くための最小証拠 (B[7] を採用)

- 今回の submit receipt と acquisition receipt、その request / source / script / binary の束縛。
- registered の実 bytes と SHA-256、attempt の `calibration.json` との一致、対象が
  silo / rr5 / t48 / pegasus、`quality.status = accepted`、`cache_floor_warning = false`。
- 今回の `publish.json` と `published-self-comparison.json` が成功していること。
- `job-result.json` の `calibrate_rc = 0` と、request 固有の終端会計。
- `failure.json` / `rejection.json` / post-probe / cleanup 証拠の確認。矛盾があれば
  「accepted な公開物はあるが wrapper は失敗」と分離して書く。

## 5. 却下が再発した場合

規律 2 により、通すための変更を一切しない。選択規則・`cache_floor` (0.50%)・`l3_multiple` (4.0)・
飽和閾値・結果 schema・早期停止条件を触らない。全点の miss / RSS / L3・選択フラグ・警告・CV を
記録し、`docs/phase3.md` は「未取得」のまま、裁定パッケージとしてユーザーへ返す。
自動で投げ直さない。

## 6. 変異事前登録 (DW-M01 / DW-S04)

**実装面 (D95 決定 2) の差分がゼロなので変異 matrix を免除する。** 免除は段 7 の最終差分で
実装面ゼロを再確認したうえで確定する。実装面が 1 ハンクでも生じたら免除は取り消し、
Codex `role=author` の実装子と変異 matrix へ戻る。**受入全走は免除しない。**

## 7. 段 5・6 の扱い

実装面がないので段 5 の実装子と段 6 の review 子は立てない (`DW-C00` 軽量版)。
測定・記録・受入・land は親が担う。
