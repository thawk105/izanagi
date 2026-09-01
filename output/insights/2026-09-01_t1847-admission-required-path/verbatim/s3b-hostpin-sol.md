## 現状の実測

結論から言うと、(A) を単独で採ると、受入を赤から skip に変えるだけで複数の固有な正しさ検査が失われます。

親の実測資料では、全走は `19035 passed / 21 error / 5 failed` で、5 pin はホストにも repo にも存在しません。これは今回再実測せず、`host-pin-facts.md:5-7,40-48` の事実を採用しました。pytest も実行していません。

依存経路は次の通りです。

- module fixture は根の存在だけを見て skip しますが、その後 POS/NEG snapshot と prompt を構築します。`test_codex_reasoning_ab.py:787-836`
- POS snapshot の golden は author/fix1/fix2 の 3 rollout を要求します。NEG の golden は空です。`tools/codex_reasoning_ab.py:925-978,3268-3289`
- POS/NEG prompt はそれぞれの rollout を要求します。`tools/codex_reasoning_ab.py:3671-3731`
- したがって現行の一体型 fixture は POS、NEG、author、fix1、fix2 の全 5 pin が必要です。
- ガードなしの 5 collected node は、m2 が補助 3 pin、prompt の 3 parameter が POS pin、collector が POS pinを使います。`test_codex_reasoning_ab.py:3128-3144,8575-8624`

fixture に依存する 21 test 関数が現に検査する性質は以下です。なお `test_m3_focus_artifact_directions` は 3 parameter です。親の実測上の「21 errors」と個々の collection item の対応は、collect-only をしていないため確認していません。

- frozen snapshot と Git 閉包:
  - POS/NEG の exact numstat。`:1957-1965`
  - integrated/artifact commit が到達不能で、ref が指定 branch だけであること。`:1968-1984`
  - commit-graph 不在、object-info 残留なし、禁止 commit と focus 履歴なし。`:2133-2168`
  - stale commit-graph の検出と manifest 化。`:2448-2470`
  - HEAD pin、mode、symbolic HEAD、ignored extra、必須ファイル欠落の拒否。`:3119-3189`
  - POS/NEG ごとの focus artifact 方向。`:3192-3208`
  - base の不変性、index 意味論、再帰 submodule、grafts の拒否。`:3211-3240`
  - POS/NEG の submodule 状態不一致。`:6104-6115`
  - artifact commit の再注入拒否。`:7139-7151`
- schedule と supervisor:
  - schema_version 無しの legacy schedule と異なる arm の許容。`:7056-7065`
  - pair の順序、環境からの `GIT_*` 除去、sandbox、identity。`:8627-8655`
  - writable bind が receipt directory を含まないこと。`:8658-8679`
  - attempt 4 を launch 前に拒否。`:11961-11978`
  - prelaunch 例外時の pair 完了記録、ゼロ課金、次世代 retry lineage。`:11981-12083`
- material replay:
  - fake experiment 全体の成功、集計値、判定、余分な session の拒否。`:8796-8852`
  - material manifest digest の差し替え拒否。`:8855-8877`
  - 成功した snapshot evidence だけを adjudication へ渡すこと。`:9254-9372`
  - shared oracle の各 run で pre/post binding を検査すること。`:9375-9489`

ガードなし側はさらに、実 rollout からの二経路 golden 一致と exact hash、prompt の置換回数 0/9/10、POS rollout の SHA、16 行目の token slice、ledger usage を検査します。`:3128-3144,8575-8624`

## 規律 2 との関係

判定は、**(A) 単独は規律 2 に触れる正しさゲートの弱体化**です。

既存 fixture に skip があることは、「root 自体が無い開発環境では optional」という設計意図の証拠にはなります。`:787-790` しかし次の理由で、26 件全部を恒久 skip へ変える根拠にはなりません。

- 既存条件は「root 不在」であり、「canonical host で frozen pin が保持期間切れになった場合」まで明示的に認めた契約ではありません。
- ガードなしの 5 node には、その optionality 自体が実装されていません。
- m1、m2、m3 はファイル冒頭で expected mutation node として明記されています。`:4-20` 恒久 skip なら該当 mutation を kill しない受入になり得ます。
- digest exchange など重複の大きい検査もありますが、mode、symbolic HEAD、focus 方向、grafts、pre/post replay、prelaunch retry などは同じ振る舞いを検査する独立 node が見つかりませんでした。

「永久に skip される test 名だけが残る」状態は、pytest の論理上は pass ではありません。しかし skip を含む全走を合格として扱うなら、その性質について反例が一切評価されないため、運用上は恒真ゲート相当です。後段に被覆を誤認させる危険は、削除より大きいです。

## 被覆の重複

検索は、射影された test ファイル内で `rg` により fixture、対象 assertion 文言、`_REAL_ROLLOUT`、`_compare_golden_routes`、`verify_snapshot` などを検索し、AST で test 関数への所属を確認しました。

重複は部分的です。

- rollout 探索と pin 配線は強く重複しています。
  - zero/duplicate、session identity: `test_codex_reasoning_ab.py:7154-7231`
  - pinned candidate、SHA、深い配置、fallback: `:7792-7999`
  - author/fix1/fix2 と POS/NEG の pin 配線: `:8366-8491`
- frozen provenance の定数値は一部が独立に固定されています。`:1765-1790`
- synthetic snapshot 構築と custom spec は既にあります。`:3741-3838,4250-4390`
  - HEAD mismatch は synthetic node に重複があります。`:5519-5554`
  - submodule、filesystem、closure の下位性質にも多数の合成入力 node があります。
- material manifest digest 差し替えは独立に重複しています。`:13230-13253`
- token ledger の validation は合成 rollout で広く検査されています。`:12086-12245`
- material packet の snapshot evidence 要求は下位関数で独立検査されています。`:15196-15238`

