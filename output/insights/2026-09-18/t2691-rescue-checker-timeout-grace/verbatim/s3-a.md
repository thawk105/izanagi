## 同値問題の検算

以下、`brief` は指定の `s1-brief.md`、`plan` は指定の `s2-plan.md`。行番号は変更前。全指定ファイルを読み、静的検査した。編集・pytest・変異実行は行っていない。

**real：brief の「親の timer は Popen 前」「子の期限は必ず親より遅い」は成立しない。**

- 親の `started` は elapsed 計測用であり、timeout の期限起点ではない（`tools/check_branch_rescue.py:1567`）。
- 使用中の Python は `/usr/bin/python3`。その実装では、`Popen` 後に `communicate(timeout=…)` を呼び、そこで期限を作る（`/usr/lib/python3.10/subprocess.py:503`、`:1149`）。
- 子の期限起点は `assess()` 冒頭の `assess_started` ではなく、その後の `Git` 構築時（`tools/check_branch_landed.py:1668`、`:1675`）。
- 通常の起動順序では子期限が後になる説明と実測は整合する。ただし、親が `communicate` 前にスケジューリングで遅れれば、その順序も保証されない。

影響：`brief:17` を放置すると、実測で観測した `checker-timeout` を全走行に一般化し、現行でも回収できる `assessment-timeout`／`checker_rc=2` を説明できない。

**real：子の早期終了と、報告の回収失敗を混同している。**

`COMMAND_TIMEOUT_SECONDS=45` と `min(command_timeout, remaining)` により、例えば子予算60秒・開始直後のGitコマンドが45秒でtimeoutする条件では、全体期限前に `assessment-timeout` を返せる（`tools/check_branch_landed.py:40`、`:227`、`:241`）。一方、`_batch_check_path_candidates` の検査は `remaining <= 0` なので、これは期限**前**の打切りではない（同`:750`）。

外側を延長しても、45秒で打ち切った探索が再開して確定判定になるわけではない。ただし、その理由JSONは回収可能である。個別コマンド上限は既存の別契約であり、本waveの改修対象ではない。

影響：`brief:6` の「100%落とす」を放置すると、子自身が探索を打ち切った `assessment-timeout` と、親が報告を失った `checker-timeout` の原因を誤分類する。

## 修正案の受理集合

**JSON検証条件について所見なし（検査した根拠：`tools/check_branch_rescue.py:1592`〜`:1620`、`plan:33`〜`:39`）。**

P1の差分だけなら、改行数、JSON/schema、rc↔verdict、対象OID、conclusive、削除非承認の検査は変わらない。D922の証拠条件を変更する差分もない。

ただし、**時間を含む受理集合は広がる**。これは `indeterminate` の理由回収だけに限定されない。従来の親期限後に届いた、契約準拠の `landed`／`not-landed` も回収対象になる。

D498はこの区別を明記している（`docs/decisions.md:20682`）。宣言した子予算を実効的に確保するという理屈は本件にも当てはまり、正しさの証拠条件を緩める変更ではない。ただしD498の起点移動と違い、固定2秒の加算は起動時間を完全に補償するものではない。

影響：`brief:26` の説明を「受理集合不変」と解釈すると、修正後にJSONが確定判定へ変わり、他の不完全要因がなければ親rcが2から0／3へ変わる可能性を見落とす（`tools/check_branch_rescue.py:1631`、`:2141`）。

`min(…, overall_remaining)` は残り、全体の設定予算も変わらない（同`:1985`、`:2067`）。ただし**実所要が不変という意味ではない**。各件の追加待機は同じ全体予算を消費する。

**scope 外 real：overall値は厳密なwall-clock上限ではない。** 残時間を取得した後に一時ディレクトリ・wrapperを準備し、終了後にも後処理する（同`:228`、`:238`、`:2067`）。`plan:138` はこの既存制約を正しく記している。裁定パッケージ候補に留め、本waveで改修しない。

影響：準備処理等が遅い条件では公称全体予算を超過し、後続処理が不完全となってrc=2になりうる。

## GRACE の根拠

**倍率と母集合の記載について所見なし（検査した根拠：`plan:26`〜`:31`、`docs/dev-wave/operations.md:104`）。**

最大値0.133860497秒に対する2秒は約14.94倍。8走、T=1を6走・T=8を2走という記載も生出力と一致する。

**疑い：適用regimeとの一致は十分に裏付けられていない。**

