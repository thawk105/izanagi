---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-29
wave: dev-wave-t2027-t2043-external-input
seq: 1
title: [T-2027] compiler input を根分類 + 根相対 path へ移し現 canonical base へ再束縛する (D1192 実装の回収 land、branch worktree-dev-wave-t2027-t2043-external-input)
---

## 本文

- 本 wave は新規実装ではなく、2026-08-28 の同名 wave が受入全走の手前で止めた完成済み branch
  (実体 commit `2e35a2596` と `104954a30`) を回収して land する回である。実装は書き直していない。
- **規律 6 の内容監査 (自分が作ったものでない差分)**: production 4 file の差分を親が読み切った。
  D1192 の択 (1) と一致し、変更はすべて受理集合を狭めるか保つ方向だった —
  no-follow 走査と TOCTOU 検査の追加、external root への descriptor policy 必須化、
  root tag と live path の canonical 一致検査、v1 の absolute path 検証の温存。
  migration も cache-miss fallback も無い。監査で挙げた非阻害の所見は 2 件:
  (a) `buildcache.py` が `s8b_compiler_input._strict_root` を module 跨ぎの private 名で呼ぶ、
  (b) 床値 campaign が dependency binding のある全 cell へ新 kwarg を渡すため、
  `build_v2` 以外の注入 `build_fn` が当該引数も `**kwargs` も持たないと TypeError になる
  (official mode は注入を拒否するので到達経路は非 official に限る)。いずれも正しさ防壁を緩めない。
- **main 取り込みの合成検査**: 着手直前の local main `d03855e92` は merge-base から
  orchestrator/tools を 103 file 変えていたが、本 wave の 8 file とファイル重複は 0 件だった。
  さらに 103 file 全部を走査し、compiler-input の収集器・検証器・manifest schema・
  receipt 発行器を参照する file が 0 件であることを実測した。main 側で唯一の
  `buildcache.build_v2` 呼び手は `source_snapshot_sha256` を渡さないため改修経路へ入らない。
- **T-2027 と T-2043 の関係**: 前 wave の段 4 裁定が既に確定していた —
  同じ validator defect が両症状の原因であり D1192 の同じ最小修理で閉じるが、
  full build digest が job ごとに異なる (`dbbcb195...` / `87aa2e6a...`) ため 1 件へ束ねず
  別 ID のまま扱う。台帳の「選択肢集合を照合するまで 1 件へまとめない」に従った。
- **受入を 2 回止めていた赤の帰属**: 前 wave の受入 attempt 1/2 はいずれも
  18319 passed / 62 skipped / 1 failed で、唯一の赤は
  `orchestrator/tests/test_growth_test_holds_contract.py::test_regular_pytest_path_keeps_single_hold_skip`
  だった。前 wave は証拠 F として F273 だけを見て「exact 関数名を含む F が無い」と判断し、
  hold 登録の循環に嵌って中断していた。本 wave が台帳を引き直したところ、該当族の正本は
  F273 ではなく F480 (絶対 wall-clock 上界が受入の並列負荷で壊れる族、`Thread.join(<秒>)` の
  上界と順序 assert も同族として追記済み) だった。族としての再発記録は F480 へ追記した。
- **処置は hold 登録ではなく上界の拡大にした**。破れた 10.0 秒は `subprocess.run` の
  anti-hang guard であって検査対象の性質ではない — 当該 node の assert は subprocess の
  終了コードと 3 つの出力 marker だけで、経過時間を一切見ていない。F480 の既存事例
  (deadline の絶対性、hook の相対順序) は assert 自身が性質だったので所有者の設計判断として
  据え置かれたが、本件はその区別の反対側にある。よって当該 1 呼び出しにだけ 120.0 秒を渡し、
  helper 既定の 10.0 秒は他 11 呼び出しのために据え置いた。受理集合は不変で、真の hang には
  従来どおり fail-closed する。
- **前 wave が中断した構造的理由**は {{F:hold-evidence-circularity}} に記録した。
- **受入 attempt 1 で別の非帰属赤を 1 件引いた**。予算を広げた node は緑になり、代わりに
  `test_mocc_g2_discriminator.py::test_transaction_watermark_surface_is_trace_guarded_and_post_store`
  が落ちた (1 failed / 18846 passed / 67 skipped)。原因は本 wave の差分ではなく、
  worktree ごとに submodule の object store が分かれていることだった。詳細は
  {{F:worktree-submodule-missing-policy-oid}}。object を持ってきて復旧し、同 file 単独走
  22 passed / rc=0 を確認してから受入を投げ直した。
- **受入 attempt 2 と 3 (2026-08-31) はテストの赤ではなく dispatch 基盤で落ちた**。どちらも
  `raw_child_rc=16` の `dispatch-attestation-missing` で、attempt 3 は collection 19126 件まで
  進んでから 3 shard とも起動しなかった。原因は残存 orphan hold で、hold が 2 つの path に
  書かれていることを知らず片方だけ撤去していた。F333 へ再発として追記した。
- **子の工数**: Codex `role=fix` 1 本 (`gpt-5.6-sol` / xhigh / workspace-write) で
  outcome=accepted、validator rc=0。子は login node の scheduler preflight 拒否で
  dispatch できず「implemented, not run」を正しく申告し、実測は親が行った。
