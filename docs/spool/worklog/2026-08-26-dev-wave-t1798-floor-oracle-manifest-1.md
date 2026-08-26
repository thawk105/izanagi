---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1798-floor-oracle-manifest
seq: 1
title: [T-1798] 床値 SWO oracle の依存材料を規則で導出した canonical root へ束縛した (コード + テスト、branch worktree-dev-wave-t1798-floor-oracle-manifest、変異 matrix = baseline PASSED・8/8 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 依頼は `/dev-wave [T-1798] 床値の SWO oracle が production で PASS できない状態を解く` (背景 job)。
  base main は `9463bcbc`。起動時の稼働 wave との編集面重複は無かった。
- **起票文の因果は正しくなかった。** 起票は「production 側でこの manifest を生成・配置する経路が
  存在しない」としたが、実測すると真因はもっと深い。floor の preflight は依存 root が VCS の
  top-level であることを要求するので、その root には必ず VCS metadata と prebuild 生成物が入る。
  一方 oracle は root 直下再帰の全 regular file 集合が宣言集合と exact 一致することを要求する。
  したがって**実 source root に manifest を置く案は最初から死んでいる**。生成器を実 root へ
  置く設計は採れない。
- **段 1 の生死確認で設計が決まった。** repo 外の使い捨て driver で、実 source root から
  宣言集合を規則 (tracked 一覧 ∪ `config.h` ∪ 生成 `PIN`) で導出した canonical root を組み立てた
  ところ、生成 manifest は fixture の `SHA256SUMS` と **byte-identical** になり pin と一致した。
  pin を緩めずに床値経路を開けることが着手前に分かった。
- **親は自分の実測を 2 度訂正した。** (a) 最初に「production の依存 root」と呼んだ path は
  Pegasus 用の永続 cache であり、床値 campaign が使うのは `<base>/masstree-src` だった。
  (b) 「build 境界と oracle が別 path を見る」という懸念は誤りで、`source_root.parent` が base
  なので同じ directory を指す。訂正後に `<base>/masstree-src` の形で測り直しても規則の成立は
  変わらず、独立な 2 root で確認できた。
- **`config.h` の再現性を実測した。** fetch のみ済みの実 root を repo 外へ複製し、CCBench の
  recipe (`bootstrap.sh` / `configure --disable-assertions` / `make` / `ar` / `ranlib`) を完走させると、
  生成された `config.h` は fixture と bytes 一致した。完走後の姿は regular 196・symlink 0・
  tracked 99 で、親が最初に測った root と同型だった。さらにそこから規則だけで canonical root を
  作り、`check_materialized_sort_swo` を実走して `OracleStatus.PASS` を得た。
  **oracle PASS までの成功経路が空でないことを着手前に実測で確定した。**
- **段 3 のレンズ A が blocker を 1 件出し、親は実装せず主張の側を撤回した。** archive を作る
  `make` / `ar` / `ranlib` / autotools は継承環境から解決され、floor は生成**後**の archive hash を
  初めて観測してそれを権威にする。細工した tool は同じ `config.h` を残したまま悪性 archive を
  作れる。本 wave が作った欠陥ではなく、tool identity の束縛は実行権威の変更で別審査に属する。
  そこで実装せず、**「因果鎖を閉じた」と主張しないこと**を選び、保証水準を成果物へ明記した。
  {{T:masstree-tool-identity}}。
- **「受理集合を広げない」を二段に言い分けた。** oracle 単体の root 述語の受理集合は不変である。
  一方「実 source root から floor が PASS する」という合成述語の受理集合は空集合から非空へ拡大する。
  これは依頼そのものであり規律 2 に反しない。段 3 レンズ A の指摘で言葉を正した。{{D:canonical-dependency-material}}。
- **親の provisional 裁定を 1 点撤回した。** 「build 境界の検査対象を canonical root へ単純に
  付け替える」案は、実 source の非 `config.h` tracked file が変わっても通るため D953 を壊す。
  段 2 プランの反論を採り、canonical へ既存 exact verifier、実 source へ canonical との等価検査、
  archive へ独立 hash という**二根検査**にした。
- **段 6 のレビューが偽緑を暴き、親は自分の段 4 裁定も訂正した。** 親は段 4 で「同一実行で
  production 全系列を通す試験を必須にする」と裁定したが、**合成 root ではこれが原理的に不可能**
  だった。生成する `PIN` の中身は実 HEAD であり、合成 checkout の HEAD が masstree の pin 済み
  commit になることはないので manifest は必ず pin と食い違う。実装子と fix 子はこの壁に当たり
  production の検査を monkeypatch で置換して迂回した。迂回は誤りだが要求の側にも無理があった。
  合成系列は「pin 不一致で fail-closed する」ことを確かめる場に改め、pin 一致から先は
  実 checkout を要する明示 opt-in が担う形へ訂正した。{{F:series-test-monkeypatched-the-gate}}。
- **段 6 レビュー A が時間方向の破れを 1 件見つけ、これは scope 内で閉じた。** 二根検査は各 file を
  読取時 identity 付きで読むが、全 file を読み終えた後にそれらが一つの安定状態だったことを
  確認していなかった。並び順の前半 file を読み終えた直後に bytes を一方向へ変えるだけで通る。
  A から B へ戻す往復すら要らない。一括再検査を足した。{{F:two-root-check-lacked-whole-state-recheck}}。
- **親の疑義 3 件はすべて refuted された。** 共有 fixture の値変更・build 境界からの receipt 再観測の
  削除・`elif` による archive 検査の消失を親が疑ったが、レビュー 2 本が独立に根拠つきで否定した。
  削除された 3 条件は新経路に包含され、`elif` へ到達する前に不一致が拒否されていた。
- **親の実走で 1 件だけ証拠が取れなかった。** floor 配線の real-root 系列 node は 5 回とも
  計算ノードへ振られ、`IZANAGI_SORT_SWO_REAL_MASSTREE_ROOT` が dispatch の env allowlist に無いため
  伝播せず skip した。**受入全走でも同じ理由で skip される。** 対策は稼働中の別 wave と編集面が
  重なるため実施せず起票した。{{T:dispatch-env-allowlist-for-real-root}}。
  generator から post-oracle build の cache miss/hit までの系列と phase marker は親が実走して緑を確認した。
- **段 8 の自己改善は候補を 3 件記録し、1 件は docs に既出、2 件は予算で入らず撤回した。**
  `--reasoning` の段別制約は `DW-C01` に既に書いてあり、親の読み落としだった (docs の欠落ではない)。
  隔離 session の cwd 回復と変異 harness の argv 制約は今回実測した新知見だが、
  `DW-C01` へ足すと単節予算 1000 bytes に対し 1246 bytes になり、同節は exact 契約で pin されている。
  安全義務を削って入れることは禁じられているので編集を撤回し、裁定パッケージへ送った。
  {{T:dev-wave-l2-section-budget}}。
- 段 3 敵対 2 レンズで所見 15 件、段 6 敵対 2 レンズで所見 8 件。fix は 2 巡。
  段 6 レビューの初回投入は親の argv 誤り (`--reasoning` は review/focus/author/fix 段で指定不可) で
  2 本とも rc=2 になり子が起動しなかった。別名で投入し直した。
- 焦点走は fix 後に `test_sort_swo_dependency_material.py` 13 passed / 1 skipped、
  `test_buildcache_v2.py` 176 passed、`test_s8b_floor_campaign.py` 461 passed / 2 skipped、
  3 file 合計 651 passed / 4 skipped。consumer 群は 147 passed と 143 passed。
  `test_s8b_approved.py` の `ModuleNotFoundError: No module named 'tests'` は file 選択走の偽赤で回帰ではない。
- **非帰属赤が 1 件ある。** `test_real_output_snapshot_excludes_git_ignored_real_output_changes` は
  `git ls-files -o -i` が**実在する** untracked ignored path しか返さないため、`output/runs` が
  実在しない新しい作業ツリーでは必ず落ちる。`.gitignore` に規則自体はあり、共有 checkout では通る。
  本 wave の差分と無関係で、変異 baseline ではこの根拠により deselect した。
- **変異は probe 巡で観測 node を集めてから本走した。** 期待 node は完全集合でなければならないため、
  初回は全 8 件中 6 件が MISMATCH になった。観測集合へ登録し直した本走で
  baseline PASSED (赤 0)、**8/8 KILLED、SURVIVED 0、MISMATCH 0、TIMEOUT 0**。初回結果は erratum として保全した。
  M08 (VCS 一覧取得の失敗握り潰し) は複数行の構造変更を要し単一理由性を保てないため登録から落とした。
  逐語と変異台帳は `output/insights/2026-08-26_t1798-floor-oracle-manifest/`。

## 次の一手差分

### 完了

- [T-1798] 床値の SWO oracle が production で PASS できない状態を解いた。実 source root から
  規則で導出した canonical root を oracle へ渡し、build 境界は二根検査で実 source との等価性を
  確かめる。oracle の検証器と pin と fixture の bytes は変更していない。
  remaining: none
  base: 92f16a6051855fded33104bd508bff3c2a66fe1e6d2aec3f3265de2c5a905e57

### 新規

- {{T:masstree-tool-identity}} **P2・新規**: masstree の prebuild が使う tool
  (`CC` / `CXX` / `make` / `ar` / `ranlib` / autotools) の identity を検証済み絶対 path へ束縛するか、
  archive に独立した期待権威を設けるかを決める。現在 recipe は継承環境から plain な tool 名を
  解決し、floor は生成後の archive hash を初めて観測してそれ自身を権威にする。細工した tool は
  pin 一致する `config.h` を残したまま悪性 archive を作れる。本 wave が作った欠陥ではない。
  CCBench の改変を伴うため D16 / D18 / D20 に従う。
- {{T:pilot-canonical-coverage}} **P3・新規**: `s8b_oracle_n_pilot` を canonical 保証の対象にするか
  決める。pilot は依存 binding の `source_root` を oracle へ渡し、build へ post-oracle capability を
  付けない。成果物は非 authoritative と明記されているので、直すか対象外と宣言するかの二択である。
- {{T:ambient-masstree-root-entry}} **P3・新規**: ambient `IZANAGI_SORT_SWO_MASSTREE_ROOT` から
  任意の pin 適合 root を受理する production 入口をどう扱うか決める。floor は明示引数を渡すので
  floor には影響しないが、`p3_s4_loop_sort` の quarantine と floor 以外の `s1_direct_comparison`
  呼び手は ambient を受理する。
- {{T:dev-wave-l2-section-budget}} **P3・新規・ユーザー裁定待ち**: dev-wave reference の L2 単節予算を
  上げるか、実測知見の別の置き場を設けるかを決める。`DW-C01` は「実測で是正した作法」を溜める節だが、
  単節予算 1000 bytes に対し既にほぼ満杯で、かつ節全体が exact 契約で pin されている。本 wave で
  実測した 2 件 (隔離 session の cwd が共有 checkout へ落ちると `cd` で戻せないこと、変異 harness の
  runner argv 制約) は、足すと 1246 bytes になり入らなかった。安全義務を削って入れることは
  禁じられているため撤回した。予算値の変更は独立審査に属するのでユーザーへ返す。
- {{T:dispatch-env-allowlist-for-real-root}} **P2・新規**: `IZANAGI_SORT_SWO_REAL_MASSTREE_ROOT` を
  dispatch の tests task env allowlist へ足し、実 masstree を要する opt-in node を計算ノードでも
  走らせられるようにするか決める。現在この env は伝播せず、当該 node は親の単独走でも受入全走でも
  skip される。本 wave では、対象 file が稼働中の別 wave の編集面と重なるため実施しなかった。
