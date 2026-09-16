## 分岐列挙の完全性

以下、`D`＝`orchestrator/campaign/paper_story_a1_paired.py`、`S`＝同 `paper_story_a1_source.py`、`J`＝`tools/pegasus/paper_story_a1_paired.sh`、`TJ`／`TP`＝`orchestrator/tests/test_paper_story_a1_{job_contract,paired}.py`。`plan` は射影の `s2-plan.md` を指す。静的検査のみで、変更・pytest・変異実行は行っていない。

**[refuted] 指定された分岐以外に、追加解除が必要な pilot 限定分岐は見つからなかった。** `orchestrator/` と `tools/` を指定4パターンで横断検索した。追加ヒットは次のように整理できる。

| 箇所 | 検算 |
|---|---|
| D:1029 | policy 選択。1035行に sized 分岐あり |
| D:1350 | sized 証明書が参照する入力 pilot の識別。sized 自身を pilot に限定する条件ではない |
| D:1440、1510、1695、1714 | `is_pilot=False` の workload・事前登録・sizing inputs 検証あり |
| D:2143、8563 | pilot 用 sizing document の生成条件。sized では呼ばれない |
| `ident.py:48`、`wal.py:122` | sized identity 登録済み |
| `tools/size_paper_story_a1_balanced.py:30`、`tools/verify_paper_story_a1_balanced_sizing.py:30` | sizing の入力 pilot を識別する定数 |

成果物への影響：これらを一律に sized へ置換すると、sizing 証明書の入力参照や pilot 専用出力を誤って変更する。現状維持が妥当。

**[real] `sizing_inputs` は実行 fixture の追加依存になる。** D:1714–1729 → D:1316 の検証は、D:1303 で `_repo_root()` 配下の入力ファイルを実読する。これは production の分岐漏れではなく、後述する fixture 計画の不足である。

成果物への影響：tmp repo に必要な入力がなければ、sized の正例が source 契約検査へ到達する前に拒否される。

## job script と Python の閉包一致

**[refuted] plan の選択方式で閉包の内容・順序・既存 count は維持できる。** plan:170–214 は共通 module・patch を複製せず、契約・追補だけ選択する。追加順序は次のとおり。

1. `orchestrator/campaign/paper_story_a1_source.v2.json`
2. `orchestrator/campaign/paper_story_a1_source.py`
3. `patches/silo-backoff-fixed.patch`
4. `output/insights/2026-09-17/t2590-a1-sized-source-amendment/README.md`

J:74 は基底10＋4、J:450／984 は基底5＋4。D:2230 の対応する閉包と一致する。各箇所で完全な文字列を一度ずつ記載すれば、TJ:435 の pilot `count == 3` と sized の同じ検査を両立できる。

成果物への影響：この方式なら terminal・receipt・driver の path 集合が揃い、pilot 閉包も維持される。

**[refuted] 「順序が違うだけで D:4084–4089 の receipt 照合が落ちる」という説明は成立しない。** binding の `files` は辞書であり、その等値比較は挿入順を比較しない。D:4846 も `set(files) == set(relative_paths)` である。順序維持は I2 の要件として必要だが、この runtime 検査が順序を強制するわけではない。

成果物への影響：順序だけの変異は既存 receipt 検証で受理され得るため、plan:214 の tuple 比較を省くと順序不変条件を証明できない。

## hydrate → staging → measure

**[refuted] plan の分岐置換には、hydrate 供給の構造的不整合は見つからなかった。**

- submit：D:3409–3415 を両 study に適用する計画。
- intent：D:2636 の必須条件を sized 全 attempt に適用。D:2599 は入力を qsub 変数へ載せる。
- job preflight：J:575 で intent と環境変数を照合。
- staging：J:1361 を両 policy に適用し、`$DEPENDENCY_ROOT/fetchcontent` へコピー。
- measure：J:1295／1327 の install path はそれぞれ `$DEPENDENCY_ROOT/{gflags,glog}-install`。D:4939 の解析結果の先頭 `.parent` は確かに `$DEPENDENCY_ROOT` となり、D:7135 の比較と一致する。

実投入受領証 `output/insights/2026-09-11/t2397-a1-attempt4/submission.json:27` にも、hydrate 元として `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2397-a1-attempt4/third-party-hydrated` が記録されている。これは staging 後の scratch path とは別であり、plan は区別している。

