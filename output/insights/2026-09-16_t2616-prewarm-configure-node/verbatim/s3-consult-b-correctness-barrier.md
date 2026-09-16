## 現物で確かめた事実

必読11ファイルは読取り可能でした。以下は静的読解と文字列・AST検査の結果です。pytest、書込み、commit、git の状態変更はしていません。変異はすべて**未実行の検査案**です。

参照略称は次のとおりです。`略称:行番号` で現物を指します。

| 略称 | ファイル |
|---|---|
| B | [s1-brief.md](/home/SFC/tanab/.claude/jobs/774bd912/tmp/wave-artifacts/dev-wave-t2616-prewarm-configure-node/s1-brief.md) |
| P | [s2-plan.md](/home/SFC/tanab/.claude/jobs/774bd912/tmp/wave-artifacts/dev-wave-t2616-prewarm-configure-node/s2-plan.md) |
| F | [parent-probe-findings.md](/home/SFC/tanab/.claude/jobs/774bd912/tmp/wave-artifacts/dev-wave-t2616-prewarm-configure-node/parent-probe-findings.md) |
| V | [verbatim-t2616.md](/home/SFC/tanab/.claude/jobs/774bd912/tmp/wave-artifacts/dev-wave-t2616-prewarm-configure-node/verbatim-t2616.md) |
| D518 | [verbatim-d518.md](/home/SFC/tanab/.claude/jobs/774bd912/tmp/wave-artifacts/dev-wave-t2616-prewarm-configure-node/verbatim-d518.md) |
| D573 | [verbatim-d573.md](/home/SFC/tanab/.claude/jobs/774bd912/tmp/wave-artifacts/dev-wave-t2616-prewarm-configure-node/verbatim-d573.md) |
| C | [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node/orchestrator/tests/conftest.py) |
| R | [real_repo_receipt_memo.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node/orchestrator/tests/real_repo_receipt_memo.py) |
| O | [sort_swo_oracle_receipt_memo.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node/orchestrator/tests/sort_swo_oracle_receipt_memo.py) |
| T | [test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node/orchestrator/tests/test_real_repo_serialization.py) |
| I | [insight README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node/output/insights/2026-09-14_acceptance-5min-floor/README.md) |

- **[refuted] 「未公開 cache は現行でも常に即赤」は成立しません。** R:632 は R:452 の blocking `flock` を経て、R:622 の存在検査へ進みます。writer が先に lock を取っていれば、現行も公開まで待ちます。即 `cache-missing` になるのは、reader が lock を取った時点で本体がない場合です。
  **変異:** writer を lock 取得直後で停止し、reader 起動後に公開させる。現行でも成功するため、この順序を新規の赤→緑に数えてはいけません。

- **[real] consumer 不在 shard への追加仕事は確定しています。** I:51–57 と訂正 F:7–12 に対し、P:109–133 の条件は全受入 shard を対象にします。現行 C:921／979 は consumer 不在なら解決しません。追加費用が collection に隠れるか、最遅 shard を入れ替えるかは未測定です。
  **変異:** consumer 不在 shard の receipt resolver にだけ遅延を入れる。旧経路では呼出し0回、新経路では wall または待機失敗に現れるべきです。

## fail-closed の後退に関する所見

- **[refuted] timeout／破損から worker が resolver を呼ぶ後退は、plan 本文からは指せません。** P:144–148 は worker の再解決を禁止し、未通知 miss と破損を失敗に残しています。現行の reader は R:597–637、O:639–692 で解決を呼ばず、T:3734–3787 は公開 endpoint の resolver 呼出し0回を検査します。期限切れで値を返す記述もありません。
  **変異:** 早期待機の timeout 捕捉を `return self.prewarm(...)` に変える。structured error と resolver 呼出し0回の両方で落とす必要があります。

- **[unknown] 「JSON 公開済み」と「prewarm 成功」の区別が足りません。** P:146 は atomic replace 成功後を ready とします。しかし R:366 の公開後にも R:474–490 の unlock／close が失敗し、O:385 と O:494–510 も同じ構造です。現行は C:2270 の join と C:2283–2290 の例外伝播が、C:2422 の同期 callback を失敗させます。新経路で JSON 優先に読むと、`.failed` が届く前に worker を通せます。P:149 が背景例外を回収するため、**走行全体が緑になることまでは証明できません**が、成功していない prewarm から test を開始する窓は未解決です。
  **変異:** JSON replace は成功させ、その直後の writer の unlock を失敗させる。worker は本体があっても test を開始せず、最終結果も赤になるべきです。

