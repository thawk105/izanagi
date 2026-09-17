# 段 4 裁定 (親) — wave dev-wave-b2-delta-min-connection、2026-09-17 07:00 JST

裁定 inbox の再走査: wave 開始後に local main が `abc7085ae` → `b4631a92e` (entry 1596、第 20 回裁定の fold) へ進み、
第 20 回裁定は **D2104**、本件の確認手番は **T-2743** として採番された (`docs/spool/FOLDED.md` の allocations、main の
worklog `:2956-2958`)。worktree は ff-only で追随済み。brief の「未採番」は着手時点の事実であり、成果物は T-2743 を `完了` で閉じる形へ改める。

## 所見の裁定 (real / refuted、採否、scope)

### 段 2 plan
| 所見 | 裁定 | 採否 |
|---|---|---|
| 行番号補正 `:1434` (ループ開始)、`:129-143`、`:903` (欄定数の違反報告用途) | real (親が現物で検算) | 採用 |
| generation 経路は workload 文字列を manifest と照合する (`:667,893-900`) | real | 採用 (対応表 5 行目) |
| `n` / `sd_max` も §5 では holdout 別、判定器は共通 `n` (`:388-392,1880-1882,1992`)、registry も共通 `n` (`trial_registry.py:800-801`) | real | 採用 (対応表 6 行目 + 設計メモ) |
| 充足許可集合は `{C10}` (`s8c_preregistration_evidence.py:3336`) | real | 採用 (対応表 11 行目) |
| P2 の二択は網羅的でない (二重評価・再集約という第三案) | real だが、T-1874 README「拒否された近道」の「judge を 2 回呼び private `_JudgeResult` を独自合成する」と同型 | 採用 (過剰断定の訂正としてのみ)。第三案を候補として推さない |
| 「裁定へ返す候補」6 件 | 候補 2 (holdout 別 mapping vs 単一値) は **D1481 で裁定済み** (plan は追補前の brief を読んだ)。候補 1・3〜6 は D1481/D1326 の実装 wave の設計メモ | 不採用 (裁定候補としては)。設計メモへ移す |

### 段 3 sol (正しさ境界)
| # | 所見 | 裁定 | 採否 |
|---|---|---|---|
| 1 | holdout 別閾値の隠れた経路は無い (manifest / prediction / source_binding / attestation / publish を点検) | refuted (親の読みが正しい) | — |
| 2 | P2「2 回呼び分けは成立しない」は広すぎる。単一 holdout manifest は拒否されるが、(a) 完全 manifest を別 params で二重評価することは禁止されていない、(b) 判定器は「異なる文字列ラベル 2 個」しか要求せず、同一 workload の別名 2 ラベルは cell 正規化では排除されない (registry が別途凍結 workload と照合) | real | 採用。P2 を「単一 holdout manifest への分割は契約外」に限定。(a) は T-1874 の拒否済み近道と同型なので候補にしない。(b) は判定器の限界として対応表 5 行目に注記 (registry `:780-799,1678-1688` が塞ぐ) |
| 3 | 「渡す先が無い」は holdout 別の受口に限定すべき。将来 caller が H1 の値だけを渡せば「H1 由来値の共通適用」という接続になり、逆接続とは限らない | real | 採用。結論文を「holdout 別値の未接続。逆接続・誤受理は確認していない。単一値を将来接続しても D1640/D2049 と一般には同値でない」へ |
| 4 | plan の裁定候補は D1481 未反映。D1481 は方向のみで `_ContrastParams` の具体改変までは指定していない。最小値集約は条件付きで受理集合を広げうる (`d1 < d2` なら H2 で `d1 < mean_delta ≤ d2` が新たに通る) | real | 採用。D1481 を「設計の方向を確定」と書く。非同値の条件付き導出を設計メモに 1 行 |
| 5 | validator の検査範囲の読みは正しい | refuted | — |
| 6 | 親表 2 行目「有限・正」は `delta_min` のみ、`sd_max` は非負。8 行目に `:903`。不在断定には探索範囲が要る | real | 採用 |
| 7 | 「gate は閉じていて測定は起きていない」は履歴全体の断定として未確定。`judge()` は C07 の発効状態を照会しない (`:1959-2013`) | real (表現) | 採用。「C07 は充足を許されず (`{C10}`)、§5 は未記入、本 wave は誤受理も測定も実証していない」へ。gate 閉を「judge が SATISFIED を返せない証明」に使わない |

