# 段 4 裁定 — [T-2273][T-2750] 成分粒度 (file → node) は実装しない、docs-only で閉じる

裁定者: 親 (dev-wave manager)。入力: 段 1 brief、段 2 plan、段 3 レンズ A (正しさ境界) / レンズ B (実効性)、親の追加実測 (相方・相関)。裁定 inbox の再走査: main は wave 開始時から不変 (38353207f)、T-2750 / T-2273 に関する新しい裁定記録は無し (decisions.md 最新は「項35 — 受入短縮は実測の最遅 worker を対象とする … 効果を先に測り、未確認のまま実装しない」で本裁定と整合)。

## 所見の裁定 (real / refuted、採用 / 不採用、scope 内 / 外)

| # | 出所 | 所見 | 裁定 | 扱い |
|---|---|---|---|---|
| A1 | lensA-1 / plan | 素直な案 (a) (file union の削除) は `test_s8c_preregistration_predicates.py::test_repository_candidate_uses_real_s8c_budget_module` (group 無し・resource リスト外、function fixture が実 object store へ `git add`/`write-tree`/`commit-tree`) の跨ホスト排他を失う。現状は file 閉包だけが同 host に留めている (golden `test_real_repo_serialization.py:438` に明記)。lock は `/tmp` で同一 host 限定 | **real** (親が code で確認: `:4701-4732, :4736-4746, :4765`) | must-fix (実装する場合)。本 wave は実装しないので「実装しない理由」として記録 |
| A2 | lensA-2 | 「リスト外の module fixture consumer は必ず排他を失う」は不成立。module fixture `repository_candidate_commit` (invariant 側) の consumer は独自 group を持ち同 shard に残る。確認済みの無保護例は **function fixture** | **refuted** (brief (P4) の記述を修正) | insight の (P4) 記述を「function fixture writer + 衝突閉包 (resource node + fixture-owned consumer + 明示 affinity)」へ改める |
| A3 | lensA-3 | inventory golden は実 repo アクセスの網羅的検出器ではない (宣言済み inventory 内の分類一致 + golden 列挙 fixture の consumer 一致 + resource node と交差する module/session fixture を seed にした閉包)。seed の無い fixture・function fixture・import 副作用は全探索外 | **real** | 記録。案 (a) の検出力維持の証明には衝突閉包の独立 literal が要る → 新設の検査 = 依頼の scope 外 (追加 gate・検査は scope 外) |
| A4 | lensA-4 | D711 の file 閉包は現状では排他の防壁も担う。案 (a) では `assignment_closure_gate` の `file_shards` を独立定義の affinity 検算で置き換える必要があり、`_validate_real_repo_shard_state` は緩めなくてよい | **real** | 記録 (実装する場合の設計制約) |
| A5 | lensA-5 | plan の自己証明 (割付器出力だけで検出力を証明) という攻撃は現記述には当たらない。ただし未実証 | **refuted** | — |
| A6 | lensA-6 | brief の D358 要約は D1618 (全 node の affinity を保った runtime 分割) を反映すべき | **real** | insight で訂正 |
| A7 | lensA 射程判定 | 規律 2 の射程は (c) 一部だけ射程内: 衝突 consumer の同居制約を失わせる部分は防壁の除去、それ以外の file 同居制約は D711 改訂の対象 | **採用** | 本 wave は防壁に触れない (実装しない) |
| B1 | lensB-1 | (P1) は「固定 duration model の下限不変」から「実 wall の期待利得 0」へ飛躍。simulation は相方・開始遅れ・fixture 再構築・配置による duration 変化を除外。原表の訂正: tail 19.9 秒は 17/20 走 (3 走は 7.5〜8.7)、平均占有は 161〜417 秒 | **real** (brief の誤記 2 点を含む) | (P1) の表現を「採用証拠不足 + 固定 duration model では最遅 shard の下限不変 + 実 wall 改善は未実証」へ改める。「期待利得 0 の実証」とは書かない |
| B2 | lensB-2 | 最長 node の移動は最遅 shard・合計 wall・資源占有を別々に変える。simulation では予測 wall の合計が 690.2 → hybrid 748.3 / node 838.3 秒へ増える (b5 群が別 shard へ散り床を作る)。主指標は `max(shard wall)` (D1620) | **real** | 記録: 均等化は最大値を動かさず合計を増やす方向 (資源効率の逆行) |
| B3 | lensB-3 | (P2) 「初期 2 unit 構造」と「約 20 秒を必ず払う」は別。相方 identity は割付・reorder で変わりうる。「worker k は cost 順 k と 48+k」の一般化は G11 (mixed-scope の dequeue 順) に穴がある | **real** | (P2) を「最忙 worker は 20/20 走で item 2 個、相方 約 20 秒は 17/20 走。session 5141225c の相方は `test_m3_ignored_extra_and_missing` (台帳 22 秒) と同定したが順位説明は一般化しない」へ改める。reorder 側 pairing は次の一手候補 (scope 外、上限 5.8%) |
| B4 | lensB-4 | (P3) 因果分離不能は妥当だが期待値 0 は導けない。`contention_check.py` の「他 47 worker 平均」は実際には (全占有 − 最長 node)/47 で相方を含む。相関 0.993 は共通の build 待ち・host 状態でも説明できる | **real** | 記録 (script の量の名前を訂正して記載)。(P3) は「既存 data では分離不能、期待値は未数値化」 |
| B5 | lensB-5 | 20 走は現行挙動の観察には強いが変更後の反実仮想を確定しない (tip・selected・台帳が異なる)。99 走の最遅 identity 94/1/4、主指標は全 shard の最大値 | **real** | 記録 |
| B6 | lensB-6 | T-2236 の「床」を負荷の話だけへ読み替えると原文の意図を落とす。最強の読みは「file 閉包が重い t080 群と背景仕事を同 host へ集め、競合が t080 自身を長くしている」。ただし README はそれを paired 実測していない | **real** (親の「wall の命題として偽」は言い過ぎ) | insight を「負荷の命題としては真、wall への波及は未実証 (paired 実測が無い)」へ改める |
| B7 | lensB-7 | 実験費用の判断と効果ゼロの証明を分ける。見送りの理由は「採用証拠不足と機会費用」 | **real** | 裁定文の理由に採用 |

