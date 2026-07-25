# [T-088] 段階 1 — floor 専用 PBS wrapper (wrapper-only wave) 材料レポート — 2026-07-25

**射程**: D86(2) が定めた順序「wrapper-only wave 先行 → 実 artifact 確認 → admission 再裁定」の
**第 1 段だけ**を実装する。`_assert_official_permitted` と CLI 固定拒否は 1 byte も変更していない。
したがって official の受理集合は**空集合のまま**である。

**成果**: `tools/pegasus/submit_floor.sh` (新規)、`tools/pegasus/floor_campaign.sh` (新規)、
`tools/pegasus/policy.json` (2 key 追加)、`orchestrator/tests/test_pegasus_floor_tools.py` (新規)。
commit = `b2b6e5c` (実装) + `82c9055` (再レビュー must-fix の解消)。

**本 wave は段階 1 の完了を主張しない。** dry-run が作る synthetic ID は DW-G04 の発火条件ではない。
実 submit artifact ID の確認は**人間の明示 `qsub`** を待つ (§6)。

---

## 1. 親が独立に実測した設計入力 (プランより前・両レンズより前)

いずれも一次資料からの実測であり、既存 docs からの転写ではない。

| # | 実測 | 結果 | 使い道 |
|---|---|---|---|
| 1 | 実 protocol + 実 freeze から driver の `_floor_reservation_budget` を実行 | 12 cells / schedule 96 行 / `required_s=28200` + `finalize_reserve=600` = **28800 秒** | walltime の下限。28800 ちょうどでは開始直後の preflight が境界で落ちる |
| 2 | gen_S の queue 詳細 (smoke 実測 `qstat_queue_detail.stdout`) | `(Per-Req) Elapse Time Limit = Max: 86400S` | 10 時間要求が queue 制約内であることの根拠 |
| 3 | `buildcache._v2_commands` の configure argv | `-DCMAKE_PREFIX_PATH` を**渡していない** | 依存の受け渡し seam が環境変数しかないことの根拠 |
| 4 | CCBench の CMakeLists | `find_package(gflags REQUIRED)` / `find_package(glog REQUIRED)` | 依存が必須であることの根拠 |
| 5 | 最小 project による CMake の挙動確認 | env `CMAKE_PREFIX_PATH` **無し**では `find_package` 失敗、**有り**では `Configuring done` | job script が env で依存を渡せることの実証 |
| 6 | `python3 -E -s -B` / `-I -B` の stdin script | 前者は `sys.path[0] == ''` (cwd が import path)・`isolated=0`、後者は `isolated=1` | interpreter 硬化の実効化 (§4) |
| 7 | driver を `-E -s -B` および `-I -B` で起動 | いずれも official 拒否 (rc=2) を正常に返す | 硬化しても driver が壊れないことの確認 |
| 8 | `--mode official` の現行挙動 | `{"status":"refused"}` rc=2 | guard 生存の確認 (裁定前提) |

**(3)〜(5) は両敵対レンズとも検出しなかった**。これが無ければ、解禁後の初回実走が build 失敗で
10 時間の allocation を捨てていた。

## 2. 検証プロセスと否定された親の裁定

親 brief (P1..P8 を攻撃対象として明記) → codex プラン起草 (max, read-only) → 敵対相談 2 本 並列
(max。レンズ A = 正しさ境界・防壁 / レンズ B = 実在性・scope・運用実効性) → 親裁定 (プラン v2) →
実装 2 単位 (逐次) → 敵対レビュー 2 本 並列 (max) → fix 2 単位 → 統合 commit → 変異 → 焦点再レビュー
(max) → fix round 2 → 変異本走 → 受入全走。

**相談・レビュー・再レビューの 5 本すべてが NO-GO を返した。** 親の provisional 裁定 8 件のうち
**4 件が否定された**。