成果物への影響：計画どおりなら、sized の各 job に hydrate 元が記録され、measure は対応する scratch 配下だけを受理する。実機成功自体は未検証。

## consumer の amended admission と configure argv

**[refuted] v1 固定条件の取り残しは plan が明示的に扱っている。** plan:129–158 は D:4860 の digest 照合と D:5219 の amended admission 発火を両契約へ広げる。D:5004 の argv 長と D:5030 以降の FETCHCONTENT 4 token 検査は変更しない。

成果物への影響：この二箇所を揃えれば、sized の正しい amended build が旧 argv 長で誤拒否される問題を解消できる。

**[real] plan:306 の「root 不一致なら `amended-source-admission-mismatch`」は、そのままでは誤り。** D:5223–5229 は root の型・canonical absolute 形式を検査するが、configure の `-S` との一致は検査しない。別の正常な絶対 path に変更した場合、一致を拒否するのは D:5030 の `_trace0_commands_match` であり、外側の error は D:5323 の `trace0-source-route-incomplete` となる。

root 変更が「非 canonical 値」なのか「configure と異なる canonical path」なのかを分け、後者には既存の route error を期待すべきである。

成果物への影響：現計画の期待 error のままでは、正しい実装がテストで落ちる。これに合わせて production 検査を増やす必要はない。

## attempt を pin しない設計

**[refuted] `load_contract` が attempt を要求するという懸念はない。** S:26 の loop は patch／policy／preregistration／amendment の4項目だけ。plan:127、139–144 は sized 全 attempt の契約検算・hydrate 必須と、pilot の attempt 制限を分離している。

成果物への影響：v2 に `attempt` がなくても契約を読める。sized は既存の再投入制限に従いつつ attempt 名だけで排除されず、pilot 新規投入の制限は維持される。

**[real] M8 の具体的な変異には注意が必要。** plan:332 の「attempt-0004 照合を sized にも掛ける」を単に pilot 条件の削除で実装すると、v2 の `contract["attempt"]` 参照で `KeyError` になる。

成果物への影響：その失敗を「attempt pin を検出した」と記録すると変異台帳の帰属が誤る。literal `attempt-0004` との比較を加える変異など、登録する操作と期待拒否を一致させる必要がある。

## test の実効性

**[real] sized fixture のコピー集合が不足している。** plan:294 は sized policy／prereg と source 4 path を列挙するが、`policy["sizing_inputs"]` の `pilot_result` と `sizing_certificate` を含めていない。

TJ:3186 の既存 fixture は `_load_policy_for_study` を stub するため submit の限定試験には使える。しかし measure 側では `workload_flags`（D:2267）、`campaign_config`（D:2297）などが `validate_policy` を呼び、D:1303 の tmp repo から sizing 入力を読む。full consumer も D:5372 で同じ検証を行う。これらを実関数で通す fixture には、その二ファイルの実 bytes も必要である。

成果物への影響：不足を放置すると正例が先行拒否されるか、回避 stub により「全層を通した」という被覆が失われる。

**[unverifiable] 計画されたテストが恒真にならないことは、実装前には確定できない。** plan:294–309 は実契約 load、実 `_v3_group_intent`、実 `_validate_arm`、公開 pilot binding の利用を明記しており、方向は適切。ただし materializer を stub する plan:303 だけでは、S:72／78 の study 引渡しを証明できない。plan:265 の「sized で発行した `SourceContext`」の確認を別途成立させる必要がある。

成果物への影響：呼出し引数を確認しない stub では、driver が sized を選んでも materializer 内部が pilot 契約を使う欠陥を見逃せる。

## 変異の帰属

全件未実行であり、KILLED の実測結果はない。

