## 総括

§5 の凍結集合拡張は NO-GO である。既存 18 秒の単一 test は静的見積りで約 5.3〜11 分となり、実 runner の各起動にも約 1.8〜3.7 分の preflight を加える。  
epoch/path literal の列挙自体はほぼ全件で、追加の直接 literal は見つからなかった。ただし重い test の duration pin と、旧 bundle の schema 互換性が表から落ちている。  
段階 2 は旧 amendment のまま受理述語を変更し、段階 4 と 5 の間は新 catalog 不在で確実に赤になる。生成 catalog まで同一 transaction に含める必要がある。  
(P1-a) の「3 索引とも新 ID」は D1432 単独ではなく、D1207 と旧 amendment §8 を合わせれば導かれる。追加再取得は旧走行相当で約 592 request、host pacing だけで直列約 77 分である。  
canonical 比較案そのものは、多重度・group 境界・join・型を保存しており、提示された擬似コードの範囲では妥当である。  
pytest は実走していない。以下は read-only の静的検査と Git tree／旧 bundle の内容集計による。

## 所見

### 1. 凍結集合拡張はテストと本番 preflight の双方を桁違いに遅くする

- **主張:** §5 は scope 外の追加硬化であり、現在の実装方式のまま 2,258 file へ広げてはならない。
- **根拠:** `validator.py:702-737` は各 frozen file ごとに `git show` を別 subprocess で起動する。`test_axis1_search_runner.py:838-873` は全 file の復元、受理検査、末尾 file の変異後検査を行うため、2,258 file では約 6,774 回の file 単位 `git show` になる。現行 128-file node は `acceptance_duration_ledger.json:135` で 18.0 秒。Git tree 実測は 128 file / 2,812,758 bytes から 2,258 file / 102,738,024 bytes への増加だった。
- **帰結:** file 数比例なら `18 × 2258 / 128 = 317.5 秒`、byte 数比例なら約 657 秒、すなわち full acceptance に約 5.3〜11 分を追加する。さらに `tools/run_axis1_search.py:127-132` は各 runner 起動で同じ検査を行うため、1 起動あたり概算 1.8〜3.7 分、最低 263 leaf だけでも約 7.7〜16.2 時間の余計な preflight になりうる。将来、凍結 bundle を累積追加すると線形に悪化する。
- **確度:** 静的推論のみ。18.0 秒は既存台帳値だが、2,258-file 版は実走していない。

### 2. duration ledger の重い node が波及表から落ちている

- **主張:** §5 の test 名または所要時間を変えるなら、表の「duration ledger 3 key」だけでは不足する。
- **根拠:** 現 node は `test_preflight_rejects_mutation_with_real_subprocess_git_and_all_128_paths` (`test_axis1_search_runner.py:838`) で、台帳 key も同名 (`acceptance_duration_ledger.json:135`)。2,258 へ名称変更すれば key の差し替えが必要であり、名称を残せば 18 秒という重みが大幅に過小となる。
- **帰結:** test は赤にならない可能性があるが、xdist scheduler が最大級の node を 18 秒として扱い、受入全走の critical path を悪化させる。
- **確度:** 現物で確認した。

### 3. 実装順序に二つの不正な中間状態がある

- **主張:** 段階 2 と、段階 4→5 の境界は commit／検査可能な状態ではない。
- **根拠:** プラン `stage2-plan.md:189-194` は、段階 2 で旧 epoch のまま条件 1 を差し替え、段階 4 で producer/schema/test path を変え、段階 5 で初めて catalog を生成する。D1432 `:12-14` は amendment なしの比較差し替えを明示的に却下している。また `load_catalog()` は `catalog.py:832-848` で ID 全集合と生成 document の完全一致を要求する。
- **帰結:**
  - 段階 2 を commit すると、旧 amendment／旧 epoch の意味だけを実装側で変更した不正な登録になる。unit test が緑でも契約違反である。
  - 段階 4 後に test path を新 catalog へ向ければ `FileNotFoundError`、旧 catalog を読むままなら新 ID matrix／schema const に不一致となる。新 catalog の生成は段階 4 の epoch transaction に含める必要がある。