## 裁定

1. **案 (a)・(b) とも本 wave では実装しない (4→7→8→9)。** 理由 (強い順): (i) 依頼の採用条件「検出力維持 + D104 の効果実証」は、素直な案 (a) では検出力維持が成立しない (A1: 跨ホスト排他の防壁を外す)。安全に実装するには明示 affinity の補完・D711 gate 4 の裁定改訂・衝突閉包の独立検査の新設が要り、後 2 者は依頼が scope 外とした「追加 gate・検査」に当たる。(ii) 固定 duration model (D1019 の式) では最遅 shard の下限 306.1 秒が 3 通りとも同値で、負荷の均等化は最大値を動かさない。実 wall 改善の経路は「同 host 競合の低減で最長 node 自身が速くなる」だけで、既存 99 session からは分離できず期待値を数値化できない。分かるのは相方 約 20 秒 (中央値 347.7 の 5.8%) が上限の目安で D357 の「変化なし」域に入ること。(iii) decisions 項35「効果を先に測り、未確認のまま実装しない」と D104 決定 3「効果を示せない機構は land しない」に従う。
2. **記録の言い方。** 「期待利得 0 を実証した」「T-2236 の床の主張は偽」とは書かない。「固定 duration model では最遅 shard の下限不変、実 wall 改善は未実証、採用条件不成立 (検出力維持が素直な案では成立せず、効果実証は paired 実測でしか得られない) につき実装せず閉じる」と書く。
3. **T-2750 は完了 (閉じる)。T-2273 (P1) は更新:** 現行の律速 = 最長 node (t080 e2e b5 群、225〜500 秒) + 相方 約 20 秒 + 固定費 約 66 秒。割付では 5 分に届かない。次の候補は (a) reorder 側で最長 unit の worker へ最小 unit を対にする pairing (上限 5.8%)、(b) 安全な案 (a) の試作 + 同一 tip の paired 測定 (費用 ≈ Codex author + 変異 + 受入 ≥6 走、期待値未数値化)、(c) b5 群 5 本の単体所要 (D2068 が fixture 側 3 案を却下済み、残る候補は e2e の分割・parametrize の縮約 = 受理集合に触れるため別裁定)。いずれも本 wave では起票のみ (新規 T は (a) と (b) を 1 件ずつ P3 で登録)。
4. **変異 matrix は免除 (実装面差分ゼロ、DW-S04)。受入全走は免除しない。** 実 repo を読む検査 (三軸語走査 `s8b_holdout_freeze search`、`test_s8b_repo_scan_invariant.py`) は記録 commit 前に実走する。
5. **段 5・6 は飛ばす。** 段 6 の敵対レビューは実装が無いので起動しない。段 3 の 2 レンズが独立検査を担った (両方 accepted)。

## やらない理由の最強の形 (記録)

実装すべき側の最強の形 (レンズ B): 「simulation は固定 duration の下限不変しか示さず wall 利得 0 ではない。成分分割は t080 群の同居仕事・相方・host を変え、既知の競合膨張 (D357) を減らす可能性がある。毎 wave で繰り返す受入への累積利益を考えれば、安全な候補を試作し同一 allocation の paired 測定で採否を決める価値がある。」— 親はこれを real と認める。ただし現証拠が支持するのは条件付きの試作・測定までで、land すべきという結論は成立しない (レンズ B 自身の但し書き)。試作の費用は安全化 (affinity 補完 + D711 改訂 + 閉包検査) を含めると本 wave の scope を超えるため、次の一手として起票し本 wave では払わない。
