---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-15
wave: dev-wave-t1087-acceptance-red-check
seq: 1
title: 依頼された P1 二欠陥が既に main で解消済みであることを実 dispatch 2 走で確定し、非帰属受理が実運用で一度も発火していない構造的理由を全件走査で特定した (実装差分ゼロ、branch worktree-dev-wave-t1087-acceptance-red-check)
---

## 本文

- 起点はユーザーの実装依頼 ([T-1087] + 裁定 inbox
  `2026-08-13-acceptance-red-check-collect-timeout.md` の collect 段 120 秒 timeout)。
  **`DW-S01` に従って前提を実測したところ、依頼が挙げた 2 欠陥はどちらも main で既に
  解消していた。** 依頼の前提を覆す新事実として brief に出し、段 4 で scope を裁定し直した。
- **実測 1 (合成 log・実在 node 1 件): rc=1 / `attributable-red` / 78 秒。**
  実測 2 (**2026-08-13 の実受入 log の逐語複製**・実赤 2 件): rc=1 / `attributable-red` / 155 秒。
  受領証が実際に書かれたことは checker receipt の `source=dispatch-receipt` と PBS request_id
  (走 1 が 1 件、走 2 が 2 件) が示す。**削除されたことの証拠は receipt の
  `deleted_receipt_path` field ではない** — この field は削除より前に組み立てられるため
  自己申告である (段 3 レンズが指摘、親が受け入れた)。実際の証拠は、collection と単独再走の
  それぞれの直後に走る清浄性検査 (`--ignored=matching` 込みで空 tree の sha256 一致を要求) を
  計 6 回すべて通過して rc=1 の判定へ到達したことである。残っていれば必ずそこで rc=2 になる。
- 78 秒 / 155 秒は [T-1090] が実測した `T(n) = 15 + 63n` の n=1 / n=2 と整合する。
- **解消の出所は 2026-08-13 の [T-1027] wave である。** とくに「限定 cleanup を空 root まで
  閉じ、環境正規化と変異の単一理由性を直す」commit が受領証面を閉じ、collect 段の timeout は
  同 wave が collection 権威を receipt へ移す過程で対称化された (両経路とも 5100 秒、
  回帰テストが 2 値組で固定済み)。裁定控え
  `2026-08-13-t1027-probe-fingerprint-vs-dispatch-residue.md` も
  「`output/pegasus-dispatch/` 側は scope 内で閉じた」と明記している。**台帳側だけが
  entry 547〜552 で持ち越し表記のまま更新されず、解決済みの P1 が生きて見えていた。**
- **主張の射程 (段 3 レンズが親の過大主張を縮小させた)。** 不再現を実証したのは
  **正常な preferred / fallback child receipt 経路**に限る。受領証の告知が無い・非一意・
  child rc 不一致の各経路は cleanup へ入る前に例外となり、root が空でなければ削除もしない。
  いずれも倒れる向きは fail-closed (rc=2) で受理集合は緩まないが、**「残渣経路は無い」とは
  言えない**。親の初稿はこれを全経路の不在証明として書いており、レンズが正しく倒した。
- **依頼が示した設計 2 択は、どちらも採るべきでなかった。** 「受領証を probe worktree の外へ
  出す」は D216 が既に実測却下している (`.gitignore` の `output/pegasus-dispatch/` は末尾
  スラッシュ付きのため symlink を ignore せず clean gate に映る)。「清浄性検査から受領証 path を
  除外する」は ignored な副作用の検出力を落とし、rerun node の副作用を拒否する既存防壁を壊す。
  main が実際に採っている第 3 の設計と、2 択を却下する根拠を
  {{D:dispatch-residue-deleted-not-excluded}} に記録した。
- **非帰属受理が実運用に到達しない理由は別にあり、それを全件走査で特定した。**
  job 領域に存在する checker receipt を打ち切らずに列挙すると 10 件で、赤を持つ 9 件は
  **すべて `attributable-red`、node 11 件すべてが `rerun_rc=0` = 帰属**。
  `non-attributable-only` は 1 件も無い。うち 1 件は probe ではなく **本番の発火**で、
  2026-08-15 の main を tested main とする実受入の赤
  (`test_dev_wave_wait.py::test_public_main_real_signal_releases_lease`) を機械が帰属と判定した。
  **この赤はエントリ 548 が人間の判断として非帰属と記録したもの**である。
