## 判定と読解範囲

**must-fix は 2 件です。** stock 成立の成功条件と、stock に適用する condition gate の設計を修正する必要があります。既存の correctness 接続、同 campaign 方針、較正 CLI の骨格は支持します。

指定資料はすべて読めました。静的読解のみで、ファイル書込み・pytest・build・計測は実施していません。以下、L＝`p3_s4_loop.py`、P＝`pipeline.py`、C＝`loop.py`、I＝`ident.py`、S＝`source_digest.py`、J＝job shell、TL/TJ/TV＝指定された各 test と略記します。

## must-fix

**M1：非 STOCK の certified 結果を stock CLI の成功に含めている。**

- **根拠：** plan:86 は新規 certified／既存 certified 復元を rc=0 とする一方、plan:95–98 は非 STOCK を candidate label にするだけです。S:2316–2322 は digest 不一致をエラーにせず別 token にし、C:634–638、695、782–792 はそのまま評価へ渡します。L:1093–1105 の label は表示上の分類であり、stock 成立の拒否条件ではありません。
- **成果物への影響：** 非 STOCK の COMMIT が生成され、候補も成功すれば `compute-result.driver_rc=0` となる経路を、計画の受入テストが許します。
- **是正案：** `_run_stock_control_resolved` の成功条件に、評価した attempt の admitted source evidence が STOCK であることを加えてください。復元でも、復元した COMMIT に対応する BUILD_START／admission を確認し、非 STOCK・不明は非零終了とする。source を復元後の tree から再解決せず、WAL を書き換えないこと。最低限、「非 STOCK だが certified」の fixture を stock CLI に通して失敗する負例が必要です。

quarantine を省くこと自体は、固定した stock source を評価する入口として妥当です。ただし保証は「提案ではない」という名称ではなく、PIN、固定 template、source evidence、build 時の再照合にあります。S:2431–2447 の検査と P:1812–1817 の evidence 照合を維持しても、**STOCK であることを成功条件にしなければ対照保証にはなりません。** また、applied tree は bytes 無改変ではなく、digest 上の inert 対照です。

**M2：候補用 condition gate を stock にそのまま適用できるという前提が未成立。**

- **根拠：** plan:64 は stock に `_require_condition_gate` を必須化しています。しかし L:426–432 は `requested_value=-1` に対して、`float(-1)` のビット列を二つの期待値にした `MeaningCase` を組みます。B-5 §5.2 の `-1` は固定値 −1 ではなく適応 backoff です。b10:1001–1016、1027–1036 の先例は stock 枝・骨格・digest の検査であり、この候補用意味宣言の成立を証明しません。さらに TL:84–87 は当該 gate を autouse fixture で無効化しています。
- **成果物への影響：** stock が gate で停止して評価 WAL を生成できなくても、plan:284 の呼出し順中心のテストが通る受理集合になります。
- **是正案：** stock 用の supply／meaning の期待値を、適応枝の契約に基づいて確定してください。候補用宣言の流用を維持するなら、その宣言で stock の意味を検査できる根拠が必要です。TL では `_REAL_CONDITION_GATE` を使い、下位の外部実行だけを模擬して、`-1` 用宣言と拒否伝播を検査する。単に gate を省略したり、green を固定したりして解消してはいけません。

射影に gate evaluator 本体が含まれないため、実行時の具体的な拒否理由までは断定しません。問題は、**意味の異なる sentinel に候補用期待値を使う設計を、検査なしで確定していること**です。

## should

**S1：anomaly の負例を performance の先頭だけでなく、最終 repetition にも置く。**

- **根拠：** plan:306–307 は全成功と performance 初回拒否を予定しています。P:2185–2188、2436–2440 が保証すべきなのは全 repetition の成功です。
- **成果物への影響：** 「一度成功したら後続の赤を無視する」「最終回を省く」回帰を受入テストが見逃す余地があります。
- **是正案：** legacy と performance の先行回を成功させ、最後の performance を赤にする負例を追加し、bench 未実行・COMMIT 不在を確認してください。legacy 赤で performance に進まない負例も同じ表で扱えます。

**S2：campaign.lock に保存された値から実効 correctness を照合するテストが必要。**

- **根拠：** plan:267–274 は lock を記録先としますが、plan:298、301 は主に cfg 捕捉と evaluate 境界の検査です。I:583–602 の永続化までを直接検査していません。
- **成果物への影響：** 正しい cfg を途中で作っても、別の cfg で lock を作る実装を、別々の境界テストが受理する可能性があります。
- **是正案：** 実 lock の preimage を読み、その動作点と verify mode から復元した flags/reps が、実 loop から pipeline に渡ったものと一致することを確認してください。新しい receipt や WAL schema は不要です。

