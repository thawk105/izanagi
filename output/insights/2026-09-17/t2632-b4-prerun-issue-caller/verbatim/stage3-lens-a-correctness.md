## 所見一覧 (番号・real/plausible/refuted・file:line)

指定資料はすべて読めた。ファイル変更・発行器実行・pytest・変異実行はしていない。以下の **real は文書・コード現物で確認した問題であり、実行で再現したという意味ではない**。

参照略号： [brief](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-prerun-issue-caller/s1-brief.md)、[plan](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-prerun-issue-caller/artifacts/dev-wave-t2632-b4-prerun-issue-caller/s2-plan.md)、[裁定](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-prerun-issue-caller/rulings-verbatim.md)。`issuer`・`ledgers` は指定された `orchestrator/campaign/p3_b4_prerun_issuer.py`・`p3_b4_analysis_ledgers.py`。

1. **real — 親 P1 は所属の根拠を恒真化する。** 「batch に含めたから真」では、事前固定した集合との照合にならない。plan はこれを採用していない。根拠：`brief:35`、`plan:129`、`裁定:89`・`:135`、`ledgers:331`・`:929`。
2. **real — N5 の「成功 precursor は registry 行にならない」は誤り。** SUCCESS は台帳型が受理する結果値で、manifest の適格性で除外される。理由 enum の欠如から登録不可は導けない。根拠：`brief:22`、`ledgers:81`・`:320`・`:926`。plan は `:38` で訂正済み。
3. **plausible — campaign 単位発行の変異が生存する。** 全 campaign が空候補なら、誤実装が最初の発行拒否で終了しても「空 batch・呼出し1回・rc=2」を満たせる。根拠：`plan:172`・`:178`・`:192`。
4. **real — 親 brief は証拠の種類を混同している。** N1・N6 はコード／テスト定義への参照であり、掲載内容だけでは実行実測ではない。空 batch 自体は未実測と明記されている。根拠：`brief:11`・`:13`・`:25`・`:37`。
5. **refuted — plan が不足 field を捏造するという疑い。** 17 field 中12 fieldを未解決として、非空候補は発行前に停止する設計。根拠：`plan:98`・`:135`・`:142`。
6. **refuted — 今回の追加が発行器・台帳の受理集合を広げるという疑い。** 変更禁止と既存発行器への委譲が明記され、緩和経路は見つからない。実装後の確認は別途必要。根拠：`plan:66`・`:75`・`:135`、`issuer:760`・`:766`。
7. **plausible — private 定数との結合は将来の互換性を失う。** `_REPOSITORY_ROOT` の名前・意味に依存する。ただし現状、名指し不一致は拒否され、黙って別 root を受理する形ではない。根拠：`plan:77`、`issuer:194`・`:218`。
8. **refuted — 空 batch 試行が凍結成果物を汚すという疑い。** メモリ内の registry／seed 構築後、書込み到達前に拒否される。根拠：`issuer:818`・`:840`・`:882`、`ledgers:1076`。
9. **refuted／限定 — 通常の単一 component ID なら P4 は予約と衝突しない。** 一方、任意 ID に対する安全性まで一般化できない。現 plan は ID 不足で停止する。根拠：`issuer:186`・`:457`、`ledgers:259`、`plan:164`。
10. **refuted — plan が D1846 の hash を genome 等で代用するという疑い。** 原 proposal document の欠落として停止する。receipt key 除去も、正式 bootstrap の受理文書では差を生まない。根拠：`plan:110`・`:127`、`p3_s4_loop.py:503`・`:2293`。
11. **refuted — 現在の N3・N4 の値が誤っているという疑い。** 本 consult で7行すべて success、gitignore 非該当、publication root 不在を再確認した。ただし親が brief 前に実測したかは、今回の確認では遡及証明できない。根拠：`brief:19`・`:20`、後述の現物位置。

## 捏造の経路

field ごとの検算結果は次のとおり。出所表の「構成可能」は、外部の事実を勝手に埋めることとは区別できている。

| field | 検算 |
|---|---|
| `schema_version` | 既存定数。構成可能。 |
| `attempt_id` | iteration からの規約を捏造せず、未解決。 |
| `registry_ordinal` | argv 順・whiteboard 配列順という呼び手の列挙操作。過去の実行時系列とは主張していない。 |
| `block_id` | 割当根拠なしとして未解決。 |
| `driver` | 3 lock の `trial`／`search_config.axis` と対応。現物と一致。 |
| `reason` | 新たに予定する操作なら `SCHEDULED`。欠落を `CORRUPT` 等で隠さない。 |
| `whiteboard_result` | 現物の exact 値。ただし台帳型へ渡す際は既存 enum が必要。 |
| `digest_red_classes` | WAL と候補の結合がなく未解決。`rejected` だけから補わない。 |
| `workload` | 候補との結合がなく未解決。lock の設定値で代用しない。 |
| `calibrated_workload_member` | 校正済み PerfConfig 欄未記入。未解決。 |
| `initial_proposal_sha256` | 原 document 不在。未解決。 |
| `bootstrap_member` | 事前固定集合との所属証拠なし。未解決。 |
| `reference_tps` | 祖先 certified snapshot と receipt の特定不能。未解決。 |
| `reference_snapshot_hash` | 同じ参照点の特定不能。未解決。 |
| `reference_receipt_hash` | 同じ receipt の特定不能。未解決。 |
| `reference_is_unique` | 祖先関係・同着・PerfConfig／env_tag の照合不能。未解決。 |
| `arm_digest_received` | 個別 precursor の受領記録なし。未解決。 |