| | 判定 | 帰結 |
|---|---|---|
| (P1) scope = wrapper + job script + tests + README | 支持 | 維持 |
| (P2) dry-run までで本 wave 完了 | **否定** | 段階 1 は人間 qsub まで OPEN。DW-G04 の発火条件を満たしたと記録しない |
| (P3) submission artifact の schema 分離 | 条件付き支持 | 分離は維持。authorization と**呼ばない**、containment を追加 |
| (P4) driver rc の忠実記録 | 条件付き支持 | rc 伝播は維持。「必ず忠実」の無条件主張は撤回 |
| (P5) `floor_walltime_s = 29400` | **否定** | **36000 (10:00:00)** へ改訂。scheduler 実 limit と照合する |
| (P6) claims の 0700 provisioning | 条件付き支持 | 維持。ただし mode を authorization gate と呼ばない |
| (P7) 実装子 2 本を並列 | **否定** | **逐次 B → A** (A のテストが B の成果物を読むため) |
| (P8) `REQUESTED_S` は policy 由来 | **否定** | **qstat の scheduler 実 elapse limit 由来**へ改訂 |

## 3. walltime の確定 (P5 の改訂)

```text
driver required_s        = 12 * (900 + (8+2) * (5*5 + 120)) = 28200
driver finalize reserve  =   600
driver が要求する capacity = 28800
job prologue (依存 build・qstat・git・hash) 見積          ≈   900
driver 定数が hard cap でないことへの余裕 (§5 の限界 2)   ≈  6300
PBS request              = 36000 (= 10:00:00、gen_S 上限 86400 の範囲内)
```

レンズ A が導出した中間再検査式 `reservation-lost iff E > REQUESTED_S - 600 - 145*(P+U)` に
初回測定前 (P+U=120) を代入すると、許容経過は 29400 案の 600 秒に対し **36000 案では 18000 秒**。
build cap 合計 10800 秒に対して 7200 秒の余裕がある。

## 4. 実装した防壁 (すべて「gate」ではなく事実の束縛として記録する)

| 項目 | 実装 | 由来 |
|---|---|---|
| 実行 bytes の束縛 | job が `sha256sum "$0"` で**実行中の bytes** を hash し receipt と照合 | A-02 |
| commit blob の束縛 | submit・job とも `git cat-file blob <commit>:<path>` の hash と照合 (working-tree hash とは別 assert) | R1-02 |
| scheduler 実 limit の束縛 | qstat の `(Per-Req) Elapse Time Limit` を parse し policy と照合。`REQUESTED_S` は scheduler 値 | A-07 |
| replay 遮断 | receipt の `job_id` と実 `$PBS_JOBID` の normalized 一致 | A-10 |
| interpreter 硬化 | 全 python 呼び出しを `-I -B` (isolated)。`PYTHONPATH`/`PYTHONHOME`/`PYTHONSTARTUP` を unset | A-03 → R3-01 |
| containment | staging・claims の全 path component の symlink 検査 + realpath が `output/` 配下、かつ**凍結・campaign namespace を除外** | A-09 → R1-05 |
| rc の忠実性 | driver rc と起動前失敗 (`floor_driver_setup`) を分離。record writer の失敗が rc を上書きしない | A-11 → R1-07 |
| git failure の非 clean 化 | submit・job とも `git status` / `git ls-files` の rc を検査 | R1-08 → R3-06 |
| 依存 provisioning | gflags/glog を pin + clean 検査つきで build/install し `CMAKE_PREFIX_PATH` を export | 親独自 (§1-3〜5) |

## 5. 正直な限界 (すべて記録として残し、gate と呼ばない)

1. **submission record は human authorization ではない。** 人間が実行しても AI が実行しても
   生成物は byte-level で区別できない。D86(3) は「人間の明示 qsub を authorization とする」と
   書くが、実体は submission の**記録**である。→ ユーザー裁定へ (§7-1)。
2. **driver の予算定数は hard cap ではない。** `buildcache` は configure と build に**各々** 900 秒を
   適用し (`buildcache.py:500-501`)、測定は rep ごと 120 秒 × 5 rep。envelope の 900/セル・
   145/attempt は見積である。→ 独立 prerequisite へ (§7-2)。
3. **PATH 由来の外部ツール (`qsub`/`qstat`/`python3`) の実体は検証していない。** fake tool は
   本 wave の防壁を通る。これらは authorization gate ではないため、新しい gate を作っていない。
