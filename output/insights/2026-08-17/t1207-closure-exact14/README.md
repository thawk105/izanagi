# [T-1207] enforcement source closure を exact 14 へ広げる — 一次資料

wave: `dev-wave-t1207-closure-exact14` / base `5a19b8ab` / 2026-08-17 (JST)

ユーザー裁定 (2026-08-16 /rulings 全件 第 3 回、[T-1207] の択 (c) =
「`__init__.py` と `report.py` を加えた 14 とする」) の実装。D442 決定 1 の exact 12 を supersede する。

## 親が段 1 前に実測した前提 (実編集 → 測定 → `git checkout --` 復元、復元後 clean 確認)

| ID | 測ったこと | 実測値 |
|---|---|---|
| M1 | 実 corpus の campaign lock | `output/**` の physical lock **32 本**、v2 は **0 本** |
| M2 | `__init__.py:16` を 1 行差し替え (`from .core import verify_trace_dir` → `from .parse import parse_trace_dir as verify_trace_dir`) | exact 12 の閉包検査は **緑のまま** (capture 12 path / live verify 例外なし)、`pipeline.verify_trace_dir is core.verify_trace_dir` が **False** |
| M3 | `report.py:46` を 1 行差し替え (`"certified": res.certified,` → `"certified": True,`) | 閉包検査は **緑のまま**、`VerifyResult(...).certified=False` に対し `result_to_dict(...)["certified"]` が **True** |

M1 の一般化範囲は **この checkout の physical `output/**/campaign.lock`** に限る。外部保存、
別 worktree、別 branch、削除済み artifact、測定後に作られた v2 は測っていない。

## 親が撤回した主張 (段 3 レンズ A の A-05 を採用)

段 1 brief §7 の「1 行差し替えで certified 選択の受理集合が epoch 診断に現れずに変わる」は
**実測から導けないため撤回した。**

- M2 が差し替えた `parse_trace_dir` は `expected_commits` keyword を受けないので
  `pipeline.py:1106` の呼出しは例外になり abort へ落ちる。**gate の無効化 (anomaly のある run が
  certified になる) は実証していない。**
- 棄却判定 `vr.certified` (`pipeline.py:1133`) は `core.py` 由来で**閉包内**にある。
  `report.py` の脅威は判定の反転ではなく **rejection payload の偽装**である。

実証できたのは (1) exact 12 の閉包検査が両 file の変更を見ないこと、
(2) dispatch の解決先と rejection payload がその 2 file から制御できること、までである。

## テスト実測

| 走 | 対象 | 結果 |
|---|---|---|
| 焦点走 (login, bounded local) | `test_t671_source_binding.py` | **rc=16 / テスト 0 件**を 4 回連続 (cgroup の `memory.max` / `memory.oom.group` を走行中に attest 不能)。以後すべて計算ノードで実測した |
| 焦点走 1 (計算ノード, 統合 commit 前) | T671 + codec | **116 passed / 0 failed** (2.78s) |
| 焦点走 2 (計算ノード, 統合 commit 前) | T671 単体 | **63 passed** (2.70s) |
| 基準走 (計算ノード, base `5a19b8ab` の再現木) | T671 単体 | **51 passed** (2.65s) |
| F357 切り分け (統合 commit **前**) | `test_layer3_report.py` | **1 failed** = `test_accepted_report_requires_e1_and_records_epoch` ただ 1 件 |
| F357 切り分け (統合 commit **後**) | 影響 8 file | **465 passed / 0 failed** |

**費用の実測 (test-time-regression-rule):** 同一経路 (計算ノード) で
**51 node 2.65s → 63 node 2.70s = 1.02 倍**。閾値 1.1 倍を下回る。

**費用クラスの訂正:** 実装子は完了報告で「新規検査は O(1)」と申告したが、段 6 レビュー B が
誤りと判定した。正しくは対照 2 node と clean node が閉包サイズ N に対し **O(N)**、census が O(1)、
既存の path 単位 parameterized 系列が **O(N^2)** である。N は repo の成長ではなく裁定でしか
動かない設計量 (8→12→14) であり、**O(履歴) の処理は 1 件も無い**。

**F357 の切り分けが実測で成立した。** 段 6 レビュー B は静的解析だけで偽赤 node を
`test_layer3_report.py::test_accepted_report_requires_e1_and_records_epoch` **1 件**と予測し、
commit 前の実走がその 1 件ちょうどを返し、commit 後に消えた。
実装子が挙げた広い候補集合 (artifact / bench / env / layer3 / S6 / S8a) は**過大**だった。
理由は artifact / S6 / S8a の E1 node が `_REPO_ROOT` を一時 repo へ差し替えているためである。

## 変異 matrix

runner 範囲 = `test_t671_source_binding.py`, `test_artifact_admission.py`,
`test_campaign_lock_codec.py`。runner = `tools/run_tests.py --force-dispatch -rf`。
harness = `tools/mutation_worktree.py` (固定 commit `03b7fa5a` の使い捨て worktree)。

### 走 1 = probe (全件 SURVIVED 期待で観測 node を集める)

baseline PASSED。**SURVIVED 0 / TIMEOUT 0 / PARSE_ERROR 0**、MISMATCH 9 (期待 node 未登録)。
ledger = `mutation-ledger-probe.json`。

### 走 2 = 権威走

baseline PASSED。**KILLED 9 / MISMATCH 0 / SURVIVED 0 / TIMEOUT 0 / PARSE_ERROR 0。
9 変異すべてで登録した期待 node が過不足なく落ちた。**
spec = `mutation-spec-final.json`、ledger = `mutation-ledger-final.json`。

