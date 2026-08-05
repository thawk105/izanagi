結論から言うと、プラン v1 は **NO-GO** である。防壁の挿入位置自体は妥当だが、公開経路のテスト検出力と次回 refreeze の proof chain が閉じていない。

pytest は実走していない。以下はコード・fixture・固定値の静的追跡結果である。

## 1. 凍結 bytes と T-080

### 所見 1 — 現行 artifact の bytes を変えずに実装すること自体は可能

- 判定: **real（親の主張はこの限定では正しい）**
- 根拠:
  - `s1_known_axes_freeze.generate()` は既存ファイルを拒否する: `orchestrator/campaign/s1_known_axes_freeze.py:769`
  - generator self-hash は生成時にだけ埋め込まれる: `orchestrator/campaign/s1_known_axes_freeze.py:634`
  - 現行 bytes は別途 manifest で固定されている: `orchestrator/tests/test_frozen_artifacts.py:38`, `orchestrator/tests/test_frozen_artifacts.py:125`
  - T-080 の active verification は旧 artifact の `/generator/sha256` と旧 migration-basis blob を照合する: `orchestrator/campaign/t080_freeze_migration.py:1072`
  - reconstruction 比較では known artifact の generator sha を除外する: `orchestrator/campaign/t080_freeze_migration.py:1100`, `orchestrator/campaign/t080_freeze_migration.py:1330`
- 影響:
  - 今回 JSON を書き換えなければ、known・measurement・holdout の raw SHA、凍結台帳参照、T-080 receipt の記録値は変わらない。
  - `METADATA_SPECS` や `test_s8b_oracle_driver` の旧 literal を今回更新してはならない。

ただし、この結論は **T-080 active receipt 経路に限る**。

### 所見 2 — 「live 編集を T-080 が許容する」は draft/reissue には当てはまらない

- 判定: **real**
- 根拠:
  - `_verify_worktree_basis_files()` は generator を含む worktree bytes を migration commit の blob と完全一致させる: `orchestrator/campaign/t080_freeze_migration.py:1459`
  - 同検査は draft capture / validation から呼ばれる: `orchestrator/campaign/t080_freeze_migration.py:1497`, `orchestrator/campaign/t080_freeze_migration.py:1659`
  - 一方、active `verify_receipt()` はこれを呼ばない: `orchestrator/campaign/t080_freeze_migration.py:1936`
- 影響:
  - 現行 receipt の公開検証は維持できる。
  - しかし同じ T-080 basis を使った draft 再発行は、新しい generator bytes を受理しない。次回 refreeze を「旧 T-080 の固定値更新」として処理することはできない。

親 brief の「live generator drift は許容される」は、active verification と draft/reissue を区別して記述すべきである。

### 所見 3 — 全 verifier の受理集合が不変という読みは誤り

- 判定: **real**
- 根拠:
  - known の legacy verifier は module-global `ROOT` の live generator を直接 hash する: `orchestrator/campaign/s1_known_axes_freeze.py:718`, `orchestrator/campaign/s1_known_axes_freeze.py:724`
  - measurement は T-080 を経由せず、known の legacy verifier を直接呼ぶ: `orchestrator/campaign/s1_measurement_freeze.py:156`, `orchestrator/campaign/s1_measurement_freeze.py:407`
  - direct comparison も measurement verifier を入口にする: `orchestrator/campaign/s1_direct_comparison.py:127`
  - calibration も既定では known verifier を呼ぶ: `orchestrator/campaign/s1_verify_extime_calibration.py:197`
- 影響:
  - source 編集後、旧 known JSON は新しい generator self-hash と一致せず、legacy S1・measurement・calibration の受理集合から外れる。
  - 現時点では s8a source drift によって既に赤なので、新たな certified 値が誤って選ばれるわけではない。しかし、失敗理由が generator drift に増え、S1 材料レポート生成・比較実行の利用可能性は回復しない。
  - T-080 static adapter を使う公開 S8b 経路だけは、旧 bytes と旧 pin のまま意味検証を追加できる。

したがって「bytes 不変」と「全 verification の受理性不変」を同一視してはいけない。

## 2. 次回 refreeze

### 所見 4 — 単純な削除→再生成では proof chain が壊れる

- 判定: **real、blocker**
- 根拠:
  - known 再生成で `/generator/sha256` と raw artifact SHA が変わる: `orchestrator/campaign/s1_known_axes_freeze.py:634`
  - measurement は known raw SHA を埋め込む: `orchestrator/campaign/s1_measurement_freeze.py:249`, `orchestrator/campaign/s1_measurement_freeze.py:256`
  - holdout も known raw SHA を記録する: `orchestrator/campaign/s8b_holdout_freeze.py:524`, `orchestrator/campaign/s8b_holdout_freeze.py:553`
  - T-080 は旧 known/holdout raw SHA を固定する: `orchestrator/campaign/t080_freeze_migration.py:44`
  - `/generator/sha256` の旧値も `METADATA_SPECS` に固定される: `orchestrator/campaign/t080_freeze_migration.py:110`
  - oracle adapter は known raw が旧固定値であることを要求する: `orchestrator/campaign/s8b_oracle_driver.py:196`
