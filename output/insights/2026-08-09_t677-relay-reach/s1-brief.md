# 段 1 brief — [T-677] 失敗診断の中継到達を機械検査する

wave: dev-wave-t677-relay-reach / branch: worktree-dev-wave-t677-relay-reach / base: main 34957a24

## 依頼

dispatch の末尾 64 KiB 中継では、後続出力が大きい全走で失敗診断の全体が中継から消えうる。
現状の「例外 message 内での末尾への要約再掲」を、診断が確実に人間へ届く形の機械検査に
置き換えるか補強する。

## brief 前の実測 (一次資料。すべて既存 artifact から取得、repo 無改変)

1. **緑の全走**: child stdout 合計 8,808 bytes。成功中継 4 KiB 上限で omitted 4,712 bytes。
   最終行 (`7505 passed, 20 skipped`) は末尾なので到達する。
   出典 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/accept.log:8`
2. **110 failed の全走**: child stdout 523,987 bytes のうち **458,452 bytes (87.5%) が中継から欠落**。
   `=== FAILURES ===` 見出しごと消え、生き残ったのは末尾側の traceback 断片と
   `short test summary info` (111 行) と最終行だけ。
   出典 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/acceptance-2.log:8,1023,1134`
3. 同種の切り詰め実績は他に 213,154 / 190,958 / 180,952 / 100,125 / 95,214 bytes。
   すなわち **T-677 の前提は仮説ではなく再現済み**である。
4. **中継の実装**: `tools/pegasus/dispatch_compute.py:35` `DEFAULT_FAILURE_RELAY_LIMIT_BYTES = 64 * 1024`、
   `:759-798` `_relay_scheduler_logs` が各 stream の末尾だけを `| ` 接頭辞付きで中継する。
   収集側は末尾最大 2 MiB (`:33,664-683`)。
5. **現状の緩和**: `orchestrator/tests/test_codex_worker_launch.py:37` `_DIAGNOSTIC_MAX_BYTES = 16 * 1024`、
   `:335` で `truth_summary` を message 末尾へ再掲。これは **message 局所**の対策であり、
   pytest 全体出力の中での位置は保証しない (T-663 段 6 R2 の D5 と同じ結論)。
6. **既存被覆 (性質で検索)**: `test_pegasus_dispatch_compute.py:266-360` は「末尾 64 KiB だけが
   中継される」「4/64 KiB のリテラル」を pin する。**「必要な診断が切り詰めを越えて残る」ことを
   主張するテストは 1 本も無い**。よって純増検出力がある。
7. **DW-O13 (gate 入力の実在)**: pytest 9.1.1 で `TestReport.longreprtext` と `nodeid` は実在。
   plugin の `pytest_terminal_summary` は wrapper の yield 点で走り、`=== FAILURES ===` の後・
   `short test summary info` の前に出力される。
8. **DW-G03 (族一般化に独立 2 例)**: 中継切り詰めが必要情報を消した独立事例は 2 件ある —
   本件 (launcher 診断) と F155 (a) の「中継出力が切り詰められて期待 node 9 件が実在しないと
   判定された」(`docs/failures.md:3762`)。族としての機構化は許される。
9. **child stdout の構造**: 実測 1 の緑ログでは pytest の最終行が child stdout の末尾であり、
   pytest 後に job script が足す出力は無い。

## scope

- **in**: pytest セッション終端に、失敗診断の bounded なダイジェストを出す機構と、その
  ダイジェストが 64 KiB 中継予算の内側に収まることを実出力で測る機械検査。
- **out**: `tools/pegasus/dispatch_compute.py` の中継仕様そのものの変更。production の
  launcher (`tools/codex_worker_launch.py`) の変更。F57 / T-190 の閉鎖。診断内容の拡充 (T-663 D4)。

## provisional 裁定 (親の provisional 裁定であり攻撃対象)

- **(P1) 方式は「補強」**。producer 側 (pytest 終端の bounded ダイジェスト) を新設し、
  dispatcher は無編集とする。理由: dispatcher は sanctioned control plane で改変コストが高い。
  producer 側なら local 走行・変異 harness・他 transport にも同時に効く。
- **(P2) 置き場は `orchestrator/tests/conftest.py` の pytest hook**。tracked な test file 150 件は
  すべて `orchestrator/tests/` 配下 (実測) なので全走で必ず読まれる。`run_tests.py` の
  pytest argv には **flag を足さない** (受入 shape 判定 `_is_full_suite` を動かさないため)。
- **(P3) 機械検査は「ダイジェスト以降に続く child stdout の bytes が失敗中継予算未満」**を
  subprocess pytest の実出力で測る。予算値は `dispatch_compute.DEFAULT_FAILURE_RELAY_LIMIT_BYTES`
  から取り、中継枠を縮めたら赤になるよう結合する。
- **(P4) ダイジェスト予算は総量上限つき**とし、1 failure あたりの抜粋にも上限を置き、
  省略 bytes と sha256 を明記する。具体値は段 2 で決める。
- **(P5) 緑走行ではダイジェストを出さない**。成功中継は 4 KiB しかなく (実測 1)、
  緑時に出力を足すと最終行を押し出す危険がある。

## 不変条件 (破ったら実装ごと差し戻す)

- 規律 2: ダイジェストは**表示専用**。テストの pass/fail、exit code、収集結果を一切変えない。
- 規律 3: 単なる再掲でなく、失敗ごとに node id と落ちた診断本体を構造化して残す。
- ダイジェスト生成中の例外がセッションの exit code を変えてはならない (fail-open で無出力、
  ただしその事実は 1 行出す)。
- 既存の relay テスト (4/64 KiB リテラル pin) を弱めない・削除しない。
- `run_tests.py` の argv・環境変数・shape 判定を変えない。
- production (`tools/`, `orchestrator/campaign/`) は無編集。今回は test harness 面のみ。

## 成果物への影響 (DW-G05)

実装しない場合、多数失敗の受入全走では失敗診断が中継から消える (実測で 458,452 bytes 欠落)。
その結果、受入赤の原因を実装差分・環境負荷・フレークのどれにも帰属できず、worklog へ
「node 名のみ・原因未確定」としか書けない。これは受入 gate の赤を実装差分へ誤帰属する
経路であり、certified 選択・材料レポートの受理判定の手前で判断を誤らせる。

## 成果物の形

- `orchestrator/tests/conftest.py` への hook 追加 (または同等の test 側 module)。
- 新規テスト: (a) ダイジェストが失敗時に出る、(b) 緑時に出ない、(c) 予算超過時の省略会計、
  (d) **E2E**: 大量失敗を含む subprocess pytest の実出力で、ダイジェスト以降の bytes が
  失敗中継予算未満、(e) 予算リテラルの結合 pin、(f) ダイジェスト生成例外が rc を変えない。
- 変異事前登録 (段 4 で確定)。

## 分割方針

編集面が小さく相互依存するため、段 5 の実装子は 1 本。段 3 と段 6 は 2 レンズ並列。