4. **path 検査は一般 TOCTOU を閉じない。** pathname 検査後に `mkdir` / `open` する構造は残る。
5. **承認済み revision への束縛はしていない。** 非 dry-run の override 拒否と commit blob 照合まで。
   実行 revision 束縛は既裁定の別 gate。
6. **実 PBS 上では 1 度も走らせていない。** AI は `qsub` しない (D86(3))。検証は一時 repo の
   dry-run / 非 dry-run stub 経路、実 qstat 出力 fixture、stub driver の rc 伝播まで。
7. **現時点で実 job を投げても driver は rc=2 で拒否される。** 確認できるのは wrapper の配線
   (qsub 応答・PBS identity・qstat parse・reservation export・rc 伝播) までであり、
   protocol load・claim 取得・build・measurement は発火しない。

## 6. 段階 1 を閉じるために人間が行う手番

```bash
cd /home/SFC/tanab/github/izanagi
git status --short                      # clean であること
qstat -Q; qstat -Q -f gen_S; pegasusinfo; rbudgetcheck; check_quota
tools/pegasus/submit_floor.sh --dry-run # 副作用: submission staging と output/claims を作る
# receipt を確認したうえで、明示的に:
tools/pegasus/submit_floor.sh
qstat -f '<表示された request ID>'
```

期待される結果は **driver rc=2 の job** である (official guard が生存しているため)。
`job-result.json` の `driver_rc=2` と `failure.json` の `stage="floor_driver"` が記録されれば、
wrapper 配線は実機で確認できたことになる。この時点で DW-G04 の発火条件が満たされ、段階 3
(単一 admission predicate) の入口条件が揃う。

## 7. ユーザー裁定へ返す項目 (実装しない)

1. **D86(3) の文言 vs 実体**: submission record は authorization ではない (§5-1)。
   D86(3) の再確認、または文言の修正が要る。
2. **driver 予算定数の hard cap 化** (§5-2): 独立 prerequisite wave で driver 側を直すか、
   walltime を厚く取り続けるかの択一。
3. **実行 revision 束縛と spool bytes の独立照合** (§5-5): 段階 3 の入力として設計が要る。

## 8. 検査結果 (実測値)

- 受入全走 (`tools/run_tests.py`) = **2968 passed / 18 skipped / 赤 0** (255.70s)。
  途中経過として、fix round 1 直後の全走で `test_dev_waves_worker.py::
  test_stdout_stderr_have_one_combined_cap` が 1 件赤になったが、単独実行 4/4 緑・同一 commit の
  再走で再現せず、並列負荷下の timing flaky と判定した (本 wave の差分は `tools/pegasus/` と
  新規テストのみで、当該テストの依存に触れていない)。
- 焦点テスト = `test_pegasus_floor_tools.py` (49) + `test_pegasus_tools.py` (52) +
  `test_plain_runner_coverage.py` (3) = **104 passed**。
- 変異本走 (最終 commit `82c9055`) = **12/12 KILLED**。台帳 =
  `2026-07-25_t088-floor-wrapper-mutation-ledger.json` (初回・再照準ラウンドを erratum として同梱)。
- `check_ai_provenance` = **340 件・違反なし**。
- 三軸語 conjunction の機械検査 = 子出力 11 本すべて **0 hit** (逐語凍結前に実施)。

### 変異の erratum (DW-M02/M04)

初回ラウンド (統合 commit `b2b6e5c`) では M6 が `ANCHOR-NOT-UNIQUE` (fix で anchor が移動)、
M9 が `RED-ELSEWHERE` (期待 nodeid が rename で stale)、**M8 が SURVIVED** だった。
M8 は `provision_claim_root` の第 1 検査だけを潰しても**第 2 検査が同じ述語を再評価して拒否する**
mask であり、両層同時変異では KILLED になった。焦点再レビューの指摘どおり、これは
「単層変異一般が等価」ではなく「call-site 変異が等価」であり、共通述語 1 箇所を撃つ最小一階変異
(N1) は最終 commit で **KILLED** である。初回結果は消さず台帳に erratum として残した。
