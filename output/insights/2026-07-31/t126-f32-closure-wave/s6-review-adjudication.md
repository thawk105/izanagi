authority: none
default_effect: no-state-change

# T-126 F3-2 closure — 段 6 レビュー親裁定 (fix 1)

## 固定入力

- fix 前 `collector.py` SHA-256 `949cea456806b53679ce669e6b7d771f9970d16e7867926b4e212d5bc23138d4`
- fix 前 `test_t126_pegasus_tools.py` SHA-256
  `a7b7c083fb5c5926295f2a5eaa7428bb8315a29e8a0c646a581282bd49657f1f`
- fix 前 snapshot: `.codex/dev-wave-t126-f32-closure-jobs/s6-fix1/pre/`
- review 正本: `.codex/dev-wave-t126-f32-closure-jobs/s6-review-fidelity/output.md` (レンズ C)、
  `.codex/dev-wave-t126-f32-closure-jobs/s6-review-efficacy/output.md` (レンズ D)
- 受入 1 回目: 計算 node `874729.nqsv` (bnode006)、related 5 files `435 passed, 9 skipped`、
  bash-n / check_codex_agents / check_docs / git diff --check / JSON / source 前後一致 すべて rc=0

両レンズとも NO-GO。段 3 所見は closed 15 / partial 0 / regressed 0 (レンズ C の表) であり、
production 実装は plan v2 §P1〜P4 に逐語一致することを両レンズが独立に確認した。
残る所見は本裁定で fix 1 へ寄せる。

## 所見裁定

| 所見 | 裁定 | 採否 / 最小境界 |
|---|---|---|
| C1 / D1 M9i mutant が targetless stage を二重 unlink し `test_m9a_*[attempt]` を巻き添え | real / BLOCKER / scope 内 | **採用 (単一理由へ再設計)**。lifecycle の判定を module 定数 `_EARLY_RETIRABLE_LIFECYCLES` へ単一正本化し、M9i をその 1 行変異にする。両 site が同じ定数を参照するので二重 unlink は構造的に起きない |
| C2 P4 guard の述語が構造的で、公開 gate は意味的。構造正・意味不正の canonical が恒久 `initial_submitted` へ落ちる | real / HIGH / scope 内 | **採用**。guard を「`attempt_state == "valid"` かつ `_validate_job_result_semantics(attempt_value, …)` 成功」へ狭める。受理集合を pre-image 側へ戻す方向で P3 適合 |
| D2 M9g の登録形が事前登録と別物で「等価」主張が反例で崩れる | real / HIGH / 文書 + 登録 | **採用**。plan v2 の M9g 記述を実登録形へ差し替え、等価性主張を撤回する (下記「変異事前登録の訂正」) |
| C3 / D3 T8 の `stage` param が判別力ゼロ。「無変更拒否」が偽 | real / HIGH / scope 内 | **採用**。T8 に `stage=True` 側の filesystem assertion を足し、docstring と裁定文言を訂正する |
| C4 T8 が series あり側を張らず、再走収束が所有外定数に依存 | real / MEDIUM / scope 内 | **採用**。T8 に `clean=True` の param を足す |
| D5 T6 / T7 に登録変異がゼロ。T6 の順序 anchor は pre-image でも緑 | real / MEDIUM / scope 内 | **採用**。retire を preflight 2 本の間へ挿入する **M9h** を新規登録し、T6 の `early-malformed-name` を load-bearing にする |
| D4 T5 の「唯一の制約対象」が過大 | real / MEDIUM / 文書 | **採用**。T5 の位置づけを訂正 (T1 の series 側 witness + 直積終端の記録。順序後半は T3/T4 が張る) |
| D7 M9e / M9g の anchor が 25 行を抱え、純粋な移動であることが機械保証されない | real / MEDIUM / scope 内 | **採用 (限定)**。meta-test へ M9e の純移動検査 (`sorted(splitlines())` 一致) を 1 本足す。M9g は guard 行追加を伴うので対象外と明記する |
| D6 新テストの receipt field assertion が恒真 | real / MEDIUM / 実装しない | pre-image から継承したパターンであり段 5 の新規弱点ではない。4 変異は verifier を触らないので kill 判定は壊れない。**docstring に恒真である旨を明記するに留める** |
| D8 全 mutant で meta-test が必ず赤になる | real / nit | **採用 (記録)**。変異事前登録表へ「全 mutant で meta-test が赤になる (anchor 消失による設計上の性質)」を明記 |
| C5 M9g の記述差 | D2 と同一 | D2 で解消 |
| C6 preflight hoist で fail-closed message の優先順位が変わる | real / nit / 記録 | 受理集合不変。訂正事項へ 1 行記録する |
| C7 registry の `node` が単数で複数期待赤を表現できない | real / nit / 実装しない | 既存 schema の制約。突き合わせは本裁定文書が正本であると明記する |
| C8 / D9 `__pycache__` の mtime と対象 tree 未追跡 | 異常なし / 記録 | `.pyc` は段 5 実装子が申告した `py_compile` と整合。未追跡は統合 commit で解消する |
| D10 埋め込み指示文字列 | 異常なし | 記録のみ |

