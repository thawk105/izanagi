結論は「現 plan のまま author へ渡してはいけない」です。(i) には既存 lock と certified consumer の素通りがあり、(ii) には承認搬送・receipt の commit・main 変動との排他がありません。さらに D956 の適用範囲が未裁定です。

Web 検索、書込み、pytest 実走は一度も行っていません。したがって緑は報告しません。

### 所見 1

1. **一行の主張:** signed gate は新規 lock 作成経路にしか入らず、既存 v2 lock の resume と certified artifact consumer が素通りする。

2. **成立条件:** `ident.py:427-433` は既存 lock を `verify_against_lock()` へ送り、同 `343-351` は live binding だけを検査する。`artifact_admission.py:843-865,1148-1172` も recorded/current map equality だけで `CertifiedCampaignView` を発行し、`layer3_report.py:665-690` がそれを certifying report へ使う。plan の v2 配線は `s2-plan.md:157` の新規 lock 側だけである。

3. **根拠:** `test_t671_source_binding.py:632-655` のように canonical v2 lock bytes は直接構築できる。正しい map・activation tuple を書けば、署名 receipt を一度も読まず resume または artifact admission へ到達できる。`require_environment_contract=False` の guided 分岐は v1 専用なので意図的免除だが、既存 v2 分岐は同じ扱いにできない。

4. **成果物影響 (DW-G05):** signed ledger の受理集合に digest が無いのに、preseed した v2 lock が `E1` certified view となり、Layer 3 report の `certifying_input=true`、`acceptance_receipt`、`campaign_verifier_epoch` を発行できる。台帳と certified 選択結果が不一致になる。

5. **scope:** scope 内、今 wave で必須。`verify_against_lock()` の certified resume と `CERTIFIED_ACCEPTANCE` の consumer 境界にも signed ratification を要求するか、campaign.lock authority へ exact signed-receipt identity を束縛して検証する必要がある。caller 個数の meta-test だけでは足りず、両素通り経路の負例が要る。

### 所見 2

1. **一行の主張:** 完了条件 (ii) は、land 後 digest を表示するだけでは達成されず、承認を trusted broker へ届ける認証経路と ratification window が欠けている。

2. **成立条件:** closure digest は commit ID を含まない (`enforcement_source_ratification.py:89-104`)。F594 は closure 変更を含む main 取り込みで失効した (`prior-ruling-package.md:61-70`)。回収 broker は準備中の HEAD 変化だけを `ratification_broker.py:236-237` で拒否する。plan は `/dev/tty` 承認を要求する (`s2-plan.md:118-120`) が、ユーザーの内容承認をその tty へ認証搬送する機構を示していない。

3. **根拠:** main が動いても 27 blob が同じなら digest は同じなので承認は使える。一方、27 file のどれかが変われば receipt は現行 gate で機械的に拒否される。この拒否は安全側だが、批准から official 初期化までの closure 変更を防止しないため、承認が繰り返し失効し得る。また人間が trusted host で broker コマンドを起動する運用なら、D758 の「コマンド実行を人間手番に置かない」に戻る。

4. **成果物影響 (DW-G05):** stale receipt は fail-closed で受理集合に入らず、certified lock、選択結果、Layer 3 report は生成されない。安全性は保てても、(ii) の「内容承認だけを起票できる状態」は閉じない。

5. **scope:** scope 内、今 wave で解決必須。選択肢は、認証済み承認 UI を持つ trusted service が承認時に HEAD/closure を再計算し append・commit・official 初期化まで直列化するか、27 path を触る land を ratification window 中に機械拒否する lease を設けること。現状のままなら「非介在条件は gate が事後検出するが、成立自体は人間運用」と明記し、(ii) 未達と判定すべきである。

### 所見 3

1. **一行の主張:** receipt を `hooks/` へ移す P3 には、append 後の commit 主体と競合制御が無く、broker が成功しても gate は開かない。

