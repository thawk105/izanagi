**結論: NO-GO（現行案の計測投入）。** workload patch と driver の実装は進められるが、以下の must-fix を事前記述と判定規則に反映してから計測する必要がある。根拠は指定された射影資料の静的検査に限る。ソース実装と親の実測は独立には確認していない。

以下、`brief` は `s1-brief.md`、`plan` は `s2-plan.md`、`addenda` は `s3-parent-addenda.md`、`draft` は `readme-prereg-draft.md` を指す。

### 所見

**A-1｜must-fix｜plan §3、draft §2 — 勝つ腕の選択が未定義**
主張: 有望点を「eligible 腕/R 比の最大値」で選ぶと、S や区間 GC が点を選び得る。代表点と隣接点で**同じ M の腕**が基準を満たす規則も明記されていない。根拠: `plan:33–40,50`、`draft:26,30`。
成果物への影響: M が勝っていないのに、1.5/1.3 達成と推奨する余地が残る。
直し方: 点選択に使える M の腕を事前列挙し、同一腕について両点の比を照合する。S・IGC は対照として別表示する。

**A-2｜must-fix｜plan §3、draft §2 — 長い読み手の完了条件が 0 超に弱められている**
主張: `batch_commits>0` でも、R の多数の完了が処置腕でほぼ消える勝ちを通す。draft の「R より大きく減る」に数値境界がない。根拠: `plan:48,50`、`draft:29`、`request-md_42.txt:18`。
成果物への影響: 長い読み手を事実上止めて得た throughput が勝ちに数えられる。
直し方: 同じ round の R に対する batch commit 数または完了率の許容下限を、結果を見る前に数値で固定する。両腕の完了数と比を各対に保存する。

**A-3｜must-fix｜plan §3・§8、brief 不変条件 — trace 検査が恒真になり得る**
主張: verifier の rc と anomaly 0 だけでは、長い read-only tx と更新の重なり、IGC の剪定、C の前進が trace 走行で起きたと分からない。plan 自身も発火 0 の可能性を認める。根拠: `brief:29–30`、`plan:52,54,89–90`、`draft:36–39`。
成果物への影響: 未行使の機構を「正しさ検査済み」と記載し得る。
直し方: 腕ごとに trace 走行の非空 witness（batch 完了、公開、剪定、前進試行・成功など）を定め、0 なら走行を延ばすか「未検証」とする。判定器には既知の壊し正例を通して検出能力も確認する。

**A-4｜must-fix｜plan §1・§8 — C 行数と batch 完了数の同一視**
主張: `batch_commits` は batch worker の slot、trace の C 行数は通常 worker を含む全 commit のはずであり、両者の一致を要求する説明は整合しない。根拠: `plan:15,54,89`。
成果物への影響: 正しい走行を失格にするか、誤った件数照合を採用する。
直し方: 全 commit 数と全 C 行数を照合し、batch 完了数は worker ID で絞った C 行または独立した batch witness と照合する。

**A-5｜must-fix｜addenda P4、draft §1・§3 — R−LR/R は上限ではない**
主張: R−LR は通常 worker を 48 本から 47 本に変え、batch worker も除く。抽選、競合、GC 公開頻度、leader の仕事、throughput の分子が変わるため、この比に数学的な上限性はない。根拠: `addenda:14`、`plan:35–38`、`draft:7–9,41`。
成果物への影響: 比が 1.5 未満というだけで「版保持を攻めても届かない」と誤って撤退を推奨し得る。
直し方: R−LR を**読み手除去の対照**として記載し、上限・不達の証明には使わない。通常 worker 数と throughput の計数対象も明記する。

**A-6｜must-fix｜plan §3、brief 不変条件 — perf build の分離を macro 名だけに依存できない**
主張: `COUNT` 等の名前を拒否する設計だけでは、計数・trace コードを別名や header 経由で取り込む経路を閉じられない。終了時出力も hot path の加算を増やさないという主張までで、測定窓の外にあることは未証明。根拠: `CLAUDE.md:58–65`、`brief:22,28–30`、`plan:15,42`。
成果物への影響: 診断コードまたは出力費用が性能比に混入する。
直し方: perf の実 compile command と前処理結果で検証専用経路の除去を確認する。batch 行は timed throughput 算出・計測窓の後に出すことを確認し、diag TPS は比の入力から拒否する。