| ID | 変異 | 分類 | 失敗 node 数 |
|---|---|---|---:|
| M1 | closure から `orchestrator/verifier/__init__.py` を削除 | negative | 52 |
| M2 | 同 `orchestrator/verifier/report.py` | negative | 52 |
| M3 | **両方を削除 (= wave 前の実コードの形 exact 12 へ戻す)** | negative | 56 |
| M4 | live verify の disk 読取を `disk = blob` にする (`if disk != blob` は残るが発火不能) | negative | 16 |
| M5 | capture 側を同様に発火不能にする | negative | 8 |
| M6 | v2 の exact key 検査を部分集合許容へ緩める | negative | 16 |
| M7 | epoch preimage の tuple を `[:-1]` にして最後の digest を落とす | negative | 4 |
| M8 | identity scope 文字列を旧 exact 12 文言へ戻す | **diagnostic sensitivity pin** | 1 |
| M9 | 記録 digest と commit blob の比較を反転させる (過剰拒否) | positive | 18 |

### path 単位の判別が成立している (本 wave の純増検出力の直接証拠)

`__init__.py` だけを閉包から外したとき (M1) と `report.py` だけを外したとき (M2) の
失敗 node 集合を比べると、**共通核 49 node に対し、それぞれ排他な 3 node がある。**

M1 だけが落とす 3 node:

```
test_artifact_admission.py::test_certified_acceptance_rejects_each_verifier_drift_fail_closed[__init__.py]
test_t671_source_binding.py::test_pre_wave_exact_twelve_misses_but_exact_fourteen_rejects_new_enforcement_face[verifier-init-dispatch]
test_t671_source_binding.py::test_shared_v2_fixture_default_uses_recorded_blobs_when_disk_is_dirty[__init__.py]
```

M2 だけが落とす 3 node は同じ形の `report.py` / `verifier-report-payload` 版である。

**したがって新設した対照 node は、対応する path が閉包に入っているときにだけ発火する。**
「広げたと謳うだけで発火しない assert」ではない。M3 (両方を外す = wave 前の形) では
M1 ∪ M2 に 1 node を足した 56 node が落ちる。

### M8 を kill に数えない理由

`DW-M03` / `DW-M08` に従う。scope 文字列を旧文言へ戻しても受理集合も fail-closed 挙動も変わらず、
落ちるのは診断文言を逐語照合する 1 node だけである。**diagnostic sensitivity pin** として
別枠に記録し、kill 数 (9) には含めるが「受理集合を守った kill」とは名乗らない。

### 閉包 member を変異させた M7 に F358 の共通核は出なかった

`artifact_admission.py` は閉包 member なので `contract-loader-drift` の共通核 (F358) を懸念したが、
実測では 4 node しか落ちなかった。`test_artifact_admission.py` の E1 node が `_REPO_ROOT` を
一時 repo へ差し替えるため、変異した実 checkout の disk/blob 比較に到達しないからである。
[T-819] が求める「runner を drift 非感受 node へ絞る」作法は、本 runner 範囲では
**既に成立していた**。

## レビューの帰結

| 段 | 子 | 判定 |
|---|---|---|
| 2 | plan | 親の brief にない編集面を 3 件発見 (独立 E1 fixture、verifier drift param、Silo ladder の別 pin) |
| 3 | consult sol (レンズ A = 正しさ境界) | must-fix 6 / should-fix 3。**却下ゼロ** |
| 3 | consult luna (レンズ B = 整合・受理集合) | should-fix 4 / nit 1 + scope 外 3。**却下ゼロ** |
| 6 | review A (恒真性と実効性) | **コード側 must-fix ゼロ**、恒真 node ゼロ、冗長 assert 6 個 (nit) |
| 6 | review B (波及・取り残し・受理集合) | **must-fix ゼロ**、should-fix 3 (費用分類の訂正・F357 集合の過大・段 7 文書 carry) |

段 3 の 2 レンズは独立に「固定 exact list は将来 module を束縛しない」へ収束した (A-02)。
親はこれを test-only の package census として採用した。

## scope 外として裁定パッケージへ返した所見

| id | 内容 | 返す先 |
|---|---|---|
| A-03 | certified sink の支配点が無い (WAL 直書き、`pipeline.evaluate` の COMMIT が verifier receipt を要求しない) | 新規タスク |
| A-04 | 弱化してから作る fresh lock は exact 14 でも拒否しない (検出するのは lock 記録後の drift だけ) | 新規タスク (A-02 後半と同じ束) |
| A-08 | detached な旧 E1 が judge で受理される (oracle validator は scope を非空文字列としか検査しない) | [T-1208] |
| X-1209 | T126 qualification の code identity が追随しない | [T-1209] |
| X-DOMAIN | 同じ `/v1` domain が 12-path grammar と 14-path grammar を指す曖昧さ | [T-1208] と同じ束 |

## 名乗ってよい範囲 (これを超えて書いてはならない)

`require_environment_contract=True` で `ident.ensure_campaign_identity` の source 検査が
実際に完了した呼出しについて、**各 path を検査が読み取ったそれぞれの時点の** enforcement
source closure exact 14 path の disk bytes は、その呼出しが authority に採用した
`contract_loader_commit` の同 path Git blob と一致した。
exact 12 から増えた保証は、後続の source 検査が `orchestrator/verifier/__init__.py` と
`orchestrator/verifier/report.py` の**記録後 drift** も拒否することに限る。

実行済み code object、import state / cache、fixed-list 外 module、CLI / wrapper、
bootstrap と runtime、全 certified sink の支配、弱化してから作る fresh lock、
cross-version の E1 認証は保証しない。

## verbatim

`verbatim/` に段 2 プラン、段 3 の 2 レンズ、段 4 裁定、段 5 実装報告、段 6 の 2 レビューを
そのまま置く。