2. **成立条件:** verifier は committed HEAD の trust root と ledger だけを読む (`enforcement_source_ratification_receipt.py:183-190,453-463`)。broker は worktree を読み (`ratification_broker.py:200,208`) shell redirect で append するだけで (`160-164,238-240`)、`git add`、commit、ledger CAS、排他 lock を持たない。`s2-plan.md:334` が commit を要求するのは初回 bootstrap だけである。

3. **根拠:** append だけでは HEAD blob は変わらない。並行 broker は同じ serial/previous hash を読み、どちらも署名して直列 JSONL を壊し得る。HEAD の再確認は worktree ledger の競合を検出しない。hooks 防壁も SSH/subprocess 内部を観測しない (`hooks/README.md:332-345`)。

4. **成果物影響 (DW-G05):** 未 commit 行は台帳受理集合を一件も増やさない。競合 append を commit すると serial/hash-chain 検査で台帳全体が拒否され、全 certified lock と report が fail-closed になる。

5. **scope:** scope 内、今 wave で必須。broker transaction に committed ledger の exact blob/HEAD CAS、外部排他、atomic append、fsync、stage/commit の主体と provenance を含める必要がある。P3 だけを receipt verifier から分離して land してはいけない。

### 所見 4

1. **一行の主張:** 親の 4 実装単位には、D905/D906 を成立させる「trusted broker の固定・起動・承認・commit 境界」という第 5 単位が欠けている。

2. **成立条件:** D906 は署名対象に実行器・検査器 bytes と排他世代を含める (`D905-D906.md:17-26`)。回収 receipt の signed keys (`enforcement_source_ratification_receipt.py:46-58`) には broker bytes や排他世代が無い。broker は closure 外 (`s2-plan.md:155,336`) であり、trusted host/account の実在も未確定 (`360-362`)。

3. **根拠:** Ed25519、receipt verifier、broker source、配線の 4 つを repo に置いても、AI が起動できない broker process は新設されない。review 済み bytes の外部 install は運用文だけで、receipt からその bytes を検証できない。D906 を本件へ適用するという親 brief の前提に対し schema が不足している。

4. **成果物影響 (DW-G05):** mutable または AI が起動可能な broker が trust-root 鍵を使えると、任意 closure が valid signature を得て台帳受理集合と certified 選択集合が広がる。逆に外部主体が無ければ受理集合は空のままである。

5. **scope:** scope 内、今 wave で決める。内部 author 作業は分割可能だが、main への着地は verifier・broker・配線・外部 deployment 契約を一体にすべきである。trusted service が実在しない場合は段 4 で「実装しない」が正しい。

### 所見 5

1. **一行の主張:** M4 の「端から端まで動く」は 95 pass から導けず、endpoint 生死確認は未成立である。

2. **成立条件:** 回収物には配線単位が無い (`s1-brief.md:43-46`)。M4 の 4 赤中、broker の正例 3 件がすべて失敗し、receipt の 1 件は恒真テストだった (`parent-measurements.txt:22-50`)。

3. **根拠:** 95 件が保証するのは、回収 component の多数の単体経路と pure-Python verifier が test-side signer の署名を検査できることまでである。`contract_loader_binding`、`ident.py:239`、新規 `campaign.lock`、Layer 3 certified consumer はその 95 件に含まれない。

4. **成果物影響 (DW-G05):** 95 pass からは signed receipt が official lock、certified 選択結果、report を一件でも生成できるとは言えない。現時点の成果物受理集合は変化していない。

5. **scope:** scope 内。今 wave に `ident.ensure_campaign_identity()` から committed trust root・signed ledger・新規 v2 lock までの正例と、receipt 無しの負例を追加する。broker の PTY 正例も別に必要である。

### 所見 6

1. **一行の主張:** M10 の「fixture 1 本で覆える」は source binding と衝突し、112 箇所という数も実行規模を表さない。

2. **成立条件:** plan は receipt の `source_commit` と exact 27 blob digest の束縛を要求する (`s2-plan.md:395`)。一方、新 fixture 案は marker だけの synthetic repo を作り (`186-189`)、その HEAD を `source_commit` にする。現 fixture は function scope (`conftest.py:194-236`)。plan 自身の棚卸しでは module marker 展開後 792 base node (`s2-plan.md:199-219`) である。

