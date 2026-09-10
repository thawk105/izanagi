# 段 1 brief — [T-740] 待ち手の正本 script 新設

## scope (確定済みユーザー裁定)

- [T-740] 裁定 (a) (2026-08-10 /rulings): **受入 lease の待ち手の正本 script を `tools/` に新設し、
  `docs/pegasus-runbook.md` §7.3 から参照する** (Codex author の軽量 wave)。
  (b) 散文手順のままにする、は不採用。
- command 引数による scope 拡張 (DW-C00「command 引数は worklog 候補より優先する」):
  **背景 producer の待ち手も同じ正本 script に含め、自己マッチによる無音死を構造的に防ぐ。**
  実害 = worklog (369) / F32 再発 2026-08-10 — 汎用待ち手 `wait.sh <done> <artifact> <pattern>` が
  `until ! pgrep -f "$PAT"` で producer 消滅を判定し、`$PAT` が待ち手自身の argv に載るため常に
  自己マッチした。`.done` も成果物も揃った後に 20 時間 23 分 / 7 時間 36 分 滞留し wave が無音で死んだ。

## 段 1 実測 (承認済み裁定の前提)

すべて本 worktree (`worktree-dev-wave-t740-canonical-waiter`、submodule 初期化済み、
`check_wave_startup.py --external-handoff ...` rc=0) で実測した。

1. **`tools/` に待ち手 script は存在しない** (`ls tools/` に lease/wait/accept 系なし)。
   裁定の前提「正本が無く各 wave が書き直している」は成立する。
2. **`claim` の実出力は JSON** — scratch lease dir へ実走して確認:
   `{"age_seconds": 0, "holder": "<12桁digest>", "holder_self": true, "main_sha": "<40桁>",
   "source": {"reason": null, "status": "ok"}, "state": "acquired"}`。
   判定は `state` の値と `acquired` の exact 比較。`status` サブコマンドだけが key=value 形式
   (`tools/wave_land_window.py` の `_print_status`)。F192 の glob 判定はここで死んだ。
3. **テストの置き場は `orchestrator/tests/`**。lease 本体の peer テストは
   `orchestrator/tests/test_wave_land_window.py`。
4. **`tools/README.md` は 2985 / 3000 bytes** (`TOOLS_README_LIMITS`) で余白 15 bytes。
   ここへ節を足す設計にしない。
5. **`docs/dev-wave/**` は加筆しない。** [T-738] 裁定 (c) が「pid 死判定禁止は memory と F32 の
   記録運用を正とする。L1 の圧縮審査 (a) と予算の独立審査 (b) は行わない」で終端しており、
   L1 への条文追加は裁定で閉じている。本 wave は script という別層で構造的に防ぐ。
6. **`docs/pegasus-runbook.md` は check_docs の byte 予算表に無い** (`COMMAND_LIMITS` /
   `SELF_LIMITS` / `TOOLS_README_LIMITS` / `PROVENANCE_*` のいずれにも不在)。§7.3 への参照追記は可。
7. **admission registry への登録は不要。** `tools/pegasus/admission_registry.json` の entries は
   `tools/pegasus/*` と `tools/claude_session_ledger.py` だけで、peer の
   `tools/wave_land_window.py` も未登録。待ち手は sleep と少数の subprocess だけで
   cgroup charged memory は login 上限に対し無視できる (`local-ok` 相当、peer 前例に従う)。
8. **pid 方式の正しい実装は既に repo 外に実在する** —
   `/work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b/wait.sh` が
   `.done` + 成果物 + `kill -0 <pid>` の 3 点照合で書かれている (事故後の修正版)。
   同 wave の `wait6.sh` は pattern を script 内へ埋め込んで正常終了した正例。
   **本 wave はこの形の正本化であり、新しい探索軸ではない** (`DW-G01` 該当なし)。
9. `python3 tools/check_docs.py` baseline rc=0。

## 不変条件 (破ってはならない)

- **待ち手自身の argv に照合 pattern を載せない。** producer の生死は pid (`kill -0`) で見る。
  pattern 照合の経路を script に持たせない (持たせれば同じ事故が再発しうる)。
- **`claim` 出力は JSON として parse し、`state` の値を `acquired` と exact 比較する。**
  出力全体への部分一致・glob・grep で判定しない (F192)。
