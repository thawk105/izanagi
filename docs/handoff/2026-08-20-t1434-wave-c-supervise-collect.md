# [T-1434] (4) codex_reasoning_ab.py Wave C (supervise_pair/collect_run層)
- 目的: model軸拡張のWave C (supervise_pair/_supervise_one/collect_run/_verify_launch_receipt) を実装する
- 状態: 作業中
- 最終更新: 2026-08-20
- 基準コミット: 165a6d2a348bf8da097d55fdcb8e9364e164c30f (worktree: t1434-wave-c, 作業ツリー clean、
  実装commit 2ffba5b1 + local main取り込みmerge c7a6cc8f 済み)

## 段1 brief

**確定済みユーザー裁定・設計判断**
- T-1146ルーリング (2026-08-16, `dev-wave-jobs/rulings-inbox/2026-08-16-t1146-model-routing-luna-ruling.md`):
  択(a) — T-189 (model-routing比較実験) を正式起票してから判断。証拠なしmodel-only swapは禁止。
- D603 (2026-08-20): 段2プランのWave A→B→C→D分割のうちA+Bのみ実装済み・land済み
  (branch worktree-lively-juggling-ripple、292 passed・変異9/9 KILLED)。C/Dは後続wave送り。
  本waveはCのみ対象、Dは引き続き対象外。
- D604 (2026-08-20): task一般化フィールド名は`benchmark_task_id`(Wave Aで導入済み、本waveで新規
  フィールド追加なし、参考情報)。
- 正本: `docs/phase3-t189-model-routing-preregistration.md` §5.2 (変更面テーブル、実装はwave scope外
  と明記されているが個々の行の要求内容自体は生きている)、§5.3 (装置以外の仕組み、本wave対象外)。

**scope (Wave C = supervise_pair/collect_run層)**
Wave A (manifest/schema/provenance) と Wave B (argv/launch/identity) は着地済みで、Wave B は
`_codex_exec_argv`/`_normalized_exec_argv`/`_launch_identity_value` に `requested_model` を明示引数
として受け取れる形をすでに用意し、コード中に「the supervisor wave が slot.requested_model を直接渡す
until」という趣旨のコメントを残している (実測、下記アンカー表)。Wave C はこの接続点を実際に配線し、
`_supervise_one`/`supervise_pair`/`_verify_launch_receipt`/`collect_run` を model-aware にする。

**(P1) 依存関係の実測結果 — command引数が指示した「Wave Dの未編集関数への依存」確認**
`grep`で`_codex_exec_argv`/`_normalized_exec_argv`/`_verify_launch_receipt`の全呼出し元を洗った。
3関数とも呼出し元は`_supervise_one`/`collect_run`自身に完全に閉じており (3466-3467, 3977, 4279)、
Wave D所有関数からは一切呼ばれない。

**訂正 (段3レンズB・段6レンズBが独立に指摘、当初の下線部の言い切りは不正確だった):**
`supervise_pair`→`_validate_schedule` (3693行) という既存のC→D呼出し自体は実在し、これは変更しない。
Wave Cの`requested_model`配線がここに**依存する**——`_validate_schedule`が受理した schedule slot の
行 dict を `{**row, ...}` でそのまま pass-through し (5104/5140行、現在の行番号は5091/5140付近)、
未知フィールドを削らないという既存の実装特性のおかげで、`requested_model` を持つ slot が
`block_slots`まで無傷で届く。**この pass-through 特性が将来 Wave D の実装で変わった場合
(例: `_validate_schedule`を`normalize_schedule`系へ置き換えて構造化 dict を返すよう変える等)、
Wave Cが依存するこの経路は無警告で壊れうる。** 依存が「無い」のではなく「既存動作に対して
安全に乗っているが、D側の将来変更で壊れうる」が正確な記述である。D本体を今回変更しない判断
自体は変わらない (段2/段3/段6で独立に3回確認済み)。