生出力のloadは23.69〜26.64。hostname、CPU数、共有FSの状態、親の環境準備時間は記録されていない。「login node」という場所の一致だけでは、軽〜中負荷という分類や掃除時の負荷分布との一致までは確認できない。`git ls-files` の遅延をPython import時間の根拠に使うこともできない（`brief:15`、`:27`）。

2秒は**観測した8走に基づく暫定的な余裕**としては説明できるが、共有FS高負荷を含めた回収保証にはならない。

影響：適用範囲を広く書きすぎると、高負荷時に再び `checker-timeout`／`child-report-unavailable`／rc=2となる結果を想定外として扱ってしまう。

また、追加待機の害は「同じ理由に戻るだけ」に限定されない。複数件で余裕を消費すれば、後続commit、終了snapshot、ledger auditに残る時間が減る（`tools/check_branch_rescue.py:2042`、`:2079`、`:2112`）。これは誤った確定判定を受理する害ではなく、**全体の可視化がさらに欠ける可能性**である。

## test の実効性

**変更行への到達について所見なし（検査した根拠：`plan:78`〜`:84`、`tools/check_branch_rescue.py:1576`〜`:1588`）。**

計画どおり親のsubprocess・時計を差し替えなければ、fake checkerでも変更対象の外側timeoutを実際に通る。既存のmonkeypatch型テストとは役割が異なる。

**real：P4の未証明unit回収要件を、planの正例は検証しない。**

`plan:65`〜`:75` のpayloadには `proof_units` がなく、`:86` は欠落理由を検証している。説明自体は正確だが、`brief:29` が求める具体的な未証明unitの回収証拠にはならない。

是正は、同じ正例payloadに既存形式の未証明unitを1件入れ、その識別情報・理由の回収を確認することで足りる。追加sleepや実checkerテストは要らない。

影響：放置すると、期限後JSONのreasonは回収できても、`unproven_unit_details` が欠ける回帰を新規正例が見逃す。

時間境界の評価は次のとおり。

- 正例の終了余裕は約1.7秒あり、M4対策でsleepを2.5秒へ延ばす案より余裕がある。
- 沈黙例の上限10秒は余裕がある。下限2.8秒は、M4の約2秒と分離する。
- overall例の上限1.5秒には公称打切り0.5秒から1秒の余裕がある。ただしelapsedにはwrapper作成・削除も含まれる。

**疑い：flake率と追加所要+5秒以内は未確定。** 公称4.8秒に対して余裕0.2秒しかなく、`plan:90` の4.82〜4.96秒を裏付ける当該テストの実測はない。

影響：環境遅延により正しい実装が赤になるか、追加所要制約を超える。productionのJSON・台帳・rcへの直接変更はない。

実checkerによる期限到達を通常テストへ追加する必要はない。変更機構は実subprocessのfakeで検証でき、既存実checkerテストもある（`orchestrator/tests/test_check_branch_rescue.py:1758`、`:1789`）。段6の同条件T=1／8の2/2回収は今回の実repo確認として足りるが、将来の全負荷での保証とは分ける。

## 変異の単一理由性

**通常の実行条件では、担当テストと失敗機構の対応に所見なし（検査した根拠：`plan:98`〜`:110`、`docs/dev-wave/mutation.md:7`）。**

| 変異 | 担当 | 単一の失敗機構 | 成果物への影響 |
|---|---|---|---|
| M1：GRACE→0 | 正例(a) | 報告到着前に親timeout | reasonが`checker-timeout`、checker_rcがNoneになる |
| M2：overall cap除去 | overall例(c) | 0.5秒capを守らず約7秒待つ | 理由・rcは同じでも時間契約を破る |
| M3：子予算にも加算 | 正例(a) | argvに従う子が3.3秒眠み、親3秒を超える | 理由JSON・unitを回収できなくなる |
| M4：加算をmaxへ変更 | 沈黙例(b) | 約2秒で切り、下限2.8秒を割る | 許された報告待機区間を1秒短縮する |

M4を正例の長いsleepで殺す必要はない。planの算術は正しく、2.5秒案は合計6秒となり、+5秒制約にも反する。

段4ではM4の置換を **`min(max(timeout, GRACE), overall_remaining)`** と明記する必要がある。外側式全体を `max(timeout, GRACE)` に置換するとoverall capも消え、M2を混ぜた変異になる（`plan:103`）。

**疑い：時間遅延による変異のmask。** M4で親準備・終了処理等が0.8秒以上増えれば下限を満たしうる。M3も親の待機開始前の大きな遅延で関係が変わりうる。実測時に別要因の赤やSURVIVEDを成功扱いしないことが必要。

