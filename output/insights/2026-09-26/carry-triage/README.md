# 持ち越し 619 項の整理 (2026-09-26)

authority: none
default_effect: no-state-change

可変状態の正本は worklog の末尾と決定 (本 wave の decisions fragment `carry-triage-withdrawal`) である。本書は取り下げの一覧と経緯の控え。

## 1. 何をしたか

worklog「次の一手」の active 619 項 (着手時の local main `7c1b53a4b`、entry 1869) を 1 項ずつ読み、501 項を取り下げ、118 項を残した。

- 取り下げ一覧 (T・区分・理由 1 行): `withdrawn.tsv`
- 残す一覧 (T・残す理由): `kept.tsv`
- 区分の記号: `a` = 実害の実測が無い仮想リスクへの防壁・受領証・束縛・gate・台帳・検査・一般化の追加、`b` = 記録・注記・限界明記だけ、
  `c` = 本文が既に終端を言う、`d` = 研究・論文の項で上位の裁定により止まった・置き換わったもの、`old` = 旧系列
  (8b/8c 正式系列・official 床値・凍結 chain、D2212 項 5)。複数付く項はカンマで並べた。

件数 (筆頭の区分): a 181・b 116・c 102・old 89・d 13 = 501。`old` がどこかに付く項は 118。

## 2. 手順

1. 母集合: `/work/1/SFC/tanab/scripts/worklog_carry_resolve.py --json` (619 項、未解決 0)。
2. 親が全項の本文を読み、一次判定 (drop 508 / keep 52 / 要確認 59)。性能・所要の改善案は 4 区分に当たらないので残す側へ戻した。
3. 要確認 59 項を sonnet 子 2 本が実装・決定・worktree と照合 (結果は `verbatim/fix-02b-check.tsv`・`verbatim/fix-05-check.tsv`)。
   この照合で **B-4 が現行系列** (D1936 項 8「B-4 は記述統計へ限定して進める」、D2201 項 2) と分かり、親が「床値」「B-4」を旧系列・停止扱いに
   していた項を洗い直した (`verbatim/fix-03-b4.tsv`・`verbatim/fix-04-b4prereg.tsv`)。official 床値は旧系列のまま。
4. codex read-only の相談 4 本 (gpt-6-sol、reasoning medium): lens A (過剰な取り下げ・研究を止める取り下げ)、lens B (規律 2・6 の穴・実害の見落とし)、
   各 前半 344 項 / 後半 275 項。逐語は `verbatim/consult-*-out.md`、prompt は `verbatim/consult-a1.md`・`verbatim/consult-b1.md` (後半は担当部の path だけ違う)。
   受領証 4 本とも accepted / completed、各 21〜33 call、206〜318 秒、約 10〜15 万 token。
5. 段 4 裁定 (`verbatim/fix-06-stage4.tsv`): 所見 40 件 (重複 3)。
6. 段 6 の read-only レビュー 1 本 (`verbatim/review-1-out.md`、受領証 accepted、32 call・400 秒): NO-GO、must-fix 5・should 5。裁定は `verbatim/fix-07-review.tsv` (§3.1)。
7. 焦点再レビュー 1 本 (`verbatim/review-2-out.md`): R1〜R10 のうち 9 件 closed・R6 partial、新規 must-fix 1 (N1)。裁定は `verbatim/fix-08-closure.tsv` (§3.2)。
8. 焦点再レビュー 2 巡目 (`verbatim/review-3-out.md`): R6・N1 とも closed、GO (must-fix 0)。nit 1 件 (worklog 本文に 2026-08-16 第 3 回の裁定の名指しが抜けていた) を直した。

## 3. 段 4 の裁定

**前提 P1 の改訂 (相談 4 本がそろって指摘):** 親の初版は「実害の実測」を本文に誤記録・誤判定の記述があるかだけで判定し、
現物で具体的に示された現行経路の欠陥まで (a) に入れていた。「現行経路で現物に示された欠陥の局所修正は残し、実例の無い防壁・束縛・gate・台帳の
追加だけを落とす」へ改めた。

| 扱い | 項 |
|---|---|
| 残す側へ戻した (現物に示された現行経路の欠陥) | T-2451・T-2453・T-2459・T-2415・T-2648・T-2739・T-841・T-1072・T-2218 |
| 残す側へ戻した (実際の判定・記録への影響) | T-2207・T-2322・T-2840 |
| 残す側へ戻した (4 区分に当たらない整理・所要改善・研究) | T-1703・T-1944・T-2084・T-2205・T-2250・T-2387・T-2463・T-1882、同型の整合で親が足した T-2404・T-2461・T-2538 |
| 取り下げ側へ移した | T-469・T-470 (現行 checkout に certified 選択の consumer が無い、`layer3_report.py` :1004-1008)、T-842 (8c の preview と completeness にしか届かない) |
| 区分・理由の訂正 (取り下げは維持) | T-473・T-860・T-1638・T-1893・T-2439、軸 1 の文献検索の T-1969・T-1970・T-2031 (次節。T-2092 は段 6 で残す側へ戻した) |
| 退けた (取り下げを維持) | T-2219 (認可 gate の要否調査)、T-2393 (8b の holdout 試行)、T-2238 (D669 の除外は既に消えており、残るのは失効の記録だけ) |
| 段 4 では退けたが焦点再レビューで残す側へ戻した | T-733・T-2344・T-2402 (source closure の段階拡張)、T-734 (全 certified sink への source gate)。§3.2 |
| 段 4 では退けたが段 6 で残す側へ戻した | T-1883 (RW2 化)、T-2323 (axis_complete の供給経路の調査)。§3.1 |