- **食い違いの構造。** `DW-O18` は「差分が到達しえない赤は単独再走で実測し、再現しなければ
  帰属せずフレーク起票する」と定め、続けて非帰属 checker を「この機械化」と名指す。ところが
  checker は **差分到達可能性を入力に一切持たない**。人間が使う条件 (エントリ 548 の場合は
  「当該 file に 1 行も触れていない」と lease 干渉という機序) を評価できず、残った単独再走
  だけで決める。加えて受入は 48 worker の分散走、checker の再走は新規 worktree の単独 node 走
  なので、**同時実行に起因するフレークは構造上そもそも再現しえない**。
- **refuted: 「フレークは必ず帰属に倒れる」は言い過ぎだった。** 段 3 レンズが倒した。
  持続性フレーク・共有環境障害・同一 worker 内の順序依存は単独再走でも赤になりうるため、
  非帰属分類は原理的に発火する。**実測が言えるのは 11/11 が帰属だったことまで**であり、
  全称命題ではない。親はこれを受け入れて主張を実測の範囲へ戻した。
- **refuted: 単独再走前後の指紋比較は恒真ではない。** 親は「直前の清浄性検査が両指紋を
  空 tree の sha256 に固定するので到達不能」と裁定しかけたが、レンズが反例を出した —
  清浄性検査の後に一過的な並行書込みがあれば before と after は異なりうる。テスト被覆は
  ゼロだが、削除すると競合検出面を失うため不採用とし、新規タスクにもしない。
- **段 3 レンズが新しい実欠陥を 1 件出し、親が独立に検算した。** checker は子 pytest へ渡す
  環境から pytest 選択系の変数しか除去せず、task-run 記録の変数を残す。これが設定されていると
  `run_tests.py` は既定で **probe worktree 内の** `output/task-runs` へ記録を書き、
  gitignore 対象でないため清浄性検査が非空になって rc=2 になる。本番 consumer は受入 preflight で
  repo 内 task-run root を拒否するので守られているが、`DW-O18` が親へ求める checker の直接実行は
  守られていない。現行セッションでは当該変数は未設定 (実測) なので潜在欠陥であり、
  `DW-G04` に従い実装せず起票した。
- エージェント工数: codex 子 1 本 (段 3 敵対 consult、lane sol、reasoning max、
  671 秒、rc=0、`check_codex_output` 受理、7,603 bytes、所見 8 件)。
  段 2 プラン子と段 5 実装子は起動していない — 実装差分ゼロの docs-only wave であり
  `DW-C00` の軽量版に該当する。**レンズは親の結論を 3 点で倒した** (射程の過大、
  削除証拠の取り違え、全称命題)。所見ゼロではないので `DW-M02` の裏取り義務は発生しない。
- セッション異常 1 件。live dogfood の 1 回目が投入 0 秒で
  `--tested-main does not equal refs/heads/main HEAD` で落ちた。投入直前に別 wave が land して
  main が進んでいたため。取り込み直して再投入した。checker は tested_main を走行の前後 2 回
  照合するので、**受入と同様に main の追い越しで丸ごと無効化されうる**。
- **本 wave 自身が、記録したその欠陥で止まった (2026-08-15 08:17–08:21 JST)。** 受入 1 回目は
  `1 failed / 11033 passed / 65 skipped / 141.52 秒` で、赤は
  `test_dev_wave_wait.py::test_signal_after_core_success_uses_restored_real_handler` の 1 件だけ。
  これは [T-1058] が起票済みの signal handler フレーク族である。非帰属 checker は自動で走り、
  単独再走が緑だったため**帰属**と判定し、待ち手は receipt を出さずに rc=70 で終わった。
  **本 wave の差分は `docs/spool/` の fragment 2 本だけで、実装面を 1 行も持たない。**
  待ち手のテストへ到達する経路は存在しないので、`DW-O18` の「差分が到達しえない赤は単独再走で
  実測し、再現しなければ帰属せずフレーク起票する」に照らせば非帰属である。機械はその逆を返した。
  上記の全件走査 11 node に本件を加えて **12 node すべてが帰属判定**となり、
  本 wave は自分の主張の 12 例目を自分で踏んだ。受入を再走して緑の窓を取り直した。
- 段 8 の改善候補は 1 件で、**予算で塞がれたため実装しなかった。** 上記の追い越し事象から
  「重い投入 (受入・checker) の直前に local main を再確認する」を明文化したかったが、
  話題が合う `DW-O18` は既に単節予算の際にあり、意味等価な縮約もできない。
  これは [T-1100] が記録した予算閉塞と同型であり、新規に起票せず同項へ委ねる。
  command 入口への追記は「事故を伴わない明確化を追記理由にしない」規約に反するため行わない。

