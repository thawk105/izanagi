## 所見

**B1 — real：旧変異成果物4本が回収対象から漏れている。**

元 commit `ec17af5dc` は、13本の逐語・README・job証拠に加えて、次の4本を含む。

- `mutation-spec-probe.json`
- `mutation-report-probe.json`
- `mutation-spec-final.json`
- `mutation-report-final.json`

旧 report は `repo_head=18704ae18212d08e25df439316de5bcbf903f4c5` に束縛される。現行 directory の変異成果物は回収 wave の `35a740cd4805763b6600e190409cf9db5bd21f91` に束縛された別実測であり、代替にならない。旧4本の blob は `HEAD` の insights 全体にも存在しなかった。

plan は旧 M8「1 node」の叙述を回収する一方、その根拠となる旧 report を回収しない。**「研究記録を取りこぼさない」という完了主張は成立しない。**

**B2 — real：旧 worklog にしか残らない事実の回収が明記されていない。**

旧 `spool/2026-09-10-dev-wave-t2515-calib-rr95-rr5-3.md` には、下記の事実がある。13本の逐語と現行回収資料では対応する記録を確認できず、plan の「未着地・救出に関する経緯」だけでは保存対象が確定しない。

- `timeout 900` により queue 待ち中の dispatch を終了させ、qdel後も orphan hold が2箇所残ったこと。
- 子への `--reasoning` 指定が `rc=2` になったこと。
- 元レビューBの初回が `### 総括` により採用拒否されたこと。
- 子 worktree への git 操作拒否に対し、全比較→所有path複写→再比較を3回行い、所有外差分0を確認したこと。
- 受入失敗を「完全に非帰属」とした判断が覆ったこと。25 file追加と既存testの11 subprocess化という資源面の到達経路があった。
- 既存balanced 2件の binary hash が互いに異なり、source headも当時のpinと異なっていたという観測。

後続裁定を復活させず、これらの**観測・判断訂正だけを既定の追記節へ残す**余地がある。

**B3 — real：consumer の列挙が不完全。**

`test_check_docs.py::test_real_repo_clean` の導出は正しい。しかし、新規 insights は全repo走査のconsumerにも届く。下記の検査接触を「ない」と扱えない。

**B4 — refuted：既着地directoryへの追加そのものが凍結違反になる。**

対象directoryを固定するmanifest・exact member集合は、確認した検査にはなかった。D1941も、日付配下にあるtopicへの追加を禁止していない。

**B5 — refuted：6 commitから未着地のコード変更が残っている。**

確認した差分では反例なし。rratio拡張、実起動負例、interpreter選定、抽出harness修正は現行に存在する。専用関門部分はD1936項6で失効。t1259 fixtureは元tipと現行のファイル差分がなく、対応するinventory登録も存在する。漏れは研究記録側である。

## main 側に無い事実の列挙 (回収すべき / してはいけない の 2 分)

以下の「不在」は、主として指定された現行insight・回収逐語との照合結果である。

**回収すべき**

| 出所 | 現行READMEにない節・数値・因果 | planの被覆 |
|---|---|---|
| 元README §2 | A-6の停止原因はFetchContent失敗であり、較正不足という依頼前提が誤っていた | 明記あり |
| §3 | `892707`、`3c9932591`、`0218acc61` の年表。潜在不整合と関門経由の発火開始の違い | 明記あり |
| §3 | 初回rr5 `988654` も21秒で失敗、2本同一traceback | 逐語追補で保存される |
| §6 | 元waveの変異8件、旧M8が静的検査1 nodeに検出されたこと | 叙述のみ。旧spec/report欠落 |
| §7 | レビュー3本が見落とした抽出harness破損を焦点走が検出、`1 failed / 1349 passed` | 明記あり |
| 旧worklog | 上記B2のセッション異常、非帰属判断の訂正、binary/source世代の観測 | 保存内容が未確定 |

一方、**重複回収に注意する事実**もある。

- Python 3.9 import失敗と後段選定の問題は、現行README「当時の失敗実測」に既載。
- BACKOFF_FIXEDによる2種類の構造化拒否、rr95 receipt、accepted未取得も既載。
- shell限定のexact集合、M5/M6の実起動検出、M8の世代差も既載。
- F500には同じscriptのinterpreter不整合、F766には主題でなくファイル名で既存Fを探す誤りが既載。planの再発扱いは妥当。

**回収してはいけない現行主張**

- 「8月6日以降ずっと故障」「約3週間の連続実走不能」という期間断定。
- patch materialize・receipt拡張・rr50再取得を「解き方は確定」とする旧判断。
- BACKOFF_FIXEDの宣言撤去案を、現在も却下済みとする説明。
- 定期smokeやwait修正を、新しい未裁定Tとして復活させること。
- 元waveがacceptedを取得した、または後続rr5却下が解消したという説明。

