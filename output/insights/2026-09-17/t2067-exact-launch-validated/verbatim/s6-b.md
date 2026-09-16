## docstring / comment の整合

以下、`D` = `orchestrator/campaign/s8b_oracle_driver.py`、`N` = 新規 `orchestrator/tests/test_s8b_gate_core_exact_launch_validated.py`、`T` = `orchestrator/tests/test_s8b_oracle_driver.py`、`R` = `orchestrator/campaign/s8b_ratified_freeze.py`、`S` = 射影された `stage4-ruling.md` とします。静的レビューのみ実施しました。

**RB-1 — severity: nit／判定: real：core の説明が refusal の優先順位を省略**

- **根拠:** `D:425–430` は token が無ければ missing-token refusal を積むと説明しますが、実装 `D:486–492` は `ratified_error` を優先します。node 6 (`N:154–172`) も token 無しで `freeze-ratify:` と `budget-null` だけを期待します。裁定も `S:38` の「必ず refusal M」と、`S:84` の error 優先が字義上は不一致です。
- **推奨:** docstring と I1' を「exact token 無しでは受理しない。既存の `ratified_error` があればその診断を優先し、それ以外は M」と明確化してください。実装変更は不要です。

**RB-2 — severity: nit／判定: real：public docstring の「必ず full launch validation」は過大**

- **根拠:** `D:590–594` に対し、明示 error (`D:598–601`)、初読失敗 (`D:605–616`)、static loader 失敗 (`D:634–652`) は `launch_validate` を呼びません。新規 race node も非呼出しを固定しています (`N:96,111`)。
- **推奨:** 「v2 を受理するには full launch validation が必要。候補取得に成功した経路で一度実行」と条件を限定してください。既存文言の問題であり、受理境界の欠陥ではありません。

旧「単体 gate CLI 経路では自身で `load_ratified_freeze` を一度呼ぶ」は残っていません。`D:419` の自身で呼ぶ対象は **`load_verified_freeze`** で、再読維持と整合します。v2 comment (`D:484–485`) も実装と一致します。

`real_repo_ratified_memo.py:37–42` は public seam の説明であり、`D:588–601` の引数・早期 return と整合しています。

## 最小差分と scope

**RB-3 — severity: should／判定: refuted：裁定外変更・必要変更の欠落・不要依存**

- **根拠:** 現物の production diff は 18 行追加・28 行削除。変更は core signature、docstring、v2 枝、public→core の二箇所 (`D:615,628`) に限定されています。新規 test は245行です。裁定 `S:82–88` と一致します。
- **推奨:** 現差分を維持してください。`_gate_check_validated`、run-block、CLI、既存 test の変更は必要ありません。

新規 import はすべて使用されています。`replace` (`N:2,205`) は frozen object を直接変更せず、内側の `RatifiedFreeze` と外側の token を再構築するための標準ライブラリ利用です。不要な依存・追加された dead code は見つかりませんでした。

## test の品質

**RB-4 — severity: should／判定: refuted：揮発値・Mock の未設定戻り値による偽緑**

- **根拠:** `N:28–61` は tmp 内の合成 document とその bytes hash を使用します。`"a"*40` 等は合成 sentinel で、実 working tree hash・日時・実 active 世代の焼き込みではありません。
- `_assert_exact_refusals` は件数と集合の両方を比較します (`N:23–25`)。既存 helper (`T:285–292`) と同じ保証です。
- `reads` の各経路は次のとおりです。

| node | 呼出前の設定／非呼出し確認 |
|---|---|
| 1・2 | 二要素の `side_effect` (`N:88,102`)、二回呼出し確認 |
| 3 | `verified` を渡す。`assert_not_called` (`N:120–123`) |
| 4・5 | token を渡す。全 seam の非呼出し確認 (`N:135–136,150–151`) |
| 6 | `return_value=verified` (`N:165`)、一回呼出し確認 |
| 7 | 全 seam の非呼出し確認 (`N:182–183`) |
| 8 | 二例外の `side_effect` (`N:189–190`)、二回呼出し確認 |
| 9 | token を渡す。全 seam の非呼出し確認 (`N:212–213`) |
| 10・11 | 二要素の `side_effect` (`N:219,232`)、二回呼出し確認 |
| 12 | fixture を使わない signature 検査 |

- **推奨:** 現状維持。通常経路で未設定 Mock が `loaded` に流れ込む箇所はありません。将来誤って loader を呼ぶ変更も、非呼出し assertion により検出されます。

**RB-5 — severity: should／判定: refuted：subclass 構築・hash None・例外文字列の検査が不成立**

- **根拠／subclass:** `R:818–831` は `slots` 指定や独自 constructor のない frozen dataclass です。`Derived` (`N:140–144`) は生成済み `__init__` を継承し、`vars(token)` は六つの field を渡します。frozen は初期化後の代入制限であり、この構築を妨げません。
- **根拠／node 9:** `N:205` は **token 内の sha を None** にします。`D:447–449` がその sha を優先採用するため、`verified` を渡さない形で `D:493` の None 拒否を直接観測できます。裁定 `S:60,87` と一致します。
- **根拠／node 6:** `RatifiedFreezeError` に独自 `__str__` はなく、`R:296` が基底例外へ `"[reason] detail"` を渡します。`D:642` がさらに `"[reason] "`、`D:487` が `"freeze-ratify: "` を付けるため、`N:157` の二重 reason は現実装から導けます。
- **推奨:** 三検査とも維持してください。二重 reason の整理は本 wave の refusal 不変条件から外れます。

