# [T-076] bounded dev-wave supervisor 機械層 — 逐語凍結と変異台帳

status: frozen
wave: /dev-wave [T-076] (2026-07-21)
branch: worktree-dev-wave-ruling-ac (基準 3a09c2c)
task-run: 20260721-t076-supervisor-mech-layer-f79fdfd9

本書は dev-wave の段構成に沿った逐語凍結である。可変状態の正本は worklog 末尾。設計正本は
`output/insights/2026-07-21_dev-waves-supervisor-design.md`、運用契約は
`output/dev-wave-supervisor/README.md`、設計判断は D74。

## 1. scope と成果物

段階導入 (設計 §13) のステップ 2 = fake child の機械層。real `claude -p`・課金・network は
不使用。新規追加のみ:

- `tools/dev_waves.py` + `tools/dev_waves/` 10 module (schema/schema_v1.json/protocol/
  receipt/redaction/ledger/worker/git_state/checker/daemon/cli/__init__)
- `orchestrator/tests/test_dev_waves_*.py` 11 本 (203 node、全て二重 runner 対応)
- `output/dev-wave-supervisor/README.md` (運用契約、親起草)
- `.gitignore` 2 行 (`output/dev-wave-supervisor/runtime/`、親)

既存 production・凍結成果物は 1 byte も変更していない
(`git diff HEAD --stat` は追加のみ、`FROZEN_MANIFEST` 対象は無変更)。

## 2. 段構成の逐語

- **段 1 (実測)**: claude CLI 2.1.214 の設計 argv 8 flag 実在、`CLAUDECODE=1` 実測、
  Python 3.10.12、greenfield を確認。D69 突き合わせ済み
- **段 2 (プラン)**: codex gpt-5.6-sol/max/read-only。P1〜P6 に異議なし
- **段 3 (敵対相談 2 本)**: 両者 NO-GO。P2/P4/P5/P6 否認、brief の「8 flag」表現の誤り
  (session persistence 裁定との衝突)、状態機械の到達不能辺、orphan child、WAL 単一 writer
  欠如、変異事前登録の F28 再発を検出 → プラン v2 差分 21 項目で解消
- **段 4 (裁定)**: P2 は「[T-076] 裁定が着手を明示承認 + 機械層は費用を消費しない」を根拠に
  進行、具体値は real-run 裁定パッケージへ。P4/P5/P6 は相談どおり修正 (`.gitignore`・README
  を親所有、共有中核先行の 3 段分割、実測は capability 存在のみと明記)
- **段 5 (実装)**: Unit A (共有中核) → B1 (ledger) ∥ B2 (worker/git_state/checker) → C
  (daemon/cli/fake/integration)。ファイル所有は完全素集合。親が patch 展開で連結
- **段 6 (レビュー)**: 敵対レビュー 2 本 (R1 正しさ / R2 整合) とも NO-GO 15 所見 →
  fix ラウンド 1 (19 項目) → 焦点再レビュー NO-GO (N1〜N12) → fix ラウンド 2 (N1/N4〜N12 +
  client cap 必須化)。R1-1 (任意 executable 経路廃止) と N2 (runtime 外書込み) は v1 非目標
  として README へ

## 3. 親が直接書いたハンク (レビュー対象として名指しした差分)

1. `test_dev_waves_worker.py` の crash 注入テスト末尾 — SIGSTOP 中 child が worker 死亡時に
   孤児 PG への SIGHUP+SIGCONT で kernel 回収され得るため両終状態を許容 (payload 非実行の
   不変条件は維持)。fix-2 で PDEATHSIG + SIGHUP 復元により再強化
2. `.gitignore` runtime 2 行 (両レビューとも「問題なし」)
3. `test_dev_waves_integration.py` の flaky 決定化 — `_start_real_daemon` の空 run_id
   再試行 (open→write 間 race) + `_wait_state` 30s + launcher timeout 30/90s。再レビューで
   「検出力低下なし」判定
4. `output/dev-wave-supervisor/README.md` 全面改稿 — 実 parser から CLI 転記、fix-2 の
   非目標を反映

## 4. real 開放前のユーザー裁定パッケージ (段階 3〜7 の前提)

1. per-wave/total の timeout・cost 具体値と client 宣言値への絶対上限値
2. real child の settings/hook 必須政策 — **新事実**: 現行 `.claude/settings.json` に
   push deny は無く、`git push` を機械遮断する配線は確認できない (相談 R1 所見 4)
3. [T-069]「実装前に明示指定」の読みの確認 (機械層は値を持てない構造で進めた)
4. v1 非目標 (同一 UID 防御なし / nested-launch は事故防止のみ / 意味的 commit 監査なし /
   NFS crash durability 非主張 / child 実支出・runtime 外書込み拘束外) の受諾確認

## 5. 変異台帳 (事前登録 → 実測)

F28 対策として各変異に単一理由 fixture を対応させ、実装後にコードを実読して置換対象が
期待個数であることを確認してから実測した。ハーネス = wave 作業領域の `mutation_harness.py`
(flock 単一走行 guard / JSONL 逐次 / ANSI 除去後の node 名記録 / 内容比較による復元検査)。

