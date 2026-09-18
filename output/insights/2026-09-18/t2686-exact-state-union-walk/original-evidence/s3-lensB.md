## 判定表

静的検査のみ。変更・pytest・性能測定は実施していません。以下、C=`tools/check_branch_landed.py`、T=`orchestrator/tests/test_check_branch_landed.py`、R=`tools/check_branch_rescue.py`、B=`s1-brief.md`、P=`s2-plan.md`、A=`s2-plan-parent-addendum.md`。

| 主張 id・検査した主張 | 判定 | 根拠 |
|---|---|---|
| 1/P1：律速への scope 移動は依頼意図に沿う | **real（条件付き）** | 同じ判定対象・証拠を保つ局所改善という目的には沿う。計測 JSON:38 の closure と introduced 合計は **2.273秒**、同:26 の exact 探索は267.132秒。D2106にも path log 合計の律速が記録されている。ただし「closure は常に律速でない／改善収益なし」までは言えない。file 名訂正と処理対象変更は別々に記録すべき（B:9、25、28）。 |
| 2/P2：別 production file なので衝突しない | **refuted** | source の編集分離は test・契約の独立性を意味しない。`test_check_branch_rescue.py:1758,1789` は実子 checker を呼び、証拠詳細を検証する。T-2691 の実差分は投影資料に無いため、実際の競合と安全な land 順は**判定不能**。待たずに着手する判断自体は否定しない。 |
| 3a：A1で timeout による verdict 悪化を塞げる | **refuted** | A:11 の「新版≤旧版＋有界走査」から、完走可能集合の非縮小は導けない。未要求の tip 一致 path も登録される（P:19）。さらに無制限再走査が残る（A:10）。D2106は受理述語と時間内完走集合を明確に区別している。 |
| 3b：親が両版を timeout で kill した場合の扱いは同じ | **real（その条件内）** | R:1587 は部分 stdout を利用せず `_empty_landed("checker-timeout", …)` を返す。rc・report hash・unit詳細は取得不能扱い（R:1486）。elapsed まで byte 一致ではない。また、片方だけが時間内に JSON を返す場合まで同じとは言えない。 |
| 4：argv 超過時の旧経路 fallback は妥当 | **real（設計方針）** | C:777の旧 command を保てば候補取得の意味は維持できる。C:785の `batch_safe` と設計上の類似はある。ただし **D2054は `batch_safe` の裁定ではない**。256 KiBという例だけでは実際の実行可能 argv サイズの保証にならない（A:20、P:53）。 |
| 5：timing 追加が既存 consumer を壊す | **refuted（確認範囲内）** | R:1536 は列挙した証拠 fieldだけを転送し、子 timing を判定に使わない。コード検索で `git_child_processes` は両 checker の生成箇所のみで、読み取り consumer は見つからなかった。ただし raw stdout の `report_sha256` は変わる（R:1629）。 |
| 6：計画の test・変異表で全条件を検証できる | **判定不能／不足は real** | (a)〜(i)は概ね妥当な設計だが実装・実走前なので KILLED は未確認。A1導入後の二走査分岐、残予算、mergeのK計数、A3 fallbackを検証する具体的な node が不足（P:123、A:7）。詳細は下記。 |
| 7：A5の事前登録で十分 | **refuted（要修正）** | timeout時の reason 完全一致を要求しないのは妥当。しかし「旧版と同じ class」は片側だけ timeout する場合には成立しない。候補列一致だけでは観測層の timeout 差も排除できない。さらに現 CLI は timeout **300秒以下**、`--main` は **local branch名**であり、900秒・main OID直接指定の測定はできない（C:2019、426）。 |
| 8：計画に要求外の一般化・gateが過剰に入っている | **refuted（提示資料内）** | 供給object・parser・fallbackは候補取得変更を成立させる局所要素。新たな一般gateや台帳基盤は見当たらない。ただし廃案のstdin設計・testと、無条件「1走査」の記述は削除・更新が必要（P:60、135、138、A:10、19）。 |
| 9：1走の結果から「union化で5倍」等を一般化できる | **refuted** | 372秒は負荷条件付き1標本。267秒・333秒・323秒は包含／重複する計測で加算不可。30.9秒対195.6秒も、この資料では対応する生データが無い。報告できるのは標本・条件を限定した観測値と、同一入力・同一分岐での process 数削減。 |
| 10：D2142を同型の先例として引用できる | **real（方法論に限定）** | 「範囲を削らずprocessを減らし、等価性と同時刻対照を事前登録する」という先例にはなる。ただしD2142の集合復元証明は、本案の候補**順序・limit+1・期限内取得**を証明しない。D2142自身も未証明の残余を明記している。 |