唯一の cross-boundary 接触は逆方向: `collect_run`の`expected_model: str = MODEL`という既定値が、
Wave D所有の`_replay_manifest`内の唯一の非CLI呼出し (6118-6129) でこの既定値に暗黙依存している。
**採用: `expected_model`→`expected_requested_model`にrenameし既定値を廃止する (原設計テーブルの
「served modelと呼ばない」「既定値を廃止」要求どおり)。`_replay_manifest`側は
`expected_requested_model=slot.get("requested_model", MODEL)`という1行の機械的な呼出し規約更新のみ
行う (adjudicationロジック自体は無改修、`DW-C01`「呼出し規約を変える取込は全呼出しを数える」の
範囲内と判断)。CLI側 (`main()`の`collect-run`, 6821-6833) は既にexplicitにexpected_modelを渡して
おり無改修。段3で「本当にこの1行で閉じるか、他にWave D側の意味論変更が要らないか」を独立に再検証する
攻撃対象とする。**

**(P2) supervise_pair自身のmodel多様性検査を新設するか**
原設計テーブルは「supervise_pairが同一taskのsol/luna blockを検証し、model順序をscheduleに従って
交互化する」ことを要求する。既存の`case`一様性検査 (3700行) と同型で、`_validate_schedule`を
変更せず`supervise_pair`内に追加できる (block_slotsの`requested_model`フィールドを読むだけ、
`_validate_schedule`は行をpass-through済みなので追加フィールドは既に透過する)。
**攻撃対象: 現状どのschedule fixtureも`requested_model`を持たない (Wave Dが manifest駆動schedule
生成を配線するまで実在するartifact pathが無い)。DW-G04「発火条件を満たす既存artifact pathが書ける
場合だけ実装する」に照らし、実在するpathを段2が示せなければこの検査は本waveで実装せず、
`_supervise_one`/`collect_run`側の配線だけに留める (投機的な検査を先回りして作らない)。**

**不変条件**
- 既存reasoning-axis (POS/NEG×max/high) の受入テスト・変異matrixが非破壊のまま緑を維持する。
- `_validate_schedule`/`_load_adjudication`/`_aggregate_verified`/`_replay_manifest`/
  `_validate_supervisor_ledger`/`make_packets`本体のロジック(cardinality・schema・adjudication判定)
  は変更しない。唯一の例外は`_replay_manifest`内の`collect_run`呼出し1行(呼出し規約更新のみ、上記(P1))。
- `requested_model`未指定のslot (既存schedule.json) は従来どおり`MODEL` (sol) にfall backし、
  reasoning-axis専用の既存run/受入を壊さない。

**変更面アンカー表 (file:line、現状 → 変更方針)**
- `tools/codex_reasoning_ab.py:3466-3467` (`_supervise_one`内): `_codex_exec_argv(actual_cli, arm,
  snapshot, output)`(legacy 4引数shim)→`_codex_exec_argv(actual_cli, requested_model, arm, snapshot,
  output)`(明示形)。`_normalized_exec_argv(codex_argv, arm)`(legacy 2引数shim)→
  `_normalized_exec_argv(codex_argv, requested_model, arm)`(明示形)。`requested_model`は
  `str(slot.get("requested_model", MODEL))`から得る。
- `tools/codex_reasoning_ab.py:3392-3407` (`_supervise_one`シグネチャ): 変更不要
  (`slot: Mapping[str, Any]`は既にrequested_modelを含みうる。新規引数は追加しない)。
- `tools/codex_reasoning_ab.py:3514-3577` (`launch`辞書構築): `requested_model`キーを明示的にセット
  してから`_launch_identity_value(launch)`を呼ぶ (現状は`_launch_identity_value`側3149-3157行が
  「無ければargvから導出してreceiptへ書き込む」フォールバックを持つが、明示セットで導出依存を無くし
  cross-check (3158-3161行) を実効させる)。
- `tools/codex_reasoning_ab.py:3951-3953` (`_verify_launch_receipt`シグネチャ): `arm: str`の並びに
  `requested_model: str`を追加。