- 変異 matrix は再走していない。前 wave の 6 件の期待 node はすべて本 wave の 4 test file 内にあり、
  本 wave が追加した唯一の実装面変更 (`test_growth_test_holds_contract.py` の 1 呼び出しの
  anti-hang 予算) はどの anchor にも期待 node 集合にも触れないことを spec を読んで確認した。

- **land 直前に承認済み裁定の前提を覆す既記録の新事実を見つけた**。main を取り込み直した際、
  T-2027 の本文が 2026-08-29 の別 wave の実測で更新されており、消える根が **2 クラス**
  (build cache 作業用 directory 31 件と job 専用作業領域 7 件) あること、
  **1 クラスだけ根相対化しても主経路は赤のまま残る**ことが記録されていた。本 wave は D1192 が
  裁定した範囲 (クラス 1) の実装を land するに留め、射程拡大は裁定へ返す。当初 T-2027 を
  `完了` で書いていたのを `更新` へ改めた。実装そのものは裁定どおりで、代案へは戻していない。

## 次の一手差分

### 更新

- [T-2027] **P1・D1192 の裁定範囲 (根クラス 1) は実装 land 済み → 射程拡大のユーザー裁定待ち**:
  branch を回収し、内容監査・main 取り込み・焦点走・受入全走を経て land した。manifest は
  `s8b-compiler-input/v2` として根の分類 (`snapshot` / `fetchcontent-masstree` / `filesystem`)
  と根相対 POSIX path を持ち、cache-hit と binary admission receipt 発行の両境界で現在の
  canonical base へ束縛し直して bytes を再検証する。manifest schema は descriptor-bound cache
  preimage に pin したので、旧 v1 completion は移行されず別 identity のまま残る。
  **完了とは書けない。** 本項の既存本文が 2026-08-29 の実測として記録しているとおり、消える根は
  2 クラスあり、D1192 の裁定文と本実装が扱うのは build cache の作業用 directory
  (`.staging-<PID>-<nonce>/_deps/…`、31 件) だけである。job 専用作業領域
  (`/scr/0_<jobid>.nqsv/{gflags,glog}-install/include/…`、7 件) は `filesystem` 根として
  jobid 入りの path のまま記録されるため、次の job の cache hit で再び解決できず主経路は赤のまま残る。
  射程を 2 クラスへ広げる裁定はユーザー手番であり、本 wave は裁定済みの範囲だけを land して
  代案へ戻さない。
  base: 32d3b7d703a742703ac4fdc1d6c093a09aec278aef2dc261638a907693311cac

- [T-2043] **P1・[T-2027] の根クラス 1 是正が land 済み → 同項の射程裁定待ち**: 原因は T-2027 と
  同一の validator defect で、D1192 の同じ変更単位で閉じる (別 ID のまま維持)。
  `_external_entry()` が絶対 path を `resolve(strict=True)` できず落ちていた経路は、
  根相対 path + 現 canonical base への再束縛に置き換わった。ただし本項を閉じるには
  根クラス 2 の扱いが決まる必要があり、その後に床値 job を 1 回再投入して binary admission
  receipt の発行段を実際に通過することを観測する。前 wave の job 再投入条件 (焦点検査・
  関連全走・事前登録変異の全 kill・docs/codex/provenance 検査が緑) は本 wave で満たした。
  base: 737db6955a86693ad8faabe86f8fddb8241d5cd41dc9dd29ba058afe2078fc4d

### 新規

- {{T:hold-evidence-circularity}} **P2・新規・ユーザー裁定候補**: DW-O18 は受入の非帰属赤を
  `orchestrator/tests/flaky_test_holds.py` へ登録するとき「main に既存の F」を証拠に要求し、
  同 file の field 契約 (`_evidence_section` 照合) はその F 節が **exact な test 関数名を
  言及していること**まで要求する。ところが新しい node について F を land するには受入全走が要り、
  その受入を通すために hold が要る、という循環が閉じている。今回は上界が検査対象の性質でなかった
  ため「治す」側へ抜けられたが、性質そのものが破れる node では抜け道が無い。
  受入 1 回分と wave 1 本を実際に失っているので、契約の境界をどう変えるかを裁定へ返す。
  詳細は {{F:hold-evidence-circularity}}。

- {{T:witness-oid-provisioning}} **P2・新規・ユーザー裁定候補**:
  `tools/pegasus/mocc_trace_v1_policy.json` の `mocc_trace.new_oid` は、pin 済み submodule commit
  から到達せず、主 checkout の submodule にある push 済みでないローカル branch 1 本からしか
  到達できない。worktree の submodule は object store が別で、init tool は仕様上 fetch しないため、
  当該 oid の実在を assert するテストは**主 checkout でだけ通り、どの wave worktree でも落ちる**。
  恒久策は (a) oid を pin 済み commit から到達可能にする、(b) init tool に provisioning を持たせる、
  (c) witness を upstream へ出す、のいずれかで、外部 repo の扱いと受理集合に関わる。
  テストを緩める案は採らない。詳細は {{F:worktree-submodule-missing-policy-oid}}。