- **[unknown] `.pending`／`.failed` の競合時の優先順位が未定義です。** P:146–148／188 には、failed と本体が共存した場合、公開後の miss、marker 自体の読取り失敗の扱いがありません。現行 R:549–553 は既存 cache を writer が再利用することも拒否します。「本体が読めれば成功」へ縮めると、この失敗情報を迂回できます。
  **変異:** 同じ job に `.failed` と schema-valid な本体を共存させる。failed を優先し、resolver 呼出し0回で赤にする必要があります。

## snapshot 単一性・nonce 契約に関する所見

- **[unknown] 全 worker を止める保証は設計上の約束で、現物の実装ではありません。** P:144／154 は全 test body 開始前の両 memo 待機を要求しますが、現行 C:2298–2314 は worker の prewarm を除外するだけです。現在の保証点は controller の C:2422 とその先の C:2270。そこを外した後の代替保証を指せる実装行はまだありません。特に consumer getter だけの待機では、背景 reader が C:899 の実 repo lock を取る前に writer test が走れます。
  **変異:** 待機対象を consumer のいる worker だけに狭め、receipt job を C:899 の直前で停止する。別 worker の writer の setup／body が開始したら失敗とする。既存 lock が保護するのは取得後なので、この順序が必要です。

- **[refuted] controller から path を渡すこと自体は D573 の事前予測防止を弱めません。** C:2607／2664 は controller で nonce を新規生成し、C:2336／2355 は既に worker へ伝播します。R:131–140、O:128–136 の同じ鍵を使う限り、path の追加伝播だけでは固定 `--testrunuid` から未来の名前を計算できません。marker を作成・上書きできるのは、その directory／file への書込み権限を持つ主体です。同一実行ユーザーの worker／plugin は候補になりますが、別ユーザーの可否は未定の mode 等に依存します。in-flight nonce 観測後の偽 payload race は D573:11–17 が明示的に対象外にしています。
  **変異:** controller の新規 nonce 生成を継承環境値の再利用へ置換する。同じ UID・HEAD の別 invocation が同じ path になる負例で検出するべきです。

- **[unknown] path 伝播で現在の identity 検査まで省略するかが不明です。** 現行 reader は R:602–619、O:644–669 で UID・nonce・HEAD から読取り先を決めます。P:145 は controller の path を渡すとしますが、worker 側で何と照合するかを指定していません。旧 invocation の descriptor や HEAD 取得失敗を、その path だけで通せば赤→緑になります。これは事前予測とは別問題です。
  **変異:** nonce B の worker に nonce A の成功済み descriptor を渡す。T:3589–3625 と同様、A の値を返してはいけません。

## 受理集合が変わる箇所 (緑→赤 / 赤→緑 の両方向)

- **[real] 赤→緑：通知済み job がまだ cache lock を取得していない順序。** reader が先に lock を取得すると現行 R:622–625 は赤です。P:128／147 の早期待機では、その後同じ job が期限内に公開すれば緑になります。**これは今回明示された時間順序の受理拡大です。固定 snapshot の不正な値を受け入れる証拠とは区別します。**
  **変異:** writer の cache lock 取得を reader の最初の存在検査より後へ遅らせる。通知ありだけ成功し、通知なしでは従来どおり即赤になる必要があります。

- **[real] 緑→赤：成功するが新 deadline より遅い writer。** 現行 R:452 は lock を無期限に待ちます。P:148／152 の変更後は、同じ成功結果でも deadline 超過なら拒否します。これは fail-closed の強化ですが、「受理集合が完全に不変」ではありません。
  **変異:** writer が lock を保持し、期限直後に正常公開する。新経路は赤のままにし、遅い成功で timeout を取り消してはいけません。

- **[real] 緑→赤：consumer 不在 shard の不要な resolver 障害。** 現行 C:913–929／971–988 では呼ばれない resolver が、P:139–146 の早期全受入経路では呼ばれ、P:149 により背景例外が伝播します。その shard のテストには不要だった失敗原因が増えます。
  **変異:** consumer 不在 shard でだけ resolver を例外にする。旧経路の呼出し0回と、新経路の赤を対比する必要があります。

- **[real] 赤→緑：plan の予算式は「最大120秒」を超える待機を許します。** V:6 は最大120秒ですが、P:194–206 は120秒を確定値とせず `B = ceil(2 × max(W))` を提案し、上限を付けていません。例えば観測 max が70秒なら B=140秒となり、130秒で公開される入力が120秒契約の赤から緑へ変わります。数値例は実測値ではありません。
  **変異:** fake clock で観測 max=70、公開時刻=待機開始後130秒を与える。最大120秒契約なら拒否すべきです。