旧判断を逐語の歴史資料として保存することと、現在の方針として再登録することは区別すべきである。

## 検査・pin への接触 (path で引いた結果)

| 参照経路 | 判定 |
|---|---|
| `orchestrator/tests/test_check_docs.py:12540` → `tools/check_docs.py:1259` `_check_spool_guard` → `tools/spool_fold.py` `validate_spool_tree` → `_discover` | planの導出を確認。新fragmentを読む |
| `test_s8b_repo_scan_invariant.py:27` → `orchestrator/campaign/s8b_holdout_freeze.py:592` `search_repository` → `:370` `enumerate_repository_files` → tracked/untrackedのfile読取 | **plan未列挙のconsumer**。insightsも対象 |
| `test_s8c_preregistration_invariant.py:622` → 同じ列挙・`search_repository` → `_assert_search_pass` | **別の間接consumer** |
| `test_login_headroom.py:1602` → `git ls-files --cached --others` → 全textの数値literal照合 | insightsも対象 |
| `test_frozen_artifacts.py` → 固定path/hash manifest | 対象topicは含まれない |
| `tools/check_docs.py:2591` → insights直下・日付直下のMarkdown列挙 | topic内部の逐語はplaceholder走査対象外 |
| `tools/spool_fold.py:1195` → `docs/spool` root exact集合 | ledger配下への正規fragment追加は通常経路 |

13本にはholdoutの三軸literal conjunction、およびlogin memory ceilingの対象literalを確認しなかった。したがって、**consumer接触はあるが、今回の13本で違反が発生する根拠は見つからない**。実走結果は述べない。

spool形式はplanどおりで整合する。

- failures `seq: 1`、worklog `seq: 2` はwave内連番。
- failuresのtitle省略、worklogの無引用titleは契約どおり。
- failuresは `## 再発` → `## supersede 追記`、再発は `### Fnnn`。
- supersedeは指定書式の1物理行。
- `## 次の一手差分` は**本文も操作も空**なら有効。そこへ「操作なし」などの説明文を入れると、`_parse_worklog_delta` が未解釈contentとして拒否する。
- 旧placeholderを転載せず、新waveのfrontmatterで必要事実を再記述する方針は妥当。

## 配置の択一の判定

**既存日付topicへ元資料を追加し、今回の作業記録を新日付topicへ置く案を支持する。**

既存topic内なら、当時のjob証拠・回収後実測・元逐語を同じ入口から区別して読める。新日付topicへ元逐語を置く案もD1941には適合するが、当時資料の所在が分散する。

D1941のbytes保持は既存資料の移動整理についての規定であり、今回明示されたREADME末尾追記と衝突しない。

`docs/phase3.md:534` と9月13日の後続insightは、このREADMEを先行回収・当時の拒否実測として参照する。既存本文を保持し、追記を回収日付きの歴史説明に限定すれば参照意味は壊れない。ただし「acceptedは現在も一切ない」と一般化すると、9月13日のrr95 accepted記録と衝突する。

## 親 brief と plan の誤り

- **brief：** 「13逐語＋README追記＋spool」で完全回収とする根拠が不足。元変異4本を落としている。
- **brief：** 「mainのどの台帳にもない」という広い不在主張は不適切。年表の未記録と、既存の失敗型F500・F766を分ける必要がある。
- **plan：** 旧worklogの固有観測について、回収対象を明示していない。
- **plan：** consumer導出がdocs checkerで止まり、repo全体走査を取りこぼしている。
- **planの訂正は支持：** 新規Fを作らず再発にすること、3週間故障の断定を弱めること、旧decisionsを現行裁定へ再登録しないこと。

## scope 外の real 所見 (裁定パッケージ候補)

**旧変異4本の保存範囲。** 親briefの成果物一覧には含まれないが、「未着地研究記録の完全回収」には必要な一次資料である。既着地6本を変更せず、旧4本を回収対象へ含めるか、今回の回収を限定回収と明記するかが裁定対象となる。新しい検査・gate・台帳は不要。

旧worklogには「codex子9本」と、内訳合計11本との不一致もある。工数を確定値として再掲せず、原文の不一致として扱うべきである。

## 総括

**現planのまま「完全回収」とする判断には反対。** 旧変異4本と旧worklog固有の観測が取り残される。

配置・spool形式・docs-only方針は妥当。未着地コードの反例は確認できなかった。静的確認のみを行い、ファイル書込み・git状態変更・テスト実行は行っていない。