- `tools/codex_reasoning_ab.py:3977-3979` (`_verify_launch_receipt`内): `_normalized_exec_argv(
  launch.get("argv", []), arm)`(legacy 2引数shim)→`_normalized_exec_argv(launch.get("argv", []),
  requested_model, arm)`(明示形)。
- `tools/codex_reasoning_ab.py:4256-4268` (`collect_run`シグネチャ): `expected_model: str = MODEL`→
  `expected_requested_model: str` (既定値廃止、上記(P1))。
- `tools/codex_reasoning_ab.py:4279` (`collect_run`内): `_verify_launch_receipt(launch_receipt, launch,
  requested_effort)`→`_verify_launch_receipt(launch_receipt, launch, requested_effort,
  expected_requested_model)`。
- `tools/codex_reasoning_ab.py:4410` (`collect_run`内): `contexts[0].get("model") != expected_model`→
  `expected_requested_model`参照に更新。呼称も「model mismatch」のままでよいか、「served model」的な
  誤解を招く文言が無いか段2で確認。
- `tools/codex_reasoning_ab.py:6118-6129` (`_replay_manifest`、Wave D所有・機械的1行更新のみ):
  `collect_run(...)`呼出しに`expected_requested_model=slot.get("requested_model", MODEL)`を追加
  (上記(P1)の唯一の許可された越境)。
- `tools/codex_reasoning_ab.py:6730` (`main()`のargparse): `collect.add_argument("--expected-model",
  default=MODEL)`→dest名を`expected_requested_model`に揃えるか、argparseの`dest=`で吸収するか段2で
  決める (CLI利用者向けフラグ名`--expected-model`自体は human ergonomics として維持でよい)。
- `tools/codex_reasoning_ab.py:6821-6833` (`main()`の`collect-run`ディスパッチ): kwarg名を
  `expected_requested_model=args.expected_requested_model` (またはdest経由) に更新。
- `tools/codex_reasoning_ab.py:6834-6848` (`main()`の`supervise-pair`ディスパッチ): 変更不要
  (モデル情報はCLI引数でなくschedule.json経由、原設計どおり)。

**成果物の形・並列分割方針**
実装子1本 (role=author、単一実装単位)。対象は上記アンカー表のproduction箇所と
`orchestrator/tests/test_codex_reasoning_ab.py`の対応テスト
(既存: 629, 658, 847, 874, 5941, 5971, 6035行のsupervise_pair/collect_run呼出しテストが引数変更の
影響を受けうる。766, 810行のmodel関連テストも確認対象)。編集面は1つの呼出し連鎖に閉じているため
分割不要 (Wave Bのreasoning-pin事例のような多unit分割は不要と判断、段2で規模を再確認)。

**DW-G05 (成果物影響、1行)**
実装しない場合、`_supervise_one`/`collect_run`はrequested_modelを実質無視し続け、T-189のmodel-routing
比較実験がpaired sol/luna runの起動・受理を装置レベルで区別できないまま残り、D423/T-1146ルーリングが
要求する比較実験の実施基盤が未完成のままになる。

**DW-G01〜G04**: 本waveはPhase 3 campaign軸の新設ではなくdev-wave tooling (T-181装置) のrefactorの
ため、G01 (生死実験先行)・G02 (初回cycle前blocker限定)・G03 (族一般化に独立2例) は不適用。G04
(条件付き機能の発火gate) は上記(P2)で適用済み。

## 進捗 (段1〜7完了、残るは段9 land)
1. 段1〜4完了: brief→段2 codex plan→段3敵対相談2レンズ→段4裁定 (依存関係はWave Dの未編集意味論に
   依存しないと4回独立確認、唯一の許可された越境は`_replay_manifest`の1行)。
2. 段5完了: 実装子1本 (production 37行+テスト362行)。launcher `## 総括`欠落でnot_acceptedだったが
   親がdiff監査で完全性を確認。
3. 段6完了: 敵対レビュー2レンズ→real所見2件→fix 2巡 (rename+RC経路分離、被覆漏れ1テスト追加)→
   変異matrix8件事前登録→8/8 KILLED, SURVIVED 0, MISMATCH 0→受入全走=verdict=child-green
   (tested_main=595662be, tested_tip=165a6d2a)。実装commit 2ffba5b1、local main取り込みmerge
   c7a6cc8f。受入lease保持中 (holder_self=true、land完了まで解放しない)。
