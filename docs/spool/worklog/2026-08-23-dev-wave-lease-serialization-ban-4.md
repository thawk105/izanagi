---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-lease-serialization-ban
seq: 4
title: 受入 lease の待ちループと待ち行列を機構ごと除去した (コード+テスト+docs、branch worktree-dev-wave-lease-serialization-ban、変異matrix = baseline PASSED・MUT-1〜8 8/8 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- ユーザー依頼: 「dev-wave で lease の直列化をやらないよう厳しく制限する。Pegasus 計算ノードが
  混雑しており、lease の直列化で研究が破滅している」。D662 決定 1 は 2026-08-22 に待ち行列廃止を
  裁定済みだったが、実装は opt-in flag に留まり、入口 command は同じ日に
  「lease を取れたときだけ投入せよ」と命じたままだった。設計判断は {{D:lease-wait-unreachable}}。
- **親 brief の実測解釈を段 4 で訂正した。** 段 1 で「lease が free なのに待ち札 4 枚が滞留し、
  新着 wave が `queued` になる状態が現に発生している」と書いたが、段 3 敵対レンズ (sol) が
  待ち札の stale 閾値 300 秒を根拠に反証した。観測した 4 枚は齢 12〜17 分で全て stale であり、
  その瞬間に新着が `queued` になることはなかった。正しい主張は「直前 17 分の間に 4 つの wave が
  即取得できず札を登録した」という混雑の証拠であり、各札の fresh な 300 秒窓の間だけ
  free lease でも新着が `queued` になる。依頼の定性的な結論は worklog entry 831 の実測
  (15 件以上の並行 wave が同時ブロック、最長 63 分超) が独立に支持しており変わらない。
- **段 3 レンズ B の所見 1 件を refuted にした。** 「並行 branch `worktree-dev-wave-lease-cmd-entry-sync`
  が DW-O27 を checker の必須集合から外す」は実 diff と食い違う。同 branch の
  `tools/check_docs.py` 変更は段 6 逐語 3 行だけで、`REQUIRED_REFERENCE_SECTIONS` と条件 18 の
  `DW-O27` は無変更。`orchestrator/tests/test_check_docs.py` はむしろ decoy case を 2 件
  追加して入口検査を強化している。
- **段 3 レンズ A の懸念 1 件は方向が逆だった。** 「既定を unclaimed にすると no-verdict retry が
  通常経路で失われる」— retry gate が lease 所有を要求するのは事実だが、本 wave は `queued` を
  `acquired` へ変えるので ACQUIRED 頻度は上がる。retry 可用性は悪化せず改善する。
- **段 6 レビュー A の must-fix 1 件 (M2) を不採用と裁定した。** 「`held`/`queued` の malformed
  payload を fail-closed で拒否せよ」は、lease directory の破損という一点で全 wave の受入が
  止まる設計であり、D662 が否定した「一つの wave の不具合が全体を止める」形そのものである。
  実害も無い — 未取得経路は claim payload の holder と main SHA を採らず自分で計算した値を使う。
  残る細部 (`holder` が自己 digest なのに `holder_self:false` なら lease を取り逃す) は、
  待ち行列廃止後は誰も止めないので nit として裁定パッケージへ送る。
- **段 6 レビュー B の結論**: 現 tip の受入経路から、lease の `held`/`queued` を理由にした
  待機・poll・再 claim・待ち札登録は到達不能。flag の有無に関係なく 1 回だけ非 blocking claim。
- 段 6 で残った must-fix は 2 巡で全件 closed。Pin C を state × flag の 16 ケースへ展開し、
  race 3 件 (`FileExistsError` retry / stale lease 消失 retry / 所有外 ticket を消さない cleanup) を
  新設し、Pin A の docstring を「未取得経路の投入前 claim は 1 回」へ限定した。
- **codex 実装子 3 本とも pytest を実走できなかった** (`qstat -Q` が sandbox から届かず rc=16、
  child 未起動)。全員が「実装済み・未実走」と正直に申告し、親が計算ノードで実走した。
- **非帰属赤 1 件を実測で確定した。**
  `test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean` が login node で
  再現的に落ちるが、main (83baeefa) の detached probe worktree でも同じく落ち、計算ノードでは
  緑になる。lease と無関係な `IZANAGI_EXPLORATION_OUTPUT_ROOT` の外部 output root 検証であり、
  本 wave に非帰属。
- **手順ミス 1 件**: 変異 probe の走行中に spool fragment を untracked で作り、harness が
  `runner/test 実行前に untracked file を検出` で rc=2 中止した。変異前に止まったので実害なし。
  memory `no-acceptance-run-during-mutation` の「tree へ書かない」に該当する。
  probe attempt 1 は `fresh --attempt-out が既に存在する` でも rc=2 になり、DW-O19 に従って
  `--out`/`--attempt-out`/`--wrapper-attempt` を毎回新しくする runner へ直した。
- 進捗報告の JST 時刻 5 件を実測せず推定で書いた。F1 の再発として記録した。
- 入口 `.claude/commands/dev-wave.md` の段 6 文言は本 wave の scope 外に置いた。
  `worktree-dev-wave-lease-cmd-entry-sync` が同じ行と `tools/check_docs.py` の逐語 pin を
  所有しており、触れば land で競合するためである。両レンズが「最大の穴」と判定した real 所見であり、
  同 branch が着地するまで入口は旧条件を命じ続ける。

- **受入は完走していない。受領証は発行されていない。land も未実施である。**
  attempt 1 は判定器 `check_acceptance_reds.py` が
  `cache-only submodule URL rewrite failed with rc=255` で rc=2 (判定不能) となり rc=70。
  attempt 2 は判定器が 28 分走り続けたところでユーザー指示により停止した
  (「check_acceptance_reds.py をオフにしろ。使うな。41 分かかる？ふざけるな。
  それは研究開発が壊れる。全並行セッションにも通達しろ」2026-08-23)。
  通達は稼働中の 9 セッション全部へ送り、うち 3 セッションは同じ裁定を直接受けていたと回答した。
- **受入の実測内訳。** テスト本体は 335.55 秒 (5 分 35 秒)、41 failed / 14249 passed / 96 skipped。
  赤の内訳は `test_sort_swo_oracle.py` 26 件 (main commit 98badc9b で known-violation 登録済み)、
  `test_codex_worker_launch.py` **15 件**、`test_t338_submission_gate_unit5.py` 1 件。
  launcher 15 件の署名は
  `NG: Codex 起動前検証後に wall_clock_admission_bound_s へ到達した` で、高負荷下の
  タイムアウトである。main (d1722822) の detached worktree で同じ 2 file を計算ノードで
  単独実走すると **222 passed / 9.4 秒**なので、本 wave にも main にも帰属しない。
- **判定器を使わない場合、テストを絞って child-green にする回避策は land できない。**
  `tools/dev_wave_land.py:736-784` が receipt を
  `argv == ["python3", "tools/run_tests.py"]`、`resolved_runner_path == "tools/run_tests.py"`、
  `PYTEST_ADDOPTS` / `PYTEST_PLUGINS` が空、で pin している。`--ignore` を足した receipt は
  rc=23 で拒否され main は 1 bit も動かない。これを実測した時点で、同じ回避策を
  投入しようとしていた並行セッションへ緊急で伝えた。
- **land は 2 つの外部依存が解けるまでできない。** (1) `test_sort_swo_oracle.py` 26 件が
  main から消えること (別 session `remove sort-swo-oracle test` が担当、runner 側で
  受入形のときだけ `--ignore` を注入する形なので land の argv pin と両立する)、
  (2) launcher 15 件の負荷タイムアウトが出ない状態で素の全走が rc=0 になること。
  ユーザー裁定により本 wave は branch を残して終了し、除去の着地後に別 session が land する。

- **受入 1 回に 40 分かかる原因を実測で分解した。** 内訳は queue 待ち 5 分 26 秒
  (09:16:26 投入 → 09:21:52 開始)、テスト本体 5 分 41 秒 (341 秒、job 939080.nqsv)、
  **赤の非帰属判定器 約 29 分**。遅いのはテストでも計算ノードの混雑でもなく判定器だった。
- **裁定 D678「判定器を受入経路で使わない」がコードで守られていないことを発見した。**
  受入 command が赤で戻ると `tools/dev_wave_wait.py` が
  `tools/check_acceptance_reds.py` を自動起動する (`_RED_CHECKER_PATH` 経由、
  別 session `pegasus test distribution optimization` が独立に file:line で裏取り)。
  親は判定器を使わないつもりで投入したが、赤になった瞬間に走り 29 分を失った。
  **散文の裁定が機構で守られていないと全 wave が同じ穴に落ちる**という一般則の実例である。
  ユーザー裁定 (2026-08-23):「自分が原因じゃないテスト失敗は一瞬で直せるなら自分で直す、
  難しそうなら後続別新規ウェーブで直すべき。自分が原因じゃないテストで main land に
  5 分以上かかるべきではない。全ての並行セッションにも通達しろ」。稼働中 9 セッションへ通達した。
- **親の判断ミスを 2 件、peer の指摘で撤回した。両方とも「直す」より「止める」へ安易に倒れていた。**
  1. `test_sort_swo_oracle.py` へ一律 module-level skip を入れたが、main が着地させた
     原因特定型の skip (`_skip_if_real_cpp_e2e_masstree_is_unavailable`) の方が優れており、
     さらに `test_pytest_collection_config.py::test_explicit_sort_swo_target_still_collects_without_runner_ignore`
     が pin する「明示指定なら収集され続ける」契約を破っていた (焦点走で 1 failed を実測)。撤回。
  2. `test_codex_worker_launch.py` を除外契約へ載せようとしたが、別 session が既に**修理**し
     実走で緑を確認していた (170 passed / 6.55 秒、request 939036.nqsv)。原因は
     144 test 中 22 件が小さい `max_wall` を渡しながら検査対象は別の limit だったことで、
     wall を subprocess timeout (10 秒) より大きくすれば検出力を落とさず直る。
     除外していたら 144 test を失っていた。実装子を停止して撤回。
     親の観測「15 件 → 10 件と赤の件数が揺れる」が、固定欠陥ではなく負荷依存であることの
     証拠として先方の記録へ引かれた。
- 判定器の自動起動を `tools/dev_wave_wait.py` から到達不能にする実装を投入した。
  受理を child-green の 1 本だけにし、赤はそのまま失敗として返す。
  `tools/dev_wave_land.py` と `tools/check_acceptance_reds.py` 本体は非接触。
  裁定側は「D678 の拡張ではなく新規 D で追認する。実装は待たずに進めてよい」と回答した。

## 次の一手差分

### 新規

- {{T:sort-swo-oracle-repair-and-reenable}} **P1・新規**: `orchestrator/tests/test_sort_swo_oracle.py`
  を修理して再有効化する。本 wave で**ファイルごと無条件に skip した**
  (ユーザー裁定 2026-08-23:「ゴミテストはオフにする。壊れたテストは直してから使うものだ。
  修理が小さそうなら自分でやれ。そうじゃないなら別タスクで後でケア」)。
  53 テスト関数のうち 26 件が恒常的に赤で、原因は
  `orchestrator/campaign/sort_swo_oracle.py` の oracle environment 解決が masstree の
  `config.h` を要求するのに、共有 cache は素の clone で `config.h` も `configure` も持たず、
  どの worktree も ccbench を build していないため `<ccbench>/build/_deps/masstree-src` も
  無いこと。**別 wave のビルド副産物の残存に暗黙依存したテスト群**である。
  修理は「テストを甘くする」のではなく、依存の解決経路を明示的に用意する方向で行う。
  再有効化は修理が済んでから。main commit `98badc9b` で known-violation 登録済み。

- {{T:lease-noverdict-retry-unclaimed}} **P2・ユーザー裁定待ち**: 未取得 (`held`) 経路でも
  no-verdict retry を許すか。現行は lease 所有を要求するが、この条件は待ち行列時代の前提に由来する。
  受理集合の変更なので本 wave では実装しなかった。
- {{T:lease-compat-flag-removal}} **P3・ユーザー裁定待ち**: no-op になった `--lease-optional` と
  `--poll-seconds` を将来削除するか。稼働中の並行 wave が rc=2 で死ぬのを避けるため今回は受理を残した。
- {{T:dev-wave-entry-lease-condition-pin}} **P2・新規**: 入口 command 段 6 を、no-op フラグ名でなく
  「lease の取得可否で受入投入を止めない」という条件そのもので pin し直す。
  `worktree-dev-wave-lease-cmd-entry-sync` の着地後に行う。
- {{T:exploration-output-root-login-red}} **P2・新規**: login node でのみ再現的に落ちる
  `test_exploration_external_root_keeps_wave_clean` を調べる。main 単独でも再現し、
  計算ノードでは緑になる環境依存赤である。
- {{T:lease-holder-self-inconsistency}} **P3・新規**: `claim` が `holder` に自己 digest を返しつつ
  `holder_self:false` を返した場合、受入は未取得として進み lease を取り逃す。
  待ち行列廃止後は誰も止めないため実害は lease 残留 (TTL 2400 秒) だけだが、記録として起票する。
- {{T:dev-wave-docs-budget-saturated}} **P2・ユーザー裁定待ち**: dev-wave docs の予算が満杯で、
  実測した作法を 1 行も追記できない。段 8 で「変異走行中に tree へ書かない」(本 wave 実測、
  untracked 1 件で rc=2 中止) を DW-M05 へ足そうとして L1.5 が 9566/9566 bytes と判明し、
  140 bytes の追記で超過した。L2 側も DW-O19 が 998/1000、DW-M07 が 978/1000 で頭が無い。
  自己改善契約は「予算に収まらなければ止めてユーザー裁定へ返す」「予算値を上げる変更は
  独立審査対象」と定めるため実装せず起票する。予算引き上げか L1.5 の縮約審査が要る。
