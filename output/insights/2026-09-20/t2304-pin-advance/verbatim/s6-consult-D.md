## 決定

**O2 を選ぶ。** 本 wave は tested tip まで完成させ、T-2724 の A/X と帰結修正・検証を含む wave 全体の land 後に land する。

D2150 の①④⑦という実装範囲、②③⑤を新系列の着手時に置く順序は維持する。追加するのは、新事実の決定台帳への追記と、既存系列の実行元を明示する運用記録である。

## 理由

pin 前進は承認済みであり、旧 submit-tree の稼働 attempt を停止させない。一方、独立 full OID だけでは新 main 上の live 消費を保護できないことは、`build_admission.py:499`、receipt 照合、driver の policy 束縛から確認できる。D2150 の「影響を受けない」は適用範囲を訂正する必要がある。

今すぐ新 main を必要とする測定が止まるという確証より、**T-2724 の残工程へ新しい拒否原因を持ち込む危険の方が具体的**である。同 wave は実 repo の真値取得、gate-check、受入、post-claim merge を残す。先に pin を land すると、その統合後検証へ protocol 解決不能・policy 不一致が加わり、既存の lineage 矛盾との切り分けが増える。

O2 はこの干渉を避ける。ただし、**待つだけで g1 の新 main 上の launch が可能になるわけではない**。T-2724 の既存 lineage 問題も、本 wave の policy 世代移動も残る。

## 採らない案の最も強い形

- **O1:** 承認済みの順序を直ちに実体化でき、固定 submit-tree の測定は継続する。T-2724 が新 pin を含む統合状態で必要検証を済ませているなら合理的。しかし提示された現況ではその証拠がなく、残工程への干渉を避ける O2 を選ぶ。
- **O3:** 「主経路に無影響」が承認判断の重要な前提なら、誤りを人間へ返すのが最も保守的。しかし今回、候補の正しさが否定されたわけではなく、既存測定を維持する実行面もある。相談後に親が決める恒久指示の下では、事実訂正と順序調整で処理できる。
- **O4:** policy を pin から分離すれば、将来の不要な世代移動を減らせる可能性はある。しかし admission の受理集合・identity 設計を変える。本 wave の①④⑦には収まらず、今ここで実施する根拠はない。

## (i)〜(iv) への回答

**(i) 今日〜数日の実害**

| 作業 | 読む code／実行元 | 今回の停止との関係 |
|---|---|---|
| T-2724 の残工程 | 現在は専用 wave tree。post-claim merge 後の検証は取り込んだ main の変更を読む | pin が先に入れば、新 policy・gitlink が検証に加わる。すべての gate が resolver を呼ぶわけではないが、実 repo 検証への干渉はある。O2 の直接の保護対象 |
| g1 の W-4／後続 launch | 将来選ぶ checkout。現在、実行中の固定 launch tree は提示されていない | 本日 launch 可能ではなく、lineage 矛盾等が先行 blocker。新 main ではさらに policy 不一致等が加わる。旧 tree を選んでも既存 lineage 問題は解消しない |
| B-4 床値の窓 job | `submit_floor_pair.sh` が指定した detached checkout。job は同じ root から driver を import し、投入時 HEAD と照合 | **s8b floor の resume と区別が必要。** `floor_pair_driver.py:1101` は既存の `expected_policy=None` 経路を使い、current floor resolver を呼ばない。固定 checkout の窓 job が今回の resolver 例外で止まるとはいえない |
| K2 round 4 | 提示された稼働 attempt は固定 submit-tree | 稼働中 attempt は停止しない。新 main で新規起動すると、旧固定 `PIN` との checkout 不一致、policy／identity 移動が障害になる。resolver 例外が直接原因とは限らない |
| A-1 sized 再走 | 提示された稼働 attempt は固定 submit-tree | 稼働中 attempt は停止しない。新 main から再投入する場合は旧 source 契約と現行 policy の整合が必要。これも resolver 例外そのものとは別 |

B-4 の根拠は [D2145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2304-pin-advance/docs/decisions.md:67225) と [floor-pair の receipt 検証](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2304-pin-advance/orchestrator/campaign/floor_pair_driver.py:1090)。具体的な窓 job の投入済み HEAD・時刻は今回の資料では確定していないため、稼働済みとは断定しない。

