## 所見 (重い順)

1. `orchestrator/campaign/buildcache.py:1416-1428` — `**kwargs` を持つ旧 collector が fail-closed を迂回する。
   `supports_policy` は新しい名前付き引数を持たなくても `VAR_KEYWORD` だけで真になる。したがって新引数を無視する fake でも external policy 下で呼ばれる。`CompilerInputManifest` は `s8b_compiler_input.py:55-59` の単純な dataclass なので、fake が dependency input を省いた v3 manifest を返すと、後段 validator は自己申告された entry しか検査できない。追加テスト `test_buildcache_v2.py:2847-2869` は名前付き旧 signature しか殺さず、この分岐を検査していない。
   影響は主に test seam の偽緑だが、依頼された fail-closed 契約を満たさない。external policy または EVOLVE-BLOCK proof 有効時は全引数の明示的な signature を要求し、`**kwargs` だけの fake を呼ばない負例を追加すべき。委譲 wrapper は明示 signature または `__wrapped__` を公開させる。
   **scope 内、must-fix。**

2. `orchestrator/campaign/s8b_compiler_input.py:1049-1058,681-682` — m06 は mask される。
   `None` の明示拒否条件を削除しても、直後に `_canonical_dependency_prefix_roots(None)` が呼ばれ、「root sequence でない」と再拒否する。裁定 `s4-adjudication.md:185` の「B3 の唯一の拒否点」は成立しない。
   m06 は `None` を空 tuple として扱うところまで含む exact block replacement へ再照準し、`test_v3_none_dependency_context_is_rejected_but_explicit_empty_is_accepted` で殺す必要がある。
   **scope 内、must-fix。**

3. `orchestrator/tests/test_buildcache_v2.py:3246-3260` — 裁定で落とすと明記された node が混入している。
   `s4-adjudication.md:143-147` は `test_v3_dependency_prefix_hit_validation_failure_never_rebuilds` を形 B 由来として明示的に除外しているが、現物に存在する。`s5-author.md:58` も追加済みと報告しながら、総括では「形Aのみ」としている。
   新規 node を除去し、形 A の同一根 hit 正例 `test_v3_dependency_prefix_hit_revalidates_same_identity_without_rebuild` までに留めるべき。
   **scope 内、must-fix。**

4. `orchestrator/campaign/buildcache.py:1316,2778` — runtime-only の逐語契約と現物が矛盾する。
   裁定 `s4-adjudication.md:120-123` は「絶対根を completion へ保存しない」とする一方、completion の `preimage.dependency_prefix` は絶対根を保存する。追加テスト自身も `test_buildcache_v2.py:3103` で `expected_roots` の保存を要求している。これは D1220 に従う既存 identity 経路で、新フィールドの直接 serialization ではないが、絶対値は同じである。
   durable receipt は `s8b_binary_admission.py:269-285`、runtime built record は `s8b_floor_campaign.py:4435-4448` を見る限り、新フィールドを直接保存していない。台帳側にも同フィールド名の参照はない。一方、明示 `dependency_prefix` の場合は configure argv に絶対根が入り、`s8b_floor_campaign.py:4441,4712-4719` から portable built record へ残り得る既存経路がある。
   D1220 を維持するなら契約を「新しい root field を重複保存しない」へ訂正すべき。絶対根そのものを completion から除く変更は D1220 と衝突するため本 wave の scope 外。
   **契約訂正は scope 内で must-fix、identity 変更は scope 外。**

## 変異 m01〜m06 の帰属判定 (1 件ずつ)

- **m01:** `s8b_compiler_input.py:45` に逐語 old が存在する。v3 dependency entry は `_normalized_v3_inputs()` の root membership で初めて拒否され、shape、path、digest に先行拒否はない。**非 mask。現照準でよい。**

- **m02:** `s8b_compiler_input.py:1118` に `if len(matches) != 1:` が存在する。`test_s8b_compiler_input.py:732-750` の二根は非 overlap、同一 relative path、同一 bytes なので他層は拒否しない。**非 mask。現照準でよい。**

- **m03:** 実際の exact old は `s8b_compiler_input.py:1133` の `special_roots.extend(current_dependency_roots)`。登録表の old は説明文であり逐語ではない。偽造 manifest は policy、shape、digest、bytes が正しく、同じ入力を先に拒否する層はない。**帰属は正しいが、exact old へ再登録が必要。**

