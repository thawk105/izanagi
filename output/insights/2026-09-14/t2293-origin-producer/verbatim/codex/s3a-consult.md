## 総括

**判定は「作り直し」**。現 plan は障害調査としての材料はあるが、実装・受入まで閉じた計画になっていない。特に、探索 issuer の修正、生死確認、台帳遷移、supervisor への返却契約の依存順が未確定である。

また、**P6Unavailable 到達と公開 trial の `complete` は別条件**であり、plan はこの区別を一部混同している。指定ファイルと引用先を静的に読解した。変更・テスト実行はしていない。以下の A/E/C/L/T/H/P/F/I/D は plan と同じ略記を用いる。

## plan の file:line 検証

主要な引用の照合結果は次のとおり。誤差だけで成果物への影響を示せないものは nit とした。

| 判定 | 引用 | 現物との照合 |
|---|---|---|
| 一致 | A:3938、3951–3991、3995–4028、4062 | 関数位置、認可検査、cfg 解決、単一 layout、generation loop は記述どおり。 |
| 一致 | A:4895、4901、4913、4920、4942、5087、5156 | 導出→envelope→永続化→digest→lifecycle→observation→scope の順序は一致。 |
| 一致 | A:449–491、1689–1692、1840–1889 | 入力・runtime・caller bytes の転送は記述どおり。 |
| 一致 | A:1238、1271–1332、1388–1398、1739、1782–1795 | identity 導出、plan 束縛、capability 発行と launch digest の出所は一致。 |
| 一致 | A:3027–3041、4840 | reservation preflight は trial 全体の時間を受け、呼出し側は戻り値を保存しない。 |
| 一致 | A:2352、4361、H:734、768–820、1005 | 既存呼出し鎖と source 適用位置は一致。H の呼出しに `output_root` と evidence context はない。 |
| 一致 | E:240–254、447–448、1213–1214 | context は **14 field**。探索 layout を拒否する exact-type gate は両方に実在。 |
| 一致 | E:959–968、1157–1171、1353–1405 | record の決定的 path と provenance の content-addressed 配置は一致。 |
| 一致 | E:1421–1470、artifacts:224、244、250 | path 正規化、regular-file read、writer の fsync/read-back は実在。 |
| 一致 | C:393–415、633–682、778–799、1364–1480 | envelope、sealed member、record、terminal の照合位置は一致。 |
| 一致・解釈要修正 | C:1113–1130 | JSON parse・digest・`ordered_passes` 検査はあるが、**canonical bytes への再符号化一致検査はない**。「同じ canonical parse」を新設すると既存述語の維持ではなくなる。 |
| 一致 | P:10634–10696、10754–10804、10933–11032、11085–11089 | 物理証拠の後付け、台帳 seal、入力注入、観測 wrapper の所在は一致。 |
| 一致 | P の列挙された9 test の定義位置、10520 | 関数名・行番号は一致。 |
| 一致 | I:112、319–374、433、543 | synthetic checkout、観測注入、official 指定、実 issuer test の位置は一致。 |
| 一致・根拠不足 | D:572–586、645–647、903–904 | その記述は実在する。ただし「未存在」の設計記述だけでは、現在の実装不在を再実測した証拠にならない。 |
| nit | P:10364、互換 test:134 | 前者は helper 定義で、`evidence_path` 代入は **P:10371**。後者は `_origin_enabled_bundle` 内の呼出し位置。成果物への直接影響なし。 |

**親 brief の引用訂正：**

- **nit** — P:11116 は `_finish_trial` の monkeypatch。`_run_workload` は **11117**、その wrapper は **11085–11089** で本物へ委譲する。行番号の訂正自体による成果物変化はない。
- **nit** — `CampaignSummary` の field は **L:63–64**。親の L:62–63 はクラス定義を含み、`layout_root` を含まない。
- **nit** — golden literal は **test_reflux_result_evidence.py:36–39**。親の24–27は import。
- **nit** — 親の R3 範囲 E:1196–1341 は、実際の durable write **1388–1405** を含まない。

## blocker 所見

1. **blocker — 探索 issuer 修正を scope 外へ返したまま、成功を executor 着手条件にしている。**  
   根拠：L:451–452、542 → E:1213–1214、447–448。現コードで生死確認が失敗することは静的に判明しており、「まず試す→失敗なら停止」では予定された修正へ進めない。  
   **成果物影響：探索 run の result-evidence は発行されず、formal receipt と試行台帳の evidence 参照を生成できない。**