- **確度:** 現物で確認した。

### 4. schema の in-place epoch 更新で、旧 bundle を現行 checker から検証できなくなる

- **主張:** 旧 bundle の bytes は保存されるが、現行 CLI による再検証能力は失われる。
- **根拠:** `axis1_search_page_evidence.schema.json:99,105,132`、checkpoint schema `:51` は単一 epoch/path の const である。`verify_bundle()` は常に現行 schema を読む (`validator.py:984-1006,1054-1069`)。`tools/check_axis1_search.py:41-47,85-86` には旧 schema を選ぶ引数がない。旧 page/checkpoint の schema version も新計画で bump されず、page は `v1`、checkpoint は `v2` のままである。
- **帰結:** 新 const 適用後、旧 catalog を明示しても、旧 bundle は epoch/path const で失敗する。旧 bundle を現行 schema で検証する test が無いという brief の主張は正しいが、それは互換性破壊が未検出になることも意味する。
- **確度:** 現物で確認した。

### 5. (P1-a) の結論は妥当だが、根拠の記述が不足している

- **主張:** 現行契約のままなら3索引すべて新 ID・再実行となる。ただし D1432 と旧 §3.1 だけからは導けない。
- **根拠:** D1432 `:3-4` は新 epoch/query ID を要求するが対象範囲を明記しない。D1207 `:3-5` は「新しい query ID・全枝の再実行」を要求し、旧 amendment §8 `:448-454` も意味的 amendment に全枝再実行を要求する。§3.1 `:116` は旧 amendment 自身の「旧 ID は継続しない」という実例であり、単独では一般規則ではない。
- **帰結:** OpenAlex だけ新 epoch にする案は D1208 自体には違反しない。新 successor が旧 bytes を参照することは可能である。しかし現行の母集合定型 (§2 `:81-85`)、単一 `REGISTRATION_EPOCH` (`catalog.py:23,280-315,403-492`)、schema の共通 prefix、`load_catalog()` の完全一致、D1207／§8 の全枝再実行に衝突する。成立させるには multi-epoch catalog と契約の再裁定が必要で、本 wave 内の代案ではない。
- **確度:** 現物で確認した。

### 6. 再取得費用は brief より具体化できる

- **主張:** 旧 arXiv/DBLP 完走部分の再取得は、旧走行相当で約 592 HTTP attempt である。
- **根拠:** 旧 bundle の 593 page evidence を静的集計すると、arXiv 523 attempt（200: 521、429: 2）、DBLP 69 attempt（200: 55、500/503: 14）、OpenAlex 1 attempt だった。契約上の最小間隔は arXiv 3 秒、DBLP 45 秒 (`prior-amendment:438-439`)。
- **帰結:** host 別 pacing 下限は arXiv 約 26.1 分、DBLP 約 51 分。直列なら約 77 分に HTTP latency・backoff が加わる。OpenAlex 全体は別途、旧実行記録を訂正した最低 154 request・2 quota window 以上 (`blocked-insight-README.md:90-96`)。旧走行形を合わせると全体の planning baseline は少なくとも約 746 attempt だが、件数 drift の上界ではない。
- **確度:** 現物で確認した。

### 7. runner fallback helper 化は本題ではなく追加硬化である

- **主張:** `runner.py` の16 fallbackを「epoch 欠落なら拒否」へ変える部分は scope 外である。
- **根拠:** production CLI は `load_catalog()` を通し (`tools/run_axis1_search.py:137-155`)、同関数は生成 document の完全一致を要求する (`catalog.py:846-848`)。したがって production catalog の epoch 欠落は既に拒否される。新 helper が新たに閉じるのは主に内部 fake／直接 API 呼出しの malformed catalog 面である。
- **帰結:** 本 wave に必要なのは新 epoch への追随であり、欠落 catalog の新しい fail-closed gate と負例追加は別 hardening として分離すべきである。
- **確度:** 現物で確認した。

