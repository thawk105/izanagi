結論は「現プランのまま採用不可」です。以下は指定資料だけによる静的所見で、pytest・CLI 実走はしていません。

## 所見

### 1. 任意 `runner` / executable が closure と receipt を丸ごと偽造できる

- **(a) 何が壊れるか** — 呼び手が偽 executable または stateful runner を渡し、CLI を実行せず compliant envelope、別 session ID、tool use 0 を生成できる。3 性質すべてが自己整合した偽 receipt になる。
- **(b) 根拠** — `s2/plan.md:44-46` は両者を公開注入し、`claude_projected_provider.py:146-149,220-223,274-344` は任意 runner の返値を信頼する。実行 hash は記録するだけで許可値との照合がない。F592 `docs/failures.md:15286-15298` の自己選択 trust root と同型。
- **(c) 最小是正案** — certified mode では `runner is subprocess.run` を要求し、executable の絶対 path と SHA-256 を事前登録済み許可値へ照合する。注入可能 mode の receipt は `test_only=true` とし正式 consumer が拒否する。
- **(d) 成果物影響** — 偽 receipt の block が受理集合へ入り、critic が変えた候補列から certified 集合が変わり、材料レポートと試行台帳が偽の閉鎖証拠を参照する。

### 2. `tools=[]` 周辺の観測は総合的な「道具ゼロ」を証明しない

- **(a) 何が壊れるか** — inline `tools=[]` は宣言、setting sources 無効化は設定源、strict MCP と空 config は MCP 面しか閉じない。`permission_denials=[]` は拒否記録なし、`server_tool_use==0` はその集計面の未使用にすぎず、local tool surface の不存在を示さない。しかも `observed_tool_events=[]` は観測でなく定数である。
- **(b) 根拠** — `claude_projected_provider.py:171-178,221-241,306-344,347-360`。元 role は Bash を宣言し digest 自己実行を許可する `critic.md:4,13`。F17 `docs/failures.md:297-315` が同じ「一面の tools 0 を総合 tool-free と誤認」を禁止する。
- **(c) 最小是正案** — pinned CLI の raw tool descriptor と全 tool event を保存・検証し、Read/Bash/digest 実行を強制する負例で拒否を確認する。完全な event 面が取得不能なら OS sandbox を追加するか、性質1を未充足のままにする。
- **(d) 成果物影響** — off critic が赤 WAL を取得できれば次候補と certified 到達率が変わり、B-4 の paired outcome は off 汚染として判定不能になる。

### 3. 親 brief の1回の実測は能力遮断へ一般化できない

- **(a) 何が壊れるか** — critic が digest 実行を試さず、返答にも読んだ痕跡を書かなかった1回から「実際に到達不能」「campaign を読まなかった」と結論している。非試行と能力不存在、非言及と非読取を区別できない。
- **(b) 根拠** — `brief.md:28-35`。provider は tool event を解析せず空配列を記録する `claude_projected_provider.py:347-360`。F16/F21 `docs/failures.md:279-290,372-389` の「presence・単体動作を live 全連鎖へ一般化」と同型。
- **(c) 最小是正案** — brief の結論を「当該 payload では自己実行を観測しなかった」へ縮小し、性質1の根拠には数えない。強制負例が通るまで前提条件3を解除しない。
- **(d) 成果物影響** — 実測を根拠に不適格 block を受理すると、台帳の能力遮断欄と材料レポートの B-4 根拠が過大表示になる。

### 4. repository root という禁止語の trust root を呼び手が選べる

- **(a) 何が壊れるか** — 実 repo と異なる `repository_root=/tmp/decoy` を渡せば、実 repo path が payload にあっても非開示検査を通る。neutral-root 排除判定も同じ偽 root を使う。
- **(b) 根拠** — 公開 API は caller 値を受ける `s2/plan.md:33-36,42-47`。provider もそれをそのまま `_create_neutral_root` へ渡す `claude_projected_provider.py:185-190`。F592 `docs/failures.md:15286-15298` と同型。
- **(c) 最小是正案** — repository root は module location から独立導出する。互換用引数を残すなら導出値との exact equality を要求し、相違は invocation 前に拒否する。
- **(d) 成果物影響** — repo/campaign 由来情報を得た off critic の出力が正規標本へ入り、試行台帳の `campaign_identity_absence_checked` が偽になる。

### 5. 直接 substring 検査は同じ path の別表現を通す

