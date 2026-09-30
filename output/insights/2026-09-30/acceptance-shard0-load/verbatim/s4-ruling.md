# 段 4 裁定 — acceptance-shard0-load (md_6)

固定時刻: 2026-09-30 (JST、対照・変異の結果を見る前)。入力: brief.md、codex/plan-out.md、codex/consult-out.md。

## 所見の裁定

| 出所 | 所見 | 裁定 | 処置 |
|---|---|---|---|
| plan 反証 1・consult 1 (高) | P1 の比較器は、racy clean・並行書込み・mode 変更の組合せで現行と受理集合が異なる (広げる入力・狭める入力の両方を構成できる) | real | **P1 は本 wave で実装しない。** D1709 (形式的にでも受理集合を広げる変更は wall 効果がばらつきを超える場合だけ) に照らし、同値を主張できない。反例と、受理集合を変えない別案 (9 関数を 2 本ずつの xdist group にして process 内 cache を共有する D771 型: 鎖 約 120〜160 秒、節約は初回 5 回分程度) を数値つきで一次資料へ残す。起票・裁定パッケージにはしない (研究前進・実測欠陥ではなく最適化候補) |
| plan 反証 2・consult 2 | mode 変更・混在行・object 消失 | real | P1 不採用で閉じる。一次資料の反例列挙へ含める |
| plan 反証 3・consult 5 (中) | 項 6 の hit 時指紋は過剰で、完全性も示せない | real | **項 6 は最小形に替える:** 共有 base を 1 回作り、2 つの consumer が各自の複製へ書込み (tracked 書換え・untracked 追加・commit) をした後も、共有 base 自体の tree (全 file の bytes・mode・symlink target と HEAD) が不変であることを固定する test を新設する。hit 時の照合は足さない。一次資料に「共有 base 自体の改変検出機構は無く、consumer が複製にだけ書くことを test で示す」と範囲を書く |
| consult 3 (高) | P2 は consumer の無い shard-1/2 でも構築し、失敗・hang の新経路を作る | real | P2 は維持し、(a) 構築の失敗は既存の早期 job と同じく session 終了時に例外として伝播 (fail-closed。consumer 側は `complete.json` 不在なら従来どおり自分で構築する)、(b) hang は finish の join を上限 900 秒で打ち切り例外にする (上限の根拠: 構築 1 回の実測 98〜154 秒 (probe2・probe4、単独)、受入の T-080 1 本の最大 155〜159 秒 (baseline) の約 5.7 倍。finish は全 test 後なので通常は完了済み)、(c) s1/s2 の代償は対照の L3 で検出する |
| consult 4 (中) | 終了順 | real | finish は join → error 回収 → controller の `bases.close()` の順で、可視 output の cleanup より前。失敗時にも close する。test で固定 |
| consult 6 (中) | P1 と P2 の同時投入は帰属不能 | real | P1 不採用で本 wave の変更は P2 (+ 項 6 の test) だけになり、対照は P2 単独の効果を測る |
| consult 7 (中) | 総仕事量から最忙 worker の短縮は導けない | real | W・span・占有の改善は対照実測だけで述べる。群 A の所要合計は診断量 |
| consult 8 (中) | 内訳 98 秒の出所が射影外、単独走からの外挿 | real | probe4 の集計出力を `probe4/lines.out` に保存して一次資料から参照する。1,000〜1,800 秒・約 500 秒は「外挿」と明記 |
| consult 9 (低) | P3 の成果物影響 | real | DW-G05: 「P3 未実装、nodeid・受理集合・成果物 bytes 不変、残る費用 約 8 秒 × 6 本は単独走の値で受入では未測定」と書く |
| plan P2.5 と既存 harness | `_early_memo_cache_probe` (test_real_repo_serialization) と `test_t080_visible_output_snapshot_starts_once_and_preserves_copy` (oracle_driver) は configure_node を本物で呼ぶ | real (親の実読) | 新しい起動関数を差し替える `mock.patch.object(<conftest>, "_start_t080_shared_base_prewarm")` を、この 2 箇所の setup に 1 行ずつ足すことを許可する。assert・期待値・nodeid は変えない。`test_acceptance_schedule_order` の `workerinput` 完全一致 test は shard spec が無く非選択なので不変 (prewarm は `workerinput` に key を足さない) |