2. **blocker — reserve/commit/seal を scope 外にしたまま、実行証拠から終端へ進む接続先がない。**  
   根拠：A:1859–1860 は読み取りのみ、C:668–682 は sealed member の digest と record の対応を要求する。P:10754–10804 はその遷移を test helper で補っている。active batch の不存在と seal の不存在は、一連の未実装遷移として扱うべきである。  
   **成果物影響：33 record ができても対応する sealed batch がなく、FC01 で拒否され、P6Unavailable の receipt を得られない。**

3. **blocker — 「既存 gate を維持する origin entry point」が実装可能な契約まで降りていない。**  
   根拠：H:765 の proposal 検査、781–797 の template・quarantine・auditor・condition gate。plan は planner/auditor の供給元を未解決のまま、A:4021 直後から直接物理実行へ分岐する。  
   **成果物影響：実装不能で証拠が出ないか、gate を省略して従来拒否対象を実行・証拠発行する受理集合へ変わる。**

4. **blocker — 公開経路の返却値・失敗処理・会計の契約がない。**  
   根拠：A:4038–4045 の既存 cell 初期化を飛ばす一方、A:3051–3053 は単一 `campaign_root`、3784–3789 は admission と formal completion、3792–3795 は generation 列からの計測集計を要求する。plan の「その結果を return」では足りない。  
   **成果物影響：33 run の時間が集計されない、報告が partial/例外になる、または一つの root を33本の代表として誤参照する。**

## must-fix 所見

1. **must-fix — 生死確認は leaf の確認であり、R1/R3 の supervisor 結線確認ではない。**  
   根拠：提案 test は I:413 相当の `run_campaign` 直呼び。R1 は A:4913–4943、実際の workload への転送は A:3608–3610。  
   **成果物影響：leaf test が成功しても、envelope に束縛された実行証拠が公開 trial から生成されることは証明されず、台帳参照の出所保証が残る。**

2. **must-fix — 既存公開正例の移行を「helper の変更」で済ませられない。**  
   根拠：P:11041–11047 は `generations=2`、fixture provider、`sub="/unused"`、`do_build=False`、fake drive。互換 test:1261–1265 は origin-enabled と generation-two の比較を行う。  
   **成果物影響：この設定のままでは物理証拠を生成できず、公開正例の `complete` と終端参照を維持できない。実 build 用入力と origin report 契約の設計が必要。**

3. **must-fix — 完了到達と報告成功の因果関係を訂正すること。**  
   根拠：formal completion は **A:3789**、completeness 検査は **3902**、Layer-3 chain は **3920**。後段の失敗だけから「P6Unavailable に到達不能」とは言えない。  
   **成果物影響：台帳 terminal の commit 後に報告保存が失敗する可能性があり、terminal と公開 report の整合性を取りこぼす。**

4. **must-fix — 失敗時にも全件 disk 回収へ進む経路を設計すること。**  
   根拠：A:3611–3655 は workload 例外を cell に変換し、A:3788–3789 は origin completion を無条件に呼ぶ。  
   **成果物影響：途中停止で未生成の record を再読して別例外になり、最初の失敗理由や実行済み prefix が報告・台帳から失われ得る。**

5. **must-fix — 「production 証拠だけを consumer が受ける」は API 全体の性質にならない。**  
   根拠：C:1376 は bytes 引数を維持し、C:1386–1388 は writer identity を証明しないと明記している。field 削除は A:1882 の供給経路を閉じる変更である。  
   **成果物影響：supervisor 経由の受理経路は狭まるが、formal consumer 直接呼出しの受理集合は残る。名乗りを supervisor 経由に限定する必要がある。**

「結線できない部分」の全行を再分類すると次のようになる。