受入時間について、親提示の新規17 node・4.69秒は300秒の約1.6%です。ただし単独走から受入全体の上限遵守は断定できません。未登録 node の割付け重みは1秒/node (`tools/acceptance_shards.py:396–404`) であり、実所要とは別です。

## 裁定 §7 との突合

**RB-6 — severity: should／判定: refuted：node の過不足・parameterize id の不一致**

**根拠:** `S:87` と新規ファイルを照合した結果、名前・id は一致し、12種17 nodeです。

| node | `test_` を除く関数名 | 件数・観測点 |
|---|---|---|
| 1 | `public_reread_v2_requires_launch_validated` (`N:85`) | 1：race 後 M のみ、二読、static/launch 非呼出し |
| 2 | `public_reread_v2_ignores_injected_ratified` (`N:99`) | 1：public 注入でも同じ拒否 |
| 3 | `core_v2_without_launch_validated_is_refused` (`N:115`) | 3：`both/floor-only/budget-only`、M＋null 診断 |
| 4 | `core_exact_launch_validated_preserves_predicates` (`N:129`) | 3：同じid、both は受理、片側はnull診断だけ |
| 5 | `core_rejects_launch_validated_subclass` (`N:139`) | 1：exact type 拒否 |
| 6 | `public_ratified_load_errors_preserve_refusals` (`N:162`) | 2：`RatifiedFreezeError/RuntimeError`、翻訳＋budget-null |
| 7 | `public_explicit_ratified_error_keeps_early_return` (`N:175`) | 1：明示 error のみ、loader 非呼出し |
| 8 | `public_two_failed_reads_preserve_refusals` (`N:186`) | 1：二読目例外を含む四診断 |
| 9 | `core_launch_validated_missing_hash_remains_refused` (`N:203`) | 1：token sha None の拒否 |
| 10 | `public_reread_v1_never_gets_missing_token_refusal` (`N:216`) | 1：floor-null、budget-null だけ |
| 11 | `cli_gate_check_transports_missing_token_refusal` (`N:229`) | 1：in-process CLI の rc・JSON・M |
| 12 | `gate_core_signature_has_no_ratified_injection_port` (`N:244`) | 1：core signature に ratified が無い |

**推奨:** node 追加・削除は不要です。裁定外 node、欠落 node はありません。旧 fallback との差は hash 一致 fake により静的に説明できますが、変異 KILLED は未実測です。

## consumer 取り残しと波及

**RB-7 — severity: should／判定: refuted：core 引数削除による既存 caller の破損**

- **根拠:** repo の Python ファイルで `_gate_check_core` と `ratified=` を検索しました。production の core 呼出しは **6箇所／2関数／1 module**：`D:610,623,636,645,667,692`。core に `ratified=` を渡す残存箇所は **0** です。
- 既存直接 consumer `T:2859–2866` と `test_s1_known_axes_freeze.py:1145–1149,1154,1169` にも該当引数はありません。新規 helper `N:77–82` の呼出しにもありません。
- `recording_gate` (`T:5146–5150,5230–5234`) は `_gate_check_validated` の差し替えです (`T:5174,5249`)。`D:1392–1397` が渡す引数をすべて受け取れます。余分な optional 引数は今回の互換性を壊しません。
- `T:5850–5864` の検査対象も private gate の caller と public signature であり、今回の core 引数削除と衝突しません。
- **推奨:** 既存 consumer の編集は不要です。この結論は静的に見つかった caller の範囲であり、動的呼出しを含む権威ある閉包の証明ではありません。

## 段 3 所見の反映

**RB-8 — severity: should／判定: refuted：B-2・B-8・B-9・B-11 の未反映**

- **B-2:** 旧 docstring 全体が置換され、v2 comment も更新済み (`D:425–430,484–485`)。ただし文言精度の残件は RB-1・RB-2。
- **B-8:** `S:25,74–78` は焦点走を代表経路、残りを受入全走と区別しています。親提示の28 passed／6 skippedを全 consumer の検証完了へ一般化できません。
- **B-9:** `S:38` は「admission しない＋集約継続」へ訂正済み。実装も M 追加後に `D:500–578` の診断を続けます。「必ず M」の限定不足だけ RB-1 に残ります。
- **B-11:** `S:11` と author 報告81行は6箇所へ訂正済み。現物の件数も一致します。
- **推奨:** 反映済み部分を維持し、文言の残件だけ親裁定で扱ってください。

## 総括

**must-fix は見つかりませんでした。real 所見は文言の nit 2件（RB-1・RB-2）です。** 実装範囲、12種17 node、Mock の実効性、既存 caller との整合は裁定に沿っています。

ファイル編集・pytest 実行は行っていません。親提示の実測を前提として扱い、変異 matrix・受入全走・受入5分以内は未確認です。