影響：放置すると、時間契約を破る実装を変異検査済みと誤認する。M1／M3はreason文字列だけでなく、checker_rc・報告内容の回収失敗をkill根拠にする。

等価変異の追加価値は小さい。追加するなら `min` の引数順交換など、許容される有限正数入力で等価な変異をSURVIVED期待にできる。ただし新しい機構の裏取りにはならず、本waveの必須項目にはしない。

## docs

**planの置換案について所見なし（検査した根拠：`plan:119`〜`:121`、`docs/unreachable-object-ledger.md:91`）。**

「JSONを回収できれば」という条件とoverall残時間のcapが入り、brief P6の無条件な説明より正確である。判定件数×（子予算＋2秒）にinventory等を足す見積りも必要。ただし性能保証ではなく、件別待機の保守的な見積りである。

**real：briefの「checker-timeoutは予算＋余裕でも応答しない場合」だけでは条件不足。**

overall残時間が短ければ、予算＋余裕より前にも `checker-timeout` になる。残時間が最初から0以下なら `overall-timeout` になる（`tools/check_branch_rescue.py:1568`、`:1584`）。また、子の `assessment-timeout` には45秒の個別コマンド上限も含まれる。

影響：`brief:31` をそのまま文書化すると、短いoverall残時間による台帳の `assessment_reason` を子の応答異常と誤読する。planの条件付き文言を維持すれば、この誤りは避けられる。

## 親 brief の実測値と一般化

| 主張 | 検算結果・根拠 |
|---|---|
| 子8走、すべてrc=2 | 一致。`overshoot-T1.txt:1`〜`:6`、`overshoot-T8.txt:1`〜`:2` |
| wall−T=0.103〜0.134秒 | 一致。厳密には0.103562748〜0.133860497秒 |
| 子の内部超過0.002〜0.030秒 | `total_elapsed−T`なら丸めとして一致。ただし期限起点以前の初期化時間も含む（`tools/check_branch_landed.py:1668`、`:1675`、`:2007`） |
| Python起動0.073〜0.077秒 | **疑い：指定ログには独立計測がなく検算不能**。wallから子のtotal_elapsedを引いた残差は約0.0905〜0.1234秒で、起動・出力・終了等を分離できない |
| 親で0/2回収 | 一致。`parent-repro.txt:1`〜`:2`。この2条件を超えた失敗率は示さない |
| `_audit`の子にdeadline引数がない | 一致。`tools/check_branch_rescue.py:1797`、`tools/audit_dangling_commits.py:1977`〜`:2023`。ただし内部の有限待機や所要計測まで無いわけではない |
| `_audit`の子は理由JSONを出さない | 一致。テキスト報告とrcを返す（`tools/audit_dangling_commits.py:2066`〜`:2107`） |

内訳を断定したままにすると、2秒の根拠を誤って起動時間の保証に一般化し、実際に残る `checker-timeout`／rc=2の条件を説明できない。

**real：適用経路と回収成果物の説明にも省略がある。**

`--ledger-check` **単独**では `_landed_assessment` を通らない。対象は `--branch`／`--retire-worktree` を伴うpreview経路であり、掃除コマンドは実際にそれらを併用する（`tools/check_branch_rescue.py:2007`、`:2100`、`.claude/commands/cleanup-branches.md:39`）。

また、親の返却値はreason・unit詳細等への射影で、子の `phase_outcomes` 全体を返してはいない（`tools/check_branch_rescue.py:1621`〜`:1632`）。台帳ファイルの `assessment_reason` を自動更新する変更でもない。

影響：`brief:6` を放置すると、ledger-check単独や既存台帳の再評価まで改善した、あるいはphase outcome全文を回収したと過大報告する。是正は完了報告の記述修正に限定し、CLI・台帳・返却schemaを改修しない。

## 総括

P1の2箇所のproduction差分に、正しさの検証条件を緩める欠陥は見つからなかった。ただし、次を修正してから実装・実測結果を評価すべきである。

- briefの「Popen前」「必ず」「100%」を、実装上の起点と観測した2条件に限定する。
- JSON検証条件の不変と、時間を含む受理集合の拡大を区別する。
- 2秒の根拠を観測8走に限定し、共有FS高負荷の保証にしない。
- 同じfake正例に具体的な未証明unitを加え、P4の回収要件を満たす。
- M4はoverall capを残す単独変異として登録する。
- 改善対象をpreview経路の理由・unit回収と記し、phase全文や台帳自動更新まで主張しない。

追加所要+5秒、M1〜M4のkill、実checkerの2/2回収は未検証。今回の静的検査を緑の実測結果として扱わない。