4. 段7完了: worklog fragment (`docs/spool/worklog/2026-08-20-t1434-wave-c-2.md`)、
   decisions fragment (`docs/spool/decisions/2026-08-20-t1434-wave-c-1.md`、{{D:t1434-4-wave-c-boundary}})。
   `check_docs.py`違反なし、`spool_fold.py --dry-run`= status=planned。

## 未完の作業と次の一手 (段9 land)
1. 本handoff・spool fragment 2件をdocsのみcommit (AI-Agent: role=author; scope=docs)。
2. `tools/dev_wave_land.py`で local main へ ff-only land (audited-commitは
   tested-main(595662be)..tested-wave-tip(165a6d2a)の範囲、main-worktreeは
   `/work/1/SFC/tanab/izanagi` (canonical path、worktree配下を渡さない))。
3. land成功後、受入leaseを `python3 tools/wave_land_window.py release --lease-dir
   /work/1/SFC/tanab/dev-wave-jobs/land-lease --wave t1434-wave-c` でrelease。
4. `tools/collect_wave_usage.py`を実行 (loginで必ずblockされる既知事象、実施記録のみ残す)。

## 落とし穴・気づき
- `EXPECTED_SCHEDULE`は既に`LEGACY_EXPECTED_SCHEDULE`から構築されるcompatibility aliasに変わっている
  (275-278行、Wave Aの成果)。`_validate_schedule`(5069-5140)自体はこの新しい間接参照を意識しておらず、
  依然としてハードコードされた10 slot・`{"max","high"}`arm集合の検査をしている。Wave Cはこれに触れない。
- `normalize_schedule`/`normalize_legacy_schedule`/`expected_schedule_from_manifest`
  (2354-2521行、Wave A成果) は「Wave C/D must wire that production path to this validator」という
  docstringを持つが、supervise_pair側から見て**この配線はWave D所有の`_validate_schedule`の書き換えを
  伴う**ため、本briefでは対象外と判断した (P2の判断根拠と同型)。段2がこの判断に異議があれば
  独立に指摘すること。

## dev-wave 改善候補 (段8で裁定)
候補2件を発見。dev-wave docs (core/operations/workers/mutation.md) の3層予算は既知で満杯
(`dev-wave-docs-compression-breaks-exact-pins`と一致) のため、Wave A+Bの前例に倣い即時の
reference節統合は試みず、候補記録のみに留めユーザー裁定へ返す。

1. **段5/段6 (author/fix) 完了報告の`## 総括`必須はDW-O01 (F43) に一般則としてあるが、
   DW-S05-C (段5実装子契約) 自身には明示的に列挙されていない。** 本waveで実装子の1回目試行が
   これを書き忘れ`not_accepted`になった (実害は親のdiff監査で吸収、やり直し不要)。
   DW-S05-Cの列挙項目に「完了報告はfenced code block外に`## 総括`見出しを含めること (F43)」を
   1行追加する候補 (発火段に対応する既存leaf節への統合、新設ではない)。
2. **`tools/mutation_harness.py`と`tools/dev_wave_wait.py acceptance`はいずれも起動直前に
   working treeのuntracked fileをtracked/index dirtと同様に検出し停止する。** DW-M05は
   「元ソースの固定HEAD束縛」としてこれを暗示するが、「受入も同型の pre-run clean-tree 検査を
   持つ」「段6の受入再走が進行中の間は段7 spool fragment等の新規untrackedを作らない」という
   順序上の含意は明記されていない。本waveで2回 (変異harness起動時1回、受入prerun-clean時1回)
   untracked docsが原因で即座に止まった (実害は都度repo外への退避で解消、遅延のみ)。
   DW-M05または段6のU節に「変異・受入とも、段7記録物の起草は該当gateの完了確定後に行う」
   という順序を1行追加する候補。
