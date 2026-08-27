# 段 1 brief — [T-1647] A-2 certification の投入を計算ノードへ分割する

基準 commit: dd6621397 (local main)。branch: worktree-dev-wave-t1647-a2-cert-fanout。

## 依頼と、着手前の実測で分かったこと

依頼は「A-2 の 4-cell certification を実走して回収する」+ ユーザー補足「時間がかかりすぎ。
可能な限り計算ジョブとして分割してどかっと計算ノードに投げるべき」。

着手前に 2 点を実測した。

1. **批准の終端は今も出る。** 現行 closure digest は
   `a14a261280e60a25ca28135695fc80c0bfeee2071922d03da4b7225b65190ab3`。台帳
   `hooks/enforcement-source-closure-ratifications.v1.jsonl` は 1 行のみで
   `db511c3d84...` (A-1 が 2026-08-25 に批准した別版)。
   `require_ratified_closure()` は `enforcement-source-closure-unratified` を送出する。
2. **原因は D1028/D1038 の非認証成果物型ではない。** D1070 が「D1028 が批准 gate の定義域の外へ
   意図的に出した非認証成果物型は、対象に含めない」と明記している。非認証経路で回しても
   certified を名乗れない (規律 2) ため、A-2 certification の代替にならない。
   真の原因は **D905 の執行主体 (批准 broker) が main へ未着地**であることである。
   その実装は branch `worktree-dev-wave-t1629-ratification-broker` に存在し、main 未着地。
   同 wave 自身が「D905/D906 を満たしたとは書かない」と主張上限を設定している。

したがって **本 wave では certification の数値は取れない。** 実走できる形を作ることまでが scope。

## scope (この wave でやること)

- A-2 の投入を **workload 単位の login 側 fan-out** へ分割する。先例は
  `tools/pegasus/submit_b10_backoff_grid.sh` (「Login-side fan-out: submit one independent job for
  each B-10 workload」、admission class = `local-ok`)。
- 分割した投入を実機へ 1 回投げ、**gate の手前までの配線が通ることを実測**する
  (期待する終端は上記の批准エラー)。DW-G01 の生死確認にあたる。
- 切り分けの結果と、gate が開く条件を台帳へ記録する。

## scope 外

- 批准そのもの。D905 が「設計が着地するまで批准は進めない」と定めている。人間へ台帳 1 行の転記を
  依頼する案は D758 決定 2・D905 が却下済みであり、本 wave からは提案しない。
- `campaign_lock.py` / `contract_loader_binding.py` / `artifact_admission.py` の変更。
  T-1629 が所有しており編集面が衝突する。
- certification の判定規則・受理集合・検証回数。規律 2 により一切緩めない。

## 不変条件

- `run_workload` は 1 campaign 内で stock → adopted の順序対を必須とする
  (`if len(cells) != 2 or [cell.role ...] != ["stock", "adopted"]`)。この対を跨いで分割しない。
- 正しさ検証の反復回数を実行時間のために減らさない (D1059、規律 2)。
- 投入記録は `job_body_sha256` と argv 末尾 = policy の `scheduler.job_body` を束縛する
  (driver 816-823, 1042, 2521-2523)。分割後もこの束縛を恒真にしない。
- 成果物影響 (DW-G05): 分割しない場合、gate が開いた後の回収は 6 時間の直列 job 1 本のままで、
  途中で切れると 4 cell 全部を失う。分割すれば失うのは 1 workload = 2 cell に留まる。
  certified な cell の集合そのものは変わらない。

## 判断が割れうる前提 (親の provisional 裁定であり攻撃対象)

- **(P1) job body は 1 本のまま `IZANAGI_A2_WORKLOAD` で径数化し、login 側から 2 回投げる。**
  B-10 と同型。policy の `job_body` が単一 path を pin しているため、job body を 2 本に割るより
  pin 閉包が小さい。
- **(P2) 並列度の上限は 2 である。** cell 単位に割ると stock/adopted の対照条件が壊れる。
  「どかっと」に応えるため反復 5 回を別 job へ割る案は、各反復を別 campaign・別 lock へ束縛し直す
  ことになり proof chain を変える。**採らない**を provisional とするが、段 3 で攻撃してよい。
- **(P3) `finalize-raw` は login 側で 1 回走らせる。** 計算資源を使わない集約であり、
  2 job の完了後に走る必要がある。
- **(P4) attempt root は 2 job で共有し、`raw` の fresh 検査を workload 単位へ狭める。**
  `compute-result.json` と `reservation.json` は job ごとに分ける。現行の
  `if [[ -e "$raw_root" ]]` と `compute result already exists` は 2 job 目を必ず殺す。

## 成果物の形

- `tools/pegasus/submit_paper_story_a2_certification.sh` (新規、login 側 fan-out)
- `tools/pegasus/paper_story_a2_certification.sh` (改修、1 job = 1 workload)
- driver の attempt/raw 層と finalize の対応改修
- `tools/pegasus/admission_registry.json` / `docs/pegasus-runbook.md` の表 / `test_hooks.py` /
  `test_paper_story_a2_job_contract.py` の追随
- 実機投入 1 回分の証跡と、切り分けの記録

## 並列分割方針

段 2 は 1 本 (plan)。段 3 は 2 本 (レンズ = 「分割が proof chain を壊さないか」/「分割が
gate・投入記録の束縛を恒真にしないか」)。段 5 は実装子 1 本 (編集面が 1 系統のため)。
段 6 はレビュー 2 本 + fix。
