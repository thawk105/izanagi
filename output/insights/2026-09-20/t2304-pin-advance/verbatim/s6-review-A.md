## 所見

1. **過剰変更 — refuted / nit（問題不成立）**

   commit の変更は gitlink、定数・説明、テスト 7 literal、docs 2 行。②③⑤⑥⑧、比較 policy、`.gitmodules`、新 gate・helper・台帳への変更はありません。

   根拠: `orchestrator/campaign/pin.py:35`
   ```python
   PREVIOUS_PIN = "028f34d"
   ```
   `PREVIOUS_PIN` も据え置きです。

2. **削除・弱体化 — refuted / nit（問題不成立）**

   群 A の差分は literal の置換だけで、assert の向き・件数・skip 条件は不変です。

   根拠: `orchestrator/tests/test_p3_s4_loop_sort.py:778`
   ```python
   def test_default_cfg_axis_is_sort_marker():
       cfg = S.default_cfg()
       assert cfg.search_config.get("axis") == S.MARKER_ID
       assert cfg.ccbench_commit == S.PIN == "e9e477c"
   ```

3. **分類の誤り — real / must-fix、2 件**

   **3-a. 旧 source fixture とされた 2 テストが実 checkout の HEAD を読んでいる。**

   対象:
   - `orchestrator/tests/test_dynamic_backoff_transitions.py:17,781–790`
   - `orchestrator/tests/test_t2187_adaptive_const_probe.py:47,427–439`

   前者の根拠:
   ```python
   head = subprocess.run(
       ["git", "-C", str(CCBENCH), "rev-parse", "HEAD"],
       check=True,
       capture_output=True,
       text=True,
   ).stdout.strip()
   assert head == PIN_FULL
   ```
   後者にも同じ比較があります。旧 commit の checkout や source の固定化はなく、前者は続いて現在の `CCBENCH/include` をコピーします。「固定旧 source」という分類理由は成立しません。

   **放置時:** 新 pin に同期した正しい checkout が拒否され、受入レポートでは patch／遷移テストが検査本体に入る前に失敗します。

   現行 checkout を検査するなら期待値を追随させる必要があります。旧系列専用の検査を維持する意図なら、旧 source を明示的に用意する修正が必要です。

   **3-b. s8b golden は旧凍結成果物ではなく、現行 builder の期待値。**

   対象: `orchestrator/tests/test_s8b_protocol_builder.py:55,83–98,122`

   ```python
   def _build_golden() -> fc.BuiltProtocol:
       _requires_repo()
       return fc.build_protocol_document(
           _G_SEED, _G_ENV, stock_configuration=_G_STOCK,
           extime_s=_G_EXTIME, wired_min_rel_floor=_G_FLOOR,
       )
   ```
   ```python
   assert built.canonical_bytes == _GOLDEN_BYTES, "canonical bytes が独立 golden と不一致"
   assert built.sha256 == _GOLDEN_SHA
   ```
   本番 builder は `s8b_floor_campaign.py:1312` で新 `CCBENCH_FULL_SHA` を埋めます。したがって旧 pin を含む golden bytes と一致しません。この node は確認した hold 対象にも含まれません。

   **放置時:** 正しい新 pin の生成 protocol がテストで拒否され、builder の受入レポートが失敗します。

   literal だけでなく `_GOLDEN_SHA`、別の builder 正例の固定 hash（122 行）も独立に再計算してください。保存済み floor protocol の変更は不要です。

4. **文字列集合外の追随漏れ — real / must-fix、2 件**

   **4-a. characterization の pin 更新に policy hash が追随していない。**

   対象: `orchestrator/tests/test_s8a_trigger_sweep.py:108–110,680`

   ```python
   _CHARACTERIZATION_PIN = "e9e477c"
   _ADMISSION_POLICY_SHA256 = (
       "949ddcc2951935405f661ce70cb7df1031fedfd162788655e78faaadac671a44"
   )
   ```
   `build_admission.py:502` の policy preimage は `repo_stock_pin=CURRENT_PIN` を含み、738 行で receipt の policy hash と exact 比較します。ソースの registry literal から独立に計算すると:

   | pin | policy SHA-256 |
   |---|---|
   | 旧 | `949ddcc2951935405f661ce70cb7df1031fedfd162788655e78faaadac671a44` |
   | 新 | `db6bc9ea80440a5e0d162319b0d91efab9fb3783a959bc3a2931601e253ca18a` |

   **放置時:** characterization 正例が schema/policy 不一致で拒否され、部分実行・保存則などの負例も狙った判定へ届かず、受入レポートが失敗します。

   108 行の **A 分類は正しい**ですが、変更が不完全です。独立した hash 期待値も追随させる必要があります。

   **4-b. 現行 config の campaign ID を旧 ID と比較している。**

   対象: `orchestrator/tests/test_s8a_trigger_sweep.py:120–123,354–370`

   ```python
   current = {
       tag: str(ident.campaign_id(cfg)) for tag, cfg in configs.items()
   }
   ```
   ```python
   assert current == _T816_S8A_CAMPAIGN_IDS
   ```
   `configs` は現行の `W.config_for()` から生成されます。同関数は新 pin と新 admission policy を identity に含めるため、旧 ID の期待値は据え置けません。

   **放置時:** 正しく変化した新 campaign ID が拒否され、campaign identity の受入レポートが失敗します。

   歴史 ID は保持し、現行 config に対する独立期待値を分けてください。併せて発見した s8b の pin 文字列を含まない固定 hash は 3-b に含めています。短縮表記・`g` 接頭辞・fixtures・tools の検索では、これ以外の現行 pin 追随漏れは確認できませんでした。

