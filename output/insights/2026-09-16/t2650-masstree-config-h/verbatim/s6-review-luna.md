## 新しい import 辺の健全性と private 関数の跨ぎ使用

- **主張:** 現行経路で循環初期化や新たな実行副作用を起こす根拠はない。private 関数の跨ぎ使用は結合を増やすが、本 wave では裁定どおり。
- **根拠:** `s8b_floor_campaign.py:3475` は関数内の相対 import。`p3_s4_loop.py:63` 以降で依存 module をロードするが、同 module 自身のトップレベル処理は定義・定数・正規表現などで、実走は `:2889` の main guard 内。既存の `s1_direct_comparison.py:842` も全 `prepare_cell` 呼出しで同 module を import している。import invariant の制約は名前空間・path・bootstrap・相対 import（`test_campaign_import_invariant.py:31`、`:1238`）で、今回の辺は適合する。
- **成果物影響:** 初回ロードが prebuild 後へ前倒しされる。既存の実 cell 経路に新しい module 群を追加する変更ではない。import 時間は未計測。
- **重大度:** 情報。
- **是正案:** 本 wave の変更は不要。共通 helper への所有替えは設計上自然だが、裁定が既存生成器の利用を指定しており、今回の必須修正にはしない。

## dependency_prefix 分岐の実在と token 数の整合

- **主張:** `prepare_kwargs` に `dependency_prefix` が入る現行経路はない。`.get(...)` の非空値側は到達不能で、token は 4 本。
- **根拠:** 辞書の構築は `s8b_floor_campaign.py:3415`、追加は `:3422` の 3 source dir のみ。`:3481` は常に空文字を取得する。生成器は `p3_s4_loop.py:363` で非空 prefix の場合だけ 1 本追加し、`:369` で本数を確認する。テストは `test_s8b_floor_campaign.py:3834` および `:3893` 付近で 4 本を pin する。
- **成果物影響:** 現行の 4 本 assertion と矛盾しない。ただし optional な入力経路が存在するように読める。環境変数 `CMAKE_PREFIX_PATH` の存在とは別問題である。
- **重大度:** 低、可読性上の指摘。
- **是正案:** `dependency_prefix=""` と明記すれば現行契約が明瞭になる。将来向け分岐のための検査新設は不要。

## 搬送 field が identity / receipt へ漏れていないか

- **主張:** 永続 identity／dependency receipt への漏入はない。ただし Python の自動生成 hash と、postflight 再構築は区別が必要。
- **根拠:** `cache_receipt()` は `s8b_floor_campaign.py:2150`、`private_dict()` は `:2156` の明示射影で、新 field を含まない。永続 dependency receipt は `:4322` でその射影を使用する。materialization identity も `s8b_materialization.py:117` の明示辞書から導く。`replace(binding, ...)`（floor `:3323`）は搬送値を保持する。一方、postflight の `replace(after, ...)`（`:4022`）は搬送値を復元しないが、呼出し側 `:4575` は戻り値を採用しないため、次 cell の binding は失われない。
- **成果物影響:** 保存 schema・cache identity は変わらない。名指しすべき全 field hash は、`@dataclass(frozen=True)` の **`_FloorOracleDependencyBinding` 自身**（`:2128`）が生成する Python `__hash__`。新 field は equality/hash に参加するが、この hash を永続同一性へ利用する経路は確認されなかった。
- **重大度:** 情報。
- **是正案:** 現行成果物への修正は不要。postflight の戻り値まで搬送値が保持される、と説明してはならない。

## 生成タイミングと例外経路

- **主張:** 生成時点で 3 source dir は確定済み。prebuild 失敗から不完全 binding が cell へ流れる経路はない。
- **根拠:** `s8b_floor_campaign.py:3397` で staged sources を検証し、`:3422` で入力を確定、`:3427` で prebuild。失敗は `:3428` 以降で例外化される。source／payload 検証（`:3457`、`:3467`）後に引数生成し、canonical materialization 後の `:3493` だけで返す。cell ループは `:4339`。prebuild 本体も `buildcache.py:2090`、`:2096` の configure/build 成功後に返る。
- **成果物影響:** 失敗時に下流 build が進むことはない。新しい import／生成器自体の例外は既存 preflight 診断変換の外側なので、その場合は通常例外として停止する。
- **重大度:** 情報。現行入力で新たに発生する例外条件は確認できない。
- **是正案:** 不要。

## 他 campaign 経路への波及

- **主張:** 他 consumer の引数・receipt を変更しない。`paper_story_*` が同じ `prepare_cell` 経路を使うという前提は、そのまま一般化できない。
- **根拠:** 追加引数は floor 内 closure の `s8b_floor_campaign.py:4364` に限定される。共有 API の既定値は `s1_direct_comparison.py:836` の空 tuple のまま。oracle は `s8b_oracle_driver.py:721` から共有 materializer、共有側は `s8b_materialization.py:133` で従来の引数を渡す。pilot は `s8b_oracle_n_pilot.py:936` の独自 wrapper を維持する。paper story の依存準備は `paper_story_a1_source.py:85` の pristine 検証と `:90` の直接 prebuild、configure 引数は `:99` の独自生成。A2 の floor 利用も `paper_story_a2_certification.py:3682` の pristine 検証である。
- **成果物影響:** floor closure を経由しない呼出しの設定・receipt は変わらない。
- **重大度:** 情報。
- **是正案:** 不要。

## 裁定違反の有無

- **主張:** 実装 scope の逸脱はない。記録文言の裁定違反は次節の 1 件。
- **根拠:** commit の変更対象は floor 実装・既存テストの 2 ファイルだけ。prebuild 条件は `s8b_floor_campaign.py:4270` の sort を含む production campaign のまま。既存 build 起動点は `buildcache.py:2096`。裁定の禁止対象は `ruling.md:77`。正負例は `test_s8b_floor_campaign.py:3900` 以降で、base/source 分離も実装されている。
- **成果物影響:** 非 sort 単独 campaign への prebuild 新設、Pegasus script、materializer 登録簿、新しい build 起動点への変更はない。
- **重大度:** 情報。
- **是正案:** scope に関する修正は不要。

## commit message の主張と実装の一致

- **主張:** **「受理集合は変えない」は不正確で、採用済み裁定の文言訂正を反映していない。** reason code の定義と sort 限定 build 注入が不変という部分は一致する。
- **根拠:** `ruling.md:9` は「判定規則は不変、依存欠落による検査不能を解消」への訂正を採用済み。実装は `s8b_floor_campaign.py:4364` で検査入力を変える。追加テスト自身も `test_s8b_floor_campaign.py:3960` と `:3967` で供給時の green／欠落時の `preprocess-failed` を対照にしている。sort 限定 build 注入は floor `:4446` 以降で維持され、判定器・reason code 定義には差分がない。
- **成果物影響:** commit 履歴が、検査不能だった入力を検査可能にする修正を「受理結果まで不変」と誤読させる。実装不具合ではなく、変更の意味を記す成果物の不正確さ。
- **重大度:** 低。ただし明示裁定への追従として訂正対象。
- **是正案:** 「**判定規則・reason code 定義・sort 限定の build 注入は維持し、依存欠落による検査不能を解消する**」へ修正する。

## 総括

実装の must-fix は確認されなかった。訂正対象は commit message の「受理集合不変」。`.get("dependency_prefix", "")` は現行では常に空となる冗長な表現である。

静的レビューのみ実施。pytest・実機 campaign の成功は確認していない。