**A-7｜must-fix｜plan §3、addenda P5 — 対の成立と単独性の定義が足りない**
主張: P5 は両 GC 間隔を同一 job にまとめるが、腕と間隔を合わせた位置均衡、他 job を含む node の排他、予備と 30 秒比較の独立性を実行記録から検査する規則がない。「残存 benchmark process」の検査だけでは node 単独性を証明できない。根拠: `plan:44–50,61`、`addenda:9–15`。
成果物への影響: 順序・共存負荷・予備 run の再利用が腕/R 比を動かす。
直し方: job 配置、node 割当、実行順、同居 process、run ID を記録して拒否条件を設ける。30 秒 run ID は予備と重複禁止にする。

**A-8｜must-fix｜addenda P5、plan §7 — build 共有の provenance と 5 分枠**
主張: binary SHA だけでは、その binary が予定した pin・patch 順・macro・compiler から作られたことを示せない。基本 11～12 本でも、22.6 秒/本なら 1 job は約 249～271 秒で、準備費用を含めると 5 分を超え得る。根拠: `addenda:15`、`plan:42,82–84`。
成果物への影響: 別 build を走らせても同条件の性能値として集約し得る。
直し方: binary ごとに source/pin、patch と順序、macro、compile command、compiler、binary SHA を結ぶ manifest を確定し、node local copy 後に照合する。smoke の build 実時間で shard 数を決める。

**A-9｜should｜plan §2 — gate の owner 検査と header 経路**
主張: owner の `#if` 2 箇所と companion header の 2 箇所を数えるだけでは、header 内の条件分岐が意図した owner TU で有効か、0 で完全 inert かを証明できない。根拠: `plan:11,17,23`、`brief:32`。
成果物への影響: macro を登録しても、実際の workload が腕間で揃わない可能性がある。
直し方: owner TU の実 compile flags による前処理で 0/1 の差分を検査し、header がその TU に取り込まれたことを確認する。

**A-10｜should｜plan §2 — 総和 pin の加算根拠が未確認**
主張: 「298 に owner site 数だけ足す」は、総和が何を数えるかを source 側で確認した結論として提示されていない。companion を別登録することと、総和に含めないことは同義ではない。根拠: `plan:23–25`。
成果物への影響: gate test が誤った定数を固定し、登録漏れを見逃す。
直し方: 完成 patch の実 site と総和の計算式から期待値を再導出する。定数だけを先に更新しない。

**A-11｜should｜brief 前提、addenda 実測、plan §8 — patch 適用結果の一般化**
主張: 親が示したのは既存 patch の特定順序での適用成功である。新 workload patch は未作成で、trace 上の適用成功も build・実行・意味の一致を示さない。根拠: `brief:15–19`、`addenda:3–7`、`plan:19,88`。
成果物への影響: 作れない腕、または異なる workload の腕を比較表に入れる。
直し方: 全 perf・diag・trace 木で patch を 1 件ずつ適用し、実 build と workload の出力・挙動を確認してから腕を投入する。

**A-12｜must-fix｜plan §7、request 計算枠 — 隣接点を削ると継続基準を判定できない**
主張: 予算超過時に「長時間比較の第 2 点」を削る案は、隣接 ≥1.3 という事前基準を失わせる。根拠: `plan:50,84`、`request-md_42.txt:15–18`、`addenda:11`。
成果物への影響: 代表点だけの勝ちを、基準達成として扱う余地が生じる。
直し方: 隣接点を削った場合は継続基準を「判定不能」と固定する。判断に必要なら addenda の相談経路を使い、両点を維持する。

**A-13｜should｜draft §1・§2 — SOTA への推奨範囲**
主張: draft は Steam・HANA を SOTA に含め、その未比較を認めている。R に対する 1.5/1.3 の達成だけで「C の SOTA に勝った」や論文成立とは言えない。根拠: `draft:14–22,26–30`、`request-md_42.txt:8–17`。
成果物への影響: 一次資料の推奨が、この wave の実測範囲を超える。
直し方: 最終推奨を「R に対する研究継続判断」と明記し、区間 GC の未比較を独立した残課題として残す。

## 総括

- 現行案は同一 round の対比と R 側での GC 間隔選択を備えているが、**勝つ M の腕**を固定する規則が足りない。
- `batch_commits>0` は「長い読み手が完了しなくなる勝ち」を除外する条件として不足する。
- trace の anomaly 0 と、IGC・C が実際に発火したことは別に確認する必要がある。
- P4 の R−LR/R は有用な対照値になり得るが、利得の上限とは記載できない。
- P5 の binary 共有は可能な設計だが、SHA と build 入力の束縛、実測に基づく job 分割が必要である。
- 隣接点を削った結果からは 1.5/1.3 の継続基準を判定できない。
- ソース実装・実行結果は未調査であり、上記の実効性は親の段階で確認が必要である。