退けた理由: T-2219 は依頼が名指す gate の追加で、T-2393 は旧系列。どちらも実例の観測が無い。

### 3.1 段 6 の裁定

| 扱い | 項 |
|---|---|
| 残す側へ戻した | T-2323・T-1883・T-2092 (止めた上位裁定を示せない研究・調査。D1760 は軸 1 OpenAlex の取得を止めた裁定で、これらを名指さない)、T-2754 (D2120 項 19 が実在と分類した穴の局所修正)、T-2755 (F300 の再発 5 例)、同型の T-2726 (F370 の再発 3 回)・T-2727 (F1014) |
| 区分の訂正 (取り下げは維持) | T-2402 → (a)、T-1768 → (b)、T-2466 → 旧系列の再起票文を付けた |
| 記述の訂正 | 軸 1 は「取得済み 78 leaf」でなく登録 78 (取得証拠あり 77・未走 1)。決定の「消したのは未実装の追加予定だけ」を、走査対象から外した項 (記録だけ・終端済み・研究の項を含む) へ直した |

### 3.2 焦点再レビューの裁定

N1 (T-2402) を受け入れ、同じ取り組みの T-733・T-2344 と、同型の T-734 も残す側へ戻した。D1884 はユーザー裁定 D1075 (certified 経路が束縛する材料を推移閉包へ広げる) の継続で、
正しさ防壁自身が束縛されていない穴を閉じる取り組みと明記し、実害 0 件を据え置きの根拠にしないとしている。T-734 は 2026-08-16 第 3 回のユーザー裁定「課す」(認証の意味が出口ごとに違う状態は規律 2 に触れる)。
依頼文はこれらの裁定を名指していないので、親が覆すのは承認済み裁定の不採用に当たる。**止めるかどうかは、ユーザーが D1075 と当該裁定を名指して決める判断として残る。**

## 4. 依頼文の例示と台帳の食い違い

依頼は「文献検索 [T-1969]/[T-1970] は D1760 で停止」と例示したが、軸 1 の取得は D1760 の後に D2095 (2026-09-17、ユーザー直接指示) で再開され、
T-2035 (2026-09-18〜19、archive worklog entry 1660・1689) で登録 78 leaf すべてに裁定が付き (取得証拠あり 77・未走 1、`docs/related-work/claim-survey/2026-09-19-axis1-search-execution.md`)、後継の凍結記録へ反映して区切られていた。
取り下げは依頼の名指しどおり行い、理由はこの経緯で書いた。

## 5. 付随して観測した事実

- **land の fold 関門で T-139 を戻した。** 受入全走 (27,684 passed・74 skipped、tested main `f9206053f`) の後、land が `rc=31 fold-gate-failed`
  (JUnit collected 2・failed 1、main は不変) で止まった。fold 関門の登録 node `test_spool_fold.py::test_cli_base_digest_real_corpus_resolves_active_and_rejects_completed`
  が実台帳で T-139 を active と固定しており、T-139 の取り下げが fold 後の木で落とした。テストの変更は実装面で scope 外なので T-139 を残した
  (`verbatim/fix-09-t139.tsv`)。取り下げた他の T を括弧付き literal で使うコードは orchestrator・tools・hooks に 0 件。

- repo 外の `/work/1/SFC/tanab/scripts/spool_base_digest.py` が carry 鎖の深さで `RecursionError` を出した (T-011 で再現)。
  同型は T-2192 (`sweep_pending.py`) で既に直されている。本 wave は `sys.setrecursionlimit(200000)` と `threading.stack_size(512 MiB)` の thread 内で
  runpy 実行して回避した。T-011 と T-2861 の digest は `tools/spool_fold.py --base-digest` と一致した。
- T-2541 (consult の受領証が本文を出し切っても not_accepted になる) は本 wave の 4 本では起きなかった (4/4 accepted)。
  現行コードに該当構造は残る (`tools/codex_worker_launch.py` :2487-2506、sonnet 子の照合) ので項は残した。
- 着手後に main は `6c3913bc5` まで進んだ。持ち越しの差は T-2847 の完了と T-2850 の本文更新だけで、どちらも残す側の項である。
  その後 `1f169cbbd` (entry 1873) まで進み、差は残す側の T-2273・T-2560・T-2850 の本文更新だけだった。取り下げ 501 項の base digest は `1f169cbbd` の現物から取った (その後 `c18633656` (entry 1876) まで進んでも取り下げ側の本文は不変)。
- 取り下げた T-1851・T-2724 には worktree が残る (`.claude/worktrees/dev-wave-t1851-c3c-official-floor`、`.codex/worktrees/t2724-g1-gen`・`t2724-chain-scratch`、lock 付き)。
  最終更新は 2026-09-15・09-18 で、関係するプロセスも ListAgents の session も無いので、稼働 wave ではなく残置と判断した。

## 所在の移動・撤去 (2026-09-30 追記)

取り下げた T-2724 の残置 worktree `.codex/worktrees/t2724-chain-scratch`・`t2724-g1-gen` と branch `scratch-t2724-chain-check`・`freeze-g1-gen-t2724` は、2026-09-30 の掃除 wave で回収せずに撤去する。G `32ba8cae4` は main の祖先で残り、scratch branch は束 bundle に退避した。
判定の根拠・木ごとの退避の所在・残る写しの一覧は `output/insights/2026-09-30/cleanup-originals-migration/README.md` を正本とする。上の本文は当時の事実として書き換えない (記録された測定・判定は撤去を理由に無効にならない、規律 7)。撤去は同 wave の land の後に行う。