| 変異 | 判定・根拠 |
|---|---|
| M1 | **unverifiable**。literal sized tuple と比較する plan:288 なら独立に検出可能。契約表から期待値も生成すると恒真になる。 |
| M2 | **unverifiable**。S:23 だけを狙うなら、JSON の意味を変えない空白変更等が必要。参照 path を壊すと S:27 に先取りされる。 |
| M3 | **unverifiable**。S:26–28。契約 JSON は固定し、対象の参照ファイルだけ変える必要がある。契約内 digest の変更では S:23 が先に拒否する。 |
| M4 | **unverifiable**。D:2243 の sized 追加だけを落とし、literal tuple を比較すれば帰属可能。 |
| M5 | **unverifiable**。J:450 または984の一箇所を確定し、その production 区間を評価する必要がある。文字列 count だけでは条件変異を検出できない。 |
| M6 | **unverifiable**。J:1361。plan:300 の実区間評価なら staging と CLI 引数の欠落で検出可能。 |
| M7 | **real：説明の修正が必要**。D:5219 を v1 限定に戻すと、正例も FETCHCONTENT 付き argv の長さで落ちる。plan:306 の正例を先に置く単一 node では、不正 admission の固有 error assertion より先に失敗する。 |
| M8 | **real：前節の `KeyError` 帰属問題**。D:3411／7127 のどちらを変えるかと操作を確定する必要がある。 |
| M9 | **unverifiable**。D:2636。直接 `_v3_group_intent` を呼ぶ plan:297 なら submit の先行検査を避けられる。ただし記録済み intent がない欠落ケースを使う必要がある。 |
| M10 | **unverifiable**。TP:4774 と同様に driver の `_validate_source_binding` を通すなら検出可能。`a1_source.binding_matches` だけを直接呼ぶ test では D:4860 の変異を検出できない。 |

成果物への影響：特に M7 は「amended 正例の誤拒否を検出」と「不正 admission の固有拒否を検出」を区別しないと、台帳が証明した内容を過大記載する。複数テストが落ちること自体ではなく、狙った assertion に到達したかが問題である。

## 受入時間

**[refuted] 新規 clone/build 試験を増やす提案はない。** plan:261、300、317 は追加しないと明記する。TJ の `_clone_canonical_ccbench` 呼出しは483行の一箇所で、boundary の parameterize により既存3ケースとなる。計画上の追加呼出しは **0**。

成果物への影響：既存の実 materialization 試験を sized 分だけ倍増する計画ではなく、受入時間への主要な追加負荷は避けている。

**[unverifiable] 5分以内は未保証。** plan:317 自身が保証していない。親の baseline 135.72秒から追加 fixture・選択した campaign tests・受入処理の所要時間までは導けない。

成果物への影響：受入完了・時間上限内という記録は、実受入結果が出るまで確定できない。

## brief の実測値と一般化

**[real] 「現行 sized は7133行で落ちる」は停止順序が違う。** 前段を通過したとしても、D:7127 の study 不一致が先に成立し、7128行で拒否される。7133行はその分岐を修正した後に現れる次の問題である。

成果物への影響：7133行だけを根拠に staging 修正で閉じたと扱うと、sized の受理集合は空のままになる。plan は7127行も修正対象にしている。

**[refuted] `configuration` が今回の hash 原像に入るという懸念はない。** S:50 の直接呼出し先 `s8b_expected_materialization.py:631` は645行で非空文字列を確認し、729行で生成 tree の digest を返す。この呼出し経路ではラベルによる recipe 選択を行わない。

成果物への影響：今回のラベル変更だけでは期待 tree digest は変わらない。ただし別 API の configuration 選択まで無関係とは一般化できない。

**[refuted] pilot の `0ba074…` は live module pin ではない。** 公開 `receipt.json:242–244` の歴史 SHA を確認した。S:34–38 が固定するのは契約・patch・追補の3 digest であり、module SHA は含まれない。

成果物への影響：module の実装変更だけで、この歴史 binding の3 digest 検証が拒否へ変わるわけではない。

**[real／nit] plan:16 の逐語資料訂正指摘は、今回の射影現物と食い違う。** `rulings-verbatim.md:64–71` は既に A-1 の項5で、`docs/decisions.md:60073–60078` と一致する。

成果物への影響：実行受理集合は変わらないため nit。ただし不要な「B-4 取り違えの訂正」を裁定参照の記録に残すべきではない。

## 総括

production の主要分岐について、plan は submit・job・measure・consumer を一貫して扱っている。追加の pilot 限定解除漏れは見つからなかった。

author 前に直すべき点は、**sized fixture の sizing 入力2ファイル、root 不一致の期待 error、M7／M8 の変異帰属**である。加えて、materializer を stub する試験とは別に、内部まで sized 契約が伝わる確認が必要。

現段階で言えるのは静的な計画整合までであり、全層の受理、pilot 回帰不変、変異 KILLED、5分受入は未検証である。