## must-fix / should / nit

### must-fix

- **A1の非退行主張を撤回する。** 放置すると、旧版が `landed` を返せる入力を新版が `indeterminate` にする可能性を「受理集合不変」と誤報する。
- **再走査は同じ `Git`・同じdeadlineを使う。** 2本目も `min(45, git.remaining())`、残り≦0なら起動せず `assessment-timeout/truncated`。期限再起算・失敗後再試行を入れると予算契約が変わる（C:215）。
- **A1の三分岐をtestへ追加する。** `n<K`、`n==Kかつ全path飽和`、`n==Kかつ未飽和`、merge親別entryの重複、2本目開始前／実行中の期限切れを区別しないと、不完全候補を完全として渡す経路を検出できない。
- **A3/A6の失敗memoの範囲を明記する。** union全体の失敗と、旧経路fallbackのpath単位失敗は別物。fallbackの1 pathの失敗を全pathへ再送出すると、旧版が試せた別pathの証拠取得まで抑止する。
- **argv閾値の根拠と境界を固定する。** モジュール定数で十分だが、固定argv・実際のenv・pointer分を含めるか、安全な余裕の根拠が必要。C:230の起動で `OSError` が出れば現行は捕捉しないため、推定漏れはJSON契約まで壊しうる。
- **受入実験を実行可能な形に事前登録し直す。** CLI上限300秒とlocal branch限定を無視すると、測ったつもりの900秒・固定main比較が成立しない。
- **T-2691との統合検査をland条件にする。** 後からlandする側が統合差分と両test fileを確認しないと、Git上の無衝突でもconsumer契約が壊れうる。

**A1の反例構成：** 登録集合を `{p,q}` とし、`p`は近い履歴で証明可能、`q`はtip一致だが更新履歴が多い場合を考える。旧版は `p`の有限候補走査と `q`のtip確認だけで済む。新版は `q`もunion対象にし、K件時点で`p`が未飽和なら全履歴を再走査する。これはA1を通過する逆転経路であり、具体的な秒数を仮定しなくても「悪化を塞いだ」という論証は崩れる。

**変異の帰属：**

| 変異 | 静的評価 |
|---|---|
| a：prefix削除 | `file_directory`で、`f/child`更新が`f`の対照列に含まれることを明示すれば有効。 |
| b：OID sort | P:157の非整列assertが必須。実OIDが偶然整列したfixtureだけでは無効。 |
| c：limit+1→limit | list長比較とT:1005の65件assertで殺せる。ただしT:986は「最後の追加1件で正証拠」を検証していないため、その境界正例も必要。 |
| d：separate削除 | 両親mergeを対照が含むこと、非変異版parserが正常完走することを確認。parse errorによるkillと候補欠落によるkillを記録上区別する。 |
| e：full-history削除 | TREESAME mergeの対照への包含assertがあれば有効。 |
| f：showRoot削除 | repo-local falseを設定する設計は妥当。 |
| g：nameゼロ検査削除 | 他の文法検査が同じ入力を拒否するなら等価変異になりうる。対象条件だけを外したときの到達点を確認する。 |
| h：旧per-pathへ戻す | 意味論ではSURVIVED、process契約ではKILLEDという分類は正しい。ただし「1本」nodeは再走査不要・fallback不発のfixtureに限定する。 |
| i：コメントのみ | SURVIVEDが正しく、全KILLED集計から除外する。 |

既存testの注入面変更は、次の条件なら「意味上の期待値を維持」と言える。

- **T:395**：候補供給だけstub化し、batch解析は実コードを通す。先頭一致でも後続不正行を拒否する検査を残す。
- **T:455**：重複1025件はbatch境界専用の人工入力として妥当。ただしカウンタを手動加算して5へ合わせるのは検証にならない。実commandを通す場合も、union統合のprocess検査とは区別する。
- **T:488**：非通常stateがbatchを呼ばず、所定順でtree確認する期待は維持可能。
- **T:1037**：shell selectorは既に先頭`-c`を処理する（T:1053）。必要なのは主にPython側T:1083の更新。実`TimeoutExpired`のcause、timeout値、未遅延の正例を保持する。A3採用後のstdin対応は不要。

