## 所見一覧 (番号、real / refuted / 判定不能、根拠、影響)

以下、`brief`＝射影された `s1-brief.md`、`plan`＝`s2-plan.md`、裁定名・probe・facts＝射影された `verbatim/` 内の各ファイル、`README`＝T-2224 insight、`driver`＝`orchestrator/campaign/between_run_floor.py` とする。real / refuted は各項目に記した疑義への判定である。

1. **refuted — P1 が D1373 を「規律2の関門」と解釈するのは誤り、という疑義。**  
   D1373:30 は関門廃止を「規律 2 の関門を人間の注意力へ移す」と明記する。同:18–20 は、この経路では trace 無効 build を verifier に通さず、当該判定が唯一の関門だと説明する。親の解釈は逐語と一致する。現行関門を維持し、本 wave で between-run を走らせない判断を支持する。

2. **refuted — within-run 登録を許し、between-run 生成を拒否する非対称が、直ちに裁定矛盾になるという疑義。**  
   D2044 項12:5–6 は実証済み protocol/workload の **within-run** 保留だけを解除する。D1373:3–7 は **between-run 生成経路**の受理条件を定める。後者の撤回は書かれていない。統計量や用途が異なり、同じ trace-disabled 計測であることから許可を横展開できない。なお driver:304 の関門は、同:159–175 の within-run／between-run 両測定より前にある。「within-run なら任意の経路で測ってよい」という解除でもない。

3. **real — P5 の「D1360 が禁じるのは性能比較値の流入」という限定は逐語より狭い。**  
   D1360:4–5 は stock 専用計測経路を「偵察としても解禁しない」とし、同:8–10 は正しさ未検証の性能観測を「公式 report・selector・比較表・順位・headline のいずれにも入れない」とする。比較・順位に使わない CV でも、公式 report に載せる読み方は成立する。phase doc も公式成果物として登録する以上、「物差しだから禁止対象外」と断定できない。登録根拠は、後続の明示的裁定 D2044 項12の用途限定解除に置くべきである。

4. **refuted — 4対の選定に漏れ・余計な対象があるという疑義。**  
   README:33–35 の新規3件と同:75 の既取得 mocc rr50 を合わせると、親の4対と一致する。指定資料に非 silo の5件目はない。legacy 2件と silo rr95 は非 silo 解除の対象外。非 silo rr5・cicada は同:124–126で未取得と明記される。

5. **real — 「hook を含む commit へ pin を進めれば関門を通る」は条件不足。**  
   driver:125–140 は commit 履歴や pin 文字列を検査せず、実 checkout の source を読む。コメント・literal `#if 0` 除去後、CMake の SOURCES に列挙された**同一ファイル**に `trace.hh` include、`#if TRACE`、`izanagi_trace::…(` が揃う必要がある。列挙外ファイルや header に hook があるだけでは足りない。  
   根拠：driver:75,112–140、`orchestrator/verifier/model.py:94–180`。plan:98–101,128 の「必要条件」「正しさを証明しない」は適切だが、実 checkout と具体的証拠条件を補う必要がある。tictoc はさらに baseline 対応が必要（driver:285–288）。

6. **real — 「between-run floor は現行 pin で起動不能」は対象を省くと過大。**  
   plan:54–55 は protocol を省いている。probe:1 は silo=True を示し、全 protocol の起動不能は支持しない。「本件の mocc／tictoc を現行 driver・source で実行すると、測定開始前に拒否される」と限定すべきである。

7. **refuted — login node の結果は計算ノードへ一切一般化できない、という疑義。**  
   同じ driver、同じ読取対象 source・CMake・ファイル解決条件なら、拒否は計算ノードでも同じと静的に判断できる。protocol 引数判定と source 関門は、環境選択・測定 profile・build より前にある（driver:285–325）。判定 helper も CPU・負荷・scheduler を参照しない。  
   ただし **pin SHA が同じだけでは十分でない**。helper は実ファイルを読むため、checkout、読取可否、参照先の違いは結果に影響し得る。「計算ノードで実走確認済み」とは書けない。