反証されず維持: `_early_memo_selected` を流用して非受入走を外す方針、既存 `_T080SharedBases.get()` と key の再利用、P3 の見送り。

## plan v2 (実装子 1 単位 + 計測 runner 1 単位)

### 単位 U1 (Codex author、所有: orchestrator/tests/test_s8b_oracle_driver.py、orchestrator/tests/conftest.py、orchestrator/tests/test_real_repo_serialization.py の `_early_memo_cache_probe` への 1 行だけ)
1. oracle_driver: `_t080_join_shared_bases` の session path 計算を、明示 `run_id` を受ける helper に抽出 (worker の既存経路は不変)。`_t080_stub_free_e2e_repo` の 5 要素 key を既定引数から作る helper に集約し、default と active-v2 (第 5 要素だけ True) を controller もこの helper から得る (tuple literal の複製禁止)。`_t080_copy_visible_output` に明示 run_id を渡す経路を足す (process 全体の環境変数を書き換えない)。
2. conftest: `_start_t080_shared_base_prewarm(node)` を `pytest_configure_node` の `_early_memo_selected` 分岐で `_start_t080_visible_output_snapshot(node)` の直後に置く。1 session 1 回。同期部分で module を import・ROOT を照合し、共通 session path で `_T080SharedBases` を生成 (= `workers.lock` の LOCK_SH 参加) してから thread を起こす。thread は default・active-v2 の 2 本を並列に起こし、各々が可視 output の `result.json` の成功を待ってから (失敗・180 秒超過は error、実 repo 複製へ黙って fallback しない) `bases.get(key)` を呼ぶ。`workerinput` に key を足さない。
3. conftest: `_finish_t080_shared_base_prewarm(config)` を新設し、`_finish_memo_sessions` の finish 列で可視 output の finish より前に置く。join (合計上限 900 秒、超過は例外) → error 回収 → `bases.close()` (finally)。first error の既存規律に従う。
4. 既存 harness 2 箇所に上記の差し替え 1 行 (段 4 で許可した setup 変更だけ)。
5. 新設 test (名前は変異の期待 node なので固定。小 builder を monkeypatch し実 builder は呼ばない):
   - T1 `test_t080_shared_base_prewarm_publishes_both_keys_before_consumers` — prewarm 後、consumer の `get()` が hit で builder 回数が増えない。
   - T2 `test_t080_shared_base_prewarm_waits_for_visible_output` — `result.json` 公開前に builder が呼ばれない。`ok: false` なら builder を呼ばず finish が例外。
   - T3 `test_t080_shared_base_prewarm_controller_participation_keeps_tree` — worker 側の参加者が先に close しても木は残り、controller の close が最後なら木を撤去する。
   - T4 `test_t080_shared_base_prewarm_error_propagates_and_closes` — builder が例外 → finish が例外を伝播し、controller の lock を解放済み。
   - T5 `test_t080_shared_base_prewarm_not_started_when_unselected` — 非選択 (spec 無し・絞り込み・collectonly・worker) で session dir を作らず builder を呼ばない。
   - T6 `test_t080_shared_base_prewarm_join_timeout_raises` — builder が event で止まるとき、上限を小さく差し替えた finish が例外 (その後 event を解放して thread を終わらせる)。
   - T7 `test_t080_shared_base_unchanged_after_consumers_mutate_copies` — 項 6。実 git repo を持つ小 builder で base を作り、2 consumer が複製へ tracked 書換え・untracked 追加・commit をした後、共有 base の全 file bytes・mode・symlink target・HEAD が構築直後と一致。
6. 禁止: 既存 test の assert・期待値・nodeid・関数名・parametrize・xdist group・skip の変更 (上の 1 行 × 2 を除く)、`tools/`・所要台帳・hooks の変更、`_build_t080_stub_free_e2e_repo` の中身の変更、key digest 規則の変更。