- **m04:** 実際の対象は `s8b_binary_admission.py:239-241`。正常な v3 issuer 入力では admission、binding、snapshot 検査が先に通り、`None` を渡した live validator だけが落とす。負例 node は元から拒否するため殺さない。`test_portable_validator_accepts_v3_after_live_dependency_roots_disappear` または bridge 正例へ照準する。**非 maskだが、登録 old を exact block に直す必要あり。**

- **m05:** 登録 old の `result.compiler_input_dependency_prefix_roots` は現物に存在しない。実装は `s8b_floor_campaign.py:4331-4333` で `getattr` し、`4396-4398` で局所変数を渡す。対象は後者の exact keyword block にするべき。keyword 自体を削ると test spy の辞書参照が real issuer より先に `KeyError` になるため、単一帰属を保つなら値を `None` または `()` に変える変異がよい。正例 bridge が殺し、負例 bridge は殺さない。**現登録は適用不能、再照準必須。**

- **m06:** 明示条件を消しても sequence 型検査が拒否する。**mask。現照準は不受理。** `None` の場合に `current_dependency_roots = ()` まで到達させる block replacement に変更する。

なお、裁定表 `s4-adjudication.md:182-185` の m03〜m06 は逐語 old ではなく説明文であり、そのままの文字列置換では適用できない。変異 probe は `s5-author.md:105` のとおり未実走なので、KILLED node 集合はまだ確定していない。

## 焦点走の追加対象

裁定 §4.5 の四ファイルと `test_s8b_floor_campaign.py` に加え、参照関係から最低限次を追加するべき。

- 間接 `build_v2` 経路:
  `test_campaign.py`、`test_s8b_oracle_driver.py`、`test_build_site_gate.py`、`test_t126_qualification_driver.py`、`test_t1416_backoff_compiler_binding.py`、`test_backoff_requested_us.py`、`test_backoff_overthrottle.py`、`test_backoff_extended_sweep.py`、`test_b10_backoff_shape_sweep.py`。

- issuer 互換 consumer:
  `test_s8b_floor_stats.py`、`test_s8b_predicate_build_proof.py`、`test_s8b_ratified_verify.py`。`s8b_v2_freeze_fixture.py` は後二者などから使われる helper。

- built record、portable projection、永続 artifact:
  `test_s8b_materialization.py`、`test_s8b_freeze_io.py`、`test_s8b_ratified_freeze.py`。この三つは handoff の具体一覧から漏れている。

- 新規 test file のメタ契約:
  `test_plain_runner_coverage.py`。これは `os.listdir()` で動的列挙し、新規 file は README allowlist に無い一方、`test_s8b_dependency_prefix_bridge.py:154-159` に self-run harness があるため静的には漏れていない。
  `test_pytest_collection_config.py:423-433` にも動的 `test_*.py` 列挙があるが、oracle/verifier exclusion 用であり、新規名は該当しない。

## 同意した箇所 (短く)

- cache hit は `buildcache.py:2500-2518,2555-2566`、fresh build は `2652-2685,2840-2851` で根を validator と `BuildResult` の双方へ渡している。
- production の receipt issuer caller は `s8b_floor_campaign.py:4377` の一箇所で、新 keyword を渡している。
- descriptor 経路の `dataclasses.replace()` は `buildcache.py:3003-3009` で未指定フィールドを保持する。oracle wrapper と pipeline 経路で根は失われない。
- bridge test は build 側を seam 化しているが、`build_cells()` は production 本体で、spy は `original_issue()` を呼ぶため issuer は実物である。両側 stub の偽緑ではない。
- pytest 未実走、rc=16 はテスト結果ではない、floor job 未投入という報告は正直である。

## 総括

名前付き production 経路の配線自体は fresh、hit、floor、issuer、oracle、pipeline まで閉じており、bridge test も実 issuer に到達する。ただし、`**kwargs` collector seam の fail-closed 穴、mask された m06、適用不能な変異 old、裁定で禁止された cache-hit node、runtime-only 文言と completion 実体の矛盾が残る。

したがって静的レビュー判定は **差し戻し**。pytest は実走しておらず、緑とは判定していない。