- 影響:
  - known だけ再凍結すると、旧 holdout と T-080 adapter が新 known raw を拒否する。
  - known・measurement・holdout を一緒に再凍結しても、旧 T-080 receipt の raw SHA・metadata closure が不一致になる。
  - `METADATA_SPECS` や旧テスト literal を上書きすると、過去 receipt の意味を後から変更することになり、凍結台帳そのものを壊す。
  - 必要なのは旧 T-080 の書換えではなく、新世代 artifact と transition receipt / trust-root 更新である。これは今回実装する必要はないが、**次回 refreeze の前提タスクとして明記する必要がある**。設計上も versioned family と successor transition が予定されている: `docs/freeze-permanent-design.md:440`, `docs/freeze-permanent-design-s2.md:74`

## 3. テスト検出力

### 所見 5 — private `_trigger_entries()` 負例だけでは「generate が書く前に拒否」を証明しない

- 判定: **real、blocker**
- 根拠:
  - 公開経路は `generate()` → `build_document()` → `_trigger_entries()` である: `orchestrator/campaign/s1_known_axes_freeze.py:608`, `orchestrator/campaign/s1_known_axes_freeze.py:769`
  - プランの生成負例は private `_trigger_entries()` を直接呼ぶ構成で、公開経路を通らない。
- 影響:
  - 将来 `build_document()` が別経路で predicate を構築したり、helper call を迂回しても負例は緑のままになる。
  - その場合、非 canonical predicate を含む known artifact が create-only 書込みされ、measurement/holdout の raw hash・variant binding・材料レポート参照まで汚染し得る。

修正案は、private の二負例を残したうえで、完全 mock 化した `generate(output_path)` 負例を最低一本追加し、`FreezeError` と `not output_path.exists()` を同時に確認すること。

### 所見 6 — proposed public verifier test は過剰決定

- 判定: **real、blocker**
- 根拠:
  - プランは現行 frozen document の predicate を改変して `verify_document()` に渡す。
  - source 編集後、その document の `/generator/sha256` は live generator と不一致になる: `orchestrator/campaign/s1_known_axes_freeze.py:724`
  - source provenance にも独立した拒否理由がある: `orchestrator/campaign/s1_known_axes_freeze.py:729`
  - schema 検査を削除しても、その後の generator/source 検査で `FreezeError` になり得る。
- 影響:
  - テストが単に `FreezeError` を期待するだけなら、検査配線を消しても赤くならない。
  - certified 集合を守る新防壁が消えたことを検出できず、既存 provenance 拒否に偶然救われるだけになる。

公開 wiring テストには次のどちらかが必要である。

- live source に対して自己整合する document を作ってから predicate だけを壊す。
- generator/source/ancestry を hermetic に成立させ、rebuild を sentinel にして schema 段階でのみ落ちる fixture を作る。

エラーメッセージの完全一致も必要だが、それだけで多重拒否理由を放置しない方がよい。

### 所見 7 — 直接負例は純増、正例の多くは重複

- 判定: **real。ただし正例重複自体は nit**
- 根拠:
  - frozen 六述語と emitter の exact 比較は既にある: `orchestrator/tests/test_reflux_ir.py:445`
  - test-local golden にも六 predicate の独立 literal がある: `orchestrator/tests/s1_expected_goldens.py:168`, `orchestrator/tests/s1_expected_goldens.py:638`
  - membership の strip 挙動も既に固定されている: `orchestrator/tests/test_trigger_gate_binding.py:225`
- 影響:
  - 「現行六述語が通る」「前後空白を許す」だけでは受理集合の新しい保証はほぼ増えない。
  - 一方、`_trigger_entries()` の gate/ident を個別に壊す負例と、`_validate_schema()` の gate/ident を個別に壊す負例は、新 call site を独立に殺せるため純増である。

private 負例では `_source` と `_module_source` の両方を mock し、main/remeasure equality など別理由で落ちないようにする必要がある。

## 4. 巻き込み