- **各段の rc を個別に見る。** パイプへ通さない、`|| true` で潰さない、複合条件を 1 行にしない (F37)。
- **fail-closed。** 判定できない・前提が崩れた場合は受入を投入せず、lease を release して非 0 で返す。
- 受入を投入できる状態になってから待ち始める (head-of-line blocking の回避)。
- 既存の受理集合を変えない — 「いつ受入を投入してよいか」の条件は runbook §7.3 の現行散文と同値にする。
  script が新しく緩める・厳しくする点があれば所見として挙げ、実装しない。
- 実装面は Codex `role=author` が書く。親は brief・裁定・統合・全走・記録・commit だけを行う。

## 成果物の形

1. `tools/<新 script>.py` — 2 つの待ち手を提供する。
   - 背景 producer の待ち手: `.done` 実在 + 成果物実在 + producer 死 (pid) の 3 点照合。
   - 受入 lease の待ち手: `claim` loop → `acquired` → local main 取り直し → behind なら
     `merge --no-ff --no-commit` + `commit -F` → 再検査 → 受入 command 投入 → 終端で必ず `release`。
2. `orchestrator/tests/test_<同名>.py` — 上記不変条件の positive/negative テスト。
   **自己マッチ変異が殺せること**を明示的に検査する。
3. `docs/pegasus-runbook.md` §7.3 から新 script を参照 (散文は正本の位置を指す形へ)。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 1 ファイル 2 サブコマンド (`producer` / `acceptance`) にする。2 ファイルに割らない。
  理由 = 「照合 pattern を使わない」「rc を個別に見る」という共通規律を 1 箇所へ集約するため。
- **(P2)** 言語は Python。`tools/` の既存 script と言語方針に揃え、pytest で不変条件を検査できる。
  bash では自己マッチ禁止をテストで固定しにくい。
- **(P3)** 受入 command は script が組み立てず、`-- <argv>` で外から渡す。
  理由 = 機体固有値・test 選択を repo のコードへ焼かないため (runbook が正本)。
- **(P4)** producer の pid は `--pid-file` (producer 自身が `echo $$` で書く) を第一とし、
  `--pid` 直接指定も許す。**pattern を受け取る CLI 面を作らない** (F156/F32 の構造的封鎖)。
- **(P5)** claim の poll 間隔は既定 30 秒、`--poll-seconds` で 10 秒へ詰められる
  (memory `acceptance-lease-poll-30s`: 4 wave 飽和時は 30 秒でも足りない)。
- **(P6)** merge が必要になったのに `--merge-message-file` が渡されていなければ、
  merge せず fail-closed で止めて release する (自動 message / `--no-edit` は `DW-O17` が禁止)。
- **(P7)** 変異事前登録には、**wave 前の実コードの形**として
  `until ! pgrep -f "$PAT"` 相当 (待ち手 argv に pattern を載せる形) と、
  `state=acquired` の部分一致判定を必ず含める (memory `mutation-must-include-pre-wave-form`)。

## 成果物影響 (`DW-G05`)

- 実装しない場合: consumer (各 wave の親) が散文から待ち手を書き起こし続ける。実測された帰結は
  (i) 自己マッチで待ち手が永久ループし wave が無音で死ぬ (28 時間の滞留、worklog 369)、
  (ii) glob 判定で取得済み lease を 2 時間見落とす (F192)、
  (iii) 取り込みを省いて受入を投入し、**受入結果が land 不能になり全走 1055〜1273 秒が捨てられる**
  (F191)。いずれも certified 選択・レポート・台帳そのものの値は変えないが、
  **受入全走という land 前提の検査結果を無効化する**ため、監査済み成果集合の入口が塞がる。

## 分割方針

実装単位は 1 つ (新 script + そのテスト) で所有は素集合。docs (runbook §7.3) は親が書く。
子は同一 worktree で 1 本、並列分割しない。

## 敵対検証子を省かない理由 (`DW-C00`)

散文で書かれていた「いつ受入を投入してよいか」の判定を機械化するため**受理集合の表現が変わる**。
散文と script の非同値は F191/F192 が実証した事故の本体そのものなので、
段 2 プラン起草・段 3 敵対 2 レンズ・段 6 敵対レビュー 2 本を省かない。