8. **real — plan の mocc rr50 欠落扱いは、新たに射影された一次値により訂正が必要。**  
   facts:6 に `miss_rate_at=0.14821268619041902`、`cv=0.014348130441228051`、`n=10` がある。したがって **LLC miss 14.821%、within-run CV 1.4348%、n=10** と出典付きで記載できる。README に数値がないという記述を根拠に、record にある値まで欠落扱いする必要はない。plan:25,47–48,91–92,160–161 および関連訂正・検査方針を修正する。

9. **判定不能 — accepted calibration が protocol の意味論的正しさを保証する、という主張。**  
   facts の `quality=accepted` と README:64–65 の trace 分離検査は確認できるが、verifier 通過の証拠ではない。D1373:9–11 も text-level 判定が意味論的正しさ・verifier 通過・測定値の正しさを証明しないと明記する。今回の登録に correctness certification を付加してはならない。

## 規律 2 との整合判定

**docs-only の限定登録は支持する。ただし P5 の理由付けと再開条件の記述を修正すること。**

D1373 の関門維持は逐語に直接支えられている。D2044 項12は、実証済みの within-run 較正を公式成果物へ入れる根拠になるが、between-run 関門の廃止、stock 専用計測経路の一般解禁、性能比較、正しさ認定を許可していない。

D1360 を広く読めば較正値の公式登録も禁止文に触れる。その緊張は、「CV は元から対象外だった」と言い換えず、**D2044 項12で明示された範囲だけ登録可能になった**と記すことで扱える。関門や verifier の弱体化を解決策にしてはならない。

また、D1639:4–5 の床値は session-median の between-run CV である。今回の within-run 登録では、論文環境節に必要な走行間ばらつきの実測を充足しない。brief:9 の研究前進説明にもこの区別を残す必要がある。

## 裁定の射程 (4 対の照合結果)

| 対象 | record | 照合根拠 | 判定 |
|---|---|---|---|
| tictoc rr50 | `calibration-9b49335d02ad4d2e.json` | README:17,33,131、facts:2 | 対象 |
| tictoc rr95 | `calibration-cb98513996e5ae35.json` | README:18,34,132、facts:4 | 対象 |
| mocc rr50 | `calibration-449d0ad22f13e366.json` | README:75、facts:6 | 対象 |
| mocc rr95 | `calibration-b3329d93417c76ad.json` | README:19,35,132、facts:8 | 対象 |

4件とも records=1,000,000、threads=48、n=10、quality=accepted。facts:9–13 は4件とも acquisition receipt の head SHA が `511c9538e4e8efa54b45cda62e72389ed3b706ec`、`pinned_clean=true` だったと示す。

README §8 の新規3件だけでは mocc rr50 を落としてしまうため、§4 の既取得一覧との合算が必要である。

5件目の非 silo 候補は指定資料にない。README:73–74 の legacy rr50 2件は silo 仮定、同:76 の rr95 は明示的に silo。いずれも本解除の範囲外であり、無効化するという意味ではない。非 silo rr5・cicada も対象外。

「4対」は索引として使えるが、記録された genome・workload・測定条件を保持し、同じ protocol／rratio のあらゆる構成が実証済みになったとは書かない。

## 書いてはいけない文の指摘

- **phase3 追記案：plan:35「性能比較や床値本走の完了を意味しない」**  
  否定による限定であり、違反文ではない。`accepted calibration` も較正の受理状態として妥当。ただし plan:54–55 の無限定な「between-run floor は…起動不能」は、本件2 protocol に限定する。

- **decisions 草案：plan:105「D1360 の stock 専用経路による certified cross-protocol 比較の禁止」**  
  certified 取得を主張してはいない。しかし禁止を certified 比較だけに狭め、uncertified な公式 report 流入を許すように読めるため修正する。  
  修正文例：  
  「D1360 の stock 専用計測経路の禁止を一般解除しない。今回公式成果物へ登録するのは、D2044 項12が明示的に保留解除した実証済み4対の within-run 較正に限る。」

