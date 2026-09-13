## A. 昇格の意味の候補

以下の `file:line` は、指定 worktree 内の相対パス。ファイル変更・テスト実行は行っていない。

「consumer 不在」は意味を限定する必要がある。**gap 証拠を検査して受理・発行する consumer は実在するが、それを研究目標・回復計測・pipeline の適格性へ変換する consumer は確認できない。**

| 候補 | 想定する状態遷移と調査先 | 判定 |
|---|---|---|
| 1. ledger 適格性の昇格 | `patches/ledger.json:14` の非適格値を適格へ変更、または適格 entry を追加する writer。既存の検査先は `silo_ladder_rung1_contract.py:495` `_check_ledger_consistency()` | 昇格 writer は見つからない。exact-one・false 固定を検査する consumer が実在 |
| 2. gap 較正を通した rung の受理 | `silo_ladder_rung1.py:4733` `_collect_command()` が未検査の correctness/gap 証拠を検査済み成果物へ変える | **証拠受理として実在**。独立した `performance-calibrated rung` 状態・登録集合への昇格は見つからない |
| 3. ladder 証拠の研究成果への昇格 | `silo_ladder_rung1.py:1252` `_validate_schema()` を満たす ability-probe 成果物を、別 consumer が研究目標・回復計測適格として受理する | 見つからない。producer・validator とも非適格値を要求 |
| 4. inert patch の upstream 採用 | patch を upstream / izanagi-trace の採用済み実装へ移す | `docs/decisions.md:311` の D18 は**人間判断**。自動昇格 consumer は見つからない |
| 5. pipeline 評価対象への昇格 | `pipeline_eligible=false` の rung を通常 campaign の評価入力へ変換する | 見つからない。専用裸マクロ、射影除外、materializer 非適格登録がある |
| 6. 正しさの認証〔追加〕 | trace を verifier が検査し、serializable / certified を返す | 正しさ consumer は実在する。ただし ladder 成果物全体の研究適格性とは別 |

`ability_probe` は昇格フラグではない。既存 entry は `patches/ledger.json:13` ですでに **true**。親が提示した「適格性 field を false→true」の並びから分離すべきである。

## B. consumer の実在判定

**間接参照を含む確認経路**

| 経路 | 読取り・書込みの実体 | 昇格権威か |
|---|---|---|
| `silo_ladder_rung1.py:3991` correctness／`:4290` gap → contract `validate():657` → `validate_ledger():687` → `_check_ledger_consistency():495` | JSON を parse。`:518` 以降で entry 数、`:539` の辞書と `entry[key]` の比較で適格性値を検査 | **負制約**。ledger を書き換えない |
| 三つの loop loader：`p3_s4_loop.py:2371`、`p3_s4_loop_sort.py:520`、`p3_s4_loop_trigger_gating.py:1000` → `projection_guard.py:385` → `load_projection_policy():168` → `entry.get("ability_probe"):210` | nested string と除外 token/path を照合して拒否する | **負制約**。適格化 API ではない |
| `silo_ladder_rung1.py:5096` CLI collect → `_collect_command():4733` → `validate_evidence():1590` → `_validate_schema():1252`／`_validate_performance():1214` | correctness・gap・raw・binding を検査し、`:5061` で create-only 発行 | **characterization 証拠の受理は実在**。classification は `:4960` で非適格に固定 |
| 同ファイル `:5100` CLI verify-result → `validate_evidence()` → schema／performance 検査、さらに `validate_raw_bundle():2956` と `validate_current_bindings():3737` | 読み直しと失敗判定、終了コード | 読取り consumer。昇格しない |
| `fetch_third_party.py:723` main → `_load_policy():67` → `_driver_module():52` → driver の `third_party_policy():875` | module を返す helper を経由して共有依存 policy を読む | source の取得・配置。ladder 証拠の適格化ではない |
| `s8b_floor_campaign.py:2334` → `_load_floor_third_party_policy():2273` → `_silo_ladder.third_party_policy():2278` | alias 経由で共有依存 pin を読む | **floor が module を import することは ladder 昇格の証拠にならない** |
| `hooks/guard_bash.py:242` → source の `compile/exec` → namespace 内の loader `:259` → `pegasus_admission_registry.py:120` | JSON registry の実行場所分類を取得。登録は `admission_registry.json:298`、`:364` | local/dispatch 判定。成果物適格性とは別 |

