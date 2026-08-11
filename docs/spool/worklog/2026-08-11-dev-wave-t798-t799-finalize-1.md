---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t798-t799-finalize
seq: 1
title: fold transaction を単一 finalize protocol にし観測値で束縛した — 実装 wave (コード + docs、branch worktree-dev-wave-t798-t799-finalize)
---

## 本文

- **依頼引数は [T-798]/[T-799] だったが、裁定 inbox §105 が [T-820]/[T-821] を「同 wave 同梱」と
  裁定していたため 4 件を束ねた。** とくに [T-821] (receipt へ base / tested tip / wave ref) は
  依頼の動機「certified 選択の proof chain を main 履歴へ帰属させる」そのものである。
  wave 中の main 取り込みで、この 2 件の裁定が canonical 台帳にも現れた (scope 判断の裏取り)。
- **段 1 の前提実測 2 件は、いずれも「存在証明」であって普遍命題ではない** (両敵対レンズが
  独立に一般化を攻撃し、親が縮小した)。
  - **post-commit crash**: 本番 land は `core.hooksPath=/dev/null` で hook を無効化するため
    hook 注入が使えず、main の ref を tight loop で監視する watcher から fold commit 直後に
    SIGKILL した (rc=-9)。**測った 1 注入点では**残骸は durable かつ clean で、canonical も
    fragment GC も commit 済み、state 無し、同 argv の再投入は rc=10 `stale-main` だった。
    **ただし postcondition (`verify_declared_fold_commit` を含む) は 1 つも走っていない**ので、
    「certified に健全」とは言えない。**この実測が示したのは「削除を postcondition 後へ移すと
    新しい相を作る」ことであり、finalize 経路が必須の構成要素である**という裁定の裏取りになった。
  - **archive 跨ぎ T 重複**: 現行 worklog 末尾へ archive 専有 ID `[T-013]` の新規項を実編集で
    1 行足し、実 `tools/check_docs.py` を走らせて **rc=0「違反なし」**を得た (復元後 sha256 一致・
    tree clean を確認)。**測ったのはこの 1 形だけ**で、D/F・見送り台帳・別配置は未測定である。
- **敵対レンズ 4 本 (段 3 の sol/luna、段 6 の sol/luna) が計 22 件を返し、段 6 は両方 NO-GO だった。**
  親は 1 件ずつ独立に裁定し、**実装 6 件・格下げ/裁定パッケージ 6 件・誤り 1 件**に分けた。
  - **最も効いたのは「本 wave が作った受理集合の拡大」1 件**である。noop 回帰を閉じる際、
    `apply_fold` が `status="noop"` を名乗る plan を中身を見ずに素通しするようになっていた。
    pending fragment を持つ plan を forged noop へ書き換えると、canonical 追記も fragment GC も
    せずに成功していた。段 6 レンズ A が見つけ、noop の空検査を足して閉じた。
  - **fold commit の author が prefix 比較**で、正規 identity の後ろへ任意 bytes を足した commit が
    通っていた。timestamp と timezone まで含む厳密形へ直した。
  - **「noop で FOLDED 検査を飛ばせる」というレンズ B の所見は誤りだった** — `_discover` は
    noop 経路でも `FOLDED.md` の receipt を parse する。canonical を読まない点は wave 前と同一で
    回帰でない。
  - **「finalize の unlink 後から自動復旧できない」は real だが回帰ではない** — 段 1 実測で
    wave 前も同一の残骸だった。閉じるには受理集合を広げる新経路が要るので裁定パッケージへ回した。
  - **「state の ID 検査が CAS でない」も real だが改善済み** — wave 前の `_rollback_fold` は
    ID を見ずに無条件 unlink していた。
- **親の provisional 裁定 (P5) は両レンズが独立に「必要だが不十分」と判定した。**
  親は「phase を権威にしない」原則だけ採り、**fold commit の identity (単一 parent・author・
  message bytes・親との diff の path/status/mode/blob OID の完全一致) を受理の権威にする**形へ
  強化して採用した。phase field は検証可能な事実を 1 つも足さないため、tree と矛盾したときに
  phase を信じる方が危険である。
- **段 2 プランが親スケッチに無かった事実を 3 つ持ち込んだ。** (i) resume 時に現 filesystem を
  そのまま hash すると、transaction 自身が target を書き換え fragment を GC しているため
  **正常な resume でも必ず closure 不一致になる** (正規化規則が schema 契約の一部になった)。
  (ii) `git commit` と phase 書換えの間の残余窓。(iii) 前 wave の「壊れる pin は 1 本」は
  「削除を pin する数」としては正しいが、state 残存で**連続 fold を行うテスト約 10 本**が
  別理由で赤になる。