| 対象 | 静的な巻き込みと成果物への影響 |
|---|---|
| `s1_measurement_freeze` | `known_axes.verify_document()` を直接呼ぶため、旧 known の generator drift で停止する。T-080 で救済されない。将来 refreeze では known raw pin が変わるため measurement も再発行必須。`orchestrator/campaign/s1_measurement_freeze.py:156`, `:256` |
| `s8b_holdout_freeze` | known JSON を読むが、known の `_validate_schema()` / `verify_document()` は呼ばない。raw hash と binding を記録するだけである。`orchestrator/campaign/s8b_holdout_freeze.py:524`, `:540`, `:709` |
| `s8b_oracle_driver` | active T-080 adapter と legacy known verifier の二経路がある。実 artifact を通す正例を明示的な回帰対象にすべきである。`orchestrator/campaign/s8b_oracle_driver.py:364`, `:406` |
| `s1_direct_comparison` | upstream では measurement verifier に止められ、sink にも独立 membership 検査がある。新防壁と重複するが defense-in-depth として有効。`orchestrator/campaign/s1_direct_comparison.py:526` |
| `p3_s4_loop` | 同じ shared helper で membership と canonicalization を既に行う。helper 自体を変えない限り production 巻き込みなし。`orchestrator/campaign/p3_s4_loop.py:202` |
| `conftest` | fully mocked な新テストなら allowlist 追加不要。live `build_document()` を使う公開 wiring テストなら serial node を追加する必要がある。`orchestrator/tests/conftest.py:39` |
| meta-test | conftest を変更した場合、独立 golden も同時更新しないと meta-test が落ちる。`orchestrator/tests/test_real_repo_serialization.py:35`, `:352`。既存 self-runner は新しい引数なし test を自動発見するため README allowlist は不要。`orchestrator/tests/test_plain_runner_coverage.py:25` |

### 所見 8 — standalone holdout verifier の semantic closure は未解決

- 判定: **疑い。脅威境界を明記すべき**
- 根拠:
  - holdout の build/verify は known raw と binding を扱うが、known predicate の canonical membership を検査しない: `orchestrator/campaign/s8b_holdout_freeze.py:524`, `:709`, `:809`
- 影響:
  - 正規の known generator 経由なら今回の生成防壁で守られる。
  - しかし、別途発行された非 canonical known JSON を直接与えると、standalone holdout はそれと整合した freeze を作り得る。公開 oracle の sink では最終的に拒否されるものの、holdout 台帳・材料参照は不正な known raw を記録し得る。
  - 今回の保証対象が「正規 known producer と公開 verifier」に限定されるなら非 blocker。holdout freeze 単体まで保証するなら共有 schema 検査の導入が必要で、fixture 波及を伴う。

### 所見 9 — 次回生成される selection rule が新規則を記録しない

- 判定: **real**
- 根拠:
  - generator が出力する `selection_rules.system_gate` は main/remeasure の exact equality しか説明していない: `orchestrator/campaign/s1_known_axes_freeze.py:657`
  - 現行 artifact も同じ記述である: `output/s1-freeze/known_axes_freeze.json:14`
- 影響:
  - 今回 artifact を再生成しないため現行 bytes への影響はない。
  - しかし次回 refreeze では、実装は canonical membership を要求するのに凍結台帳上の selection rule はそれを説明しない。certified 値自体は守れても、材料レポートから「なぜその受理集合なのか」を再構成できない。

generator 側の rule 文言は今回更新し、現行 JSON は不変のままにするのがよい。

## 5. 既存 G7 赤テストの修正

プランの修正方法は、次の条件を守れば **テストを弱めない**。

- 判定: **real（提案は妥当）**
- 根拠:
  - テストの本来の標的は holdout generator tamper の拒否: `orchestrator/tests/test_s8b_oracle_driver.py:2694`
  - 現在は公開 `gate_check()` まで通して exact refusal 数も検査している: `orchestrator/tests/test_s8b_oracle_driver.py:2725`, `:2729`
  - known verifier は resolver ではなく module-global `ROOT` から generator を読むため、stub root への `ROOT` patch が必要: `orchestrator/campaign/s1_known_axes_freeze.py:724`

安全条件は以下である。

1. historical known generator bytes の digest が document の pin と一致することを先に assert する。
2. `ROOT` patch は実際の `gate_check()` 呼出しの周囲だけに限定し、必ず復元する。
3. holdout generator の tamper、期待する exact refusal、総 refusal 数の assertion は維持する。
4. `verify_document()` や T-080 adapter を mock しない。

これなら、無関係な live known-generator drift だけを fixture から除き、generator tamper が公開 G7 に到達するという元の意図は維持される。

## 総括

**NO-GO**

- Blocker 1: private 負例だけでは公開 `generate()` の write-before-reject 防壁を証明できず、公開 verifier 負例も stale generator/source により過剰決定である。
- Blocker 2: 次回 refreeze が known→measurement/holdout→T-080 receipt を壊すため、旧 pin 更新ではなく新世代 transition を前提タスクとして明記する必要がある。
- Blocker 3: 次回 artifact の `selection_rules` が canonical membership を記録せず、実装上の受理集合と凍結台帳の説明が不一致になる。