## fix 1 の実装内容 (単一 worker、所有は 2 ファイル)

### F1. lifecycle 判定の単一正本化 (C1 / D1)

1. `collector.py` に module 定数を追加する。

   ```
   _EARLY_RETIRABLE_LIFECYCLES = ("after-publish",)
   ```

   配置は `_RESULT_STAGING` 等の既存 module 定数の近傍とし、
   「global preflight の直後に回収してよい lifecycle。canonical と同一 inode / 同一 bytes を
   共有するため情報保存的であり、後段の fail-closed 拒否より前に消しても唯一の複製を失わない」
   という理由をコメントに書く。
2. `_retire_after_publish_attempt_staging` の guard を
   `if lifecycle not in _EARLY_RETIRABLE_LIFECYCLES: return` へ変える。
3. `_reconcile_job_results` の in-function apply を
   `if attempt_lifecycle not in _EARLY_RETIRABLE_LIFECYCLES:` へ変える。
   `attempt_lifecycle is None` (stage なし) のときも真になるが、`_apply_result_reconciliation` は
   `stage is None` で即 return するため挙動は不変である。この不変性をコメントに書く。
4. これにより「早期に回収する lifecycle 集合」と「in-function で回収する lifecycle 集合」が
   同じ 1 つの定数の補集合関係になり、二重 unlink は構造的に起こりえなくなる。

### F2. P4 guard を公開 gate と一致させる (C2)

5. `invalid` return 直前の guard を、`attempt_state == "valid"` **かつ**
   `_validate_job_result_semantics(attempt_value, submit=submit, protocol=protocol,
   series_preimage=series_preimage, series=series)` が例外を投げない場合だけ発火させる。
   例外 (`CollectionError` / `QualificationArtifactError`) は握りつぶして guard を発火させない。
6. 理由をコメントに書く: 公開側 `_verify_post_job_receipt` の `pointer_missing_canonical` は
   意味検証後の `canonical_state == "valid"` を要求するため、構造だけ valid な canonical は
   pre-image どおり `job-result-publication-failed` の failure receipt へ閉じるのが正しい。

### F3. テストの補強

7. **T8** に param を足す。現行の `stage` に加えて
   (i) `clean` (`False` / `True`)、(ii) canonical の意味的妥当性 (`semantic-valid` /
   `semantic-invalid`、後者は `wmax_s = 29101` 等で構造は valid・意味は invalid) を張る。
   - `semantic-valid` 側: 現行どおり新 guard message で `CollectionError`、receipt 未生成、
     ledger `initial_submitted`、再走収束。加えて **`stage=True` のとき
     `assert not stage_path.exists()` と `assert canonical.stat().st_nlink == 1`** を必ず入れる
     (C3 / D3。「唯一の複製を壊さない情報保存的 retire を除き無変更」であることの pin)。
   - `semantic-invalid` 側 (**C2 の正例 / 過剰拒否の検出**): guard は発火せず、
     `job-result-publication-failed` の failure receipt へ閉じ、`job_result is None`、
     ledger `initial_failed`、公開 verify valid、再走冪等であることを pin する。
