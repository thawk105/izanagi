単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s6-adjudication-2.md

## 必読事項の射影

作業 repository は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix2`
(branch `fix-dev-wave-t1851-c1b-2`、base `2cb24ead5`) である。コードはすべてこの worktree の中で
読み書きする。次を上から順に読む。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s6-adjudication-2.md` — **親の 2 巡目裁定。本作業の契約。** S-1〜S-4 と 3 節の変異再登録。
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s6-rereview.md` — 焦点再レビューの逐語 (失敗シナリオの詳細と file:line)
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s6-adjudication.md` — 1 巡目裁定 (R-1〜R-8。**closed を壊すな**)
4. `<repo>/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md` — 契約の正本 (特に 7 節 crash 後の権威、1.4、2 節)
5. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/refs/decisions-verbatim.md` — D1113 / D1341 / D1522

## 所有 path (これ以外は 1 byte も変更しない)

- `orchestrator/campaign/s8b_terminal_evidence.py`
- `orchestrator/campaign/attempt_registry_core.py`
- `orchestrator/campaign/s8b_attempt_profile.py`
- `orchestrator/campaign/s8b_attempt_registry.py`
- `orchestrator/campaign/s8b_floor_attempt_launcher.py`
- `orchestrator/tests/test_s8b_terminal_evidence.py`
- `orchestrator/tests/test_attempt_registry_core_s8b_profile.py`
- `orchestrator/tests/test_attempt_registry_core_equivalence.py`
- `orchestrator/tests/test_s8b_attempt_registry.py`
- `orchestrator/tests/test_s8b_floor_attempt_launcher.py`

**所有外に必要な変更が見つかったら実装せず完了報告に書け。** docs の編集と commit はしない。

## 依頼 — 焦点再レビューが出した S-1〜S-4 を閉じる

**すべて real と裁定済みである。全件を直せ。**
**1 巡目で closed になった R-1・R-2・R-4・R-5・R-6・R-7・R-8 を壊すな。**

### S-1 (blocker) — external evidence digest を durable replay で再照合できるようにする

現状、`external_evidence_sha256` は `SealedTerminalEvidenceDraft` の **canonical bytes 外の
private 属性**であり (`s8b_terminal_evidence.py:762-769,1170-1181`)、canonical outer keys に
同 field は無い (`同:168-199`)。promotion は canonical bytes だけを写すので validated capability へ
渡らず (`s8b_attempt_registry.py:1197-1210`)、照合は発行時の `record_sealed_attempt_terminal()`
だけにある (`同:3157-3169`)。replay loader は binding と durable identity は見るが external digest を
読まない (`同:1437-1498`)。

**攻撃 (再レビューが具体化済み):** 正当な evidence file の `probe_before_sha256` だけを偽 digest へ
変え、canonical bytes と row の `terminal_evidence_sha256` / `event_sha256` を作り直す。
probe summary、E1 projection、契約 7 の 11 項目、attempt binding、durable slot identity は
変えないので、**replay が受理する。** private issuer は不要。

**直し方 (再レビューの推奨):** pre-output evidence の canonical bytes を **external digest 名の
create-only file** として保存し、**replay 時にそれを読み直して** classification receipt と
probe / failure / launch-failure の各 digest を再導出して照合する。
代案として、永続化済み component digest から再導出可能な composite digest を canonical evidence へ
足す形でもよい。**どちらを採ったかを報告に書け。**
**発行時と replay 時に同一の検査を対で置け。**

### S-2 (must-fix) — canonical 往復の前に exact-type を検査する

rep observations は値を検査する前に `_canonical_copy()` で JSON 復元され
(`s8b_terminal_evidence.py:520-529`)、opened source 全体も canonical 化・復元されてから
(`同:567-576`) `_derive_rep_integrity()` が呼ばれる (`同:918-949`)。
terminal campaign record も値検査より先に canonical 化される (`同:578-602`)。

**その結果、`s8b_floor_stats.py:480-499,514-532` が持つ `rep_index` / `returncode` /
perf counter の exact-int 検査が source object に対して発火しない。** private rep sink へ
`int` subclass や `IntEnum` を入れると、旧経路では `type(v) is int` が偽で rep integrity failure
だったものが、JSON 復元で通常の `int` になり **`rep_integrity_failures == 0` の `observed` が
作れてしまう。v2 の受理集合が意図せず広がっている。**

**直し方:** stateful `Mapping` を再読しない原則は保ったまま、**一度 `dict` 化した直後に、
その exact dict の各 source field を型検査してから canonical 化する。**
rep observations は `_derive_rep_integrity()` が要求する exact scalar 型を **snapshot 前に**検査し、
terminal record も `_campaign_plaintext()` 相当の source-shape 検査を canonical 化前に行う。
**`int` subclass、`str` subclass、`IntEnum` の負例を追加せよ。**

### S-3 (must-fix) — F1 と F3 の変異テストを単一理由へ再照準する

`_RecorderRegistry.record_sealed_attempt_terminal()` は**無条件に例外を送出する**
(`orchestrator/tests/test_s8b_floor_attempt_launcher.py:191-201`)。F1 のテスト (`同:1714-1746`) と
F3 のテスト (`同:1836-1901`) はこの fake を使うため、**対象 gate を外しても後段の fake が必ず
拒否する。冗長 gate による見かけの kill であり、単一理由の kill に数えられない。**

**直し方:** この 2 テストでは **accept-only な fake recorder** (sealed draft を保存して正常
return する) を使い、**現実装では対象 gate で拒否され、mutant では最後まで到達して偽 draft が
観測できる**形にする。F1 は private reservation snapshot を直接 sealer へ渡す**純関数 test** へ
分離してもよい。

### S-4 (must-fix) — F2 を実効 gate へ再照準する

opened snapshot は builder 前に完成し (`s8b_floor_attempt_launcher.py:1080-1087`)、builder 呼出しは
その後 (`同:1116`) なので、**builder へ元 sink を共有しても攻撃は成立しない。**
F2 対応テスト (`orchestrator/tests/test_s8b_floor_attempt_launcher.py:1798-1833`) の最後の
「元 sink が変わっていない」assertion は防御多重化であり、受理可否を変えない。

**直し方:** F2 を **`_snapshot_opened_source()` の削除 / builder 後への遅延 / sealer による
builder-exposed sink の再読**のいずれかへ再照準し、**その mutant で偽 terminal が accept-only
recorder まで到達する**ようにする。元 sink 非共有の構造テストは残してよいが、
**単一理由の security kill には数えない。**

## 変異の再登録 (裁定 3 節。実装後にこれで検査される)

**維持:** F4 (実 slot 3 identity・発行と replay の各 3 負例) / F5 (capture・count の正負対) /
F6 (例外名正規化の helper 直呼び) / F7 (test seam の origin gate)。**これらを壊すな。**

**再照準して登録し直す:** F1' (protocol の builder 後再読) / F2' (opened snapshot の削除・遅延・
再読) / F3' (campaign record の二重読み = SplitRecord)。**いずれも accept-only recorder で
偽 draft が到達することを示せ。**

**新規登録:** **F8** = S-1 の修正で足す replay 側の external evidence 再照合を削除する
(replay 負例だけが赤になること) / **F9** = S-2 の修正で足す canonical 化前の exact-type 検査を
削除する (`int` subclass / `IntEnum` の負例だけが赤になること)。

**各変異について「同じ入力を拒否する層が前後にも内側にも無い」ことを確かめ、確かめられないものは
完了報告にそう書け。**

## 禁止 (違反したら差し戻す)

- **既存テストの期待値を変更しない。反転・緩和・skip・削除を禁じる。赤になったら実装側が誤りである。**
- 親が許可した既存期待値の意味変更 **2 箇所**
  (`test_v2_profile_is_rejected_before_any_registry_side_effect`、
  `test_v2_profile_is_additive_empty_retryable_and_budgeted_by_cell`) **を超えない。**
- **v1 の受理集合を 1 bit も変えない** (event key exact 24、retryable reason 集合 空、
  既定 `retryable_reason_field="failure_reason"`、R-7 の正規化を v1 へ漏らさない)。
- **1 巡目で closed になった R-1・R-2・R-4・R-5・R-6・R-7・R-8 を壊さない。**
- **`expected_use_perf` の導出は launcher の既存 gate 1 本のまま。leaf に perf 述語の新しい
  直接 call を置くな** (契約 9 節)。
- `attempt_registry_core.py` に `aborted=False` の keyword 呼び出しと `OriginSealed(False, ...)` を
  書くな。
- **`IZANAGI_RUN_GROWTH_HELD_TESTS` を設定して growth hold を解除するな。**
- 要求外の gate・検査・台帳・互換層・一般化・防御的な追加コードを足すな。
- 期待値へ揮発 payload を焼き込むな。
- commit しない。docs を編集しない。

## 検査・報告 (DW-S05-C を継承)

- 実走は自走 harness を使う。
  `cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix2 && PYTHONPATH=. python3 orchestrator/tests/<file>.py`
  の形で **所有 5 test file すべて**を走らせろ。**`run_tests` は使うな。**
- **緑には実走 nodeid・範囲を併記する。** 実走不能なら `closed` と申告せず「実装済み・未実走」と書け。
- 変更した production file を参照する consumer test も自分で引いて走らせろ。親は
  `test_trial_registry` `test_p3_autonomous_workload_trial` `test_s8b_holdout_admission`
  `test_s8c_acceptance_receipt_v2` `test_ccbench_spawn_sites` `test_s8b_scheduler_accounting`
  `test_official_perf_closure` が緑であることを実測済みである。**回帰させるな。**
- 機構の正例・負例は実体を名指しし、依存先を stub しない。**テストを甘くして緑にしない。**
- **契約の条項が実体化できないと判断したら、回避策を自作せず止めて報告しろ。**

## 制約

- 出力へ結合文字 U+0300〜U+036F を使わない。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。

## 総括

最後に `## 総括` 節を置き、次を書く。

- **S-1〜S-4 の対応表 (closed / partial / 未実施)。** file:line つきで
- S-1 でどちらの案 (external evidence の create-only file / composite digest) を採ったか
- **R-1〜R-8 の closed 7 件を壊していないことの確認方法と結果**
- 実走した nodeid の範囲と結果 (緑 / 赤 / 未実走)
- F1'・F2'・F3'・F4〜F9 のうち単一理由で殺せると確かめられたものと、確かめられなかったもの
- 所有外への波及
- production / test の差分行数