**S3：job rc と測定結果を混同しない負例を追加する。**

- **根拠：** L:3132–3136 の proposal CLI は停止理由と checkpoint の存在で成功を判定します。候補の `outcome=aborted/rejected` が必ず非零になる契約ではありません。plan:314 の任意 rc を返す stub だけでは、この違いを検査できません。
- **成果物への影響：** 候補が拒否され stock が成功したとき、`driver_rc=0` を「候補と stock の二本が測定成功」と読む実装・テストを排除できません。
- **是正案：** 候補拒否でも既存 CLI は rc=0 になり得ることをテストで固定し、対照成立の判断には両 attempt の WAL outcome と新規評価の有無を使う、と明記してください。既存候補 CLI の rc 契約を変更する必要はありません。

## 正しさゲートと exact correctness の記録

規律 2 の接続は、次の範囲で支持します。

| 要件 | 現物の根拠 |
|---|---|
| legacy を維持 | C:153–161 が追加 pass を選び、P:1719–1722 が legacy の後ろに追加 |
| anomaly を含む verifier 拒否で停止 | P:633–665 の certified 判定、2137–2143 の ABORT、2185–2188 の repetition 即停止 |
| 全 pass 通過後だけ COMMIT | P:2436–2440、2705–2720、2565–2575 |
| 拒否候補の bench を採らない | P:2707–2708 が拒否を返し、2715 の bench に進まない |
| bench-first を使わない | L:2012–2020 は screening を渡さず、P:2593 の既定は None |

pipeline は anomaly 数だけを独立判定するのではなく、verifier の certified 判定を受けて拒否します。したがって、実 verifier の赤 trace を使う plan の回帰試験は適切です。

**記録先として campaign.lock を使う案は、本 wave の「指定した exact 引数の記録」として条件付きで十分です。** P:215–223 の変換は決定論的で、完全な perf 構成と verify mode が永続化されれば performance correctness の flags/reps を復元できます。source は P:1899–1910、binary と toolchain は P:2030–2081、環境 authority は I:583–598、文法版は L:1563–1564 の既存記録と合わせて評価すべきです。

ただし、次は区別が必要です。

- lock だけに、実行 argv・binary・toolchain のすべてが入るわけではありません。
- 実 argv には P:438–440 の launch prefix と `clocks_per_us` もあります。
- 通常 campaign の verify payload は argv を記録しません。P:644–653 の argv 記録は qualification 用です。
- verifier mode/version、残余引数、seed の最終固定は §5.5 が §12 の発効束に残しています。

したがって「§5.5 全体が成立済み」とするのは過大ですが、今回独立 argv receipt を必須にするのも過剰です。S2 の永続化検査を追加し、予定引数の記録と実 argv の独立観測を区別すれば足ります。P:945–961 の exact payload 契約を壊して flags を足す必要はありません。

## identity と既存記録

**同 campaign とし、`--stock-control` 自体を identity に焼かない判断を支持します。** I:212–223 の preimage は spec、PIN、search tag/config、trial であり、評価する genome の集合ではありません。候補 only と pair が同 ID になるのは、この設計では意図した結果です。ID は「この job で pair を取得した」という証拠にはなりません。

較正時の `records/threads` 更新も意味変更ではありません。L:1562 と L:1634 の既存値は性能動作点に対応し、較正後も同じ意味で一致させます。`extime/reps/workload` の追加は動作点の識別を強めます。

`workload` の dict は、現行の balanced schedule と実行上衝突しません。C:433–444 の `name` 要求は `balanced_schedule is not None` の専用分岐です。S4 はその schedule を渡しません。共通 schema として交換可能だとは言えませんが、今回 key を改名する必要はありません。

K2 manifest は必須の同一性条件です。L:1611–1618 が knowledge level と manifest SHA を preimage に加えます。plan:136 の stock 側転送と plan:290 の両経路比較は適切で、critic の stock label だけではこの一致を証明できません。

`409e13f8…` の維持は、今回読んだ資料だけでは確定できません。同じ preimage なら同 ID ですが、較正・verify opt-in、manifest、policy、環境束縛の変更は ID を変えます。D2172 項3どおり、三巡目の候補 only 記録は保持し、fresh layout の pair 結果を別の実行証拠として追記すべきです。

## 順序・回数・失敗時の扱い

候補後の stock は、D2172 項3の K2 同 job pair として十分です。同項は stock 先行を要求していません。一方、§5.4 の初期 `current_perf` への供給には不足します。