3. **根拠:** marker-only commit に 27 closure blob は無いため、計画した source-binding 正例は成立しない。fixture は synthetic repo へ exact 27 blobs を commit してから署名する必要がある。さらに `test_s6_sort_sweep.py:622-664` と `test_s8a_trigger_sweep.py:831-873` は fixture 後に別の closure repo へ `_REPO_ROOT` を差し替えるため、certified consumer に signed check を足すと共有 fixture の receipt と一致しない。

4. **成果物影響 (DW-G05):** fixture を計画どおり直すだけでは正例が全滅する。逆に artifact consumer の素通りを残してテストだけ通すと、Finding 1 の未署名 certified 受理集合を偽の緑で覆う。

5. **scope:** scope 内、今 wave で test-support 設計をやり直す。closure repo ごとに trust root・source commit・signed ledger を同じ helper で構築し、fixture の返値・副作用契約を維持する必要がある。

### 所見 7

1. **一行の主張:** `_committed_receipts` は暗号検証が履歴版数に対して二次化し、source binding を素朴に足すと Git 読取も同じく二次化する。

2. **成立条件:** 各 history blob ごとに全行を `_load_rows()` し (`enforcement_source_ratification_receipt.py:394-450`)、各行で `verify()` と source commit 検査を行う (`281-390`)。receipt 1 行の verify は prompt 指定どおり 4 scalar multiplication。履歴版 j の行数を `n_j`、版数を M、最終行数を N とする。

3. **根拠:** scalar multiplication 数は `4 × Σ(j=1..M) n_j`、計算量は一般に `O(MN)`。1 commit 1 append なら `M=N`、verify 呼出しは `N(N+1)/2`、scalar multiplication は `2N(N+1)`。M11 の 1.54 秒を監査中のおよそ 261 回の自前 verify で粗く割ると約 5.9 ms/verify である。これは外部ライブラリ照合等を含む粗い上側校正にすぎないが、暗号部分だけでも次の規模になる。

   | N | 1 gate | 112 gate 呼出し | 792 gate 呼出し |
   |---:|---:|---:|---:|
   | 1 | 約 0.006 秒 | 約 0.7 秒 | 約 4.7 秒 |
   | 10 | 約 0.33 秒 | 約 36 秒 | 約 4.3 分 |
   | 100 | 約 29.8 秒 | 約 55.6 分 | 約 6.6 時間 |

   さらに source binding を 27 blob の個別 Git 読取で実装すると `27 × Σn_j`、N=100 で 136,350 blob 読取になる。112 は fixture の textual site 数であり、実 gate 呼出し数そのものは未計測である。

4. **成果物影響 (DW-G05):** timeout や受入上限超過では検証が fail-closed し、その走行の有効受理集合が空になり、acceptance receipt と certified report が生成されない。ledger 値自体は同じでも開発を止める。

5. **scope:** scope 内、今 wave で直す。最終 chain の署名を各行一度だけ検査し、履歴は blob prefix/parent 関係を検査する `O(M+N)` 形、または canonical row hash/source commit 単位の安全な cache と batch Git 読取が要る。blob・行長・行数の上限も必須である。

### 所見 8

1. **一行の主張:** P7 は後発の D956 に抵触する可能性があり、適用範囲を親が裁定するまで author を開始できない。

2. **成立条件:** D956 は「正式受入の gate」は exact 25-path closure を編集せず、必要ならユーザー裁定へ返すと定める (`docs/decisions.md:34200-34215`)。P7 は `campaign_lock.py`、`contract_loader_binding.py`、批准 verifier を変更し、closure を 27 path へ拡張する (`s1-brief.md:95-96`, `s2-plan.md:153-160`)。

3. **根拠:** D956 は D905 より後の 2026-08-26 決定である。本件を「formal acceptance gate」ではなく「campaign initialization authority」と解して対象外にできる可能性はあるが、brief/plan はその区別を一言も記録していない。

4. **成果物影響 (DW-G05):** 適用対象なら変更自体が無裁定である。25-map v2 lock は codec で拒否され、既存 certified campaign/report の受理集合が縮む。M12 は tracked artifact だけの測定で、repo 外 official output root は覆わない。

