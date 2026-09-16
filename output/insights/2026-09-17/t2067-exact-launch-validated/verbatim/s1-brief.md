# 段 1 brief — [T-2067] `_gate_check_core` の二読 fallback 廃止 (exact `LaunchValidatedFreeze` 必須)

作成: 2026-09-17 00:35 JST、base = local main `1042a1bc95057fa03117d504cfa2b0fafaae60d0`

## 研究前進 (土台)

certified 選択の proof chain を守る oracle gate (`gate_check`、D65 決定 (5) 「public gate_check は v2 で必ず自己検証」) が、
v2 freeze に対して「launch validation 必須」と「active 世代 sha256 一致だけ」の 2 通りの意味を持つ穴を閉じる (D1872、規律 2)。
止めている研究の実測: なし (到達は「初回 read 失敗 → 直後の再 read 成功」の外部要因の race のみ、D1831 決定 2)。
最小差分 = core の v2 分岐で exact `LaunchValidatedFreeze` を必須化し self-load (`load_ratified_freeze`) を撤去する。
完了判定 = fallback を復活させる変異が新規 test で KILLED、既存 test と受入全走が緑。

## scope

- production: `orchestrator/campaign/s8b_oracle_driver.py` の `_gate_check_core` (v2 else 分岐 :487〜505、docstring :416〜435)
  と、その呼び手 `gate_check` (:594〜685) の引数整合。CLI `main` の `gate-check` (:2044) は `gate_check` を経由し変更不要。
- test: **新規 file** (名前は plan で確定、候補 `orchestrator/tests/test_s8b_gate_core_exact_launch_validated.py`)。
  `orchestrator/tests/test_s8b_oracle_driver.py` は触らない (t080 系 branch `impl-dev-wave-t080-accept-speed` が 865〜1950 行を
  保持、他 5 worktree でも dirty)。`real_repo_ratified_memo.py` の docstring は `gate_check` の `ratified=` / `ratified_error=`
  に言及するので、public 引数を変えるなら整合が要る (触らないのが既定)。
- scope 外: 仮想リスク向けの gate・検査・台帳・一般化の追加。caller 閉包メタテストの新設 (D1984 で不採用)。
  D1241 / D1313 の advisory / non-certifying 上限の解除。library 経路 (`verify_manifest` / `build_observations`) への選択強制 (D1831 決定 5)。

## 確定済みユーザー裁定

- D1872 (2026-09-09、択 (ii)): v2 fallback を廃し exact `LaunchValidatedFreeze` を必須にする。「現状維持で台帳へ記録」は却下済み。
- 実装面なので D95 の Codex `role=author` + 変異事前登録 (段 4)。
- D1984 (2026-09-14) はメタテストの不採用と件数の出所の記録法だけを決めており、D1872 を撤回していない
  (「未配線 2 群の扱いも変えない」は母集合の記録の扱い)。[T-2067] 持ち越し本文 (entry 1527、09-16) も D1872 を「裁定済み・着地は未確認」と書く。

## 不変条件

- (I1) `_gate_check_core` が v2 freeze (`floor` または `budget` が non-null) を gate predicates (known-axes / floor / budget / manifest)
  へ進めるのは `launch_validated` が exact type `LaunchValidatedFreeze` のときだけ。無ければ構造化 refusal で fail-closed。
  refusal 文字列は既存の `v2-execution: launch-validate:` 接頭辞に揃えるのを既定とし、文言は plan で確定する。
- (I2) `_gate_check_core` は `s8b_ratified_freeze.load_ratified_freeze` を呼ばない (self-load 撤去)。
- (I3) fallback 発火時以外の refusal 集合は不変: v1 freeze 経路、初回 load 失敗 → 再読も失敗 (`holdout-freeze-verify:`)、
  `ratified_error` の翻訳 (`freeze-ratify:`)、正常 v2 経路 (`launch_validate` 厳密 1 回)、run-block 経路 (`_gate_check_validated`)。
  既存 node `test_v2_standalone_gate_check_requires_full_floor_validation`、`test_nonnull_floor_without_active_generation_is_refused`、
  `test_gate_check_core_rejects_reverified_freeze_token`、`test_private_validated_gate_has_only_run_block_as_production_caller`、
  `test_s1_known_axes_freeze.py::test_historical_oracle_nonadapter_reaches_current_semantics` (既定 freeze は v1) は無変更で緑。
- (I4) `gate_check` の public signature に `launch_validated` を足さない (D65 (5))。
- (I5) 規律 2: 受理集合は狭まるだけで、広がる変更を含まない。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1) 廃止の形: core の freeze 再読 (`:458`、`verified` 未指定時) は残し、v2 到達時を refusal 化して閉じる (最小差分)。
  代案は再読も撤去し `gate_check` が loader 例外を core へ渡す形。provisional = 前者 (再読は v1 の `holdout-freeze-verify:` 構造化に
  使われ、D1872 が名指すのは v2 fallback)。
- (P2) core の `ratified` 引数 (dead になる) は削除し、`gate_check` 内の 4 call site (:619, :632, :646, :655) も揃える。
  `gate_check` の public `ratified=` / `ratified_error=` は残す (memo docstring と既存 test が依存)。provisional = 削除。
- (P3) 新規 test の形: 「初回 `_load_verified_freeze` 失敗 → 再読成功」を `mock.patch.object(driver, "_load_verified_freeze", side_effect=[exc, loaded])`
  で作り、`load_ratified_freeze` が呼ばれない (AssertionError side_effect) + refusal exact 一致 + `decision.allowed is False` を固定。
  D1831 が「仮想遷移の新設」と呼んだ形だが、D1872 で実装が裁定された以上、変異 KILL の唯一の観測点として要る。
  freeze fixture は既存 `_build_v2_repo` を新規 file から import して使えるか、合成 v2 document で足りるかを plan で決める
  (実 repo・実 active 世代は読まない)。

## 成果物

driver 差分 + 新規 test (Codex author、1 単位)、変異事前登録 (段 4)、insights `output/insights/2026-09-17/t2067-exact-launch-validated/`
(brief・逐語・変異台帳)、spool fragment (worklog / decisions)、段 9 land。

## 並列分割・環境

- 段 2 plan 1 本、段 3 consult 2 本 (レンズ A = 規律 2 / 受理集合差分の完全性と fail-closed、レンズ B = consumer 取り残し・既存 test・docstring・最小差分)、
  段 5 author 1 本 (編集面が小さく所有分割の利益なし)、段 6 review 2 本。
- 受入全走は `tools/dev_wave_wait.py acceptance --lease-optional` (計算ノード)。変異 matrix は専用 container worktree + 焦点走。

## 新事実 (承認済み裁定を覆すもの)

なし。着手直後に main が T-2630 の land で `20a92f6a6` → `1042a1bc9` に進んだが、編集面 3 file に差分なし (ff 済み)。
DW-O09: driver source の sha256 pin 0 件、path pin は歴史記録のみ → 凍結 bytes 影響なし。DW-O13: 受理形を狭めるので不成立。
