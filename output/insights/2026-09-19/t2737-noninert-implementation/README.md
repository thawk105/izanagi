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
## 変異の裏取り

製品anchor `0bd0895da` と同じ本体を独立cloneへ固定し、authorの一回限りprobeと入力データだけを
private commit `e9409610e` に追加した。この検証用commitはmainへ取り込まない。
既存mutation harnessを使い、baselineは1 passed (102.69秒)。各走の入力は独立したpristine複製である。

| 変異 | 実測結果 | 最初の拒否・判定 |
|---|---|---|
| M1 helper除去 | KILLED | 4軸がpreprocess-failed。依存準備の欠落を検出 |
| M2 study条件include復活 | KILLED | IMPLだけdependency-closure-drift、他3軸はgreen |
| M3 WFG条件include復活 | KILLED | WFGだけdependency-closure-drift、他3軸はgreen |
| M4 DLR marker差の復活 | KILLED | DLRだけcompile-command-drift、他3軸はgreen |
| M5 publish_wait呼出し1箇所削除 | 自動probeはSURVIVED、全TU比較で拒否 | read_internalの実呼出し欠落が追加1ハンクとなる |
| M6 wfg.cc無条件source追加 | KILLED | plain SのcompileでSS2PLWfgMode未宣言。既存不在validatorは未到達 |

M5について、各attemptの絶対rootだけを同じ表示へ置き換えてbaselineの旧新diffと比較すると、
transactionに `publish_wait(*this, &tuple->lock_, SS2PLWfgMode::read);` の消失1ハンクが加わり、
他3 TUのdiffは一致した。計器呼出しの保存条件に反するため、同じ差分判定で拒否する。
この比較を関門の自動killに計上せず、自動probeの限界も保持する。生diffは
`receipts/tu-diffs.json` にUTF-8文字列・元bytes数・SHA-256で可逆保存した。

harnessは5 KILLED・1 SURVIVED、全6件が事前の自動判定期待と一致、MISMATCH/PARSE_ERROR/TIMEOUTは0。
wrapper rc=0、共有木の前後観測一致、復元・teardown完了。原台帳とwrapper受領証は `receipts/`。
受入全走はこの記録commit時点では未実施。実装と計器保存、局所の検出力をcontrols全体の成立へ拡張しない。

## 受入の赤と目録testの修正 (回収session、2026-09-19 21:29〜23:30 JST)

記録commit `fdbf21820` の後に中断したwaveを回収した。main `2ba400087` (baseから35 commit) を統合commit
`4c9d9ecc2` で取り込み (衝突は `docs/phase3.md` の先頭項目1か所、両項目を保持)、check_docs・spool dry-run・
焦点走 (`test_ss2pl_lock_study.py` + `test_hooks.py`、586 passed) を緑にしてから受入全走を投入した。

受入attempt 1 (21:29〜21:39、tested main `2ba400087`、tip `4c9d9ecc2`、3 shard) は **3 failed / 25276 passed /
69 skipped**。赤はすべて `orchestrator/tests/test_ccbench_spawn_sites.py` の define 目録:
`test_patch_define_inventory_matches_condition_gate_registry` (`SS2PL_WFG_HH`・`SS2PL_LOCK_HH`・
`SS2PL_STUDY_LOCK_HH` が `DEFINE_SPECS` に無い)、`..._classifies_t2155_production_sinks_exactly`
(`proven-unreachable` 38≠35)、`..._t2520_certify_entry_removal` (同 28≠25)。F945型ではない。

原因は本wave起因である。3 macroは patch c (一次資料 §1.1、`#pragma once` が `-E -P` に残渣を残すため
新規header 3本を include guard へ) の guard で、baseとmainの patch には無い (どちらも hit 0)。目録関数
`_patch_added_define_interfaces()` は patch が足した `#if/#ifndef` 条件の新規 macro を外部供給 TU define と
みなして registry と照合するが、include guard 慣用句の構造的除外を持っていなかった (他の patch は新規 header を
足していないため前例が無い)。焦点走が `patches/` を directory glob で読む consumer test を名前検索で落とした
点は F386 の再発として台帳へ追記した。

裁定 (`verbatim/fix3-ruling.md`): `#pragma once` への復帰は裁定違反、`DEFINE_SPECS` 登録は supply macro 化、
期待値更新・skip・deselect は弱体化なので採らず、目録関数に「新規 file の先頭 `#ifndef X`・直後の値なし
`#define X`・末尾 `#endif`」の慣用句だけを除く構造的除外を Codex author で足した (fix3、+53/-8、
`verbatim/fix3.md`、統合commit `134ea235c`)。焦点走 (spawn_sites + ss2pl + plain_runner_coverage +
real-repo meta 2 node、計算ノード 10723.nqsv) は 180 passed / 2 skipped。

受理集合が変わる変更なので read-only の焦点再レビュー (`verbatim/focus3.md`) を1本入れたところ **NO-GO**:
fix3 は guard macro X をその file の全条件行から除くため、guard 形の新規 file が本文で `#if X + 0` を使うと
外部供給 macro X が候補から消える (反例 escape.hh)。fix4 (`verbatim/fix4-ruling.md`、`verbatim/fix4.md`、
+12/-1、統合commit `7f24b1c32`) で除外を guard 自身の `#ifndef X` 行1行に限り、反例を unit test の負例に
足した。焦点走 (10762.nqsv) は 180 passed / 2 skipped。実物の patch では guard 3個以外に候補差は無く、
`SS2PL_LOCK_IMPL`・`SS2PL_LOCK_KIND`・`SS2PL_DLR`・`SS2PL_WFG_DIAG` は候補に残る (focus3 の実測)。

変異は fix 最終commit `7f24b1c32` を独立cloneの main に固定して再走した (`receipts/mutation-spec-fix4.json`、
`receipts/mutation-ledger-fix4.json`、`receipts/mutation-wrapper-fix4.json`)。runner は
`run_tests.py --force-dispatch orchestrator/tests/test_ccbench_spawn_sites.py`、baseline PASSED。

| 変異 | 実測結果 | 殺した test |
|---|---|---|
| M7 除外を変更 file の guard へ拡大 | KILLED | 負例 (変更 file 内 guard が候補から消える) |
| M8 値付き `#define X 0` も除外 | KILLED | 負例 (既定値慣用句が候補から消える) |
| M9 除外を file 全条件行へ (fix3 の挙動) | KILLED | 負例 escape.hh (`#if X + 0` の X が候補から消える) |

3件とも期待 node (`test_patch_define_inventory_excludes_only_new_file_include_guards`) だけで KILLED、
MISMATCH/SURVIVED/TIMEOUT は 0、wrapper は共有木の前後一致・teardown 完了。fix3 版の M7/M8 (2 KILLED、
`receipts/mutation-ledger-fix3.json`) は fix4 で置き換えた参考値として保持する。
Codex 子は fix3 11 call / 215秒、fix4 7 call / 106秒、focus3 6 call / 127秒。子はいずれも計算ノードの
dispatch preflight で pytest を起動できず「実装済み・未実走」で報告し、実走はすべて親が行った。
この節の時点で受入再走・land は未実施。
