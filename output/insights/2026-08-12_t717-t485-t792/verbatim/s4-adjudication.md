# 段 4 裁定 — dev-wave [T-717]/[T-485]/[T-792]

軽量版のため段 2・3 は省いた (DW-C00: 設計択一はユーザー裁定で確定済みで割れない、
正しさ防壁に触れない、受理集合を変えない — 3 条件とも不成立)。
段 6 の敵対レビュー 2 本も同条件で省く。実装面 2 件があるため段 5 の Codex `role=author` は必須。
実測 (段 1 前提・変異 matrix・受入全走) は省かない。

## 親 provisional の裁定

- **(P1) 採用**: T-485 は `docs/decisions.md` の新 D (spool fragment) を正本とし、
  `docs/phase3-8c-wiring-design.md` へ resolver 契約の小節を 1 つ足す。
  理由 = 同文書 §4.1 条件 1 が「raw digest が ledger の値と一致する」を要求しながら、
  bytes をどう取得するかの契約が本文に無い。取得方式を書かないと条件 1 は検査不能。
- **(P2) 採用**: T-717 に「60 分」を pin するテストは足さない。
  理由 = 裁定の再訪条件が「R-c が効いたら戻す」であり、値の pin は将来の戻しを機械的に阻害する。
  既存の下限 pin (`test_default_walltime_preserves_acceptance_runtime_margin`) は
  受入実測 1809 秒 × 1.25 = 2261.25 秒を要求する不等式であり、40 分 (2400s) でも
  60 分 (3600s) でも成立する。よって本変更で期待値の書換えは発生しない。

## 実装契約 (段 5 の実装子へ)

1. `tools/pegasus/dispatch_compute.py:28` の `DEFAULT_WALLTIME = "00:40:00"` を `"01:00:00"` へ。
   他の行 (`:1293` `:1832` `:1926` の既定値参照) は定数参照のまま変えない。
2. `orchestrator/tests/test_real_repo_serialization.py` の 4 行
   (`:826` `:827` `:909` `:910`) の `from tests import X` を `from orchestrator.tests import X` へ。
   `sys.path` 操作 (`:30` `:31`) は変えない。conftest への path 追加 ((a) 案) は裁定で不採用。
3. 既存テストの期待値を 1 つも変えない。skip / xfail / 削除を行わない。
4. docs を編集しない。commit しない。

## 変異事前登録 (DW-M01)

**単一理由性の事前確認 (コードで確認済み):**

- M1 の対象 (`DEFAULT_WALLTIME` の値) を拒否する層は下限 pin ただ 1 つ。
  `_walltime_seconds` は形式検査 (HH:MM:SS・正) だけで下限を持たないので、
  `"00:20:00"` は形式検査を通り下限 pin だけが落ちる。前後に重複層は無い。
- M2 の対象 (qsub argv への定数伝播) を拒否する層は `:255` の argv 完全一致 assert ただ 1 つ。
  `--walltime` override 経路 (`test_walltime_override_is_bound_to_pbs_and_total_bound`) は
  literal `"01:02:03"` を渡すので既定値の hardcode では落ちない。
- M3 の対象 (import の解決経路) を拒否する層は import 文それ自体。runner 範囲に
  `test_reflux_ir.py` を含めないことが単一理由性の条件であり、runner argv で固定する。

**runner 範囲 (期待 node と対、memory 実測の罠):**

`orchestrator/tests/test_pegasus_dispatch_compute.py orchestrator/tests/test_real_repo_serialization.py`
の 2 ファイルのみ。`test_reflux_ir.py` を含めると M3 が `sys.path` 副作用で SURVIVED になる。

| id | 対象 | 期待 | 単一理由 |
|---|---|---|---|
| M1 | `DEFAULT_WALLTIME` を `"00:20:00"` (下限 2261.25 秒未満) へ | KILLED | 下限 pin |
| M2 | qsub argv の `elapstim_req={walltime}` を旧 literal `elapstim_req=00:40:00` へ | KILLED | argv 一致 assert |
| M3 | 修正した 4 import を `from tests import` へ戻す | KILLED | 焦点範囲で module 解決不能 |