一方、次は同値な重複がありません。

- 実 3 rollout から二経路で同じ golden を導出し、exact historical hash に一致すること。`_compare_golden_routes` を実データで通す node は m2 だけです。
- 実 POS prompt が旧 root を exactly 9 回含むこと。
- 実 POS rollout の SHA、16 行目の token slice、実 usage 値。
- mode、symbolic HEAD、focus 方向、grafts、legacy arm pairing、artifact commit 再注入の exact behavioral node。
- supervisor の完全な bind 集合、pre/post replay、成功 evidence のみの forwarding、attempt 4、prelaunch pair/retry。
- full fake experiment には synthetic な近似がありますが、既存の host-dependent node と同じ経路・assertion 集合ではありません。`:8951-9251`

従って、skip の損失は「歴史的 bytes の検査だけ」ではありません。歴史的 fixture を便宜的な入力としていた一般的な正しさ検査も一緒に消えます。

## 推す案

**第三案を推します。履歴依存の性質と一般的な正しさの性質を分解し、後者を合成入力へ移植する案です。**

具体的には次の切り分けです。

- snapshot、supervisor、schedule、material replay の一般的な性質は、既存の synthetic snapshot、direct supervisor、synthetic manifest/replay helper を使って常時実行可能な node に作り替える。
- prompt 置換と golden 二経路も、synthetic JSONL、計算した SHA、external task manifest、synthetic Git commits で機能面を再現する。
- 「2026-07-29 の exact bytes そのものとの一致」だけは、元 bytes が無いため復元不能です。この部分は裁定を得て撤去するか、受入被覆ではない historical audit と明記する必要があります。私は永久 skip より撤去を推します。

実現可能性は既存コードが裏付けています。

- 合成 rollout と identity 探索: `:7154-7231`
- 合成 snapshot と spec: `:3741-3838,4250-4390`
- history 不要の direct supervisor launch: `:1142-1196`
- external manifest の prompt 経路: `:8494-8572`
- synthetic material replay: `:8951-9251`

この案は失われた rollout bytes を再生成せず、repo へ取り込む元 bytes も要求しません。ただし historical bytes との exact 一致だけは、どの案でも回復できません。その損失は明示的な裁定対象にすべきです。

(A) 単独は変更が小さい反面、固有被覆を暗黙に消します。(B) で関連 node 全部を撤去すると、合成入力で維持できる被覆まで捨てます。二者択一なら永久 skip より (B) の方が正直ですが、最善は性質分解です。

## 述語の設計

(A) を暫定採用する場合でも、単なる bool の「見つかった」判定にはすべきではありません。

- pin は `TASK_MANIFEST` の session id と SHA を正本にする。`:330-378`
- 利用可能とは次の全条件です。
  1. session identity に一致する rollout が exactly 1 件解決する。
  2. 解決 path の bytes が pin された SHA と一致する。
  3. 読取りと JSON/session identity 検査が成功する。
- `_find_rollout` の戻り値だけでは不十分です。高速候補の SHA 不一致を捕捉した後、full scan に fallback し、unique identity file を SHA 再検査なしで返せます。`tools/codex_reasoning_ab.py:612-637` したがって probe は戻り path に `_verify_rollout_sha` を必ず明示適用します。`:640-655`
- skip にしてよいのは exact な zero-match だけです。duplicate、wrong SHA、壊れた JSON、予期しない例外は test failure に残します。全部を `except Exception: skip` にしてはいけません。
- node ごとの最小依存にします。
  - 現行の一体型 `benchmark_snapshots`: 5 pin 全部。
  - m2: author/fix1/fix2。
  - prompt 3 parameter と collector: POS のみ。
  - fixture を POS/NEG に分割するなら、POS snapshot は POS+補助3件、NEG snapshot は NEG のみ。
- `_REAL_ROLLOUT` の固定日付 path を直接読む node は、probe が返した resolved path を使うよう変更します。そうしないと、別ディレクトリで正しく解決した場合でも直接読みに失敗します。
- probe 自身には、tmp_path 上の合成 JSONL で「exact pin は利用可能」「zero は missing」「duplicate と wrong SHA は failure」を検査する常時実行 node を置きます。これで probe が壊れて常に missing を返す変異を検出できます。
- 実 pin が本当に全件消えた状態と、実環境向け設定が誤って全件 missing になった状態は、skip された実 node だけでは区別できません。missing label 一覧と skip 数を受入結果に明示し、これを「全被覆 green」と報告しない運用が必要です。

## 変更単位

**独立 wave にすべきです。**

本 wave の変更は B-4 admission record であり、この赤へ到達せず、対象 tool/test は main と byte 同一だと親資料が確認しています。`host-pin-facts.md:109-118`

また、この問題は全 wave の受入を止める横断的な基盤障害です。本 wave に混ぜると、admission 変更と correctness-gate 再設計の provenance、レビュー、回帰範囲が結合します。独立の先行 wave で修正し、その後に本 wave を更新するのが適切です。

## 総括

(A) 単独は、固有の mutation・snapshot・replay 被覆を恒久 skip に変えるため規律 2 に触れます。  
pin 探索そのものには十分な合成入力被覆がありますが、赤い node 全体の被覆は重複していません。  
推奨は、一般的な性質を合成入力へ移植し、復元不能な historical byte binding だけを明示裁定する第三案です。  
暫定 skip を使うなら、node ごとの最小 pin、identity+SHA、zero-match のみ skip という三値 probe が必要です。  
pytest は実行しておらず、host 上の欠落事実と全走結果は親の実測資料に依拠しています。  
変更は B-4 admission wave へ混ぜず、全 wave 共通の独立 wave とすべきです。