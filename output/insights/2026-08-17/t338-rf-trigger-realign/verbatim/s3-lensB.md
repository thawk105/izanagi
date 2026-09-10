所見 1 — D1/D2/B を land しても、実装 wave は進まず、公開層待ちが D292 の解禁 decision 待ちへ一段ずれるだけである。

real — `s2-plan.md:73-77,208-210`、`docs/decisions.md:13473`、`docs/decisions.md:13583-13588`、`orchestrator/publication/report.py:229-231`。`pilot_submission` は維持され、実装 consumer も増えない。

**成果物影響** — certified 選択・材料レポート・公表台帳・受理集合は不変で、pilot/producer artifact は生成されず、実質的に次の実装 wave は着手できない。

最小の是正案 — 本 decision を「解禁前の依存分離」と明記し、直後の wave を D292 準拠の pilot 専用解禁 decision と指定する。

所見 2 — P1 は末文だけを失効させる範囲自体よりも、pilot 実走と公表台帳への投入を分離する保存条件が不足している。

real — `s2-plan.md:67-71` は pilot を追補 P 凍結から切り離すが、`docs/decisions.md:13359-13363` は公表 core の分析 admission に追補 P を要求し、`docs/decisions.md:13460-13462` は P blob/p03 を別承認としている。

**成果物影響** — 現在値は変わらないが、将来の解禁 decision を「P 未凍結でも pilot 結果を公表台帳へ入れてよい」と誤読すると、材料レポート・proof chain・公表 entry の受理集合が不正に広がる。

最小の是正案 — 「pilot は実走可能になり得るが、P の `requires_addendum_p`、P blob 未承認、p03 未確定、公表台帳への投入禁止は維持する」と明記する。

所見 3 — D229 の順序は保たれているが、「D229 (6) を supersede しない」という書き方が、D1 による D162 (10)(ii) の限定的 supersede と衝突する。

real — `docs/decisions.md:10750-10755` は順序と D162 非 supersede を同時に定め、`s2-plan.md:57-60,85-89` は D162 を改訂しつつ D229 (6) 全体を非 supersede と書く。

**成果物影響** — 即時の certified 値は変わらないが、後続 resolver が D1 を拒否するか、逆に D229 の順序まで変更されたと読むため、発火条件と着手順序の参照が分岐する。

最小の是正案 — 「D229 の順序と pilot による計測設計は保存し、D229 内の D162 非 supersede の手続き文だけを D1 の範囲で supersede する」と分解する。

所見 4 — 無し（P4 の worklog action は二重在籍を作らない）。

refuted — 現在の active は `docs/worklog.md:2398-2399` に T338/T339 が各一件で、`tools/spool_fold.py:1760` は同一 ID の複数操作を拒否し、`tools/spool_fold.py:1727-1740,1804-1810` は active 集合保存則を検査する。`docs/phase3.md:698` に見送り先 H3 も存在する。

**成果物影響** — fold 後は T338 だけが active に残り、T339 は完了ではなく見送り台帳へ移る。certified 選択・材料レポート・受理集合への影響はない。

最小の是正案 — 無し。`見送り`、H4 `研究・計測系`、理由、正しい `base` を維持する。

所見 5 — ユーザー裁定 D1 + D2 → B に D3 の 2 段階化が紛れ込んでいる所見は無し。

refuted — `s1-brief.md:11-17` が裁定を明記し、`s2-plan.md:85-89,96-102` は全順序と本走後置を明記し、D3 を却下している。

**成果物影響** — 段階数、受理集合、既存成果物の値は変わらない。

最小の是正案 — 無し。ただし所見 3 の限定的 supersede 表現は追加する。

所見 6 — 「末文」の前向き失効は、D282/D322 のような対象部分・発効時点・保存範囲の一意な記録になっていない。

real — `s2-plan.md:67-71` は自然言語の「末文」だけで、`docs/decisions.md:12884-12891` の `forward_supersedes/preserved` や `docs/decisions.md:14600-14603` の明示的な一文限定を備えていない。さらに D291 は固定 fold commit の bytes を読む (`orchestrator/publication/approval_d291.py:25-29,486-487`)。

**成果物影響** — resolver が「D291 の禁止状態は維持」と読む場合と、「`addendum_p_freeze_precondition` 全体を失効」と読む場合に分かれ、pilot 解禁・公表台帳受理・report の `possible_supersession` 解釈が不一致になる。

最小の是正案 — `D291.operational_state_on_fold.addendum_p_freeze_precondition` の引用文を exact に指定し、発効は新 decision の fold 後の将来 pilot 試行だけ、D291 bytes・禁止状態・公表 admission は保存と書く。

所見 7 — M5 の「`docs/decisions.md` を読む live consumer は 1 つだけ」は過大な一般化である。

real（nit）— `s1-brief.md:27` に対し、`orchestrator/campaign/s8c_preregistration.py:1384-1403` も固定 commit の decisions 見出しを読む。D291 の意味を解釈する consumer が report だけ、という限定なら成立する。

**成果物影響** — 今回の新 D 追加で s8c の固定 ruling 検査値は変わらないため、certified 選択等への直接影響はない。consumer 棚卸しの根拠だけが不正確になる。

最小の是正案 — M5 を「D291 の supersession semantics を消費する production consumer は report.py の 1 件。固定 ruling を検査する generic reader は別にある」と狭める。

pytest、受入全走、check_docs、spool fold の実走はしていない。静的検査のみで、緑は主張しない。

## 総括

NO-GO。最も重いのは所見 1 で、この decision は pilot を動かさず、D291 の依存を D292 の解禁 decision 待ちへ移すだけである。