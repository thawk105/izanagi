## 判定と検査範囲

**must-fix 2 件、should 4 件。** 既定 on 化の patch に撤去漏れや必要な防壁の削除は見つかりませんでした。修正対象は主に集計器の入力契約と、事前登録に現れない除外条件です。

指定資料を静的に照合しました。pytest・集計器の selftest・変異は実行していません。親の焦点走は、提供された要約に **1210 passed / 7 skipped、rc=0** と記録されています。

表中の `brief`、`ruling`、`analyzer` はそれぞれ指定された `s1-brief.md`、`s4-ruling.md`、`probe/t2766_adopt_analyze.py` を指します。refuted 行の重さは nit とし、修正要求には数えません。

## 所見

| # | 所見 | 位置 (file:line) | real/refuted | 重さ | scope | 根拠 | 提案 |
|---|---|---|---|---|---|---|---|
| 1 | **段 4 の入力仕様では集計が完了しない** | `ruling:25`; `analyzer:280`, `:301`, `:423`, `:936` | real | must-fix | 内 | 仕様は `arm / tip_tested / started / finished / session_root / leaders_at_go / load1_at_go`。実装は `condition / tip_sha / tip_after / submitted_at / finished_at / session_dir / other_leaders / load1` 等を要求する。仕様どおりの入力では無効走になり、さらに時刻検査で全体が例外終了する。必須 CLI の tip 集合も段 4 に未記載。selftest は実装側の形式だけを使うため、この不一致を検出しない。 | 親の生成形式と集計器を一つの契約に合わせ、段 4 に必須フィールド・時刻形式・CLI を明記する。仕様例をそのまま入力する接続確認を親で行う。 |
| 2 | **bytecode 環境の未記録だけで、事前登録上の有効走を除外する** | `brief:64`; `analyzer:296`; `analyzer:821` 付近 | real | must-fix | 外（根拠未提示の追加除外条件） | `env.PYTHONDONTWRITEBYTECODE_SET != "no"` は値が欠落していても走を無効化する。投影資料の有効走条件にも入力仕様にも、この必須条件はない。これは本番の新 env ではないが、解析上の採否条件の追加である。 | 適用される事前登録の根拠を明示できなければ、値は条件差として記録するだけにし、この除外分岐と対応 selftest を削除する。clean・copy 等の必須条件も入力契約で区別する。 |
| 3 | **「B = A + 採用 commit」と main 移動を許す運用の説明が一致しない** | `brief:12`, `:21`, `:65`; `analyzer:382`, `:723` | real | should | 内 | 集計器は `main_moved` を記録し、移動した対も有効として land 判定に使う。これは実装漏れではなく selftest でも固定された挙動。ただし対内 main が異なれば、一般には B と A の差分は採用変更だけではない。tip 集合への所属検査は、その差分の内容を証明しない。 | A/B を「各走の tested_main に対する採用前／採用後」と定義し直し、移動対を含めることを明記する。親が許容 tip を確認する際、採用変更以外の差分と影響を対表に説明する。main 移動だけを理由とした新 gate は不要。 |
| 4 | **門番条件・他 wave の干渉を記録できなくても有効判定が進む** | `brief:12`, `:68`; `analyzer:277`, `:492` | real | should | 内 | `other_leaders` と `load1` は任意取得で、欠落時も走表に `None` が出るだけ。指定資料には leader ≤ 1・load < 60 の判定時点や、他 wave の識別情報も定義されていない。投入時の数値だけから走行中の干渉がなかったとは言えない。 | 既存の門番ログから、観測時刻・leader 数の数え方・load・分かる範囲の他 wave を記録する。途中の干渉が未観測ならそう明記する。追加の監視基盤は不要。 |
| 5 | **短縮対象を受入待ち全体と読み違えられる余地が残る** | `brief:7`, `:66`; `analyzer:242`, `:480`; `t2766-ab-README-s7.md` の残存限界 | real | should | 内 | 計算しているのは **3 shard の JUnit testsuite time の最大値**。待ち手経由でも queue 待ち、claim、merge、開始ずれ、receipt 等を含む総経過時間にはならない。前 wave の限界説明は明確だが、今回の解析出力にはこの説明がない。 | brief 冒頭と解析 notes に測定対象を明記する。101.7 / 112.9 / 144.3 秒、24.2% は前 wave の限定的観測として保持し、待ち手全体の短縮量に換算しない。 |
| 6 | **P1 の保持は妥当だが「費用は数百 KB 増えるだけ」は根拠を超える** | `brief:26`; `conftest.py:1873`; `test_acceptance_schedule_order.py:1892` | real | should | 内 | 前 wave の択 (a) は property 保持を明示的に許す。既存 property への追記、skip を含む JUnit 到達、B witness に用途がある。一方、4 property/item は転送・直列化・解析にも影響し得る。今回資料には consumer 全体の互換性や時間費用の実測はない。 | P1 は維持し、「数百 KB/shard は前 wave の概算、時間費用・consumer 全体への影響は未実測」と限定する。今回自然に得られる XML サイズは記録してよいが、追加計測 wave は不要。 |
| 7 | opt-out・新しい本番 env/gate・台帳の混入、旧 opt-in の撤去漏れ | `conftest.py:1022`, `:1869`, `:2333`; `dispatch_compute.py:118`; `test_acceptance_schedule_order.py:1843` | refuted | nit | 内 | env/token 定数、opt-in 関数、分岐、allowlist 行、伝播 test は撤去済み。dispatch 本体と test は `947fd160a` との差分ゼロ。旧 env の文字列は、無視されることを検査する指定済み負例に残る。 | 現状維持。負例の文字列や前 wave の保存資料を撤去漏れ扱いして削除しない。 |
| 8 | cardinality・短 queue・hold/selected・配布反例の削除、G8 の弱体化 | `conftest.py:1788`, `:1812`; `test_acceptance_schedule_order.py:1169`, `:1865`, `:1876`, `:1931`, `:1983` | refuted | nit | 内 | cardinality 検算と早期 return は保持。関連保全 test・実配布反例も残る。G8 は pairing を恒等化する目的を明記し、96 位 cost と空台帳時の no-op を保持。G12 の期待 partner 列は固定値。M1〜M5 の検出先も静的には残る。 | 保持する。変異 kill の実測は親で確認する。 |
| 9 | 集計器が本番 helper を oracle にしている、A/B witness・tip 検査が未実装 | `analyzer:92`, `:147`, `:151`, `:182`, `:283`, `:443` | refuted | nit | 内 | 標準 library のみで selected・JUnit・台帳から独立再計算する。A の property 0 件、B の被覆・rank/partner 集合・cost 多重集合・cardinality・worker 件数を検査。arm 別許容 tip 集合への所属と終了後 tip 一致も確認する。 | 保持する。ただし許容 tip の由来・実際の tested tree の確認は親の責任として明記する。 |
| 10 | 無効対再試行・10 走上限・判定枝の欠落 | `analyzer:326`, `:358`, `:405`, `:851`, `:878` | refuted | nit | 内 | 有効対数から次の AB/BA 順序を決め、無効対は同 slot を再試行。最初の有効 3 対、10 走上限、反復不足、閾値未満、符号混在、ゼロ、全対負を扱う。対応 selftest も存在する。 | 判定ロジックは維持。入力契約と除外条件の不一致は #1・#2 で直す。 |
| 11 | 実アンカー表の主要行番号が誤り、P2 が裁定違反 | `brief:20`, `:43`, `:44`, `:45`, `:46`; `verbatim/D2172-item1.md` 項 1 | refuted | nit | 内 | X1 `715bf37b7` の定数・opt-in 関数・reorder 分岐・hook 分岐は記載行と一致。P2 は任意の機序調査を省く選択で、裁定に反しない。A の item→worker witness 不在により機序未同定は残る。 | X1 の行番号を現在の行番号に置き換えて誤訂正しない。A witness は採用の前提に追加しない。 |

## 総括

**must-fix 2 件、should 4 件。** 本番 patch に必須修正は見つからず、集計器の入力契約と未記載の除外条件を先に整合させる必要があります。

brief 自身には、main 移動時の A/B 定義、条件記録の具体性、測定量の限定、P1 の費用断定への所見があります。主要 X1 アンカーと再試行・数値判定規則は整合しています。

削除してよいもの：旧 env/token・opt-in 関数・allowlist・伝播／旧 off 検査の撤去は妥当。根拠を示せない bytecode 環境の追加除外分岐も削除対象です。
削除してはいけないもの：cardinality 検算、unit < 96 の早期 return、hold/selected・既存 property 保全、配布反例、G8 の cost 規則検査、B witness に使う property とその検査。