| 項目 | 分類・反証 | 放置した場合の成果物影響 |
|---|---|---|
| 探索 layout | blocker。E:1213、447 の実障害 | record 未発行 |
| 固定名 provenance | **must-fix。要件不整合であり、consumer 到達の本質的 blocker ではない**。E:1355–1364、C:953–981 | 誤った path を検査して正当な出力を不合格にする |
| 予約済み batch | blocker。A:475–491、T:435–448 | 実予約に対応しない batch 参照 |
| disk→sealed batch | blocker。A:1859–1860、C:668–682 | FC01、receipt 不成立 |
| 残時間保証 | must-fix。A:4840、reservation:105–116。**開始前検査だけでは実行時間上限の保証にならない** | 予算超過・途中 prefix の扱いが未定義 |
| wire→source | blocker。H:765、781–797 | gate 脱落または実行不能 |
| attestation→ctx | must-fix。required は loader 配線可能。optional は L:184–198 で receipt がなく、E:1245–1253 に届かない | 対象環境によって record 未発行 |
| production CLI | 本番発火には blocker。A:5475–5498。**API integration の blocker とは別** | 現 CLI の成果物は originless のまま |
| generation metadata | **nit：そのままでは blocker とする根拠なし**。A:1520 は2を保持すれば通り、D:811–813 は別の33本反復を指示 | 分離を守れば成果物への悪影響なし |
| completion/report | 公開 complete には blocker。A:3051、3902。P6 到達とは区別が必要 | 報告・計測・terminal が分離 |
| P6 自体 | **nit：今回の目標に対する blocker ではない**。目標そのものが C:1480 | P6Unavailable を成功した P6 と扱わなければ問題なし |
| authority/FSM/renderer/実測 | 複数項目を一括した scope 宣言。A:1859、D:645–647 | 本番発行や材料レポートへの反映を名乗れない |

## nit

- **nit — 一覧は11件ではなく12行。** 最後は複数の scope 外項目を束ねている。件数訂正による成果物変化はない。
- **nit — 段5の組替え案は、列挙済み path に限れば排他になっている。** A:462、1840、4022 の所有をすべて単位Aへ移したため、親案の同一ファイル競合は解消する。ただし「対応する evidence/consumer test」は具体的 path として確定し、B の loader/context 契約確定後に A を接続する依存順が必要。現時点で成果物への具体的悪影響は未確定。

## 親 brief への所見

- **blocker — 「欠けているのは executor だけ」は現物と合わない。** E:1213、A:1859–1860、H:781–797 が別々の接続不足を示す。放置すると33本反復だけ実装しても evidence→terminal の受理経路が成立しない。
- **must-fix — 物理 root の生成主体が誤っている。** F:688–742 は合成 WAL/provenance、F:745–784 は fixture tree。campaign root・lock・固定名 provenance を作るのは P:10634–10696。誤った helper を除去対象にすると、後付け証拠経路が残る。
- **nit — 否定の再確認範囲を限定して記録すべき。** 非test の Python/shell 検索では `run_origin_trial` は A:5282 の定義のみ、context は L 内部参照のみ、`_execute_origin_topology` は一致なしだった。これは静的な直接参照の確認であり、動的呼出しを含む全経路不存在の証明ではない。
- **nit — 374〜908秒、authority 0件、発行条件0/3を今回の実測として再認定できない。** 指定された実装と設計文書だけでは測定ログ・現 authority の独立確認にならない。これらによる現在値の変化は主張しない。

完了判定は、例えば次へ明示的に書き換える必要がある。

> fixture authority と test が行う正規の台帳遷移を許す。空の実行 root から、production executor・runner・issuer が33本の lock/WAL/provenance/record を生成し、supervisor が disk から回収した証拠で formal consumer が P6Unavailable に到達する。合成した物理証拠の注入は禁止する。本番 CLI、production provisioning/FSM、公開 report の complete、性能実測は別の到達条件として管理する。

これは既存期待値の緩和ではなく、**新しい受入条件の境界の訂正**である。既存公開正例と互換性 test を維持する方法は、別途解決しなければならない。

## 裁定パッケージ候補

1. **blocker：探索 evidence producer の受理型を scope に含める。** E:447、1213 の明示対応を先行し、official と originless の既存制約を維持する。影響は探索 evidence の受理型集合。
2. **blocker：台帳遷移の責任境界を決める。** fixture ledger integration に限定するか、reserve→commit→prepare→seal を追加 scope にする。根拠 A:1859–1860、C:668–682。影響は terminal receipt と台帳 digest 参照。
3. **blocker：source entry point と origin completion/report の scope を確定する。** H:781–797、A:3051、3792–3795、3902。影響は gate の受理集合、実行時間の集計、33 root の報告参照。
4. **must-fix：本番 caller を除外するなら、本番発火を完了条件から外す。** A:5475–5498。影響は現 CLI の成果物が originless のままという名乗りの境界。
5. **must-fix：固定名要件を record ref の検証へ訂正する。** E:1355–1364、1398–1401。影響は検証対象の参照先。別名 writer を追加する必要性は現 consumer からは導けない。

## 判定 (plan 採用可 / 部分修正 / 作り直し)

**作り直し。**

先に探索 issuer・source gate・台帳遷移・返却/会計契約の責任範囲を確定し、その後に「leaf の2本確認→supervisor 経由の33本 integration→公開報告の互換性」を別々の受入として組み直す必要がある。