- **変異 matrix は 8/8 KILLED (baseline PASSED、MISMATCH 0・SURVIVED 0)。**
  wave 前の実コードの形へ戻す変異を 4 件含み、いずれも殺された。
  **M06 は初回 probe で SURVIVED した (erratum)** — 狙った `_complete_shape` の GC 残存検査は
  そこへ到達する時点で GC が完了しており他層に mask される。実効 gate である `_discover` の
  active 受理条件へ再照準して KILLED になり、両層同時変異でも同じ node が殺すことを確認した。
- **codex 子は pytest を 1 度も走らせられなかった** (`qstat -Q preflight rc=1` / sandbox が
  予約台帳更新と socket を拒否)。実測はすべて親が行い、子の報告は一貫して
  「実装済み・未実走」で受け取った。
- **セッション事象**: 段 2 の初回投入は `--artifact-root` の親 directory 不在で rc=2 (起動前の
  argv エラー、成果物ゼロ) だった。directory を作り新しい artifact 名で再投入した。

- **受入全走で main 由来の赤 2 件を観測し、ユーザー裁定で既知赤 waiver W2 を新設した。**
  対象は `orchestrator/tests/test_t793_report.py::test_deny_only_report_contains_authority_and_both_submission_denials`
  と `orchestrator/tests/test_t793_report.py::test_actual_head_d292_reference_is_reported_fail_closed` の
  **2 node のみ**である。原因は本 wave の差分ではなく、main の `docs/decisions.md` にある
  **D305 が D291 を 6 箇所参照している**ことで、[T-793] の scanner
  (「D291 より後の decision が D291 を参照したら fail-closed」) が `D292` と `D305` の
  両方を返す一方、テストは `["D292"]` だけを期待している。
  **本 wave は `docs/decisions.md` を 1 byte も変えていない** (差分で確認)。
  テストは main の `c820722a` で land し、その後の fold commit `427da17c` (main の tip) が
  D305 を追加して壊した。
- **W2 の適用条件 (毎回検査する)。** (1) 赤が上記 2 node **だけ**であること
  (他の赤が 1 件でもあれば適用せず停止)、(2) 自 wave の差分が `docs/decisions.md` を
  変更していないこと、(3) canonical の D305 が D291 を参照していることを実際に確認すること。
  **並行セッションも同じ 3 条件でだけ適用してよい。**
  失効: [T-793] の scanner 仕様かテスト期待値のどちらが正かが裁定され、その修正が land した時点。
- **W2 の失効見込み — 修正は既に存在する。** 並行 wave [T-827] から共有があり、
  `worktree-dev-wave-t827-slow-tests` の commit `292151a5` が
  `orchestrator/tests/test_t793_report.py` だけを直している (production は正しいので不変)。
  向こうの裁定は「`status == "possible_supersession"` は exact 維持、`"D292" in decision_ids` を
  必須にし、**完全一致は要求せず**昇順・重複なしという構造的性質を検査する」であり、
  D292 を落とす変異で両 node が KILLED になることを確認済みとのこと。
  **本 wave は cherry-pick しない** — 向こうが land 準備中で、同じ commit を二重に持つと
  land 時に衝突するため。向こうの land 後に main を取り込めば W2 は自動的に失効する。
  なお `git diff --stat main -- orchestrator/publication/ docs/decisions.md` が空であることを
  本 wave でも実測し、入力が main と byte 同一であることを確認した。

## 次の一手差分

### 更新

- [T-798] **P2・実装済み (2026-08-11 実装 wave)**: 統合案どおり、既存 transaction state へ
  phase (`applied`/`committed`) と起源を持たせ、state 削除を land の postcondition 後へ移し、
  finalize を land 専用にした。`validate_spool_tree` の active 受理は
  `check_docs.py --expect-active-transaction <id>` の明示宣言を要求し、既定は従来どおり拒否する。
  残る相 (finalize の unlink 後、rollback 途中失敗) は {{T:fold-terminal-idempotence}} と
  [T-800]/[T-801] へ切り出した。
  base: 526fe4c671824debb5f6c9cb27255d4687750350c839509dbb6e1a11a1371a79
- [T-799] **P2・実装済み (2026-08-11 実装 wave)**: state へ land 起源・base・tested tip・
  wave ref・rollback ref に加えて **trusted cutoff・audited digest・plan 入力 closure の hash** を
  束縛し、`transaction_id` の payload にも含めた。closure には canonical・archive・fragment・
  rotate limit に加えて **fold engine (`tools/spool_fold.py`) と `tools/check_docs.py` の bytes** を
  入れた (敵対レンズが「engine を未 commit で書き換えて standalone apply し、戻してから land
  させると現行 engine なら作らない採番を commit できる」経路を示したため)。
  mutation 前に HEAD と closure を照合し、resume でも clean preflight を通す。
  base: 5f32ffffd71a3567991c5cfab8b0302c8e1806cd296f41fd1653e566fc0f9e96