- **(a) 何が壊れるか** — `/a/b` に対する `/a/x/../b`、`file:` 表現、percent encoding、文字列としての `\u002f` などは model が復元できても禁止 byte と一致しない。key sort と数値表現は主因ではなく、文字列内の alias と二重 escape が穴である。
- **(b) 根拠** — 禁止集合は3つの実値だけで、raw/escaped byte の substring 検査に留まる `s2/plan.md:93-105`。負例も実値の直接注入だけ `s2/plan.md:107-115`。
- **(c) 最小是正案** — 保証を「exact byte 非出現」へ明示的に縮小するか、全 string leaf に対し escape decode、URL decode、path lexical normalization を有界に適用して各 view を検査する。各別表現を負例にする。
- **(d) 成果物影響** — semantic path disclosure を direct-byte 非出現として受理し、材料レポートの性質2と台帳の受理集合が実態より広がる。

### 6. 禁止語の母集合が campaign 由来識別子の全 producer を覆わない

- **(a) 何が壊れるか** — variant、src token、genome、WAL notes/evidence、候補順序ラベルなど、3禁止語と一致しない campaign 固有値が digest に残り得る。1 fixture の正例は入力分布全体の非開示を証明しない。
- **(b) 根拠** — payload は `make_critic_digest` 全文 `s2/plan.md:86-91`。green は identity projector 無しで admitted view を render し、projector は red にだけ渡る `p3_s4_loop.py:542-572`。ラベル自体も WAL 順で作る `p3_s4_loop.py:466-537`。role は genome 別情報と任意 notes を読む `critic.md:13-22`。
- **(c) 最小是正案** — green/red 双方を通す B-4 専用の型付き renderer を置き、identity-bearing field を明示列挙して中立 label へ射影する。WAL 由来自由文の各 channel に直接・間接識別子負例を置く。
- **(d) 成果物影響** — arm/campaign を推測できる特徴が critic の方向選択へ入り、certified 候補集合と primary paired outcome が treatment 外要因で変わる。

### 7. receipt の `arm + digest_sha256` は正しい reflux 分岐を証明しない

- **(a) 何が壊れるか** — off controller が誤って `reflux=True` で digest を作っても、`arm="off"` とその digest hash を書けば自己整合する。receipt に admitted view/WAL commitment がなく、consumer は再計算できない。通常の Python object なので arm field の後書換えも設計上未封鎖である。
- **(b) 根拠** — arm は controller 属性から導出するとだけ規定 `s2/plan.md:117-128`。receipt fields は view/WAL hash を持たない `s2/plan.md:138-161`。実切替は bool 1個 `p3_s4_loop.py:542-572`。
- **(c) 最小是正案** — arm 引数を `invoke` から除き、生成時 binding を private immutable record にする。receipt に admitted-view hash を持たせ、独立 verifier が同じ snapshot から arm 別 digest を再計算して exact equality を要求する。
- **(d) 成果物影響** — 赤入り off digest が有効 receipt として受理され、off の次 synthesis、certified 集合、B-4 効果量が直接汚染される。

### 8. provider・neutral root の再利用を pair receipt が検出できない

- **(a) 何が壊れるか** — 同じ provider を両 controller に持たせても、CLI が別 session ID を返せば pair 検査を通る。異なる controller ID は provider 分離を含意せず、receipt に provider instance/root commitment がない。
- **(b) 根拠** — pair が拒否するのは controller/session/campaign ID の同値だけ `s2/plan.md:121-136,163`。receipt fields に provider instance/neutral root がない `s2/plan.md:140-149`。session 集合は provider 内だけで、cross tracker は optional `claude_projected_provider.py:195-196,368-377`。
- **(c) 最小是正案** — on/off pair を単一 factory で同時生成し、provider の create-once lease ID と neutral-root commitment を receipt に含めて不一致を検査する。共有 session tracker も必須化する。
- **(d) 成果物影響** — arm 間で provider 状態や context が共有された block が正規標本に混ざり、台帳上だけ fresh と表示される。

### 9. `whiteboard.result` と digest が同じ試行を表す保証がない

- **(a) 何が壊れるか** — 別 campaign からコピーした checkpoint、または読み取り間の更新により、最新 digest と別試行の coarse result を組み合わせられる。iteration 数の一致だけでは origin・variant・attempt を束縛しない。
- **(b) 根拠** — plan は view と checkpoint を別々に読み、末尾 iteration だけ照合する `s2/plan.md:73,86-88`。既存 loader は campaign origin・entry 件数・iteration 整合を対象外と明記 `p3_s4_loop.py:744-758`、読み書きも独立 file 操作 `p3_s4_loop.py:786-806`。
- **(c) 最小是正案** — coarse result を同じ admitted WAL snapshot から導出する。難しければ checkpoint に campaign ID、terminal variant/attempt、view hash を持たせ、read後の再確認か単一 lock で snapshot を固定する。
- **(d) 成果物影響** — critic が誤った `success/fail/rejected` を受け、次候補、certified 到達、台帳の block outcome が食い違う。

### 10. receipt の主要 field が raw evidence から再検証できない

