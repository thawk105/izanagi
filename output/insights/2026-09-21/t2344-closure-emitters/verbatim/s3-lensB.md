## 所見 1: corpus 0 本での無条件収載は、裁定の参照関係から導けない

**判定: real。最大の欠陥。**

**根拠:** `rulings-verbatim.md` の D1653「決定」は、実在 corpus の確認を収載条件として明記する。D1770 は D1653 を追認し、変更したのは再発行禁止の説明の射程だけである。D2193「決定」も「収載条件は D1653 のとおり実在 corpus の確認」と明記する。D2194 項 4 は同 commit 収載を **「(D2193)」付きで参照**しており、corpus 条件の撤廃・上書きを明記していない。末尾のユーザー回答控えにも、その撤廃はない。

| 案 | 判定 |
|---|---|
| A: corpus 0 でも収載 | 現在の逐語だけでは支持できない。新しい、より具体的な裁定であるという理由だけで、参照先の条件を消せない。 |
| B: corpus 0 なら収載しない | 収載判断時点で 0 なら整合する。ただし着手時の 0 を land まで固定すると、新たな corpus を取り逃がす。 |
| C: 受入直前に再確認して決める | 三案では最も整合的。存在確認できれば同 commit に収載し、未確認なら収載しない。 |

D2193 の「8 日の空白」は、**既に存在した lock の可読性を同 commit で維持する理由**であり、存在未確認 grammar を収載する例外条件ではない。

親の理由について、(i) は将来 corpus が生まれる可能性と再確認の必要性を支えるが、無条件収載までは支えない。(ii) の「D1653 の必須条件はすべて満たす」は corpus 条件を落としている。(iii) の「production grammar として main に存在すれば投機的収載ではない」は、裁定に書かれていない条件の置換である。

**欠陥箇所:** brief P2 と、それを「本件明示指示」として採用した plan「方針と確認結果」。

**直し方:** C を採り、最終的に選んだ差分を受入対象にする。二案の準備または直前の差分変更は実際の追加工数であり、変更後は関連検査と受入を取り直す。判断を runtime 分岐にはしない。

## 所見 2: 「実在 corpus は 0 本」は、走査結果を越える一般化

**判定: real。**

**根拠:** `measured-facts.md` §2 の対象は、指定された二つの root のうち除外 directory を除き、さらに **mtime ≥ 2026-09-20 21:55** を満たす lock に限られる。この結果から直接言えるのは「その走査条件で 85-key v2 を検出しなかった」である。mtime を保存した複製や走査外の記録まで不存在とは証明できない。本相談では外部 corpus を再走査していない。

また、今後 85-key の記録が見つかっても、件数だけでは exact-85 grammar の証明にならない。前 wave は wire key 列と記録 commit の宣言順まで照合している（一次資料 `t2344-closure-stage1/README.md` §2）。

**欠陥箇所:** 親 measured-facts §2、brief P2 の断定と「現時点の実害 0」への一般化。

**直し方:** 「指定走査範囲・時刻・mtime 条件では未検出」に限定する。再走査で候補を得た場合は、wire 列と記録 commit の ordered tuple を照合して corpus 確認とする。

## 所見 3: 11 本という収載数は正しいが、「発行器 6 本」は全数ではない

**判定: 11 本の選定は refuted。全発行器を列挙したという読みは real。**

**根拠:** D2194 項 4 は六つの module を名指ししている。`closure-head.json` では、そのうち五つが producer-only 10 本にも含まれ、`autonomous_trial_completeness.py` だけは既存 tuple 起点の発見集合内にある。静的照合でも、既存 ordered tuple ＋ sorted 追加 11 本は proposed 96 本と一致し、次段 23 本との重複は 0 だった。

一方、六つ以外にも次が存在する。

- `backoff_sweep_report.py:60` は certified view を要求し、同 `:132` ではレポートを書き出す。
- `backoff_requested_us.py:512` は certified epoch gate を呼ぶ。
- `b10_backoff_static_tail_formal.py:393`、`t1998_stock_inline_pair.py:981` も certified consumer である。
- `layer3_report.py:1032`、`:1064` にも certified 経路がある。

したがって六つは、現在の全 consumer／全発行器を列挙した集合ではなく、**今回の裁定が選んだ seed 集合**である。