根拠は `plan:100–116`、型契約は `ledgers:127–143`。3 lock はそれぞれ `campaign.lock:1` で確認した。

真偽値は質問で強調された3つに加え、**`arm_digest_received` も含めて4つ**ある。plan は後者も無根拠な False にしていない。台帳側は boolean の型しか検査しないため、この扱いが重要である（`ledgers:331`）。

`initial_proposal_sha256` は全理由で必須であり、失敗扱いに変えても欠落を逃がせない（`ledgers:339`）。`reference_tps=(0,1)` も `reference <= 0` で拒否される（`:342`）。

最小の注意点は `registry_ordinal`。今回の順序規則は構成できるが、201超過時の先頭選択に効くため、将来それを「過去から固定されていた順序」の証拠にしてはいけない（`裁定:143`、`ledgers:476`・`:1083`）。現状は非空 batch 自体が停止する。

## P1 の循環と事前固定

P1 の問題は、publication がまだないことではなく、**何を集合として、いつ固定したかが定義されていないこと**である。

「発行対象だから bootstrap_member=True」とすると、任意の proposal に対して登録操作だけで述語を満たせる。発行器はその真偽を再検証しない。発行器自身も `caller_schedule_is_not_bound_to_an_external_authoritative_population` を非保証として掲げる（`issuer:63`）。

ただし、事前登録された root への一度の公開を集合固定の行為として使うこと自体を、今回の資料だけで全面否定する必要はない。その場合でも、対象となる initial proposal の exact な集合、固定時点、実走開始後に追加しない扱いが必要である。**「batch に入れた」の一文では、その契約を代替できない。**

最小是正は、今回 P1 を所属根拠に使わず、plan `:129` の「所属証拠未解決」を維持すること。新しい台帳や gate を作る必要はない。

## 受理集合と発行器結合

plan に沿う限り、発行器・台帳の受理集合が変わる経路は見つからなかった。

呼び手が対象入力を狭めることと、発行器自身の受理集合を変更することは別である。今回の「出所不足なら呼ばない」は前者。真偽値を補完して既存の受理条件を見かけ上満たす経路も、plan は禁止している。

private 結合の対象は関数ではなく `_REPOSITORY_ROOT`。この定数が削除されれば呼び手は壊れるが、現状の名指し検査は必ず `issuer:760` から通る。事前登録の相対 root が変わって caller の固定文字列が古くなれば、`:218` で拒否される。**互換性上の結合はあるが、現物で確認できる黙示的な受理拡大ではない。**

また、N5 の誤りを「SUCCESS を発行器が受理しないように修正する」で直してはいけない。変更するのは親の説明だけでよい。registry の全件保持契約と、manifest の適格性を混ぜないことが最小是正となる（`裁定:121`・`:128`）。

## 空 batch の実発行試行

空 tuple は `ledgers:447` の正規化を通る。schedule count 0 も `:504` で許容される。registry-genesis はメモリ内で生成されるが、適格件数0のため `:1076` で実施不可になり、発行器が `issuer:840` で例外へ変換する。

ファイル書込みは `issuer:882` の `_publish_bundle` より後で、root 作成は `:648`。したがってこの拒否経路では root・registry・manifest・receipt を書かない。乱数生成は行われるが、凍結成果物の変更ではない。

空 batch は fixture 行の投入でも n の切下げでもない。必要数201を保ったまま、不成立を取得する試行である。**許される成果の表現は「実発行器まで到達して拒否された」まで**で、封印発行成功ではない。

なお、既存の不足件数テストは200行を使う（`test_p3_b4_prerun_issuer.py:500`）。それを空 batch の実行実測と呼ぶことはできない。今回も発行器は実行していない。

## planned result path

予約は root 自体と次の5名、および各名の配下である（`issuer:462`）。

- `scheduled-attempt-registry.jsonl`
- `analysis-manifest.json`
- `prerun-issuer-receipt.json`
- `.prerun-issuer-receipt.tmp`
- `raw-record-rejections.jsonl`