**kill 8 件 (M1〜M8) + diagnostic pin 1 件 (M10)。** kill の判定基準は「受理集合または
fail-closed 挙動が期待方向へ変わった」こと。node 名は ANSI 除去後に記録した。

| ID | 変異 (置換) | 帰属 (赤 node、代表) | 受理集合/挙動の変化 | 判定 |
|---|---|---|---|---|
| M1 | receipt: error envelope の受理ゲート `if subtype!="success" or is_error` を無効化 | `test_dev_waves_receipt.py::test_envelope_accepts_only_success_false_empty_denials_matrix` ほか 1 (計 2) | error envelope が拒否→受理 | **kill** |
| M2 | daemon: 検証不合格 `if not report.ok` を無効化 | integration 36 node (failure injection・gate 群全体) | 検査不合格の wave が停止→受理 (中枢ゲート) | **kill** |
| M3 | git_state: `_is_ancestor` 検査を無効化 | `..._stops_next_wave[diverged_main-main-not-ff]` (計 1) | diverged main が拒否→通過 | **kill** |
| M4 | ledger: WAL の `sync_fn` を no-op 化 | `test_bootstrap_stages_until_first_wal_fsync...` ほか 1 (計 2) | fsync 失敗が poison→黙殺 | **kill** |
| M5 | schema: 状態遷移 guard を無効化 | ledger 3 + schema 1 (計 4) | 禁止辺が拒否→許容 | **kill** |
| M6 | schema: strict JSON の重複 key 拒否を pass 化 | cli/receipt/schema の strict テスト 3 node | 重複 key が拒否→後勝ち受理 | **kill** |
| M7 | worker: `killpg`→`kill` (leader のみ、2 行) | `test_leader_exit_with_live_group_is_rejected_and_group_terminated` (計 1) | 残存 PG が終了→残留 | **kill** |
| M8 | daemon: `serve_forever` の `CLAUDECODE` 拒否を無効化 | (nested 部分集合が timeout-hang) | nested-launch が拒否→無期限 serve (fail-closed→fail-open) | **kill (hang 証拠)** |
| M10 | git_state: completed 経路の `if before==after` 早期 return を無効化 | `..._stops_next_wave[same_main-main-unchanged]` (計 1) | **受理集合不変** (same_main は依然拒否、拒否理由が `main-unchanged`→`commit-mismatch` へ変化) | diagnostic pin (kill 外) |

補足:
- M8 は「拒否が無期限 serve に化ける」変異で、正しい挙動 (nested の拒否) が消えたことを
  hang が示す (受理集合ではなく fail-closed 挙動の変化)。timeout のため個別 node 名は取れず、
  nested 部分集合の hang をもって帰属とした。実測は nested 部分集合 (`-k nested`) に限定して
  他テストの巻き添えを避けた
- M10 は事前登録の段階で「受理集合を変えず拒否理由集合だけを pin する変異」と予測しており、
  実測もそのとおり (same_main は completed の非空 commit 要求により `commit-mismatch` で
  依然拒否される)。kill 集計に混ぜない
- M2 が 36 node を赤にするのは中枢の検証ゲートだからで、単一 fixture の過剰決定ではない
  (36 の別々の fixture がそれぞれ独立に検出している)。各 kill は「その変異が無ければ緑・
  あれば当該理由で赤」が単一理由で成立している

### 台帳の erratum (本 wave の手戻り、failures.md 追記候補)

- **変異ハーネスの二重走行汚染**: 旧セッション起動のハーネスが session teardown 後も
  process として生存し、新セッションの走行と衝突して production を変異させたまま残した
  (daemon/git_state/schema に 3 回)。原因は 3 つ — (i) 生存確認に BRE の `\|` を渡した
  `pgrep` の偽陰性 (ERE では literal 一致)、(ii) M8 (nested 検査除去) が「拒否 →
  無期限 serve」に化けて pytest ごと 900s hang、(iii) `git diff` による復元検査が
  **未追跡ファイルに対して恒真** (常に空を返す) だったため残留変異を検出できなかった。
  すべて wave worktree の正本から hash 比較で復元し、ハーネスを (a) flock 単一走行 guard、
  (b) 内容 hash 比較による復元検査、(c) M8 は nested 部分集合 + timeout=kill 証拠の明示記録、
  (d) timeout をハーネス全体の crash にしない、へ改修した
- **node 名抽出の初回バグ**: `line.split(" ")[0].replace("FAILED ","")` は "FAILED" を
  返し node 名を取り落とす (skill の「ANSI 除去して名前を取る」要件の別型)。
  `line[len("FAILED "):].split(" - ")[0]` へ修正して再走し名前を取得した

## 6. 受入

- dev_waves 全 11 ファイル: **203 passed / 0 failed** (親環境、2 連続で安定)
- 全 orchestrator/tests 受入全走: **後掲** (task-run 台帳付き)
- collected-node 三点比較: before=2370 / new=203 / after=2573、
  **after == before ∪ new、既存 node の消失 0 / 期待外の追加 0**
  (テスト蒸発を緑と数えていないことの機械的裏取り)