### 単位 U2 (Codex author、計測 runner。repo の実装面ではなく、子の worktree 内 `meas/` に書かせ親が job dir へ退避)
md_2 の `meas/run-pair.sh` (sha256 737503d8…) と `meas/aggregate.py` (dc74b89c…) を元に、A (変更前 commit) / B (変更後 commit) の 2 木を同時起動する `run-pair-ab.sh` と、shard ごとの W・pre・T (= W − pre)・worker の span 最大・占有最大・群 A 所要合計・群 B 所要合計・T-080 consumer 別所要を出す `aggregate-ab.py` を作る。両腕とも `PYTHONDONTWRITEBYTECODE` unset、`PYTEST_ADDOPTS` unset、起動差 ≤ 5 秒、expected commit を腕ごとに照合、pyc 数を起動前後で記録。

## 変異の事前登録 (DW-M01、実装後に単一理由性を確認し、成り立たなければ登録を外して再照準)

| id | 位置 | 変異 | KILLED 期待 node |
|---|---|---|---|
| M1 | conftest `pytest_configure_node` の prewarm 起動行 | 起動行を `pass` に | T1 |
| M2 | prewarm thread の `result.json` 成功待ち | 待ちを外し即 `get()` | T2 |
| M3 | `_start_t080_shared_base_prewarm` の同期参加 | `_T080SharedBases` 生成を thread 内 (build 後) へ移す、または controller の参加を外す | T3 |
| M4 | `_finish_t080_shared_base_prewarm` の error 伝播 | error を捨てる | T4 |
| M5 | `_early_memo_selected` 分岐外への移動 | 分岐の外 (無条件) で起動 | T5 |
| M6 | `_t080_stub_free_e2e_repo` の複製 | `copytree` せず base_root をそのまま consumer へ返す | T7 (と既存 copy 独立性 test があれば併記) |

T6 (hang 上限) は hang 変異になるので登録しない (DW-M06)。

## 対照の事前登録 (結果を見る前に固定)

- 腕: A = 変更前 commit (`4f412c67b`、本 wave の base)、B = A + 本 wave の実装 commit (記録 commit を含まない tip)。各対で fresh detached worktree 2 本 (submodule 再帰初期化、tests pyc 0 を確認)。
- 対 1: 専用の A1 / B1 を U2 の runner で同時起動 (起動差 ≤ 5 秒)。
- 対 2: 専用の A2 と、B 側は本 wave の正式受入 (`tools/dev_wave_wait.py acceptance`) を同時期に起動する。A2 の木は正式受入の post-claim merge が取り込む local main と同じ commit で作る (merge 後に照合し、異なれば対 2 は無効)。正式受入の木は pyc が温でありうるので、対 2 の主判定量は T0 (= W0 − pre0) とする。
- 判定量: 主 = shard-0 の T0 (test 段の wall)。副 = W0、shard-0 の span 最大・占有最大、群 A 所要合計、max(W1, W2)、pre の峰。
- land 条件 (実装を main へ入れる条件): L1 = 2 対とも ΔT0 = T0(A) − T0(B) > 0。L2 = 2 対の ΔT0 / T0(A) の平均 ≥ 5 %。L3 = 2 対とも max(W1, W2)(B) − max(W1, W2)(A) > +20 秒 ではない。L1 ∧ L2 ∧ L3 なら land。満たさなければ実装を land せず記録だけ land (D2242 と同型)。赤・infra 失敗の走を含む対は無効。有効対が 2 未満なら「判定不能」とし実装は land しない (予算上、取り直さない)。
- 計算予算: 生死確認 4 本 実測 1,492 秒 (0.41 node 時間) + 対照 専用 3 走 (md_2 の実測 1 走 約 1,014 秒 × 3 ≈ 0.85) + 正式受入 1 走 (0.28) + 焦点走・変異 (≤ 0.3 の見込み) ≈ 1.84 node 時間 < 2。超えそうになったら投入せず停止しユーザーに確認する。