8. **T6** の docstring から「順序 anchor」の過大主張を落とし、M9h が張る旨へ書き換える。
9. **T5** の docstring を D4 の訂正どおりへ書き換える。
10. **T1 / T3 / T4 / T5** の docstring に、receipt field assertion が `collect()` の自己検証から
    恒真に従うこと、独立な証拠は filesystem / ledger / `validate_failure_receipt_for_retry` の
    3 種であることを明記する (D6)。

### F4. 変異登録の更新

11. **M9i** の anchor を `_EARLY_RETIRABLE_LIFECYCLES = ("after-publish",)` の 1 行へ差し替え、
    replacement を `_EARLY_RETIRABLE_LIFECYCLES = ("after-publish", "targetless")` にする。
    期待赤は T9 の 2 param のみ (+ meta-test)。`test_m9a_*[attempt]` は早期回収へ移るだけで
    receipt は同じく publish されるため緑である。
12. **M9h** を新規登録する。anchor は `_preflight_job_result_namespaces` の本体、
    replacement は 2 つの `_reconcile_result_namespace` 呼出しの**間**に
    `_retire_after_publish_attempt_staging(attempt_dir, attempt_preflight)` を挿入した形とする。
    期待赤は `test_cross_namespace_preflight_rejects_before_attempt_stage_retire[early-malformed-name]`
    のみ (+ meta-test)。他 2 shape は attempt 側 preflight が先に raise するため緑、
    `test_cross_namespace_preflight_rejects_before_any_cleanup` は targetless なので緑。
13. registry 追随 (正規表現・`expected` 集合・key 集合・両 dict) を **同一編集単位**で更新する。
    正規表現は `m9h` を捕捉できる範囲へ広げる。
14. meta-test へ **M9e の純移動検査**を足す (D7):
    `sorted(anchor.splitlines()) == sorted(replacement.splitlines())`。M9g / M9i / M9h は
    行の追加・変更を伴うので対象外とし、その理由をコメントに書く。

## 変異事前登録の訂正 (erratum を残す)

`DW-M02` に従い初回の登録を消さず、次を erratum として記録する。

- **M9i 初回登録の誤り**: 段 4 は「guard 2 行の削除」で「`test_m9a_*[attempt]` は緑のまま」と
  宣言したが、in-function 側の targetless apply と二重 unlink になり `FileNotFoundError` が
  escape するため偽であった。両レンズが独立に指摘 (C1 / D1)。fix 1 で lifecycle 判定を単一正本化し、
  M9i を定数 1 行の変異へ再設計する。
- **M9g 記述の誤り**: 段 4 は「`_reconcile_job_results` 内の旧位置へ戻す」と書いたが、実登録は
  `collect()` 内の `_reconcile_job_results` 呼出し直後に `canonical_state` gate 付きで置く形である。
  D2 が「A 構造不正 × after-publish stage × B なし」で終端が異なる反例を示したため、
  **等価性の主張を撤回**し、記述を実登録形へ差し替える。期待赤集合 {T1, T3, T4, T5} は
  両レンズの独立トレースで一致しており、過剰決定の宣言は維持する。
- **全 mutant で meta-test が赤になる**: mutant 適用で当該 anchor が source から消えるため
  `test_fr3_mutation_node_registry_is_exact_and_complete` は設計上必ず赤になる。
  実測との突き合わせでは全 mutant の期待赤に含める。

## 焦点再レビュー 1 の裁定 (`DW-O16` 1 巡目、fix 2 なしで閉じる)

review 正本: `.codex/dev-wave-t126-f32-closure-jobs/s6-focused-review1/output.md`。
判定は **GO (条件付き) / BLOCKER 0 / closed 17 / partial 1 (C7) / regressed 0**。
固定入力は fix 後 `collector.py` `aa6a4f5c19262b40132186d56c3f1a8d9135dec3dfe8e667651b964af50c4c5e` /
test `6d1586ab35f731c18004ee3ce7a9fc7a5cbff51bccff6c3cde3d005597be1735`、
受入は計算 node `874766.nqsv` (bnode033) `441 passed, 9 skipped` / 全 rc=0。