### 8. canonical 比較の設計には、指定された弱体化反例は見つからない

- **主張:** 擬似コードどおり実装される限り、順序以外の差を吸収しない。
- **根拠:** `stage2-plan.md:28-92` は tag 付き tuple、exact key set、exact `str` 型、非空 list、group wrapper、join 値を保持し、set 化・flatten・invalid sentinel 化をしない。
- **帰結:** 多重度、入れ子、`and`/`or`、欠落と `None`、未知 key/join は区別される。実装時には expected/actual 双方への同一 helper 適用と、plan 記載の負例を維持すればよい。
- **確度:** 静的推論のみ。

## epoch 波及の独立検算

| 項目 | 検算結果 / プランとの差分 |
|---|---|
| 完全形の検索数 | プランどおり 1,554 files / 16,903 matches。`output/insights` は 1,541 files / 15,796 matches。 |
| mutable な直接 literal | `catalog.py`、`runner.py`、`validator.py`、schema 3本、axis1 test 2本、CLI 2本、mutation test 2本、duration ledger、README。プラン表以外の直接 literal は見つからなかった。 |
| 旧 path を key にする束縛 | catalog `amendment_path/supersedes`、schema const、validator/checker/runner CLI defaults、test catalog pathを確認。プラン表で網羅されている。 |
| parametrized node pin | mutation pin 2件 (`test_mutation_fanout_contract.py:591`、`test_mutation_harness.py:1057`) と duration ledger 3件 (`:143-145`) を確認。追加の epoch 付き xdist group pin は無かった。 |
| 内容走査型一覧 | acceptance duration ledger の heavy frozen test key (`:135`) が§5変更から漏れている。rename しなくても duration 値の再計測が必要。 |
| 生成 bytes pin | `test_axis1_search_catalog.py:101-108` の `render_catalog_json()` 完全一致だけ。旧 catalog digest／size を mutable code側で pinする箇所は無かった。 |
| schema 世代 | epoch const は全件あるが、schema version を据え置くため旧 bundle と新 bundleを版で識別できない。この互換性判断が表に無い。 |
| 歴史記録 | 旧 amendment/catalog/execution、旧 bundle、`docs/paper-story/2026-09-02.md:797` 等は旧 epoch の記録なので置換しない判断で正しい。 |
| §5 test 名 | `all_128_paths` を `all_2258_paths` に直す場合、duration ledger key も変更対象。名前を残すなら意味が偽になる。 |

## 新 amendment の節構成

| 旧 amendment 節 | 新版での扱い | 落とした場合 |
|---|---|---|
| header・凍結宣言 | **置換**。新日付、入力 commit/path、D1432、直前 amendment の supersede、新 catalog pathを記載 | 新版の由来と凍結境界が消える |
| §0 / §0.1 | 原則を継承し、**開示を置換・追加**。旧結果を見た後の変更、92/92 の観測、RW1・不在を作らないことを明記 | prospective 性を偽装する |
| §1 | **全面置換**。2026-08-29 amendment のどの節を継承・置換するかを新たに列挙 | successor の意味が閉じない |
| §2 母集合 | 文言を継承し、epoch と exclusion IDを**置換** | 母集合の1行定型が旧 epoch のままになる |
| §3.1 | **置換**。新 epoch、ID形、旧 ID/evidence非継続 | ID migration が曖昧になる |
| §3.2 | **逐語継承** | arXiv/OpenAlex の論理枝が変わりうる |
| §3.3〜3.4 | shard・除外・境界規則を継承し、IDのみ置換 | shard 母集合、D1155 の唯一の除外、2走義務が壊れる |
| §3.5〜3.6 | **逐語継承** | DBLP 条件1と263 leaf/267 logical の契約が落ちる |
| §4.1〜4.5 | 日付付き観測として**逐語継承**。再測していない旨も残す | quota、retry、host pacing の実行契約が消える |
| §5 全体 | **逐語継承** | index work ID、multiplicity、family層、日付判定が変わる |
| §6 | **逐語継承** | control・補助探索・感度監査の義務が消える |
| §7 条件1 | arXiv/DBLP は逐語継承。OpenAlex bulletのみ**置換**し、implicit `and`、`and/or` sibling multiset、group境界、未知値 fail-closed を明記 | D1432 を実装しても契約に反映されない |
| §7 条件2〜6、§7.1〜7.2 | **逐語継承** | 完走述語または最上位導出式が弱くなる |
| §8 | 原則を**逐語継承**し、今回 D1432 の手続きを満たす旨を追加 | 次の意味変更で新 epoch/全枝再実行が不要になる |
| §9 | 一覧を継承し、旧 IDのみ置換 | 「母集合の外」を落とす明示禁止に違反 |
| §10.1、§10.3、§10.4 | **逐語継承** | evidence、DBLP二重判定、manifest exact-set が壊れる |
| §10.2 | 一般 checkpoint 契約を継承。旧 checkpoint 固有段落を**置換**し、2026-08-29 epoch の証拠を新 epochへ算入しないと明記 | 旧 checkpoint の継続可否が曖昧になる |
| §11 | 旧開示を保持し、新たな92頁観測、T-2090診断、D1432を**追加** | outcome-informed な改訂経路が隠れる |
| §12 | 既存限界を継承。旧 README 未掲載の記述は置換し、旧 bundle の現行 checker互換性と fresh bundle条件を追加 | 実在する制限を隠す |
| §13 | U10を D1432 で解決済みとする。U7/U8/U9/U11は別裁定なしに落とさない | 未裁定事項を暗黙に解決してしまう |