`expected_nodes` は **fix 後の最終 commit で probe 走から完全集合を再導出**してから本走する
(DW-M07 / DW-M08、memory「期待 node は fix 後に完全集合を再導出」)。

**T-717 の値 (60 分) 自体に対応する変異は登録しない。** (P2) の裁定どおり値の gate を作らないため、
登録できる実効 gate が存在しない (DW-M01「確認できなければ登録せず実効 gate へ再照準」)。
この不在は本 wave の意図であり、検出力の欠落として worklog に明記する。

## 受入

実 repo を読むテスト (`test_real_repo_serialization.py`) を触るため、受入全走は免除しない
(DW-S04)。段 7 の記録 commit 込みの最終 tip で 1 回走らせる。

---

## 段 4 追補 (段 5 の停止報告を受けた実装契約の訂正)

**発端:** 実装子 (`s5b-author.md`) は実装せず停止し、新事実を報告した。親が逐語で裏取りした。

**新事実 (real、親が実測):**

- `orchestrator/tests/test_s8b_protocol_builder.py:37` = `from tests import repo_tree_util`、
  `:38` = `from tests.skiputil import Skip, skip`。
- node 1 (`test_protocol_builder_repo_tree_guard_is_wired_to_real_root`) は
  `mock.patch.object(repo_tree_util, "assert_repo_tree_unchanged", ...)` で
  **自分が import した module object の属性**を差し替え、SUT はその module 属性を呼ぶ。
  node 側だけを `orchestrator.tests` へ移すと、node が patch するのは
  `orchestrator.tests.repo_tree_util`、SUT が呼ぶのは `tests.repo_tree_util` となり
  **別 object**になる → `helper_calls` が増えず `:878` の `len(helper_calls) == 1` が落ちる。
- さらに焦点範囲では `tests` 自体が解決できないため、SUT の import 中に `:37` で
  同じ `ModuleNotFoundError` が再発する。**node 側 4 行だけでは焦点走の赤は消えない。**

**裁定:** 選択肢は (b) のまま変えない (非同値な択一へ戻さない)。**親の実装契約が狭すぎた**ので
編集面を 6 行へ広げる。これは裁定 (b) の「正規 import へ直す」を transitive 辺まで適用した
完成形であり、(a) conftest 案への転換ではない。

**訂正後の編集面 (2 ファイル 6 行):**

1. `orchestrator/tests/test_real_repo_serialization.py` の 4 行 (`:826` `:827` `:909` `:910`)
2. `orchestrator/tests/test_s8b_protocol_builder.py` の 2 行 (`:37` `:38`)

**波及の実測 (広げてよい根拠):**

- `from tests import` / `from tests.` の全出現は **3 ファイル 7 行のみ** (grep 実測)。
  うち 6 行が上記編集面、残り 1 行は `test_s8b_approved.py:31` (`from tests.skiputil`)。
- `repo_tree_util` を `orchestrator.tests` 経由で import する先例は既に 2 ファイル
  (`test_ruleops.py:24`、`test_campaign_import_invariant.py:27`)。
  すなわち二重 module object は**本変更以前から存在**しており、本変更はそれを減らす方向。
- `tests.repo_tree_util` を patch している箇所は node 1 のみ (grep 実測)。他 consumer は無い。
- node 2 は `inspect.getsource` の文字列検査だけで module identity に依存しない
  (assert 逐語で確認)。`test_s8b_binding_driftguards.py` に `from tests` は無く、
  `import test_s8b_oracle_driver` は `HERE` 経由の top-level import なので焦点走でも解決する。
  → **node 2 側の transitive 修正は不要。**
- 稼働 wave との衝突なし: `test_s8b_protocol_builder.py` を触る branch は無い
  (t827 は `test_s8b_oracle_driver.py`、floor は `test_s8b_floor_campaign.py`)。

**scope 外として返す real 所見:** `test_s8b_approved.py:31` の `from tests.skiputil` も
同じ side effect に依存しており、同ファイル単独の焦点走では同型の偽赤を生む。
本裁定の対象 node ではないため実装せず、段 7 の裁定パッケージでユーザーへ返す。

**変異 M3 の訂正:** 期待 KILLED の変異は「訂正後の 6 行を `from tests` 系へ戻す」累積置換とする。