| 所見 | 裁定 | 対応 |
|---|---|---|
| E1 T8 の 8 param 化で M9e / M9g / M9j の期待赤が無記録で拡大 | real / MEDIUM / **文書のみ** | **採用**。下記「変異事前登録の期待赤 (fix 1 後の確定版)」で更新する。コード変更・受入再実行は不要 |
| E2 M9h の anchor 34 行が meta-test との結合を拡大 | real / nit | backlog。成果物影響を 1 行で書けないため must-fix にしない (`DW-G05`) |
| E3 plan v2 の誤記に erratum への前方参照が無い | real / nit | **採用**。s4 へ前方参照を 1 行追加する |
| E4 「`output/insights/` の変異台帳」が未作成 | real / nit | **段 7 で作成**する。変異 matrix 本走の実測から生成するため、本裁定時点では未作成が正しい |
| E5 fix 後にも login node の `.pyc` 痕跡 | 異常なし / 記録 | fix 1 実装子が申告した `py_compile` (2 ファイル) と時刻が整合する。source 変更・所有境界違反はない |
| E6 「参照 site は 2 箇所」の構造保証が機械化されていない | real / nit | backlog。コメントによる担保に留める |

`DW-O16` の 1 巡目で BLOCKER 0 / regressed 0 に到達したため、**fix 2 は起動しない**。
C7 の partial は E1 の追記と段 7 の変異台帳作成で閉じる。

## 変異事前登録の期待赤 (fix 1 後の確定版、`DW-M08` の突き合わせ正本)

T8 は `stage` × `clean` × `semantics` の 8 param、T9 は `payload` 2 param、
T6 は `shape` 3 param である。全 mutant で
`test_fr3_mutation_node_registry_is_exact_and_complete` が赤になる (anchor 消失、設計上の性質)。

| ID | 期待赤 node | 単一理由性 |
|---|---|---|
| M9e | T1、T5、**T8[stage=True, clean=True] の 2 param**、meta-test | 単一理由 = 退避が series 検証より前にある。T8 の 2 param が増えたのは同じ理由 (`clean=True` 側で `verify_attempt` が stage を拒否する) による |
| M9g | T1、T3、T4、T5、**T8[stage=True] の 4 param**、meta-test | **過剰決定を宣言** (`DW-M03` の冗長 gate)。S1 と S2 の両性質を同時に壊すため単一理由 kill の証拠には数えない |
| M9h | T6[early-malformed-name]、meta-test | 単一理由 = 退避が両 namespace の preflight 完了後にある。他 2 shape は attempt 側 preflight が先に raise するため緑 |
| M9i | T9[empty]、T9[complete]、meta-test | 単一理由 = 退避を targetless へ広げない (正例側の過剰破壊検出)。`test_m9a_*[attempt]` は早期回収へ移るだけで終端が同一のため緑 |
| M9j | **T8[semantics=semantic-valid] の 4 param**、meta-test | 単一理由 = fail-closed guard。`semantic-invalid` の 4 param は guard が元々発火しないため緑のままで、これが param の判別力の証明になる |

M9e / M9g / M9j の期待赤に T8 の param が加わったのは焦点再レビュー 1 の E1 による訂正である。
初回登録 (段 4 / 段 6 fix 1 前) の値は消さず、本表を確定版とする (`DW-M02`)。

## 訂正事項 (文書のみ)

- 「無変更拒否」→「receipt / ledger / attempt ledger は無変更。A の bytes は不変。
  after-publish stage は canonical の第二の名前なので回収され、B は rejected-evidence へ保全される」。
- preflight hoist により、series あり attempt に staging 名や inode/nlink の異常がある場合の
  fail-closed message は `series result failed read-only verification` ではなく
  staging 側の message が先に出る。受理集合は不変 (どちらでも receipt 未生成・ledger 不変)。
- `T126_MUTATION_REGISTRY` の `node` は単数 field のため、複数期待赤 node の突き合わせは
  本裁定文書と `output/insights/` の変異台帳を正本とする。
- T5 の位置づけ: T1 の series 側 witness と S1×S2 直積の終端 (`observations_recorded == 2` /
  `retry_eligible is False` / `validate_failure_receipt_for_retry` の raise) の記録。
  「semantic-conflict return より前」の後半を張るのは `clean=False` の T3 / T4 である。