なお検査時、HEAD は `5efd69367`、local main は `21641fee7` へ前進していた。ただし両者間で `orchestrator/campaign` と `orchestrator/reports` の差分はなかった。

**欠陥箇所:** P1 の実装範囲には欠陥なし。brief・insight で六つを全発行器の意味に一般化する場合に欠陥となる。

**直し方:** 「D2194 項 4 が名指しした発行器 6 本」と書く。追加発見した consumer を本 wave の収載対象へ足す必要はない。

## 所見 4: scope 案は適合するが、「発行器起点も閉じた」は言えない

**判定: scope 案への攻撃は refuted。閉包完了への言い換えは real。**

**根拠:** brief P3 と plan「artifact_admission.py の scope と歴史分岐」は、D2081 の四条件を満たす。96 path、日付・commit と本版 tuple による測定の区別、内訳の削除、集合外の除外、非 import 委譲の括弧書きを保持し、発行器名や実行時計算を scope に加えていない。

D2081 条件 4 の「発行器の名前」は、同決定の対象である scope 文言への焼込みを禁じたもの。日付付き insight や test 名で裁定対象を同定することまで一律禁止する根拠はない。「指定された六つの path を収載した」という事実記述も、推移閉包全体の source-bound 保証とは異なる。

ただし、proposed-rooted 発見集合が和集合 173 と一致しても、**収載集合は 96 で、77 が未収載**である。発見できることと束縛済みであることは別である。

**欠陥箇所:** 現在の P3・plan scope にはなし。将来の insight 草稿での一般化に注意が必要。

**直し方:** 「推移閉包へ向けた段階追加」は未収載 77 と併記すればよい。「発行器起点も閉じた」は使わず、「指定 seed を追加した結果、静的発見集合が当該和集合と一致した」と限定する。

## 所見 5: 受理集合の開示は概ね正しいが、land までの発生と既存運用を分ける必要がある

**判定: 拒否の説明は refuted。影響なしへの一般化は real。**

**根拠:** `artifact_admission.py:1037` は purpose によって decoder を分け、`:1186` は certified だけに現行 capture を要求する。したがって exact-85 の歴史収載を行っても、96 へ前進した checkout の certified consumer では旧 85 を救わない。並走 wave が旧 85 を生成すれば、その記録はこの拒否対象になる。

clean committed の拡張は D1163 の既存条件の対象追加であり、記録 map と現在 map の同一性要求ではない。plan が dirty 拒否に加え、同変更の commit 後には元の記録 epoch のまま受理する対照を置くのは適切。

運用との照合では、B-10 shape job は既に dirty tree を拒否する（`tools/pegasus/b10_backoff_shape_campaign.sh:209`）。s8b oracle は spec 承認等の前提で止まっている（`docs/phase3-8b-restart-runbook.md` W-4、worklog carry 元の entry 1742）。8c runbook は提案を既存 driver へ渡す運用を記しているが、新収載の発行器 source を未 commit のまま使うことを保証してはいない。確認範囲で、今回の dirty 拒否と衝突する必須運用は壊せなかった。

**欠陥箇所:** brief scope の条件不足。plan は開発 checkout の影響を比較的正確に書いている。

**直し方:** 再走査時点の確認件数と、旧 grammar を新 checkout の certified consumer が拒否する性質を別々に開示する。HISTORICAL_RAW の維持を「最新 consumer での certified 再解析も維持」と説明しない。

## 所見 6: unavailable 分岐の scope を独立文字列で検査する局所追随が抜けている

**判定: real。**

**根拠:** `s8b_oracle_report.py:595` は unavailable 分岐にも現行 scope 二定数を投影する。既存 `test_s8b_oracle_report.py:1068` の unreadable test は state・reason・拒否を検査するが、scope 二項を検査しない。`:1009` の別 test も期待値を production 定数から取得している。

plan はこの consumer を認識しているのに、変更対象 test を五ファイルに固定し、unavailable 出力の独立期待文字列を追加していない。admission の定数検査だけでは、当該分岐が古い文言を固定して返す回帰を検出できない。

**欠陥箇所:** plan「既存 test の追随」と五ファイル限定。

**直し方:** 既存 unreadable test に、現行 96 scope 二項の独立 literal assertion を加える。新 module や gate は不要。

## 所見 7: 残る局所修正と過剰実装は、P2 を除いて壊せなかった

**判定: refuted。**