5. **docs 2 行 — refuted / nit（問題不成立）**

   `docs/phase3.md:2696` は [T-167] と旧承認・上流還元項を残しています。候補の承認時点を述べる文脈も保たれています。

   `docs/phase3-8b-restart-runbook.md:161` の新 gitlink 期待値、旧凍結 protocol の pin 保持、歴史再開の説明は実装と矛盾しません。

   根拠: `orchestrator/campaign/s8b_floor_campaign.py:1295`
   ```python
   actual_link = _ccbench_gitlink(root, _head_commit_oid(root))
   if actual_link != s8b_approved.CCBENCH_FULL_SHA:
       raise FloorCampaignError(
   ```
   frozen protocol の実行側は `protocol["ccbench_pin"]` を渡しており、この builder の比較を旧 protocol 全体の拒否条件とはしていません。

6. **変異事前登録 — refuted / nit（既登録 killer の誤りなし）**

   MUT-1／MUT-2 の明記された node は実在し、比較式は退行を検出します。

   根拠: `orchestrator/tests/test_s8b_approved.py:60–64`
   ```python
   assert actual == s8b_approved.CCBENCH_FULL_SHA, \
       f"gitlink 実測 {actual} != 承認定数 {s8b_approved.CCBENCH_FULL_SHA}"
   assert actual.startswith(pin.CURRENT_PIN), \
       f"gitlink {actual} が CURRENT_PIN {pin.CURRENT_PIN} を prefix に持たない"
   ```
   MUT-1 は full SHA 比較、MUT-2 は prefix 比較で赤になります。実測結果ではなく静的判定です。

## 分類表の検算

**53 行を検算済み。食い違いは次の 3 行です。**

| 行（`orchestrator/tests/` 配下） | 親 | 検算 | 根拠 |
|---|---|---|---|
| `test_dynamic_backoff_transitions.py:17` | B | A | 現 checkout の HEAD と比較し、その source を使用 |
| `test_s8b_protocol_builder.py:55` | B | A | 現行 builder の生成 bytes に対する golden |
| `test_t2187_adaptive_const_probe.py:47` | B | A | 現 checkout の HEAD と比較して patch を検査 |

本文の現在の動作による分類は **A 10 行 / B 43 行**です。

## 変異事前登録への意見

MUT-2 に以下を追加するのが妥当です。

`test_t126_qualification_driver.py::test_qualification_stock_source_reaches_build_with_exact_class`

根拠: `orchestrator/tests/test_t126_qualification_driver.py:815`
```python
assert result.aborted and not result.certified
assert seen == [BuildProvenance.STOCK_BASELINE]
```

source evidence は新 pin の独立 literal を持ち、実 admission の `source.ccbench_commit == CURRENT_PIN` に届きます。MUT-2 では STOCK_BASELINE を満たせず、この期待値が成立しません。

authority CLI の未確定 node は author 報告の 2 node で確定できます。ただし compiler 不在時の既存 skip がある node は、変異実測で実行されたことを確認してください。

## 攻撃したが破れなかった点

- `test_t126_qualification_driver.py:785` は A が正しい。
- floor hold/release control、模擬 job の Git/Python 応答、backoff reference 比較は B が正しい。
- mocc の旧 pin control・比較 base、A-1 登録、A2／plot fixture、実測由来の fixture は保持されている。
- assert の削除・反転・緩和や、新たな skip はない。

## 総括

**must-fix 4 件。NO-GO。**

分類誤り 3 行と、関連する hash・campaign ID の追随漏れを修正してください。静的レビューと独立 hash 計算のみで、pytest・変異実測は行っていません。