5. **scope:** scope 内の事前 blocker。対象外という親判断なら、その理由と 27-path 移行を新 decision に記録する。対象内ならユーザー裁定なしに実装しない。

### 所見 9

1. **一行の主張:** closure 27 化は ratification digest だけでなく codec、E1 report、外部 v2 artifact を変えるが、qualification は同じ digest の consumer ではない。

2. **成立条件:** codec は authority map の exact tuple を要求する (`campaign_lock.py:184-197`)。artifact admission は同じ map から別 domain の E1 hash を作る (`artifact_admission.py:784-822`)。Layer 3 はその値を report へ投影する (`layer3_report.py:591-593,679-690`)。qualification の `select_source_pair()` は lock identity と WAL の歴史的 certified flagだけを読む (`qualification/artifacts.py:900-950`)。

3. **根拠:** 25 から 27 への変更後、旧 25-map v2 lock は decode 時点で拒否され、新 report の `campaign_verifier_epoch` と `identity_scope` は変わる。T126 の現行 historical v1 source は authority mapを持たないので直接影響しない。M12 が確認したのは tracked lock と repo 内 output hit であり、外部 output root は未確認である。

4. **成果物影響 (DW-G05):** 新 Layer 3 report の epoch hash・scope 文字列・それを参照する receipt hash が変わる。旧外部 v2 campaign があれば certified accepted set から外れる。qualification の現行 source pair 受理集合は不変だが、将来 25-map v2 source を指定すれば codec 拒否になる。

5. **scope:** artifact admission の文言・golden・Layer 3 report 影響は今 wave。repo 外 v2 artifact の存在確認または「未確認」とした migration note も今 wave。qualification へ signed gate を付けるかは、evidence-only lane の意味を変えるため次 waveまたは裁定対象でよい。

### 所見 10

1. **一行の主張:** v1 の 929 行 test は削除すべきでないが、現役 gate として残すのも危険であり、legacy kernel corpus と明示して caller 0 を固定するのが妥当である。

2. **成立条件:** 実ファイルは 929 行 (`test_enforcement_source_ratification.py:1-929`)。canonical digest (`265-276`)、Git hardening、DAG merge (`465-777`)、mode (`829-849`)、shallow/graft (`852-907`) を覆う。一方 public `require_ratified_closure()` は unsigned v1 行を受理する (`352-361`)。

3. **根拠:** 削除すると v2 が再利用する DAG/Git/object kernel の回帰 corpusを失う。無印で残すと unsigned gate が現役に見え、accidental fallback の危険が残る。v1 の branch union は v2 serial/hash chain と意味が異なるため、v2 テストへ期待値をコピーしてはいけない。

4. **成果物影響 (DW-G05):** accidental fallback が生じれば unsigned digest が certified 受理集合へ戻る。逆に kernel 回帰を見逃すと置換・欠落履歴を受理するか、正しい台帳を全拒否して report を全滅させる。

5. **scope:** scope 内。production caller 0 の AST pin、legacy 命名・doc、v2 専用 divergent-chain 負例を今 wave に含める。hooks の v1 台帳そのものの削除は人間専有変更と歴史証拠消失を伴うため次 waveへ送ってよい。

### 所見 11

1. **一行の主張:** mutation 事前登録のうち non-TTY と absent-trust は、現形のままでは単一理由への帰属が成立しない。

2. **成立条件:** plan は broker が `/dev/tty` だけから承認を読むとしている (`s2-plan.md:118-120`) 一方、non-TTY rejection の無効化を kill 候補にする (`439`)。bootstrap-free broker の具体的 author bytes はまだ無く、absent-trust rejection の削除後に何が実行されるかも未確定 (`438`)。

3. **根拠:** `/dev/tty` 読取が残るなら stdin の `y` は non-TTY 条件を消しても届かない。したがって別層が同じ入力を拒否する。absent-trust も単に `raise` を削除しただけなら `None` parse、未束縛値、後続照合が拒否し、TOFU 復活を示さない。expected-path 候補 (`434`) は現在は単一理由だが、新 source-binding が row paths まで照合する実装なら二重になる。decision 候補を除外した判断 (`446`) は正しい。