- [T-820] **P3・実装済み (2026-08-11 実装 wave)**: `_load_rotate_limit` の例外囲いを
  `BaseException` へ広げ、`SystemExit`/`KeyboardInterrupt` を `SpoolValidationError` へ畳んだ。
  base: fbf9732476eea23e5f86f568dd5083929086d18c401887992e95a0bc928d5855
- [T-821] **P2・実装済み (2026-08-11 実装 wave)**: `FOLDED.md` の receipt へ base / tested tip /
  wave ref を足した。既存の 5-field record が大量にあるため、**v2 record が 1 つ現れたら以降は
  v2 exact 必須**という位置的 cutover にした (「新 field を個別 optional」にすると cutover 後の
  receipt が origin 三値なしで正式集合へ入る fail-open になる)。**読取り時の OID 実在検査は
  していない** — 書込み時に実 object/ref を観測して検査する形であり、durable 再検証ではない。
  base: ff20622ffc6f848152c236dfa8b468708aa9a5e0980d7c15232830e313296afa

### 新規

- {{T:fold-terminal-idempotence}} **P2・新規**: finalize が state を unlink した後、
  成功応答の前に process が死ぬと、`tree=after / state 無し / main=検証済み fold commit` が残り、
  **land は結果を冪等に再取得できない** (再投入は rc=10 `stale-main`)。段 1 実測で
  **wave 前も同一の残骸**だったため回帰ではないが、単一 finalize protocol の終端はここで閉じていない。
  選択肢 = (a) state 無しの verified fold commit を `already-landed` と認識する経路を land へ足す /
  (b) finalize 前に durable な completion receipt を書き、その存在で終端を判定する /
  (c) 現状維持。成果物影響 = (c) のままなら、fold は durable に成立しているのに land 成功記録・
  peer 通知・後続 certified 作業が停止し、運用者が手で照合するまで進めない。
  親推奨 = (a) だが**受理集合を広げる変更なので独立の敵対検証が要る**。
- {{T:standalone-fold-serialization}} **P2・新規**: standalone `spool_fold.py` は land lock を
  取らないため、land と同時に走ると state の read/check と unlink/replace の間に CAS が無く、
  **別 transaction の journal を削除・上書きできる** (段 6 レンズ B が経路を構成)。
  本 wave は `_rollback_fold` が消してよい state を transaction ID 一致に限定するところまで
  狭めた (wave 前は無条件 unlink) が、直列化そのものは閉じていない。
  選択肢 = (a) standalone にも land lock を取らせる / (b) [T-799](b) の同伴条件である
  lock-aware finalize / inspect command を作り standalone apply を封鎖する / (c) 現状維持。
  成果物影響 = (c) のままなら、canonical と fragment GC が journal 無しで進み、
  台帳・receipt・proof chain の対応が writer の順序で変わりうる。親推奨 = (b)。
- {{T:fold-commit-transaction-binding}} **P3・新規**: commit identity gate は content-addressed に
  「意図した tree か」を検査するため、**同じ parent / tree / author / message を持つ手動 commit も
  受理する**。transaction ID は commit へ束縛されていないので「どの transaction が作った commit か」は
  台帳から言えない。選択肢 = (a) fold commit message へ transaction ID の構造化 trailer を足す
  ([T-821] の (b) 案に相当) / (b) 現状維持。成果物影響 = (b) のままなら、canonical bytes が同じでも
  provenance 上の transaction 識別ができない。**(a) は `_FOLD_MESSAGE` の固定契約と
  `verify_declared_fold_commit` に波及する**ため、本 wave では scope 外とした。
- {{T:fold-subset-shape-flake}} **P3・新規**: `test_exploration_external_root_keeps_wave_clean` が
  部分集合走 (本 wave の焦点 4 ファイル走) で必ず落ちる。`conftest.py` の autouse fixture
  `_declare_default_test_site` は `orchestrator.campaign.site_policy` が**既に `sys.modules` に
  あるときだけ**サイト同一性を無効化するが、当該テストは campaign を実行時に遅延 import するため、
  計算ノードでは `current_site()` が PEGASUS_COMPUTE を返し
  `CertifiedWriterAuthorizationError` になる。選択肢 = (a) fixture を import 順に依存しない形にする /
  (b) 当該テストが自分で site を宣言する / (c) 現状維持。成果物影響 = (c) のままなら、
  焦点走と受入全走で受理集合が食い違い、**変異 harness の baseline が緑にならず**
  部分集合を対象にした変異検査が原理的に回せない。