**D162 決定 (7) の射程外も確認した結果**

- **ledger を経由しない成果物発行**：`_collect_command()` は `all_pass` を計算するが、研究・回復適格性は false のまま。`_validate_schema():1273` も同値を要求する。
- **gap による受理**：`_validate_performance():1243` は、両 workload について各 variant 6 本と `max(rung) < min(stock)` を要求する。これは実在する受理述語だが、別の適格性状態へ変換していない。
- **promotion と名付けられた共用 gate**：`condition_meaning_gate.py:3478` に `_PROMOTION_USE_CLASSES` がある。しかし rung の caller は `silo_ladder_rung1.py:2236` で **`use_class="raw-measurement"`** を渡す。戻り値は条件検査の admission であり、ladder classification の変更ではない。
- **pipeline 側**：`materializer_admission.py:115`、`:120` は rung の二つの builder を `NON_ADMISSIBLE` に登録。`model.py:146` → `cmake_cache_variable_for_axis():84` は通常の CMake 変数を生成し、ledger による rung 適格化を行わない。
- **certified の別義**：`pipeline.py:2440` の `res.certified=True` は独自の評価経路の正しさ認証。ladder の `all_pass` や ledger field を入力にした昇格ではない。

**test 経由の参照**

- `test_silo_ladder_rung1.py:195` → `contract.validate_ledger()` → `_check_ledger_consistency()`：schema/hash の負例検査。
- `test_silo_ladder_rung1_driver.py:556` → `driver.validate_evidence()` → schema・performance 検査：fixture の受理・拒否。
- 同 `:2568` は `"validate_current_bindings"` という文字列を使った monkeypatch。production の昇格登録ではない。
- `test_silo_ladder_rung1_evidence.py:1216` は ledger entry を JSON key と `next()` で選び、歴史的 evidence の identity を検査する。`:1202` の commit-witness 検査も適格性変更ではない。

いずれも**ソース読解で確認した経路であり、今回テストを実行して通したという意味ではない**。

**検索実測と閉包の範囲**

訂正対象の path 集合を `P` とすると、実行した argv は次の形である。配列中の `P` は下記9引数への展開を表す。

```text
P = docs orchestrator tools hooks src patches AGENTS.md CLAUDE.md README.md

R = rg --hidden --no-ignore -n -i
    -g !docs/archive/** -g !**/__pycache__/** -g !*.pyc
```

| 実行 argv | rc | 一致行／ファイル |
|---|---:|---:|
| `R 'silo 昇格入口' P` | 1 | 0／0 |
| `R 'silo[_ -]ladder\|silo.*梯子\|劣化.*rung\|performance.calibrated' P` ※実際の alternation は `\|` でなく `|` | 0 | 504／63 |
| `R '\b(research_goal_eligible\|recovery_measurement_eligibility\|pipeline_eligible\|ability_probe)\b' P` ※同上 | 0 | 38／8 |
| 下記の複数行検索 | 0 | 95／15 |

複数行検索の実際の追加引数：

```text
-U
(?s)(silo|ladder|rung|梯子).{0,250}(昇格|promotion|活性化|研究目標|回復計測)|(昇格|promotion|活性化|研究目標|回復計測).{0,250}(silo|ladder|rung|梯子)
```

追加で実行した参照検索：

```text
rg --hidden --no-ignore -n
'validate_evidence|validate_current_bindings|validate_raw_bundle|load_projection_policy|assert_no_ability_probe_material|patch_contract\.validate'
orchestrator tools hooks src
```

rc=0、**61 行／12 ファイル**。同名部分を持つ無関係な validator を分離し、上表の実参照を追跡した。

```text
rg -n
'importlib|__import__|getattr\(|setattr\(|globals\(|entry_points|add_subparsers|add_parser|set_defaults|dispatch|registry'
orchestrator/campaign/silo_ladder_rung1.py
orchestrator/campaign/silo_ladder_rung1_contract.py
orchestrator/campaign/projection_guard.py
tools/pegasus/fetch_third_party.py
```

