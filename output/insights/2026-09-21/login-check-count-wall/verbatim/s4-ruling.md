# 段 4 裁定 — 段 3 相談 A (`codex/s3-consult-A.md`) の所見 18 件と plan v2

裁定 inbox (`dev-wave-jobs/rulings-inbox/`) の再走査: wave 開始 (07:4x) 後の更新なし (最新 09-21 01:21 の第 27 回)。

## 所見の裁定 (番号 = 相談の番号)

| # | 判定 | 採否 | 処置 |
|---|---|---|---|
| 1 | real / must-fix | 採用 | P1 を「義務の発火イベント × 履行した実行」の対応表に変える。全史監査の必須数は「通常 commit 後」「親 merge 後」「受入 tool の claim 前到達数」「merge 後監査到達数 (`behind > 0`)」「land 到達数 (no-op / recovery 除く)」を別イベントで数え、tool が履行した義務を親側で重ねて数えない |
| 2 | real / must-fix | 採用 | check_docs の義務は「完了変更 (docs-only に限らない) の commit 前」+「fragment の commit 前」+「docs commit 後の repo scan invariant・影響テスト再走」+ post-claim merge 後の再確認 (checker / 対象が変わった場合) を別イベントにする。docs-only 件数から必須回数を導かない |
| 3 | real / must-fix | 採用 | fold dry-run = 「land 前 rc 0 まで」1 義務 + 「fragment 変更 commit 前」義務で、検査対象が同じなら 1 走で両方を充足しうる (共有可)。三軸語 = 凍結 commit ごと (wave 1 回に固定しない)。land 監査 = 到達数 (失敗・再試行を含む、landed 1 件から決めない) |
| 4 | real / must-fix | 採用 | 分類軸を「義務の根拠 (契約文 / tool 内蔵 = 機械強制 / 根拠なし)」と「実行主体 (親 / 受入 tool / land)」の 2 軸に分ける。`--message-file` preflight は full 監査と混ぜず付帯検査欄へ (回数・wall は出す)。必須超過を一律「習慣」と書かず、義務対応が不明な走は「理由未同定」 |
| 5 | real / must-fix | 採用 | probe A の warm 判定は `_receipt_prefix` の全条件 (schema・rc・bindings・tip 祖先・selection digest・delta・records・coverage・correction fallback) を実装し、同 tip 再利用も許す。候補順は距離・名前順 |
| 6 | real / must-fix | 採用 | 「現存 store からの再構成」と明記し、warm/cold は「再利用可能候補あり / 候補なし (再構成上 cold) / 再構成不能」の 3 値。同 tip 上書き (t2243 22:49 親 → 22:54 受入) の例を限界に書く。剪定は祖先優先・mtime 順である旨を書く。「login cold 11」「偽 cold 0」を確定値にしない |
| 7 | real / must-fix | 採用 | cold の原因は「直近祖先 1 件との比較差分」と表示し、束縛 key (environment の checker / config / inherited / schema、bindings の attributes / cab_hits / registry_manifest / policy / scope_epoch / implementation_epoch / object_format / repository) を全部列挙して重複可能にする。P3「3 分類で尽きる」は撤回 |
| 8 | 判定不能 | 採用 (表現) | t2797: 「旧 checker (7c02fb2d) で実行」は観測条件 (partition の checker sha)、cold とその原因は再構成仮説として分ける |
| 9 | real / must-fix | 採用 | env 種別は「継承 env の特徴 (GIT_CONFIG_GLOBAL=/dev/null ∧ GIT_ATTR_NOSYSTEM=1 ∧ LC_ALL=C 等、land の `_git_env` 全 key 値の一致)」で land-like / login-like / その他とし、主体・実行ノードの確定内訳とは書かない |
| 10 | real / must-fix | 採用 | 受領証の帰属は「tip の commit 所属」と「監査を呼んだ主体・attempt」を別列にし、受入 ref 走 (入力 tip = 既存 main tip) と amend 前 tip を「対応不明」で残す。t2817 の 8 監査 vs 7 受領証を例に書く |
| 11 | real / must-fix | 採用 | attempt は `acceptance*-N.started.txt / finished.txt / tip-before.txt / tip-after.txt` を一次証拠とし chain.log / gate-loop-*.log は補助。検査 log は「名前 + 内容 (終端行・件数行)」で実走を判定し、script 内の文字列は実走証拠にしない。land 前 dry-run (`land-*.fold-dry-run.json`) を数える。「find-fold-owned 0」は「痕跡 0 (実行 0 と言わない)」 |
| 12 | real / must-fix | 採用 | commit の分類は「check_docs 走査対象 path (docs/**、*.md、.claude/commands/**、.agents/skills/**、docs/spool/**) を含む」「tools/check_docs.py / orchestrator/tests/test_check_docs.py を含む」「実装面 (所在不問 .py/.sh) を含む」「merge」の重複可能な flag にする。走査対象の正確な一致は check_docs.py を読んで確定する (probe B の author が `tools/check_docs.py` の走査集合を引く) |
| 13 | refuted (親の主張が正しい) | — | P4 の別列方針は維持。上書きは同 partition 内に限る旨を書く。range は full の見えない回数へ足さず別モード |
| 14 | real / must-fix | 採用 | branch-residue は親 5 走 + 受入 1 走 = 6 走の痕跡 / 現存受領証 5 と書く。unique receipt 数で実行数を代用しない |
| 15 | real / must-fix | 採用 | wall の出所列 = 直接計測 (`/usr/bin/time`、start/end stamp) / 開始終了が裏付けられた区間 / mtime 代理区間 / 前提値 (22 / 58) / 未観測。t2803 の `audit-*.time` (112.5 / 47.4 / 54.1 秒) と t2243 の `.times` (50 秒) を直接計測として使う。`.err` が非空のときは開始時刻に使わない |
| 16 | real / must-fix | 採用 | P2 は「束ねによる短縮の候補」に弱め、15〜20 分の代表値を外す。log 完了間隔は「2 点間隔 (親手番 + 実行 + 待ち)」として個別に列挙。entry 1776 の残差との関係は「重なりうる (うちとは言えない)」 |
| 17 | real / should | 採用 | probe は採取時刻・入力 hash・mtime_ns を保持し、母集団の収支 (対象 / 対象外 / 曖昧 / 読取失敗 = 総数) を出す。12 wave の同定は「status=landed の出力 file の mtime 最大」の規則を明記 |
| 18 | 判定不能 | 採用 (表現) | 親 script 本体は J に残し、repo には sha256・由来・仮説出力 (.txt) だけを収容 (先例 wall-decomp と同じ)。実装面 0 行・変異免除の前提はこれで保つ |

## plan v2 (段 5)

- **Codex author 1 本** (workspace-write、子木 `author-login-check-probe`、所有 path = `tools/login_check_receipt_replay.py`、`tools/login_check_event_ledger.py` の 2 file。repo に land しない = 親が J/probe へ退避して login で実走)。仕様は `codex/prompt-author-A.md`。
- **親**: probe の実走 (login、read-only、数十秒) → 出力を `J/probe-out/` → insight README 起草 (`output/insights/2026-09-21/login-check-count-wall/`) + verbatim (probe 出力、契約逐語、受領証の写しは probe 出力に含む、hyp-* の親 script 出力と sha256)。
- **段 6**: read-only review 1 本 (README と probe 出力の照合、所見 1〜18 の反映確認) + 焦点再レビュー ≤ 3 巡。probe の欠陥は fix 子 (同木 branch) へ。
- **変異 matrix**: repo の実装面差分ゼロ → 免除 (DW-S04)。受入全走は実施。
- **裁定パッケージ (insight に置く、実装しない)**: 相談の表の 4 択一 (同一 shell 順次実行 = 推奨候補 / claim 前監査への集約 = 現行維持推奨 (DW-O17 通常列に触れる) / fragment 検査と land 前 dry-run の共有 = 入力不変時のみ / land env 分離維持) + 本 wave の観測から出る「三軸語 CLI (45 秒) と check_docs (30 秒) の wall が warm 監査 (22 秒) より重い」の扱い。効果は `22 × warm + 58 × cold` の前提 model と call 間隔の個別列挙で条件付き試算に留める。D690 と DW-O25 480 秒は別契約で、いずれの択一も変えない。
