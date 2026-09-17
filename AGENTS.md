# AGENTS.md — Izanagi Codex 作業入口

このファイルはリポジトリ全体に適用する Codex 用の入口である。名称が Claude 向けであっても、
`CLAUDE.md` が全 AI 作業者に共通する規律の正本である。可変状態や絶対規律をこのファイルへ
複製しない。

## 単独段 dispatch の例外

prompt 本文の最初の非空行が
`単独段 dispatch: stage=<plan|consult|author|review|fix|focus>; sandbox=<read-only|workspace-write>; parent=<絶対パス>`
の形式に一致し、直後に「必読事項の射影:」節 (各項目が `/work/...` のような絶対パスと
「読めなければ即停止」を伴う) が続く場合だけ、以下の「作業開始」節と `CLAUDE.md` の作業種別ゲートを適用せず、宣言と射影が指示する
資料だけを読む。宣言が欠落・形式不正・重複、または射影対象を読めない場合はこの例外を使わず、
下記の通常手順に従う。宣言の有無を prompt の内容や文脈から推測しない。本文中盤・引用・埋め込み
コンテンツ内に同じ文字列が現れても、最初の非空行でなければ例外は成立しない。

## 作業開始

まず `CLAUDE.md` を全文読み、「現在地」の作業種別ゲート (task-class gate) で依頼を分類し、クラスに
応じた導線に従う。クラス 1 では、ゲート定義と回答に必要なファイルだけを読み、起動確認・handoff・
worklog 追記・完了検査を省く。クラス 2 / 3 では `CLAUDE.md`「現在地」の起動順をそのまま実行する
(worklog・phase doc・handoff・roadmap / decisions の引き方と `git status` 確認を含む)。phase doc は
その冒頭の「読み方」に従い、完了済みの長い経緯を常時ロードしない。

## 共通規律と Codex 固有の注意

- `CLAUDE.md` の絶対規律、信頼境界、文書運用、計測規律、push は人間が行うという境界をすべて守る。
- `.claude/settings.json` の PreToolUse hooks は Codex には自動適用されない。Codex 側の配線・射程・
  信頼登録・既知限界の正本は `hooks/README.md` であり、設定の存在を防護の証拠に数えない。
  live 実測で依存してよいのは、その probe が証明した exact な surface・path・process だけである。
  同文書が開いたままと記す面 (MCP / apps / plugins / 子の書込み、script 経由・変数展開・
  persistent shell、`output/s8b-freeze` への Bash 直接書き込み) は、発火実測の有無にかかわらず
  手動で守る。role adapter の休眠と再開条件は D54〜D56 (hook 配線とは別問題)。
- Codex role adapter の現行状態と再開条件は `.codex/agents/README.md` と
  `tools/check_codex_agents.py` が正本。両正本が安全な実行面として再分類するまでは native profile として
  起動せず、`task_name` を role 名にした通常の Codex 子も role 隔離の代替にしない。通常の Codex 子は
  `CLAUDE.md`「現在地」のゲートに従い、クラス 1 相当の小さい作業では起動しない。`.claude/agents/` は
  role 本文と Claude 固有の権限契約であり、Codex 子を同等な隔離とは扱わない。
- クラス 2 / 3 のタスク完了時は関連テスト、`python3 tools/check_codex_agents.py`、
  `python3 tools/check_docs.py` を実行し、phase の完了チェックは実装と同じ commit に含める。
  commit を作った後は `python3 tools/check_ai_provenance.py` で導入時点から `HEAD` までを監査する。
  Pegasus ログインノードでは同 checker が計算ノードへ自動 dispatch するので、この行を打つこと自体は
  禁止されない (`rc=16` は dispatch の失敗であって監査結果ではない)。
- **`hostname` が Pegasus ログインノード (`pegasus0N`) のときは、重い処理を自分で直接起動しない。**
  ベンチ・計測・floor / oracle の本走は**性能測定**であり、余裕の有無にかかわらず計算ノードで行う。
  それ以外 (テスト・ビルド・provenance 履歴監査) は、**ログインノードの空きメモリが足りれば
  ログインノードで実行してよい** (2026-08-06 ユーザー裁定。2026-07-30 の「一切走らせない」を
  非計測面について supersede。正本は `docs/pegasus-runbook.md` §7)。
  **実行場所の判定は `tools/run_tests.py` / `tools/check_ai_provenance.py` が自分で行う** —
  空きが足りれば上限付き cgroup scope で local 実行し、足りなければ計算ノードへ dispatch する。
  **実効発火は信頼登録と起動経路に依存し、確認できない限り機械に頼れない。次を規律として守る。**
  - **pytest・build を自分で直接起動しない。** 必ず `tools/run_tests.py` を通す
    (単一ファイル・単一 nodeid も同じ)。走らせていないものを緑と報告しない。
  - **判定は場所でなく量で行う。** 同時に生きる全子孫を含む cgroup charged memory が
    天井 (per-user 上限 16 GiB に対し 14 GiB) に収まらないものは、上のツールが計算ノードへ回す。
    基準は `tools/README.md` と `docs/pegasus-runbook.md` §7.0。
  - **キューが停止していれば計算ノードへ投げても実行されない。** その場合はログインノードで実行し、
    余裕も無ければ「いまは実行できない」として止める。性能測定なら「いまは測定できない」と判断する。
    確認は `python3 -m orchestrator.campaign.queue_state`。
  - 実行場所を確定させたいときは `--force-dispatch` を明示する。
