## 総括

**判定は「作り直し」。** executor の配置以前に、brief の「受理集合を狭める」「実行が書いた証拠だけ」「production 証拠だけで終端到達」という完了条件が、提案する型追加・disk 回収・scope 外の台帳 FSM と整合していない。

指定ファイルの静的読解のみ。テスト・変更・commit は行っていない。以下の A／E／C／L／T／P／D は、提示 plan と同じファイル略記であり、行番号は今回実際に読んだ行を示す。

## 正しさゲートの弱体化

- **must-fix — anomaly の reject と「有効な rejected evidence の発行」を区別した負例がない。** E:710–749 は clean な非直列化・単一の完全 witness・terminal snapshot 一致を要求し、L:794–836 は実行例外を abort にしてから issuer を呼ぶ。単一 anomaly は `accepted` にならず、複数 witness・破損・実行例外は発行拒否になることを executor 経由で固定すべきである。**放置時の影響：33 record の存在だけを見る正例では、未証明の abort が有効な結果として試行台帳へ混入する変更を検出できない。**

- **must-fix — 失敗を「現在の失敗境界へ返す」だけでは終端条件が定まらない。** A:3788–3789 は origin runtime があれば `_complete_origin_runtime` を呼び、A:1892–1898 は formal result を commit する。executor の欠落・予算不足と、この呼出しの関係を明記し、完全実行用の33件検査失敗から `P6Unavailable` へ進まない負例が必要である。**放置時の影響：試行台帳の formal terminal と report の partial／complete が、実行済み件数と整合しなくなる余地が残る。**

## 恒真化の所見

- **must-fix — 同じ wire の2本では source 適用の欠落が恒真化する。** T:392–405 により `source_mask=0` の q0 と q1 は同じ wire になる。plan の生死確認は、source を q ごとに適用する処理を丸ごと省いても成立し得る。異なる mask の追加例と、wire／実 source の不一致負例が必要である。**放置時の影響：33個の identity／layout に同一候補の結果を対応付けても、候補別の実行を材料レポートで主張する誤りを検出できない。**

- **must-fix — summary の identity／root 一致は実行完了の証拠ではない。** L:605–614 は評価ループより前に summary の両値を設定する。これらは配置の整合性検査であり、評価・発行を省いた実装でも一致する。D:867、888 に従い、record と当該 run の実 attempt、native WAL、consumer の lock 再導出まで必要である。**放置時の影響：計画から導いた33 root の存在が、33物理実行の成立として台帳・レポートに投影される。**

- **nit — 相異検査を独立した正しさゲートとして数えない。** D:899–901 は、planned 全件一致と envelope の相異検査が含意する provenance 相異を独立変異に数えないと明記する。plan の完了時再照合にも同じ整理が必要である。**成果物の値への独立した影響は示せず、検証強度の説明を過大にする問題である。**

## 正例・負例の実体性

各行は、plan の stub 方針が証明できる範囲への所見である。

| 対象 | 分類・検査を迂回する条件・成果物への影響 |
|---|---|
| run_campaign／pipeline／issuer | **must-fix** — 本物を使うという宣言だけでは、将来の executor が別経路を使っていても直接呼出しの2-run test は緑になる。L:782、828 が production 評価・発行点。executor 経由の負例がなければ、試行台帳へ渡す証拠の生成経路を検査できない。 |
| build | **must-fix** — synthetic checkout の実 build は production source 適用を通さない。D:712–714、817–819 が要求する wire→source の entry point を別途検査しなければ、候補と無関係な binary の結果が材料になる。 |
| trace | **must-fix** — trace runner の差替えは、実行 binary→観測 trace の因果を切る。本物の verifier を通しても E:715–749 が検証するのは与えた結果と WAL の整合性である。固定 trace により候補を変えても同じ outcome が発行され、物理実行の正しさを証明したように読める。 |
| attestation | **must-fix** — 観測値固定は実環境→receipt の対応を検査しない。E:1238–1253 の照合を通すことは、本番環境の観測成立とは別である。これを混同すると材料レポートの実行環境保証が過大になる。 |
| authority／ledger | **blocker** — 「初期化 fixture」と reserve〜seal の代行を一括にしない。P:10758–10808 は実結果を材料に予約・commit・seal を行う helper である。これを実行後に呼べば事前予約の機構を通らず consumer を進められ、試行台帳の事前 commitment を production 実行の成果と誤認する。 |