- **[real] 完了判定の赤→緑：brief が300秒超を受理可能にしています。** B:9–10 の「300秒未満は目標であって受理条件ではない」は、B:38 および今回の「全体5分が絶対上限」と矛盾します。P:224 は上限を緩めないとしていますが、brief の完了判定は訂正されていません。pytest の緑と時間規則の合格を混同する具体的な入口です。
  **変異:** 新規赤0件・canonical 最遅 shard wall=301秒の receipt を与える。絶対上限の達成として受理してはいけません。

## pin との両立

- **[refuted] 二重 guard の逐語 pin を緩める必要はありません。** T:4890–4912 はコメント込み内側4行に加え、外側の呼出しブロックも要求します。両文字列が現物に各1回あることを静的確認しました。P:141／144／179 の方針どおり、worker の読取り待機をこのブロックの外へ置けば両立します。
  **変異:** 内外両 guard を除去する。T:4913–4951 の既存変異が引き続き worker payer を検出しなければなりません。

- **[refuted] `hook="configure_node"` は4キー pin と衝突しません。** T:4866–4869 はキー集合完全一致と、実行した経路の hook 値を要求します。C:2274–2278 の `hook` 値だけを変えるならキーは増えません。P:160／171 は旧2経路を残し、早期経路を追加する方針です。なお現行 barrier test は9定義です。
  **変異:** timing payload に `wait_s` を追加する。キー集合検査を赤に保ち、部分集合検査へ緩めてはいけません。

## plan を採るとしても足りない検査

- **[unknown] 非 blocking lock の再試行対象が未固定です。** P:148 は取得方式だけを指定しています。現行 R:453–461 は取得失敗を拒否します。競合以外の `EIO` 等まで再試行すると、一度は赤になる故障が後続成功で隠れます。また reader が lock を保持して pending を待つと writer の公開を妨げます。
  **変異:** 最初の lock 取得だけ `EIO`、次回は成功にする。競合として再試行せず、最初の故障で赤にするべきです。

- **[unknown] 公開後の miss を「まだ pending」として救済する余地があります。** P:147／188 は未起動 miss と pending→ready を挙げますが、ready 後の消失を分けていません。R:622–625、O:672–675 の既存の赤を残すには、完了した job の miss で待機を再開しない検査が要ります。
  **変異:** ready 後に本体を消し、遅れて再配置する。最初の公開完了を知っている reader は消失時点で赤とし、後から緑に戻してはいけません。

- **[unknown] worker の期限は背景 job の終了期限を保証しません。** P:142／149 は非 daemon thread と終了時回収を残します。現行 C:2260–2270 の join は無期限で、実 repo lock には別の245秒予算もあります（C:1028–1031）。worker が期限内に赤を出しても controller 回収が長引けば5分を超えます。これは「遅くても緑になる」と同義ではありませんが、bounded wait だけでは全体上限を証明できません。
  **変異:** resolver を worker の timeout 後も Event で停止させる。worker の赤だけで完了扱いせず、controller 回収を含む wall を検査する必要があります。

- **[unknown] 焦点走除外は複合条件の実経路検査が必要です。** P:109–116 は spec と全 suite 選択を併用しますが、利用予定の C:2016–2034 と C:1015 だけでは `-k`／`-m` を排除しません。plan は追加判定を明記しているため、漏れを実在の不具合とは断定しません。
  **変異:** parsed `keyword` の除外だけを削除し、spec＋suite root＋consumer 不在の `-k` を与える。解決・診断とも0回を要求し、P:172／178 の意味を守るべきです。

## 総括

- **[real] 現段階で「受理集合不変」とは判定できません。** 通知済み未公開 cache の赤→緑は意図された変更ですが、P:204 の予算式による120秒超の許容と、B:10 の300秒条件の後退は別に修正が必要です。
  **変異:** 130秒で公開される成功 job を与え、最大120秒の契約で赤になることを固定する。

- **[unknown] 不正な snapshot を最終的に緑として通す実装経路は未確定です。** 特に P:146 の ready 定義、P:144 の全 worker 待機、P:145 の identity 照合が未実装です。既存 pin を残すだけでは、この3点の保証になりません。
  **変異:** 本体公開後の writer unlock を失敗させ、test 開始0件・最終赤を要求する。この境界を閉じずに「fail-closed 維持」と結論することはできません。