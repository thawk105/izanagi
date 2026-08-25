---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1135-prereg-blockers
seq: 1
title: [T-1135] 8c 正式系列の残 blocker を実測で確定し、C03 の訂正は承認権限の改訂単位へ送った (docs、branch worktree-dev-wave-t1135-prereg-blockers、実装差分ゼロ)
---

## 本文

- 依頼は C03 / C05 / C08 の 3 件を実装で閉じ、T-468 は scope 外として返すことだった。
  判定器を main で実走した結果、**3 件はどれも本 wave で閉じるべきものではなかった。**
  実装差分ゼロで終端し、全件を裁定として返す。
- **C03 の落下点は 1 箇所に特定できた。** producer 到達性検査で、要求 4 target のうち
  `classify_attempt` と `begin_attempt_observation` は到達し、
  `reserve_attempt_slot` と `record_attempt_terminal` が未到達である。producer は
  D618 が確定させた formal 版 (`reserve_formal_attempt_slot` /
  `record_formal_attempt_terminal`) だけを呼ぶ。両者は `profile=` 引数だけが異なり
  同一の private 中核へ委譲する。formal profile は generic に
  `require_terminal_reason_equals_classification=True` を 1 つ足しただけの真に厳しい側である。
  述語の名前一覧が D618 より前の姿で取り残されている。
- **しかし訂正しても閂は 1 本も外れない。** 起動可否は 12 述語すべてが `SATISFIED` である
  ことを要求する conjunction 1 本で決まり、`UNSATISFIED` も `EVIDENCE_UNDEFINED` も
  等しく非受理である。変わるのは gate レポートの診断ラベルだけである。一方 D529 は
  拒否理由の意味を変える変更に版 bump と新世代 record を要求し、かつ「分割は後から接合できない」
  と定める。**後戻り不能の改訂単位を診断ラベルの付け替えに使わない**と裁定した。
  訂正は承認権限を開ける改訂単位へ同梱する。{{D:c03-fix-belongs-to-approval-activation}}。
- **C08 は実装残ゼロだった。** 構造検査を全通過した終端 return に到達している。
  残るのは証明の定義と承認権限であり、どちらも人間手番側に属する。
- **C05 は D549 の保留が今も生きている。** activation の 4 項目 (契約反転・registry 登録・
  版 bump・世代発行) は着地済みだが、`_load_s8c_schedule_authority` は今も無条件に
  unavailable を送出する。暫定 authority で artifact を commit することは D549 が
  却下済みの選択肢そのものである。
- **より重い事実が 2 件出た。** 第一に、事前登録 artifact が 3 つとも不在である
  (`trial-manifest.v1.json` / `prereg-effective-binding.v1.json` / `schedule.v1.json`)。
  第二に、非 certifying の正式起動路は 12 述語を一切参照しない —
  `admit_registered_formal_noncertifying` が見るのは opt-in、manifest、条件凍結の生存、
  launch binding の 4 点だけである。**述語は非 certifying 経路の閂ではない。**
  経路ごとに閂が別物であることを {{D:formal-noncertifying-launch-does-not-consult-predicates}}
  に分けて記した。
- **親 brief の誤りを段3 が 1 件見つけた。** 親は「C08 の早期 exit は全て `UNSATISFIED` を
  返すので `EVIDENCE_UNDEFINED` は終端と識別できる」と書いたが、registry 不在の早期 exit は
  `EVIDENCE_UNDEFINED` を返す。結論 (終端到達) は変わらないが、識別は status 単独ではなく
  status と reason code の組で行うのが正しい。
- **段3 が親の未検出の consumer を 1 件見つけた。** 親は「`EVIDENCE_UNDEFINED` を区別する
  production consumer は存在しない」と grep で測ったが、gate レポートは enum を総なめして
  status count を出すため、literal 検索では掛からない。不在の主張を識別子 grep だけで
  立てた親の測り方が甘かった。
- 段3 の敵対相談 2 レンズは、独立に段2 プランを NO-GO と判定した。レンズ A は
  「formal 名の到達可能性は厳格 profile への委譲を何も証明しない」ため受理集合の実質的な
  緩みだと指摘し、レンズ B は D529 の逐語から版 bump が必要であることを示した。
  どちらも採用した。段2 プラン自身の (P2) refuted 判定は、レンズ B により覆された。
- 段5・6 は「実装しない」裁定により省略した。実装差分ゼロのため変異 matrix は免除。

## 次の一手差分

### 更新

- [T-1135] **P2・裁定へ移行**: 本 wave で実測が確定した。C03 / C05 / C08 はいずれも
  単独では閉じられない。C03 の述語訂正は承認権限 activation の改訂単位へ同梱する
  ({{D:c03-fix-belongs-to-approval-activation}})。正式系列の閂は経路ごとに別物であり、
  certifying 経路は承認権限 1 つ、非 certifying 経路は事前登録 artifact の不在である
  ({{D:formal-noncertifying-launch-does-not-consult-predicates}})。次に動かすべきは
  述語ではなく、承認権限 (T-468) と artifact の権威供給 (T-1380) である。
  base: d26894bcd46a6dd1807d3366691ad5fc0d3e6f9bf0079cade2ba690a3166b0fe

- [T-1380] **P2・射程が広がった**: schedule authority の実体供給に加え、
  `trial-manifest.v1.json` と `prereg-effective-binding.v1.json` も repository に不在で
  あることが判明した。3 artifact とも権威が確定するまで commit できない (D549 の理由は
  3 つすべてに当てはまる)。非 certifying の正式起動路は 12 述語を見ず manifest だけを
  要求するため、この 3 artifact が正式系列の実質的な閂である。
  base: 91fb24ae7d03d3fd092d40f7c5151e97d7f971fa042fbb63936010694790823b

### 新規

- {{T:c03-contract-mismatch}} **P3・新規**: C03 の証拠契約と評価器が食い違っている。
  契約は manifest cell と effective binding と registry の照合を要求するが、評価器の
  producer 条件は attempt lifecycle の 4 target を見ている。C08 の契約はさらに、
  production に存在しない entrypoint `admit_preregistration` を挙げている。
  承認権限 activation の改訂単位で契約側も直す必要がある。

- {{T:phase-doc-8c-current-state-stale}} **P3・新規**: `docs/phase3-8c-preregistration.md` が
  二段束縛を未実装と記したままだが、admission と formal acceptance は実際には binding を
  読み直している。C03 / C08 の現在地が phase doc に正しく表れていない。

- {{T:c03-reachability-is-may-call}} **P3・新規**: C03 / C08 の到達性検査は経路の証明では
  なく may-call 集合である。到達不能分岐に置いた呼出しや戻り値を捨てた呼出しでも通過する。
  現行の generic 名検査にも同じ穴があり、本 wave で新設したものではない。承認権限を開ける
  前に、must-reach か dataflow のどちらで閉じるかを決める必要がある。

- {{T:t080-output-snapshot-shard-race}} **P2・新規**: 受入全走の shard 経路が同じ作業木から
  2 request を重ねて投入するため、`output/` の before/after snapshot を assert する検査群が
  他 shard の書き込みを拾って赤になる。本 wave で
  `test_s8b_oracle_driver.py::test_t080_stub_free_e2e_temp_roots_fail_closed_at_real_output_boundary`
  を `orchestrator/tests/flaky_test_holds.py` へ登録して受入から外したが、これは対症であり
  原因は受入基盤側にある。hold の解除条件は shard が作業木を共有しなくなること。