## 次の一手差分

### 完了

- [T-1087] 非帰属 checker が自分の dispatch 受領証で清浄性検査を落とす件は、2026-08-13 の
  [T-1027] wave で既に解消していた。正常な受領証告知経路での不再現を実 dispatch 2 走
  (78 秒 / 155 秒、いずれも rc=1 で判定到達、清浄性検査 6 回通過) で確定し、採用済み設計の
  根拠を {{D:dispatch-residue-deleted-not-excluded}} へ記録した。同時に指摘された collect 段
  120 秒 timeout も不再現 (両経路 5100 秒で対称、回帰テストが固定済み)。
  **本項が閉じるのは受領証残渣という機序だけである。** checker が判定不能になる別機序
  (受領証形の未模型化、非空 root、環境由来の別 writer) と、非帰属受理が実運用へ到達しない
  真因は下記の新規 3 項が継承する。
  remaining: none
  base: fd82c7856d3dcdcbf33e34b0add1645202c0512d8f3b5696f62bd58a68d00ec4

### 新規

- {{T:acceptance-red-flake-classification}} **P1・要裁定**: 非帰属 checker は
  単独再走が緑 (`rerun_rc=0`) の赤を帰属に分類して land を止める。存在する receipt 10 件の
  全件走査では赤を持つ 9 件がすべて `attributable-red`、node 11 件すべてが `rerun_rc=0` で、
  非帰属経路は本番でも一度も発火していない。**本 wave 自身の受入 1 回目もこれに加わり 12 node
  すべてが帰属判定になった** — 実装面を 1 行も持たない docs-only の差分に対して、
  到達経路の無い待ち手のテストの赤が帰属と判定され、land が止まった。本番発火 1 件でも、
  エントリ 548 が人間の判断として非帰属と記録した signal handler フレークを機械が
  帰属と判定している。`DW-O18` は checker を
  「差分が到達しえない赤は再現しなければ帰属せず」の機械化と名指すが、checker は
  差分到達可能性を入力に持たない。受入は 48 worker の分散走、再走は単独 node 走なので、
  同時実行由来のフレークは構造上再現しえない。候補は (a) tested main での再走を N 回に増やし
  1 度でも赤なら非帰属とする、(b) 差分到達可能性を入力に加える、(c) 批准済み既知赤 nodeid の
  registry を併設する、(d) 現状を仕様として受け入れフレークは再走で対処する。
  いずれも land gate の受理集合を変えるため裁定が要る。
  成果物影響 = 未裁定のままだと、受入が rc=1 になった wave は正しく非帰属でも
  受入と checker の時間を捨てて land できず、非帰属受理の機構が実運用へ到達しない。
- {{T:checker-task-run-env-leak}} **P2・新規**: 非帰属 checker は子 pytest へ渡す環境から
  pytest 選択系の変数しか除去せず、task-run 記録の変数を残す。これが設定された状態で checker を
  直接実行すると、`run_tests.py` が既定で probe worktree 内の `output/task-runs` へ記録を書き、
  gitignore 対象でないため清浄性検査が非空になって rc=2 になる。本番 consumer は受入 preflight で
  repo 内 task-run root を拒否するため守られているが、`DW-O18` が親へ求める checker の直接実行は
  守られていない。現行セッションでは当該変数は未設定なので潜在。
  成果物影響 = 受理集合は変わらない (fail-closed)。ただし親が `DW-O18` に従って非帰属を
  機械的に立証しようとした場面で、原因不明の rc=2 として現れて立証を不能にする。
- {{T:dispatch-setup-receipt-shape}} **P3・新規**: dispatch の setup 失敗経路は
  `output/pegasus-dispatch/receipt-setup-<nonce>.json` を root 直下へ書くが、非帰属 checker の
  受領証 path 模型は `receipt.json` と `receipt-fallback-*.json` しか持たない。この経路では
  collection が先に fail-closed するため永続残渣は出ないが、診断は「collect-only failed」としか
  出ず、受領証に入っている実際の infra 理由が読まれない。非空 root による cleanup 失敗も同型で、
  どちらも判定不能の原因究明を遅らせる。
  成果物影響 = 受理集合は変わらない。判定不能からの復帰が遅れるだけなので nit 相当。
