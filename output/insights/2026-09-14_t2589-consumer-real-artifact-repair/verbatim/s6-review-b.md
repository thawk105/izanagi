## 所見

- **real／文書不整合** — `docs/failures.md:23918` は、今回削除した canonical digest 再計算と負例を「恒久対応」として現在も掲げています。今回の修正理由と矛盾し、誤った検査を復活させる誘因になります。過去の事象は残し、この対応が fixture と producer の乖離に基づいていたことを追記するのが妥当です。
- **refuted／契約解決の例外漏出は問題でない** — 通常の公開 consumer 経路では、未登録・非一意・非 ever-active の契約が新しい resolver 呼出しまで到達しません。
  - 未登録・非 ever-active は、先行 admission の activation tuple 検証で拒否されます（`orchestrator/campaign/artifact_admission.py:1309`、`orchestrator/campaign/ident.py:325`）。
  - 非一意は registry の import 時検証で拒否されます（`orchestrator/campaign/env_contract.py:341`、`:380`）。
  - preregistration だけ異なる hash にしても、resolver より前の照合で拒否されます（`orchestrator/campaign/t1998_stock_inline_pair.py:1113`）。admission 側の例外は同ファイル `:977` で構造化拒否へ変換されます。private helper への直接注入を理由とする追加 catch は不要です。

## fixture の忠実性

- **refuted／新しい toolchain 射影の乖離はない** — `_TOOLCHAIN` の各 role は `requested / realpath / version_first_line`、digest の対象はこれに `version` 全文を加えたものです。producer の identity と full-version の二射影に一致します（`orchestrator/tests/test_t1998_stock_inline_pair.py:97`、`:121`、`orchestrator/campaign/buildcache.py:1205`、`:1248`、`:2518`）。role の挿入順は `sort_keys=True` により影響せず、fixture の `allow_nan=False` も文字列だけの対象では差を生みません。
- **refuted／`env_tag` は未使用引数ではない** — `authorize(env_tag)` に使われ、契約由来の WAL tag と launch prefix に反映されます（テスト `:175`、`:200`、`:352`）。ただし、全呼出しが既定値で、上書きするテストはありません。現状は無害な未使用の選択肢です。他環境の受入を保証する証拠にはなりません。

## テストの検出力

- **refuted／新テストは恒真ではない** — テスト `:561` は、次の変異で赤になります。
  - 常に `None` を返す：正常例が失敗。
  - prefix 比較を消す：`--interleave=0` の負例が失敗。
  - `argv[0]` を返す：正常例が失敗。

- **real／検出範囲の限界、nit** — 同テストだけでは、引数 `prefix` を従来の固定 tuple に置き換える変異は生き残ります。ただし、これは Pegasus の空 prefix を使う既存受入テスト `:545` が検出します。
  
  一方、helper `orchestrator/campaign/t1998_stock_inline_pair.py:644` の末尾を無条件の `return argv[len(prefix)]` にする変異は、新テストでは検出できません。prefix だけの argv を与えていないためです。異なる長さの prefix も未検査です。現実装の不具合ではなく、追加ガードを要求する根拠にはしません。

- **refuted／元の誤検査への回帰を許す fixture ではない** — identity 射影からの digest 再計算を戻すと、新 fixture の full-version digest と一致せず、正常受入例が失敗します。片側 digest の乖離も既存テスト `:997` と consumer の arm 間比較 `:1259` が引き続き検出します。

## 参照の取り残し

- **real** — 削除 node は `orchestrator/tests/acceptance_duration_ledger.json:23099` に `0.0` 秒で残り、新 node は未登録です。ただし、**この不一致だけで通常受入は赤になりません**。台帳は収集済み item の所要参照に使い、未登録は unknown cost、余剰 entry は参照されません（`orchestrator/tests/conftest.py:1657`、`:1703`）。台帳テストも schema・内部件数と特定 suite の固定集合を検査するだけで、T1998 の収集集合とは照合しません（`orchestrator/tests/test_update_acceptance_duration_ledger.py:306`、`:368`）。別途、変更後 JUnit に対する台帳生成器の `--check` を実行すれば差分で終了値 1 になります（`tools/update_acceptance_duration_ledger.py:500`）。

- **real／歴史資料として残存** — `output/insights/2026-09-08_t1998-stock-inline-parts/mutation-main-spec.json:203` に削除 helper、`:208` に削除 node が残り、同 wave と T2533 の mutation report にも参照があります。現 HEAD 用の変異仕様として再利用できません。過去実測記録を削除する必要はありません。

- **refuted／実行コードの参照切れはない** — repo 全体検索で、削除した T1998 helper への実行参照は見つかりませんでした。同名の残存例は別モジュールの独立定義です（例：`orchestrator/campaign/s8b_binary_admission.py:84`、`orchestrator/tests/test_calibrator_certify.py:48`）。

## 総括

**実装修正は主張どおりに効くと静的に判断します。** 修正すべき実在の不整合は F909 の現在形の説明です。台帳のずれとテストの未検査境界は、受入失敗・実装欠陥とは分けて扱うべきです。

pytest・変異実走はしていません。緑の報告ではありません。