**stock 先行を選ぶ env は今追加せず、設計メモに留める判断を支持します。** 現行 J:580–586 は保存済み proposal を読むため、呼出し順を逆転しても「初回 planner 前の stock」にはなりません。B-5 では stock 結果を planner 入力へ渡す接続が別途必要です。今回、先行 mode を消費する具体的 artifact／計測 ID が示されておらず、DW-G04 に照らして一般化を先行させる根拠がありません。

legacy 1 回＋performance 5 回は §5.5 に反しません。同節は trace extime=3 秒を定めますが、correctness の回数を指定していません。P:222 の reps 継承を保つ方針でよいです。ただし「3 秒×5」は trace 実行時間であり、verifier を含む所要時間ではありません。β には各 workload の verifier wall、総 session wall、メモリ、timeout、完走回数の実測と、read-heavy を避けた workload 選択の根拠を残す必要があります。短縮目的で黙って一回に減らすべきではありません。

候補失敗後も stock を試みる価値は、同 allocation の環境確認と対照証拠を残せることです。候補の欠測を埋めるものではありません。追加 build／verify により残時間を消費し、job kill なら stock 完走は保証できません。

plan:145 の集約は、**stock だけが非零ならその非零を返すため、stock 単独失敗を rc=0 に隠しません。** 両方失敗した場合は候補 rc だけが `compute-result` に残りますが、job 全体としては失敗です。両 rc の stdout と WAL を残す現案でよく、追加 receipt は不要です。

## nit

**N1：親 brief の「3 file の live pin なし」は、射影資料だけでは再証明できない。**

- **根拠：** TJ:418–425、654–687 には J の現役の逐語 pin が実在します。「凍結 artifact からの live hash pin がない」という限定なら、これとは別の主張です。
- **成果物への影響：** 文言だけの訂正では WAL／identity は変わりません。
- **是正案：** 「凍結物による pin」と「job 契約テストの逐語 pin」を区別し、前者には検索対象・結果を添えてください。三 file の非占有も射影内では未検証です。

**N2：「stock 評価は実走済み」という一般化は強すぎる。**

- **根拠：** b10:799–803、1027–1036 は実装と検査の存在を示しますが、今回の S4 template/compiler/gate での成功ログではありません。A-1 paired の実走 artifact は射影にありません。`run_campaign` API の存在も実走証拠ではありません。
- **成果物への影響：** 主張の訂正だけでは評価成果物は変わりません。
- **是正案：** 「stock genome と inert 検査の実装先例あり、S4 実 compiler 成立は未測定」と限定してください。

**N3：Pegasus 空 prefix と stock manifest 束縛は、静的成立と実測成立を分ける。**

- **根拠：** P:1723–1737 は契約と一致する空 prefix を明示的に許します。これは静的に確認できます。一方、新 stock 経路の Pegasus 実走と manifest 転送は未実装・未測定です。
- **成果物への影響：** 記述の限定だけでは成果物は変わりません。
- **是正案：** 空 prefix の非対応を問題視する必要はありません。計画された契約テストと、land 後の実走結果を別々に報告してください。

## 総括

**must-fix：2 件。** M1 は非 STOCK の成功扱い、M2 は stock に対する condition gate の意味宣言とテストの不足です。

| provisional 裁定 | 判定 |
|---|---|
| P1 同 campaign | **支持**。同じ preimage が条件。pair 成立は ID から判断しない |
| P2 applied template の stock | **条件付き**。M1・M2 を解消し、実 compiler 成立は別途確認 |
| P3 較正 CLI | **支持**。二口必須、完全な動作点の identity 束縛は妥当 |
| P4 verify opt-in／記録 | **条件付き**。lock 永続化検査を追加。§5.5 全体の成立とは区別 |
| P5 候補後・失敗後も stock | **条件付き**。rc 集約は妥当。driver 成功と測定成功を区別 |
| P6 段構成 | **支持**。pipeline 編集の有無にかかわらず二レンズの必要性がある |

Q1〜Q4 への回答：

- **Q1：可。** terminal 復元と fresh layout 運用を維持する。duplicate は新規同 job session と認定しない。
- **Q2：可。** legacy 1＋performance 5 は事前登録違反ではない。β で verifier 所要を測る。
- **Q3：可。** 較正二口の同時指定と、verify-performance の較正必須を支持する。
- **Q4：条件付きで可。** 実 compiler 確認を land 後に分けてよい。ただし今回、非 STOCK の成功拒否と stock 用 gate の契約検査を実装する。模擬テストの成功を inert 成立の証拠にはしない。