- **worklog 草案：plan:158,169 の性能比較・床値本走への言及**  
  いずれも未実施・対象外の明記であり、違反文ではない。plan:168–170 の「完了」「remaining: none」は、T-2634 の較正登録完了だけに束縛し、実装・受入後に使用する。plan:139 がその前提を明記しているため、現段階の虚偽完了報告とは判定しない。

- **「解除により測定可能になった」**  
  3草案にこの肯定的主張は見当たらない。保留解除の対象は既取得較正の登録であり、新規 between-run 測定経路の開通と書き換えてはならない。

## 親 brief への訂正

1. **P1 は維持するが、再開条件を具体化する。**  
   mocc は pin 更新という操作名だけでなく、実 checkout の CMake 列挙 source が所定の text-level 証拠を満たすこと。tictoc はそれに加え baseline 対応が必要。いずれも測定成功・verifier 通過の十分条件ではない。

2. **P5 の「D1360 は性能比較値だけを禁じる」を削除する。**  
   D2044 項12による用途限定解除を登録根拠とする。phase doc なら公式 report の禁止と無関係、という説明は採らない。

3. **F2 は実測と静的帰結を分ける。**  
   probe:1–4 が示すのは述語値・BASELINES・引数解析。CLI 全体の rc=2、main の build 前 ValueError は driver から導く静的帰結であり、probe がその実走を記録したとは書かない。

4. **F3 の mocc rr50 の値は維持できる。**  
   CV 1.4348% は facts:6 に裏付けられる。plan の欠落扱いを採用せず、LLC miss 14.821% と n=10 も記載する。4件すべて n=10 は facts:2,4,6,8 で確認できる。

5. **P2 の「同じ定義」は within-run CV という統計量に限定する。**  
   n=10 の一致は測定経路・条件・binary の同一性や代替可能性を証明しない。

6. **P4 の結論を、今回の必要性で支える。**  
   baseline 登録だけでは tictoc の測定を開通できず、本件の既取得較正登録にも不要なので追加しない。「起動不能な baseline の存在自体が規律違反」という一般論にはしない。

7. **brief:72「本 wave は output/ を書かない」を修正する。**  
   同:80 の新規 insight 成果物と衝突する。「既存較正 record・凍結成果物は不変、新規 insight 記録は作成する」と区別する。

## 裁定パッケージ候補 (親が段 4 で決めるべき二択以上の争点)

1. **公式登録の説明根拠**
   - A：D2044 項12の明示的な用途限定解除として記す。**推奨。**
   - B：較正 CV は D1360 の禁止対象では元からなかったと記す。D1360 の広い禁止文に支えられず、採らない。

2. **mocc rr50 の値**
   - A：facts の record 一次値を根拠に LLC miss 14.821%、CV 1.4348%、n=10 を記す。**推奨。**
   - B：README の記述に限定し、欠落・丸め値を保持する。利用可能な一次値を反映せず、登録内容が不必要に不完全になる。

3. **between-run 再開条件**
   - A：実 checkout の証拠条件、tictoc baseline 対応、関門通過と実測成功の区別を記す。**推奨。**
   - B：「hook 付き pin に進めれば測定可能」と記す。実装が保証しないため採らない。

4. **計算ノードへの一般化**
   - A：「同じ driver・読取対象 source なら計算ノードでも測定開始前に拒否される」という静的帰結として記す。**推奨。**
   - B：login node の probe を計算ノード実走の証拠として扱う。証拠の射程を超えるため採らない。

これらは段4での文面・証拠採用の争点である。D1360 が決着済みとした stock 専用計測経路の解禁を、再び未裁定の二択に戻すものではない。

## 総括

**4対の既取得 within-run 較正を用途限定で登録し、D1373 の関門を維持する方針を支持する。** 主な修正点は、P5 の禁止範囲の説明、mocc rr50 の一次値反映、実 checkout に即した再開条件、probe の実測範囲と静的帰結の区別である。

指定資料を読み、静的検査のみ実施した。ファイル書込み、pytest、性能測定は行っていない。