## 受理集合の動き

- **must-fix — field 削除だけを集合の縮小と呼べない。** A:466、1689–1692、1882–1883 の削除・置換は、入力インターフェースと証拠の取得元の変更である。C:1411–1413 は引き続き bytes を受けるため、同じ整合的 bytes を disk に置ける主体に対しては、内容の受理集合を狭めた証明にならない。**放置時の影響：「呼び手申告を拒否するようになった」という材料レポートの説明が、実際の受理境界より強くなる。**

- **blocker — 探索 layout の追加は明確な受理拡大である。** E:447–448、1213–1214 の拒否を解除すれば、従来発行不能だった `ExplorationCampaignLayout` から record が発行可能になる。D:848–850 の既裁定3写像に、この exact-type 追加は明示されていない。**放置時の影響：producer の発行可能集合が増えるのに、wave 全体を「狭めるだけ」と記録してしまう。**

  受理型が増えることだけで anomaly 即 reject 違反とは断定できない。ただし「規律2に抵触しない」は未立証であり、探索型でも同じ WAL・witness・attestation の拒否条件が効くことを、追加 scope と負例で示す必要がある。

## 信頼境界

- **blocker — disk 回収は writer 認証ではない。** E:8–10 は create-only が最初の writer を認証しないと明記し、C:20–26 は整合的な lock／WAL の後置きを拒否できないと明記する。E:1438–1469 の regular-file／inode 検査と二度の digest 一致は、内容の安定性を検査しても作者を識別しない。**放置時の影響：呼び手が置いた整合的証拠を「実行が書いた証拠だけ」と説明できてしまい、formal terminal に対する材料上の保証を誤る。**

  「誰でも書ける」という OS 権限の断定は、この読解からはできない。一方、排他的 writer 権限を実装が確立した証拠もない。必須の実 runner と create-only 衝突拒否は維持しつつ、今回閉じるのは **API の bytes 注入経路**、trusted harness の唯一 writer 性は **運用前提**と明記すべきである。

## 名乗りの上限

- **blocker — brief の完了条件は成果物へ効く全層を含まない。** A:1859–1860 は sealed batch を読むだけで、C:668–682 はその digest と record の一致を要求する。さらに A:3773–3780 は positive cell admission、A:3904–3929 は completeness／Layer-3 chain を要求する。D:825–832 は report・registry acceptance まで origin 対応が必要と明記する。**放置時の影響：producer の試験成功を公開 trial の完了と誤読させ、certified 選択・材料レポート・試行台帳まで結線したように見せる。**

  到達上限は、fixture authority／ledger を明記した **production 発行経路から consumer への限定 integration**である。C:3–8、1480 の `P6Unavailable` は正の P6 判定でも certified 選択でもない。

## 裁定パッケージ候補

| 分類 | 決める内容 | 根拠・成果物影響 |
|---|---|---|
| **blocker** | 完了条件を限定 integration に改訂するか、事前 reserve／commit〜seal、origin completion／report／registry まで scope を広げるか。 | A:1859、D:825–832、903–904。試行台帳と report を production 成果と呼べる範囲が変わる。 |
| **blocker** | 探索 layout の明示受理を追加 scope として扱い、維持する拒否述語と負例を確定する。 | E:447、1213。producer の発行可能集合が広がる。 |
| **blocker** | trusted writer を運用前提として残すか、別の変更単位で権限境界を実装するか。 | C:20–26、E:8–10。材料レポートが主張できる証拠の出所保証が変わる。 |
| **must-fix** | 固定 basename 要件を、record の content-addressed ref の検証へ明示訂正する。 | E:1355–1364、1398–1401。consumer が参照する production 証拠の所在と、生死確認の対象を一致させる。 |

## 判定 (plan 採用可 / 部分修正 / 作り直し)

**作り直し。** 完了条件・受理拡大・trusted-writer 前提を確定し、executor 経由で source 不一致、anomaly、発行拒否、予算不足を検出する負例まで含めて再提出すべきである。