## 親 brief の誤り

- **file:line:** A1、A2、A3、A6、A8、3 call site、停止分岐、`_canonical_query_object` の行は現物と一致した。A4 は `supersedes`、A5 は schema `:33,450`、A7 は page schema `:105`、A9 は多数の test literalを落としており、不完全だった。
- **183 leaf:** arXiv 171 / DBLP 12 は正しい (`prior-execution:71-76`)。
- **36,179 ID:** 3索引全体の値としては正しいが、完走183 leafの値ではない。内訳は arXiv 31,500 + DBLP 4,479 = **35,979**。残り200は未完走 OpenAlex Q1 の1頁分 (`prior-execution:82-90,121-140`)。
- **98.5 MB:** 旧実行記録の bundle 総量 98,570,351 bytesとして正しい。新 frozen path 全体は Git tree 実測で102,738,024 bytesであり、同じ値ではない。
- **(P1-a):** 結論は D1207＋旧 §8を含めれば正しい。brief の「旧 §3.1 の先例」だけでは根拠不足。
- **(P1-b):** 擬似コードどおりなら妥当。
- **(P1-c):** 「新 epoch なら fresh bundle」は誤り。`runner.py:1591,1625` は渡された bundle 内の `state/runtime.json` を読むが、CLI `--bundle` は新規／空を強制しない。
- **(P1-d):** 現行の単一 epoch/schema/exact identity 契約では正しい。
- **「既存被覆は純増」:** 登録済みの正しい expected OQO を前提にすれば正しい。`evaluate_page()` の任意入力面では、両側が同じ未知 join/key のケースを新 helper が拒否するため、無条件の純増ではない。
- **「旧 bundle を現行 schema で検証する test は無い」:** 検算して正しい。そのため schema 更新後の旧 bundle 非互換も捕捉されない。

## 裁定候補

1. **旧 bundle の現行 checker 互換性を保存するか。** 保存するなら versioned schema／epoch別選択が必要で、本 wave の単純 const 更新を超える。保存しないなら新 amendment §12 に限界を明記する。
2. **§5 の凍結集合拡張。** scope 外の硬化であり、現方式では性能上も不適。別 waveで batch Git object 読出し等へ設計し直すことを推奨する。
3. **runner の epoch 欠落 helper。** malformed catalog の一般 hardening なので別 waveへ送るのが妥当。
4. **multi-epoch 継承案。** 技術的には新しい母集合・schemaを設計できるが、D1207／旧 §8 の全枝再実行を覆す追加裁定が必要である。