### 段 3 luna (整合・実効性)
| # | 所見 | 裁定 | 採否 |
|---|---|---|---|
| 1 | D2104・T-2743 採番済み。T-2743 を `完了` で閉じる必要 | real (親が main で検証) | 採用。fragment は T-2743 `完了` (base は main の実体)、T-1874 / T-1875 は carry (本文不変) |
| 2 | plan の候補は既裁定と実装検討事項を混同。追補は正しい。D2044 項 12 は非 silo 床値で本件の起点ではない | real | 採用。insight で D2044 を引かない |
| 3 | 8b §10.2 / 8c §4 の「発効判定は欄が記入済みかどうかしか見ず、値の型・単位・範囲は検証しない」「担保は欄が空であることだけ」は現行実装の説明として不正確 | **部分的に real**。親が現物で検算: 発効判定の連言 (`s8c_preregistration.py:2061-2065` `effective = validation ∧ decider_version ∧ all_filled ∧ all_satisfied`) は `section5_value_violations` を**含まない**ので「発効判定は値を検証しない」は現行でも正しい。一方「担保は欄が空であることだけ」は、validator (`:891-961`) と living doc の invariant test (`orchestrator/tests/test_s8c_preregistration_invariant.py:674`) が実在する今、部分的に古い | 採用 (参考節として記録、本 wave では直さない — 8b/8c の改訂契約は別 wave。T-1875 insight の「陳腐化 1 件 (参考)」と同じ扱い) |
| 4 | 「docs が holdout 別入力の judge を実装済みと保証している」という読みは成立しない | refuted (親もそう読んでいない) | — |
| 5 | 中心結論は整合。brief に検索範囲が無い | real (記述不足) | 採用 (insight「再現手順」に検索範囲を明記済み) |
| 6 | decisions fragment 無しでも /rulings は拾う。ただし今回は裁定待ちを作らず完了を記録する方針が適切 | refuted (懸念は当たらない) | 方針どおり |
| 7 | F965 型の照合は記録上十分。新 F は不要 | refuted/未確定 | 新 F を作らない |

## プラン v2 (成果物の形)
- insight `output/insights/2026-09-17/b2-delta-min-connection/README.md`: 題に `[T-2743]`。上の採用事項を反映 (結論文、対応表の補正、束縛経路を「凍結 → registry の導出」と「manifest → judge の検査」の 2 本の鎖が文字列ラベルで出会う形に描き直す、既裁定の表、設計メモ、参考: docs の現状説明、再現手順、限界)。
- worklog fragment `docs/spool/worklog/2026-09-17-dev-wave-b2-delta-min-connection-1.md`: title `[T-2743] …`、本文、次の一手差分 = `完了` T-2743 (`remaining: none`、base = main の実体 digest)。T-1874 / T-1875 は暗黙 carry。decisions / failures fragment は書かない。
- 実装面の差分ゼロ → 変異 matrix は DW-S04 により免除。受入全走は免除しない。焦点走は無し (docs のみ)。親が `check_docs.py`・`spool_fold.py --dry-run`・provenance 監査を実走。
- 段 5 は無し。段 6 は insight のレビュー 2 本 (read-only): A = 対応表の各行を file:line で反証 + 結論の過剰断定、B = 既裁定・docs との整合 + fragment の形。

## 変異事前登録
実装面 (D95 決定 2) の差分ゼロ。DW-S04 により免除。登録なし。

## 追記 (07:11 JST) — 段 6 所見の閉包表 (DW-O16)

| 出所 | 所見 | 裁定 | 対応 | 状態 |
|---|---|---|---|---|
| B must-fix | 設計メモが `n` を後続 wave の設計択に戻している。D2071 は「6 cell すべてで同一、holdout 別は不受理」と確定済み | real (親が D2071 逐語 `docs/decisions.md:63558-63576` と T-1957 insight §2.1 で検証) | 設計メモの `n` 項を D2071 準拠へ書き換え、既存被覆表に D2071 行を追加、完了 item にも「`n` は D2071 のまま」を追記 | closed |
| A nit 1 | manifest の `n` は任意欄 (`:392` は `"n" in manifest` のときだけ一致要求)。共通 `n` の反復集合検査は `:400-442` | real | 対応表 6 行目を修正 | closed |
| A nit 2 | registry の検査対象は manifest の trials (`:791-801`) と runtime report の cells (`:1672-1688`)。図の "H1"/"H2" は正規 manifest の場合。「下流で逆転が起きる余地は無い」は registry 範囲に限定 | real | 対応表 5・13 行目と鎖 A の図・注記を修正 | closed |
| A nit 3 | 検索結果要約の不一致 3 件 (判定器自身の定義、`def judge` 2 件、test 2 file + ledger json) | real | 再現手順の注記を修正 | closed |
| B nit 1 | worklog fragment が insight の技術説明を再掲しすぎ | real | 本文を縮め、技術根拠は insight 参照へ | closed |
| B nit 2 | 工数・受入結果の記入待ちが残る | real (想定内) | 段 7 で実績を記入 | partial (段 7 で closed にする) |

## 追記 (07:20 JST) — 焦点再レビュー (s6-focus-1) の判定と最終閉包

closed 4 / partial 2 (B nit 1: fragment の技術再掲、B nit 2: 工数・受入の記入待ち)、regressed 0。新規記述に「nit 5 件も反映した」の
過大表現 1 件 (A nit 2 を分割して数え、未完了の B nit 2 を含んでいた)。親の対応: fragment の段 6 段落を「must-fix 1 と nit の
本文修正分を反映、工数・受入は段 7 で記入」へ書き直し、技術説明を insight 参照へ縮める。core test の hit 数は 7 (親の 6 は誤記、
下の検算行を訂正)。段 7 で工数 (receipt 集計) と受入結果を記入して B nit 1・2 を closed にする。焦点再レビューはこれ以上回さない
(3 巡上限の内側、残件は記入のみ)。

量化語の検算: 「6 cell すべてで同一」は D2071 逐語。「test 2 file」は `git grep -n "section5_value_violations" -- ':!external' ':!output' ':!docs'` の出力 (`test_s8c_preregistration_core.py` 7 hit、`test_s8c_preregistration_invariant.py` 3 hit、`acceptance_duration_ledger.json` 1 hit) から再計算。