通常の単一 component ID に対する `results/<attempt_id>.json` は衝突しない。

ただし `_is_text` は `/` や `..` を禁止しない。発行器は**完成した path** の dot／dot-dot component を拒否するが、単なる `/` は階層として受理し得る。caller が先に path を正規化して `..` を消せば、元の traversal を検出する保証にもならない。P4 を任意文字列 ID に対する安全な規約とは呼べない。

現 plan は attempt ID の出所がない時点で停止するため、この経路は未到達。今回のために ID 規約や防護機構を新設する必要はない。

現物には `namei -l` で `/` から worktree の `output/` まで実 directory が並び、publication root は不在だった。したがって、確認時点の状態なら `_inspect_result_leaf_absent` は root の不在で return する（`issuer:234`）。これは関数を実行した結果ではなく、現物状態とコードの照合である。

## D1846 との整合

plan は whiteboard、genome、src_token、raw file hash からの代用を拒否している。D1846 が要求する block 共有の初期 proposal と異なる対象を登録する設計は見つからなかった。

`plan:127` の receipt key 除去は一見 document exact value と衝突する。しかし、正式 bootstrap loader は `b4_closed_critic_receipt_sha256` を持つ文書を先に拒否する（`p3_s4_loop.py:2293–2298`）。受理される bootstrap 文書では除去対象が存在しないため、canonical hash の対象は変わらない。

この限定を外し、「任意の文書から receipt key を除けば initial proposal と同じ」と一般化してはいけない。今回の最小是正は説明を bootstrap の受理文書に限定することで足りる。原 document 不在を解消したことにはならない。

## 変異の帰属

欠落分岐、真偽値補完、候補選別、終了コードなどは、新しい caller test が直接観測する設計であり、既存 issuer test に KILLED を肩代わりさせる必要はない。

特に欠落テストは rc だけでなく、欠落 field 集合と発行器呼出し0回を確認する（`plan:173`）。他の不足 field に隠れる「True 固定」も、欠落一覧が変化する位置なら検出できる。

弱いのは **campaign ごとの発行**である。例えば、全入力の読取り後に campaign ごとに発行し、最初の例外で終了する誤実装なら、全 campaign が空候補の fixture では正しい実装と同じ観測になり得る。`plan:178` の検出保証は強すぎる。

最小是正は、既存の欠落テストを **先頭 campaign は success のみ、後続 campaign に rejected** という入力にすること。正しい実装は全候補の不足を集計して発行器0回、逐次発行する誤実装は先頭で発行してしまう。新しい production gate は不要である。

変異は未実行なので、いずれも KILLED 実測とは報告できない。

## 親 brief の実測と一般化

| 項目 | 今回確認できたこと／限界 |
|---|---|
| N1 | 不足時に書込み前拒否するコード構造は確認。brief のテスト名だけでは実行ログにならない。 |
| N2 | 3 checkpoint の whiteboard は5 field。3 WAL の payload key 集合にも proposal document はなく、genome／src_token がある。「この checkpoint／WAL から導けない」は支持できる。他の全 artifact の不存在までは一般化しない。 |
| N3 | 本 consult で現物を再計数。base 4、sort 1、trigger 2、全7行 success。親の brief 前の再計数実施そのものは未確認。 |
| N4 | `git check-ignore -v -- output/b4-prerun-publication` は rc=1。`--no-index` 付きでも rc=1。command と現在の結論は妥当。 |
| N5 | enum の読解からの推論が誤り。成功行の registry 受理と manifest 不適格を区別すべき。 |
| N6 | path 引数と予約検査、既存テストの定義は確認。テスト実行や正式 producer との経路一致の実測ではない。 |

N3 の現物根拠は以下。

- `output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/loop_state.json:10,17,24,31`
- `output/campaigns/p3-s5-sort-loop-s5-sort-autonomous-3be89e0d/loop_state.json:10`
- `output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/loop_state.json:10,17`

前 wave の再計数記録は `output/insights/2026-09-16/t2632-b4-red-precursor-stock/README.md:30–49`。今回の現物確認とは区別した。

最小是正は、brief の「実測」を一括表記せず、現物再計数・command 実行・コード読解・テスト定義確認を分けること。親が実施していないと断定する材料もない。

## 総括

**親 P1 は現状の文言では採れない。N5 の説明も訂正が必要。plan は両者を退けており、捏造・受理条件緩和・空 batch による凍結成果物の汚染は確認できなかった。**

plan 側の具体的な弱点は、campaign 単位発行の変異を全 success fixture だけで検出できるという主張。混在入力による caller test の観測で補える。

今回閉じ得るのは、現物から空候補を得て実発行器の拒否を記録する production 経路まで。bootstrap 所属証明、非空 batch の構成、封印発行成功、実走可能性は未解決のままである。