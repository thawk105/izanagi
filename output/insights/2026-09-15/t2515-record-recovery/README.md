# T-2515 — 旧 wave branch に残っていた未着地の研究記録の回収

2026-09-15。branch `worktree-dev-wave-t2515-calib-rr95-rr5` (確認 tip
`559bcbc29cfa27412f103b608e8ac708dcfae6b9`) の 6 commit を内容で監査し、main に着地していなかった
研究記録だけを回収した。**コードは 1 行も変えていない。新しい測定もしていない。**
回収した当時の資料の本体は `output/insights/2026-09-10/t2515-rr95-rr5-calibration/` に置き、
同 README の「2026-09-15 追記」節が読み方を示す。本 directory は今回の監査と裁定の記録である。

## 1. 6 commit の着地判定 (内容ベース)

merge-base(main, branch) = `960466384`。`branch..main` = 796 commit で main が大きく先行している。
**patch-id ではなく内容 (blob と意味) で判定した** — 三点 diff の行数は未着地量ではない。

| commit | 変更面 | 判定 | 根拠 |
|---|---|---|---|
| `ad002de1b` | `tools/pegasus/README.md` | 着地済み | rratio 記述 4 hunk が main に逐語一致。残差は main 側が後から入れた D1936 反映だけで、branch 側の方が古い |
| `bcfd2b931` | `submit_certify.sh` / `certify_calibration.sh` / `test_pegasus_calibration_workload.py` | 着地済み | 両 shell の rratio gate が逐語一致。`_rratio_gate_values` と `test_submitter_exposes_only_the_calibration_whitelist` も逐語一致 |
| `3dbf7ea1d` | `certify_calibration.sh` / 同 test | 一部着地・一部失効 | `CALIBRATE_PYTHON` 選定ブロックの前倒しは main に逐語存在。関門 argv の修正は D1936 項 6 が `run_condition_gate` ごと撤去したため対象が消滅 |
| `18704ae18` | `test_pegasus_tools.py` | 着地済み | main に同じ selection + shim 分割抽出と `unrelated` 4 語の assert。抽出の終端 anchor だけが D1936 後の形 |
| `ec17af5dc` | insights 25 + spool 3 | **一部未着地** | 下記 §2 |
| `559bcbc29` | `conftest.py` / `test_real_repo_serialization.py` / `test_t1259_*.py` / spool 3 | 着地済み | `test_t1259_*.py` は main と branch の blob が同一。conftest / 独立 golden の 30 node 登録も main に存在。D1936 項 43 が承認し T-2579 が実装した |

## 2. 未着地だった実体 — 17 file

依頼は `output/insights/2026-09-10_t2515-rr95-rr5-calibration/` が main に無いとしていた。
その path は確かに無いが、**内容は `output/insights/2026-09-10/t2515-rr95-rr5-calibration/` として
着地済み**だった (D1941 の日付別配置)。`job-evidence/` 7 file は blob 単位で逐語一致である。

未着地だったのは次の 17 file で、いずれも branch blob と byte 一致で回収した。

- `original-verbatim/` 13 本 — 元 wave の子の逐語 (段 1 brief、段 2 plan、段 3 相談 2、
  段 4 裁定と追補、段 5 author、段 6 review 2 / fix 3 / 焦点再レビュー 1)。
- `original-mutation/` 4 本 — 元 wave の変異 spec / report。**`repo_head` は `18704ae18`** で、
  既着地の `mutation-final*.json` / `mutation-probe*.json` (`repo_head` = `35a740cd4`) とは
  別の実測である。後者は 2026-09-10 の回収 wave が現行合成に対して再走した結果で、
  前者の代替にならない。**4 本とも同一 blob が main に 0 件**であることを全数検索で確認した。

元 README の叙述のうち main 側の圧縮版に無かった事実 (ドリフト年表、検知穴、変異の知見、
焦点走が捕まえた赤、依頼前提の誤り、セッション異常) は、既着地 README への**追記節**として残した。
**既存 1〜86 行は 1 byte も変えていない** (変更前 bytes が変更後の完全な prefix であることを検査した)。

## 3. 先行する 2 つの回収 wave との関係

- 2026-09-10 の回収 wave (worklog entry 1429) がコードと job-evidence を回収した。同 wave の
  段 4 裁定は「旧 file 全置換、`559bcbc29` と旧 spool の取り込みは不採用」と決めている。
  これは**その wave 内部の scope 判断**であり、ユーザー裁定ではない。
- T-2579 が D1936 項 43 に従って t1259 fixture 部分を回収・実装した。
- 本 wave は、この 2 つが意図的に落とした研究記録を拾い直した。

## 4. 親 brief の誤りと、子による訂正

**親 brief の (P1) は誤りだった。** 親は「3 週間故障」と「字面検索による既存 F 見落とし」を
新規 F にすると裁定していたが、段 2 が既存 F の実在を指摘し、親が台帳の現物で追認した。

| 親の当初判断 | 訂正後 | 現物 |
|---|---|---|
| 3 週間故障 = 新規 F | **F500 への再発追記** | F500 は同 script が裸 `python3` を呼び 3.10 構文で落ちる型。既載の 2026-09-10 再発は pristine source verifier の呼出しで、本件の条件関門は同族の別呼出し |
| 字面検索の見落とし = 新規 F | **F766 への再発追記** | F766 の根本原因 (1) が「台帳を主題ではなくファイル名で引いて正しい族を見落とす」 |
| 待ち手偽成功 = F355 へ再発 | 変更なし | F817 は 2026-09-03 に F355 へ supersede 済み |
| F934 へ supersede 追記 | 限定を追加 | 「未実走」の訂正であり拒否原因の解消ではない。2026-09-14 の別 driver 再発は残る |