### should

- **A5は「両版とも対象処理を正常完了した比較」と「片側／両側timeout」を分ける。** reason一致を受入条件から外しても、reason・phase・取得済みunit差は記録する。D2055の理由伝達を評価から消さない。
- **fallbackのtestは閾値0だけで終えない。** 旧commandとの列比較、LF/CR名、同path再要求、閾値直前／直後、union未起動を確認する。0だけではbyte見積りの誤りを検出できない。
- **timingの重複計上とhash変化を明記する。** 初回unit elapsedとwalk elapsedは加算用ではない。`report_sha256`変化は契約破壊ではないが、同値比較には使えない。
- **process削減を全入力保証にしない。** 全tip一致なら0本、fallbackなら旧経路、条件付き再走査なら2本になる。

**親のpayload比較手順：**

1. 比較元mainのcommitを固定し、その版のchecker単体をjob dirへ抽出。新版はworktreeのcheckerを使用し、双方のsource hashを保存する。
2. 両者へ**同じ明示的な `--repo`**、対象OID、main branch、上限値を渡す。別のrepo rootを使えばpayloadの `repository.root` 自体が異なる。
3. mainはOIDを直接指定できないため、測定用の固定local branchを用意するか、全走の開始・終了で同じmain OIDを検証し、動いた組を無効にする。
4. CLI比較は300秒以下。900秒が必要なら、同一の外部driverから両版の `assess(timeout_seconds=900)` を呼ぶ測定として明記し、production CLI・定数は変更しない。
5. 旧／新／旧／新でraw JSON、rc、wall、process数を保存。指定したelapsed fieldとtop-level timingだけを除去し、同じcanonical JSON化でbyte比較する。証拠配列・候補順は整列しない。

### nit

- `history_candidate_walk_processes`（P:48）と `history_candidate_walks`（A:24）は後者へ統一する。
- A:24のfallback本数は「登録path数」ではなく、遅延実行で**実際に走査したpath数**。
- B:13の「起動中」とB:29の「未着手」は整合させる。

## 親 brief / addendum の誤り

1. **B:P5／A1の非退行論証は誤り。** 有界化は改善策であって、時間内完走集合を保存する証明ではない。
2. **A3のD2054参照が不正確。** 提示D2054はreceipt→exact-stateの正例専用fallback。`batch_safe`の直接根拠はC:785。
3. **「同じclass」の適用条件が不足。** 旧版成功・新版timeout、またはその逆を除外できない。
4. **「closure改善は収益なし」は過剰。** 今回の標本では優先順位が低い、とするのが適切。
5. **計測値の根拠範囲が混在。** 提示JSONにはpath log **28.61秒**もあり、「4〜25秒」をこの全走の範囲としては使えない。CPU時間・Lustre原因・33/33一致はこのJSONだけでは確認できない。
6. **P:63のchunk却下理由も過剰。** 必要なのはpathごとの候補順であり、異なるpath間の全体順位は本契約の出力ではない。chunk案を採用する必要はないが、この理由では不可能と断定できない。

## 裁定パッケージ候補

- **P1を条件付き採用**：名称の誤記訂正と律速へのscope変更を分離し、「今回の固定入力の観測に基づく優先順位変更」と記録する。
- **timeout契約を明文化**：推奨は「決定的証拠の受理述語を維持、正常完了時の候補・payload一致、期限内完走集合の非退行は保証しない」。全入力のverdict不変を要求するなら現案は不採用。
- **P2を統合条件付き採用**：着手は待たず、後着側でT-2691との統合差分・両test群を確認する。
- 新たな全体予算変更、並列化、一般timeout管理基盤の追加は不要。

## 総括

P1の方向と遅延候補供給は妥当だが、A1はtimeout悪化を塞いでいない。
採用前に受理述語と期限内完走集合を分離して裁定する必要がある。
A1/A3の分岐test、fallback失敗の範囲、実行可能な比較手順を補うこと。
P2の着手継続は可能だが、「別fileだから無衝突」は根拠にならない。
速度・変異KILLED・候補等価性は、本静的検査では実証していない。