**根拠:** plan は以下を明示的に拾っている。

- `contract_loader_binding.py:2`、`:58`、`:61` の「85」。
- `test_s1_9pair_figure_provenance.py:74` の live `CURRENT_E0_EPOCH` と、凍結 report の区別。
- `test_layer3_report.py:584` の helper、歴史 param 三箇所、現行 grammar のラベル。
- timeout の独立期待値 850→960。

既存兄弟 validator の追加は D1653 が指定した構成であり、汎用互換層・新 module・registry・実行時計算の導入ではない。exact-63 の validator や scope を書き換える計画も見つからなかった。

**欠陥箇所:** P2 の収載条件を除き、brief／plan とも該当なし。

**直し方:** 上記の局所追随は残す。P2 を非収載とする場合は、exact-85 専用実装・test 群をまとめて削除し、古い grammar の検査は維持する。

## 所見 8: 変異の帰属は plan で改善されたが、無意味な source drift による赤を除く対照が不足

**判定: real。**

**根拠:** brief P6 は exact-85 分岐削除を「負例」に並べるが、これは歴史可読性の正例を壊す変異である。plan はこれを正例側へ移し、superset validator の直接呼出し、整合した通常 decoder の緩和、scope の独立 literal 比較を指定しており、この修正は妥当。

ただし先行 insight `t2344-closure-stage1/README.md` §6 では、**comment 一行だけの M0 が layer3 の五 node を落とした**実績がある。実 repo の live capture が dirty を検出したためで、狙った変異の意味とは無関係だった。今回の plan は KeyError による偽の kill を除くが、この既知の混入原因に対する M0 と runner 選定を明示していない。

**欠陥箇所:** brief P6 の分類、plan「変異事前登録候補」の対照不足。

**直し方:** 「収載追加」「歴史可読性」「未知 grammar」「certified 隔離」「歴史 scope 凍結」を分ける。無意味な comment 変更の対照を置き、live drift だけで赤になる node を狙った変異の kill 根拠から除く。

## 所見 9: 受入増分は exact-85 の 85 件だけでは見積もれない

**判定: real。**

**根拠:** `orchestrator/tests/acceptance_duration_ledger.json` の該当 per-path 群は **63 件時点**で、exact-63 の新設群はまだ載っていない。静的集計による単純外挿は次のとおり。

| 群 | ledger の合計 | 今回の増分見積り |
|---|---:|---:|
| 起動前 drift 拒否 63 件 | 20.820 秒 | ＋11 件 ≈3.64 秒 |
| live drift 拒否 63 件 | 14.000 秒 | ＋11 件 ≈2.44 秒 |
| 記録 blob mismatch 63 件 | 13.150 秒 | ＋11 件 ≈2.30 秒 |
| dirty disk の test helper 63 件 | 13.747 秒 | ＋11 件 ≈2.40 秒 |
| codec missing-key 63 件 | 0.064 秒 | ＋11 件 ≈0.01 秒 |
| exact-85 歴史 blob mismatch 新設 | exact-62 の62件が2.771秒 | 85 件 ≈3.80 秒 |

この六群だけで、**85→96 の今回増分は約14.6秒の逐次 duration 合計**。さらに新11本の certified drift、歴史正負例、layer3 param が加わるため、おおむね16秒以上を初期見積りとするのが妥当である。fixture が96本になる既存 node 自体の増加費用は、この外挿に含まれない。

一方、ledger の63件から96件への差は、既存五群だけで約32.4秒。これを今回だけの増分と数えてもいけない。いずれも shard 並列実行の wall time の予測ではない。

**欠陥箇所:** brief／plan の受入増分見積りの欠落。

**直し方:** ledger の古さ、今回増分、未計上の fixture 費用を区別して記録する。P2 を非収載とする場合は歴史85群の費用を除く。

## 総括

最大の risk は、D2194 の参照を corpus 条件の撤廃と読み替え、未確認の exact-85 を無条件収載すること。三案では C を支持する。
11 本の選定と scope 案は壊せなかったが、全発行器の網羅・閉包完了は名乗れない。
局所的な不足は unavailable scope の独立検査と、変異の無意味な drift を除く対照。
静的検査のみ。書込み・pytest は未実施。任意探索の `worklog-phase3-0921-1778.md` と二つの launcher glob は不存在だったため、現行 worklog・runbook・実在コードで補った。