4. **成果物影響 (DW-G05):** 無効な mutation を KILLED と数えると、TTY/TOFU 防壁が実際には未検証でも安全証明へ入る。TOFU が復活すれば任意 AI 鍵の receipt が台帳受理集合と certified 選択集合を広げる。

5. **scope:** scope 内。author 後の exact old bytes で再登録し、non-TTY は `/dev/tty` seam と一体の変異、absent-trust は具体的 TOFU branch を復活させる一変更として帰属を確認する。

### 所見 12

1. **一行の主張:** docs 追随は plan の列挙より広く、D526 上限を超える「人間署名」の文言も除去が必要である。

2. **成立条件:** D526 は主張上限を明記する (`docs/decisions.md:21740-21758`)。D994 は v1 DAG 集合規則を現行規則として記す (`34872-34910`)。D956 は exact 25 を現行値として使う (`34200-34215`)。`hooks/README.md` には ratification broker/trust/ledger の専用節が無い。`artifact_admission.py:67,157,789,874`、`campaign_lock.py:27`、`contract_loader_binding.py:2,58-61` に exact 25 が残る。`s2-plan.md:145` は「後日の人間署名」と断定する。

3. **根拠:** 機械的に証明できるのは configured trust-root key による署名と committed history の自己整合であり、署名 process を人間が起動したことではない。回収 verifier の docstring (`enforcement_source_ratification_receipt.py:2-8`) はこの上限内に収まっている。`docs/phase3*.md` には他の v1/exact-25 前提は見つからなかったが、`docs/phase3.md:1295` の「closure 変異で 4 node だけ」という過去一般化は今回の shared fixture 爆心地に適用できない。

4. **成果物影響 (DW-G05):** `artifact_admission` の identity-scope 文字列は Layer 3 report の値そのものなので、25 のままなら report が実際の 27-path epoch と矛盾する。人間性の過大表現だけは受理集合を変えないため、DW-G05 上は nit だが D526 違反として must-fix である。

5. **scope:** docs・report scope 文言は今 wave。過去 decision 本文は書き換えず、新 decision で D526 の no-append/CLI 前提、D994 の v1-only DAG semantics、27-path 現在値、D956 との関係を明示 supersede する。`hooks/README.md` には broker の外部主体、subprocess/Git 限界、append/commit transaction、主張上限を記す。

### M1〜M11 の検算まとめ

- M1: digest 関数の形と「commit ID を含めない」はコードで確認した。数値・0.43 秒は再実走していない。
- M2: 25 対 27、差分 2 path は確認できる。
- M3: 回収物 `394-450` は線形、main `551-616` は DAG であり正しい。
- M4: component 生死確認まで。E2E という一般化は不成立。
- M5/M9: direct Write/Edit/Bash surface の観測としてのみ有効。「AI は hooks に書けない」という全 surface の断定には使えない。
- M6: 親の環境実測。今回は再実走していない。
- M7: pin は確認でき、M14 の独立 golden・位置 slice まで必要。
- M8: direct production caller 1 本という文字列棚卸しは正しいが、effective gate closure の主張は Finding 1 により偽。
- M10: textual site 112 は確認可能だが、fixture 一改訂で意味的に覆えるという一般化は偽。
- M11: primitive の正しさを支持するが、production の二次計算量を支持しない。

## 総括

本 wave の現 plan は、D905 執行機構にも完了条件 (ii) にも届いていません。最低でも次を author 前に追加する必要があります。

- existing-lock resume と certified artifact consumer の signed gate
- D956 の適用範囲の親裁定
- trusted broker の認証済み承認搬送、固定 bytes、排他、append・commit transaction
- source-bound 27-blob fixture の再設計
- receipt history 検証の `O(M+N)` 化または同等の bounded 設計
- D526 上限内の新 decision と docs 追随

これらを同じ wave で閉じられない、または trusted host/service が実在しない場合は、段 4 で「実装しない」と裁定するのが妥当です。