rc=0、**7 行／2 ファイル**。driver は四つの明示的 CLI 分岐、fetch helper は四つの依存取得操作。別途、上表の registry／namespace dispatch を確認した。

`rg --files --hidden --no-ignore` に同じ除外指定と `P` を与えた列挙は **1,464 ファイル**。`output/**` は検索対象に入れていない。

閉包の単位は、**既存 ledger・artifact schema・識別子・公開 helper・CLI・登録表から到達する経路**である。これらには適格化への出口を見つけなかった。ただし、検索件数だけで「任意に組み立てられる文字列や無関係な汎用プログラムを含め、絶対に見落としがない」とは証明できない。**canonical 記録にも、この静的探索の射程を残すべきである。**

## C. 訂正対象の列挙

**確認した訂正対象は 0 件。** 完全一致だけでなく、上記の複数行候補と ladder 関連記述を確認した。

誤訂正しやすい箇所は次のとおり。

| 箇所 | 現行の文言・意味 | 訂正しない理由 |
|---|---|---|
| `patches/README.md:461` | 専用 driver が駆動の正本 | 直後に通常 campaign・recovery pipeline へ接続しないと明記 |
| `patches/README.md:467` | 「trace t4 で certified serializable」 | trace の正しさ認証に限定。ladder 全体の研究適格性ではない |
| `tools/pegasus/README.md:68` | characterization 専用資材 | `:72` で ability-probe 専用と限定 |
| `docs/decisions.md:18210` | 「silo 完全検証と prediction seal は活性化以前から別理由で閉じている」 | `verify-result` の失敗状態の説明。活性化権限の昇格入口として数えていない |
| `docs/decisions.md:5738` | recovery 接続を非適格性の解消として記述 | D120 の**実装しない裁定の背景**。接続済みという主張ではない |
| `docs/paper-story/2026-09-05.md:1752` | rung 1 実装と gap 実測 | `:1754` で研究目標に数えないと明記 |
| `patches/README.md:23` | 「勝てば昇格」 | 合成 variant の upstream 採用。`:11`、`:246` に人間判断の限定がある |

親が不在を記録する場合の最小 plan は、`docs/decisions.md:59667` の末尾後に、新 D として **対象を研究・回復・pipeline 適格性への昇格に限定した判定、上記参照鎖、探索範囲**を追記すること。既存 source・gate・ledger の変更は不要。D 番号はここでは予約しない。

データ内の指示形として、`src/coder-leakproof-context.md:102` の「ちょうど 1 文」、`patches/README.md:465` の「新 rung は登録必須」などを検出した。調査対象の記述として扱い、今回の作業指示には採用していない。

## D. 親 brief への反証

1. **P1 の結論は現時点で反証できなかった。** 訂正対象 0 件を支持する。ただし完全一致 0 件だけから意味的訂正対象 0 件は導けない。C の確認が追加根拠になる。
2. **「consumer は不在」の無限定な確定は広すぎる。** `_collect_command():4733` は gap 証拠を検査・受理・発行する実在 consumer。候補2まで含めて「何の受理機構もない」と記録してはいけない。
3. **D162 の射程外を明記すべき。** 成果物 classification、condition gate、materializer 登録、共用 dependency helper は ledger の三適格性 field だけでは説明できない。
4. **行番号は更新が必要。** 射影資料の classification `:4688` 付近は、現 worktree では `:4960`。validator は `:1273`。
5. **除外範囲は依頼本文を採用する。** brief の `output/insights/**` 除外より広い、`output/**` 全体を訂正対象外とした。

## 総括

consumer=不在〔確認した静的参照閉包内の、研究・回復・pipeline 適格性への昇格〕。  
consumer=実在 `orchestrator/campaign/silo_ladder_rung1.py:4733`〔gap 証拠の受理・発行に限定〕。  
訂正対象は確認範囲で **0 件**。P1 は支持するが、完全一致検索だけでは根拠不足。  
親の追記は昇格の意味と探索範囲を限定し、既存 gate・凍結 bytes は変更しない。  
ファイル変更・テスト実行・commit・push は行っていない。