- **(a) 何が壊れるか** — `fresh_context=true`、`observed_tool_events=[]`、`capability_lowering` は provider が定数で書く。計画 receipt は raw envelope hashを落とし、`permission_denials_empty` 等を成功結果から再申告するため、consumer は事後検証できない。
- **(b) 根拠** — 定数 provenance は `claude_projected_provider.py:347-365`。raw envelope hash は存在する `:292-299,362` が、receipt 一覧 `s2/plan.md:140-149` にはない。F556 `docs/failures.md:14575-14587` の「値の転写を証拠鎖と誤認」と一致する。
- **(c) 最小是正案** — receipt に argv/config、payload、raw envelope、stderr の path/hash を束縛し、別 verifier が各 derived field を再計算する。定数 field は `claimed_*` として証拠 field から分離する。
- **(d) 成果物影響** — 実値を変えずに receipt の受理集合だけ恒真化でき、材料レポートと試行台帳の参照が検証不能になる。

### 11. `projection_sha256` が実際の projection closure を hash しない

- **(a) 何が壊れるか** — provider の argv/tool 構成、canonicalizer、`make_critic_digest`、identity renderer が変わっても、新規 module bytes だけの `projection_sha256` は同じままになり得る。異なる treatment/closure を同一 projection と誤分類する。
- **(b) 根拠** — hash 対象は新規 module 全 bytes のみ `s2/plan.md:151`。実挙動は provider `claude_projected_provider.py:101-241` と digest `p3_s4_loop.py:542-572` に依存する。plan 自身も両 file を無変更 consumer 扱いから外す `s2/plan.md:191-205`。
- **(c) 最小是正案** — provider、canonicalizer、p3 digest、identity projection、role pin、B-4 consumer を列挙した closure manifest を作り、その canonical hashを projection hash とする。代替は clean checkout commit の事前 pin と実走時照合。
- **(d) 成果物影響** — 意味の違う block が同じ projection 群へ併合され、効果量、材料レポートの参照 hash、台帳の比較可能性が壊れる。

### 12. 実走後 receipt は事前登録 §5 を埋める証拠にならない

- **(a) 何が壊れるか** — §5 は実走前 commit が必要だが、model snapshot は invocation 後の envelope で初めて得る。pair 内一致だけでは precommitted expected value との一致を示さず、provider は他 modelUsage entry の併存も拒否しない。
- **(b) 根拠** — prereg の時点条件 `phase3-b4-reflux-ablation-preregistration.md:32-48,142-175`。plan の対応表と pair 検査 `s2/plan.md:153-163`。provider は opus slug 1個を選ぶだけ `claude_projected_provider.py:317-329`。
- **(c) 最小是正案** — canary で得た model snapshot、executable/prompt/projection closure hash を §5 に commit し、その admission record を controller の必須入力にする。各 receipt は期待値との一致と modelUsage の exact 許可集合を検査する。
- **(d) 成果物影響** — 値が正しくても B-4 は事前登録実験として受理できず、材料レポートは登録追試を名乗れず、台帳は protocol violation を記録すべきになる。

### 13. 新 controller は production venue の consumer から到達不能なまま

- **(a) 何が壊れるか** — plan 通りでは新 module を直接 import するのは新 test だけで、現行 driver は digest file を書くだけである。旧 `Agent(critic)` route を使っても B-4 block や receipt を機械的に拒否する consumer がない。
- **(b) 根拠** — `p3_s4_loop.py` 無変更 `s2/plan.md:5-9`、直接 consumer は test のみ `s2/plan.md:191-205`、旧 route は開いたまま `s2/plan.md:217-228`。現 driver は LLM を spawn せず `p3_s4_loop.py:25-38`、digest を file に書くのみ `:1245-1258`。F591 `docs/failures.md:15268-15280` の production 到達不能と同型。
- **(c) 最小是正案** — 新 module に sanctioned B-4 orchestration entrypoint を置き、validated pair receipt が揃うまで critic response を synthesis へ渡さない。試行台帳 consumer は receipt 無し・legacy route・pair 未検証を無条件で protocol violation にする。
- **(d) 成果物影響** — 閉じた module が未使用のまま旧 critic が certified 候補を生成でき、材料レポートの B-4 行と試行台帳が非閉鎖 block を受理する。

## 総括

最も重い3件は次です。

1. **任意 runner/executable** により、3性質と receipt 全体を偽造できる。
2. **production consumer 取り残し** により、閉じた controller を一度も通らず B-4 を走らせられる。
3. **道具ゼロの非観測性** により、`observed_tool_events=[]` を含む receipt が能力遮断の証拠にならない。

したがって、現プランは採用してはいけません。最低でも、trusted executable/runner の事前 pin、全 tool surface の live 負例、admitted view からの arm/digest 再計算、raw evidence を検証する receipt verifier、そして B-4 production consumer への必須配線が必要です。