**新規 F は 0 件になった。**

**親の監査そのものの誤りを段 3 レンズ B が 1 件捕まえた。** 親は当初「変異成果物は再走版で
着地済み」と報告していたが、`repo_head` が別で当時の実測は失われていた。親が blob の全数検索で
追認し、`original-mutation/` として回収対象へ足した。

**段 3 レンズ A は期間の断定を訂正した。** 元 wave の「認証経路が 3 週間死んでいた」は証拠より強い。
実測できたのは 4 時点と、確認した認定 attempt に当該関門の実走記録が無かったことだけである。

## 5. 棄却 finding (refuted)

- 回収が拒否を成功へ読み替える設計になっている (A) — `988706` / `988708` はいずれも
  `admitted=false` / shell `rc=2` で、追記節はそれを明記する。
- 現行 main とのコード差分が未着地実装の証拠になる (A) / 6 commit に未着地のコード変更が残る (B) —
  反例なし。専用関門の撤去は後続変更、抽出境界の変化はその整合である。
- 既着地 directory への追加そのものが凍結違反になる (B) — 対象 topic を固定する manifest も
  exact member 集合も見つからなかった。D1941 も日付配下 topic への追加を禁じていない。

## 6. 後続裁定との対応 — 当時の判断を現在の方針として読まない

`original-verbatim/` と元 wave の spool fragment には、後続のユーザー裁定で覆った判断が
歴史資料として残っている。本 wave はそれらを台帳へ再登録していない。対応表は
`output/insights/2026-09-10/t2515-rr95-rr5-calibration/README.md` の 2026-09-15 追記節にある。
関係する裁定は D1936 項 6 / 項 43 / 項 46 / 項 47 と D1986 項 1。

## 7. scope 外の real 所見 (裁定パッケージ候補・本 wave では実装しない)

- **F817 の帰属不整合。** 2026-09-03 に「以後この型は F355 へ追記する」と supersede されたのに、
  2026-09-08 の再発が F817 側へ書かれている。台帳の整理は本 wave の scope 外。
- **元 wave の工数記録の内訳不一致。** 「codex 子 9 本」と内訳合計が合わない。確定値としては
  扱わず、原文の不一致として記した。

## 8. 変異と受入

`DW-S04` により**変異 matrix を免除した** — 変更面は `output/insights/**` と `docs/spool/**` だけで、
実装面 (D95 決定 2) の差分がゼロである。コード・テスト・実行可能 script・機械設定を 1 つも変えていない。
**受入全走は免除していない。**

焦点走は **674 passed / 9 skipped / 0 failed** (計算ノード request `998883.nqsv`)。対象 4 file は
`test_check_docs.py`、`test_s8b_repo_scan_invariant.py`、`test_s8c_preregistration_invariant.py`、
`test_login_headroom.py` で、後ろ 3 本は段 3 レンズ B が「plan の consumer 導出が docs checker で
止まり repo 全体走査を取りこぼしている」と指摘して足させたものである。
`tools/check_docs.py`、`tools/check_codex_agents.py`、凍結前の三軸語走査
(`python3 -m orchestrator.campaign.s8b_holdout_freeze search`) はいずれも rc=0 で、
走査の hit は走査器自身の positive control だけ、本 wave が足した path は 0 件だった。

受入全走は tip `b357697f5` に対して **23662 passed / 68 skipped / 0 failed**
(`verdict=child-green`、`red_nodeids=[]`、`flake_nodeids=[]`) である。
この検査結果を記録へ足す amend で tip が変わるため、着地 tip に対して受入をもう 1 度通した。

受入の 1 回目は `stage=preflight-submodule-ready` rc=2 で即死した。入れ子 submodule が未初期化で、
親が `git submodule status` の top-level だけを見て clean と誤読していたためである。
正規 argv で初期化し直して rc=0。**テスト結果ではないので赤には数えない。**

## 9. 逐語

`verbatim/` に段 1 brief、段 2 plan、段 3 相談 2 本、段 4 裁定、参照した既裁定の逐語を置いた。
codex 子は 3 本 (plan 1 / consult 2)、全本 rc=0・採用検査 rc=0・再投入なし。

## 10. 段 8 自己改善の routing

候補は 2 件で、どちらも `docs/skill-self-improvement.md` の routing 規則 1 に従って
既存 F への再発追記に送った。**新しい節・gate・台帳は作っていない。**

- **受入が `stage=preflight-submodule-ready` rc=2 で走行ゼロ落ちした件** → `F320` の再発。
  2026-08-20 の supersede が入れた恒久対応 (`tools/dev_wave_submodule_init.py`) は在ったが、
  同 tool の rc=1 を止まる理由と扱わず、続けて `git submodule status` を**非再帰**で読んで
  clean と誤判定したために再発した。**恒久対応の存在は、その rc を読まない運用を防がない。**
- **親が `docs/skill-self-improvement.md` を wave 開始時でなく段 8 直前に初読した件** →
  既存 F が無く、実害も無かったため新規 F は作らず worklog のセッション異常として記録した。

`docs/dev-wave/**` の本文是正は行っていない。該当節は既に予算が逼迫しており
(F320 自身が 996 / 1000 bytes の余白不足を記録している)、本依頼は回収だけを scope としている。