運用注記の「新 main から再開するには⑤＋再 admission＋③」は、**必要条件の概略であり、十分条件ではない**。②の新 identity／登録、source 契約、g1 の証拠鎖整合も対象ごとに必要となる。新 policy で旧 lock の同一系列 resume が復活するとは書かない。旧 binary の再 admission も、新 protocol の source 条件を満たす場合に限られる。

**(ii) O2 の技術的保証**

`git rev-parse main` は OID の取得だけであり、包含確認にならない。

T-2724 の**帰結修正・検証・記録まで含む land 完了 tip**を `AX_DONE` として固定し、`git merge-base --is-ancestor "$AX_DONE" main` の成功を必要とする。A または X 単独の包含では不足する。その main を取り込んだ T-2304 の統合 tip を検証し、既存 land 手順の排他・main 更新検知の下で着地する。

包含前の先行 land を許せるのは、T-2724 が新 pin を含む統合 tip で残工程と必要検証を完了した証拠がある場合、または同 wave が終了・撤回され干渉対象が消えた場合。その際は親が順序判断の変更を記録する。単に「W-4 はまだ走らない」「A/X commit ができた」だけでは足りない。**現況では例外を使わない。**

**(iii) 決定台帳への記録**

**decisions の spool fragment を追加し、fold 時に新 D を採番する。worklog 本文だけでは不足。** 既存台帳への事実追記であり、新たな承認待ち項目ではない。brief の「decisions 不要」は新事実判明前の判断として更新する。

題は例えば `{{D:pin-advance-policy-impact}}. D2150 項1の無影響という説明を限定し、land順序を記録する`。

本文には次を明記する。

> D2150 項1の承認対象・実装範囲・②③⑤の実施時期は変更しない。「影響を受けない」は旧 pin・旧 policy の固定 submit-tree における継続と旧証拠の保持について成立する。新 main での live 消費には成立しない。policy SHA 移動と current floor protocol 解決不能を新事実として追記する。親の実施判断として T-2724 完了後に land する。

ユーザーの再裁定を受けたとは記さず、元の D2150 を遡及的に書き換えない。

**(iv) 規律7・規律2**

O2 はどちらも変更しない。

旧測定・凍結 bytes・当時の判定を保持し、新 main の拒否を過去測定の無効化と解釈しない。旧 submit-tree の使用は互換性確保の具体策であり、新測定一般に「過去の承認済み code と同一」を要求する新条件にはしない。

policy 照合の除去、resolver の曖昧 fallback、receipt の SHA 張替え、live 経路への新たな `None` 導入は行わない。B-4 floor-pair に既存の `None` があることも、他経路の緩和根拠にはしない。

## 親が land 前に必ずやること

- T-2724 の land 完了記録と full OID `AX_DONE` を取得し、`git merge-base --is-ancestor "$AX_DONE" main` が rc=0 であることを記録する。
- 取り込んだ main OID、統合後の tested tip、受入結果の対象 OID を対応づける。main が進んだ場合は既存 land 手順に従って再統合・必要検証を行う。
- gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` の同一 commit 更新と、最終 tip の3値整合を検査する。
- 焦点走の赤を全件分類する。epoch golden の追随と、実 repo の protocol 解決不能を分け、後者を期待値の機械置換や skip で隠していないことを diff で確認する。
- 必要なテスト・変異・受入を所定の runner で完了し、対象 tip と終了コードを保存する。docs／agents checker と commit 後の provenance 監査も記録する。
- decisions fragment、worklog、insight、runbook に上記の影響範囲を反映し、`python3 tools/spool_fold.py --dry-run` の rc=0 を確認する。
- 継続対象について「系列／job ID／投入元の絶対パス／full HEAD／gitlink／policy 世代」を記録する。B-4 は窓1・窓2・finalize の HEAD 同一性も照合する。未確認欄を「影響なし」にしない。
- 旧凍結・登録・測定・receipt・比較 policy の変更がないことを diff で確認する。
- D16 の同期手順を用意する。初回 `landed-postcondition-failed` は main 更新後の可能性があるため HEAD を確認し、main の submodule を記録 gitlink に同期して同じ land 要求を再実行する。旧測定 tree は同期対象に含めない。

## 総括

**O2 を採る。** T-2724 の残工程を保護してから承認済みの pin 前進を land し、D2150 の無影響という説明は新 D で限定する。新 main での旧系列の拒否は明示し、移行を終えるまでは契約を満たす固定 submit-tree を使う。

本回答は静的検査による判断であり、テスト・job 状態の再実測・書込みは行っていない。