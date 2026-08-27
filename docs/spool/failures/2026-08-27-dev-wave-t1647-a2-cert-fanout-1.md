---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-t1647-a2-cert-fanout
seq: 1
---

## 新規

### {{F:a2-completion-receipt-had-no-producer}}. A-2 の完了受領証を作る正規 producer が存在せず、批准とは別に chain が閉じられなかった [恒真ゲート] [手順不整合]

- 事象: A-2 certification の投入分割を実装する wave の段 6 レビューが、
  `record_completion_receipt()` は呼び手が用意した JSON を検証して保存するだけで、
  その payload を作る経路が repo に存在しないことを摘出した。`record_acquisition_receipt()` は
  completion を前提に導出するため、completion が作れなければ acquisition も作れず、
  `collect` へ到達できない。**批准 gate が開いても、そのままでは chain を閉じられなかった。**
- 根本原因: 投入から完了取得までの login 側手順が repo に機械化されておらず
  (`git grep IZANAGI_A2_` の hit は job body 1 file だけだった)、過去の実走は手投入で行われていた。
  手順が人の頭にある間は「payload を誰が作るか」が欠落として顕在化しない。
- 恒久対応: login 側実行体 `tools/pegasus/submit_paper_story_a2_certification.sh` へ create-only な
  `finish-group` mode を新設し、終端観測・log hash・compute/reservation hash の採取から
  `finalize-raw`・completion・acquisition の生成までを一続きで行う経路にした。
  受理集合の検査は変異 M8 (「全 driver_rc が 0」を「1 件でも 0」へ緩める) が KILLED で裏取りしている。
- 再発検知: 正式系列の driver を新設・改修する wave は、**受領証の各 schema について
  「その payload を作る repo 内の producer は何か」を段 1 brief で名指しする。**
  名指しできない schema は、その時点で到達不能な wire contract である。

### {{F:focus-run-green-because-tests-bypassed-the-real-producer}}. 焦点走が緑でも、テストが実 producer を通さず期待側を手で組み立てていたため実機で必ず死ぬ実装が通っていた [テスト代表性]

- 事象: A-2 の投入分割の実装で、焦点走 936 passed / 4 skipped が緑だった。しかし段 6 の敵対
  レビューが、campaign の出力 root が二重化しており
  (`jobs/<workload>/campaigns/campaigns/<cid>`)、実 producer は測定後の raw cell 生成へ
  1 件も到達できないことを静的に摘出した。**緑だったのは、テスト helper が実 producer
  (`run_workload` → `run_campaign` → `campaign_layout`) を通さず、期待側の layout を
  手で組み立てていたためである。**
- 根本原因: 正例が「性質」だけを検査し、実際の呼び先を名指ししていなかった。producer 側と
  期待側の双方を同じテストが構築すると、両者が同じ誤りを共有しても緑になる。
- 恒久対応: `A2.run_workload()` を直接呼ぶ正例を追加し、layout root が
  `jobs/<workload>/campaigns/<cid>` であることを実 producer 経由で確かめる形にした
  (`orchestrator/tests/test_paper_story_a2_certification.py` の
  `test_official_run_observes_and_passes_current_toolchain_manifest`)。
  この正例は stub が本物の `run_campaign` と同じ `ident.bind_admission_policy()` を通ることも
  要求するため、本物の手順から乖離すると落ちる。
- 再発検知: 出力 path・layout・identity を変える wave では、**期待値を組み立てる helper と
  実 producer が同一経路を通るかを段 6 のレビュー観点に明示的に入れる。**
  「テストが緑」を配線の証拠に使わず、実 producer を通す正例が 1 本あるかを見る。

## 再発

### F498

- **再発: 2026-08-27** — A-2 の 4-cell certification の投入を分割する wave で、着手前に同じ終端を
  実測した。現行 closure digest は
  `a14a261280e60a25ca28135695fc80c0bfeee2071922d03da4b7225b65190ab3`、批准台帳
  `hooks/enforcement-source-closure-ratifications.v1.jsonl` は 1 行のみで
  `db511c3d841128bfdbf5ba7c6bbdb2ce4da1fe0fdefe8d52aaacb0906ddeea44` (A-1 が 2026-08-25 に
  批准した別版) である。`require_ratified_closure()` と
  `verify_ratified_contract_loader_binding()` の双方が
  `enforcement-source-closure-unratified` を返す。**本 wave は解除経路を D1028/D1038 の
  非認証成果物型と切り分けた** — D1070 が「非認証成果物型は批准 gate の定義域に含めない」と
  明記しており、非認証経路で回しても certified を名乗れない (絶対規律 2)。
  解除に要るのは D905 の執行主体 (branch `worktree-dev-wave-t1629-ratification-broker` に実装が
  存在、main 未着地) の着地と、その主体による現行 digest の批准である。
  本 wave は login 側 entry point の先頭へ批准 precheck を置き、**未批准なら qsub を 1 件も
  出さずに終える**形にした (D1070 の dispatch 側を A-2 について先に満たす)。
  計算ノードの枠を消費してから 16 秒で死ぬ経路は、これで塞がっている。
