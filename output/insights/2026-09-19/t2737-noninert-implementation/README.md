# T-2737 — SS2PL 非 inert 側の局所実装

authority: none
default_effect: no-state-change

## 範囲と不変条件

D2148 項4に従う実装記録。根拠は
`output/insights/2026-09-18/t2737-ss2pl-gate-controls/README.md` §1.1・§7。
既存 `prepare_masstree_fetchcontent` を runner の条件関門前へ接続し、patch a〜d を限定移植する。
e の `wfg.cc` 条件を保存し、f/g の inert 復元は含めない。

inert 認証 target、KIND の従属、関門の比較条件、abort 所有権と inert 宣言差分は変更しない。
phase1 の supply 成立を runtime meaning の認証や controls 全体の成立へ読み替えない。
controls は S arm から build するため、phase1 の実経路検証は `build_target(arm="phase1")` を
直接呼ぶ。性能測定・certified 選択・新しい比較結果は本 wave の成果物ではない。

## 実装前の独立検査

plan と consult 2本を隔離 read-only Codex で実施した。両 consult は次の局所補正を要求した。

- study header の条件化は既存 C++ 単体テストの型参照へ波及する。テストを除外せず、既存の
  `SS2PL_STUDY_LOCK_TESTING` を使う局所対応でテスト内容を保存する。
- helper は runner の `_run_checked` を通らない。新しい制御機構は設けず、既存の時間上限を
  接続時に引き継ぐ。
- 前回の revS 実測は f/g 込みであり、a〜d 限定版の成立は新たに実検証する。
- 旧 binary の build は計器比較に不要。旧版の実 configure と全 target TU の前処理を比較材料とする。

## 実物検証

job dir: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-noninert-codex/`。
初回test dispatch (9135.nqsv) は専用環境変数が転送されず `KeyError: T2737_STOCK` で終了した。
製品の転送規則は変えず、既存generic経由 (9140.nqsv) で `run_tests.py` を実行し、
BACK_OFF=0のprobeが1 passed (94.74秒、job Elapse 100秒) となった。

最終probeは外部sidecarから実行入力を読み、通常の `run_tests.py --force-dispatch` で実施した。
job9293.nqsvは **1 passed (113.32秒、job Elapse 118秒)**。
runnerがphase1へ渡す **BACK_OFF=1、IMPL=1、KIND=0、DLR=0、WFG=1** を使い、
pristine stagingからproduction `build_target` を通した。4 supplyは
`requested-default-preprocess-different`、4 meaningは `meaning-witness-undeclared`、
raw-measurement admissionはtrue。Sは従来どおり `owner-tu-unresolved` 3件と
`configure-failed` 1件で拒否された。

Sのplain buildに対する既存WFG不在検査は3 TUで受理。abort増分の所有はtransaction 0・workload 2を維持。
IMPL=0/1で既存study_lock_test・make_db_testを実行し、sbomb_d2pl・bomb_ss2pl・tpcc_ss2plもbuildした。
plain build成功はSの関門認証ではない。pristine原本のconfig.h不在は前後で維持した。

## 計器保存の比較

旧patchと限定版のphase1全4 TUを実前処理し、全差分を個別に確認する。
BACK_OFF=0の親判定は `verbatim/live2-analysis.md`。差分は無条件rwlock include由来の
`using namespace std`、pragma残渣の空白、診断用source path、transactionのERR行150→148、
旧DLR表示のDLR0→DLR1である。数値のSS2PL_DLR表示は0のままで、比較関門を緩めていない。
計器呼出し・引数・包含する制御構造とstudy lock本体に差分はない。
生の全TUとdiffはjob dirへ保全し、受領証は `receipts/` に複写した。
BACK_OFF=1の焦点再レビューも **GO**。全200行・17ハンクを独立に読み、生TUから再生成したdiffとの
一致と上記の分類を確認した。詳述は `verbatim/focus.md`。C++原ログの成功件数はstudy_lock_testが
IMPL=0で8件・IMPL=1で11件、make_db_testは各1件である。
関連Pythonテストは最終状態で103 passed (3.77秒)。文書・Codex設定・diff検査も通過。
この段階では変異と受入全走は未実施であり、wave全体の完了とは扱わない。
