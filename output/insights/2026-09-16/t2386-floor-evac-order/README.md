# [T-2386] official 床値 result の退避と再配置の順序 — 逐語と変異台帳

- authority: none
- default_effect: no-state-change
- wave: `dev-wave-t2386-floor-evac-order` (branch `worktree-dev-wave-t2386-floor-evac-order`)
- 実装 commit: `01a8d34fb` (転送機構 + test + runbook W-2)、`99af814c3` (上書き不在の構造検査)
- 可変状態の正本は worklog 末尾と現行 phase doc。本書はその凍結スナップショットである。

## 1. 何が衝突していたか (親が現物から実測)

| # | 事実 | 出所 |
|---|---|---|
| I1 | clean scan の走査対象は tracked に加え `--exclude-standard` を通った untracked も含む。`.gitignore` に official 床値の出力 path の行は無い | `s8b_holdout_freeze.enumerate_repository_files` / `.gitignore` |
| I2 | 走査の除外は freeze namespace 1 件だけ。`clean_scan_digest` の allowlist は freeze namespace 専用の有界集合で official run directory の口ではない | `s8b_holdout_freeze.EXCLUDED_PATHS` / `s8b_floor_campaign.clean_scan_digest` |
| I3a | candidate 生成は repo 相対の official path を要求する | `_validate_floor_inputs` → `_load_repo_object` → `parse_official_run_path` |
| I3b | 同じ (env_tag, proto8) で ts がより古い適格 run を列挙し、**最古の適格 run が選択されていること**を要求する。入力は repo 内に実在する run directory だけ | `_assert_floor_selection_identity` / `_official_earlier_floor_results` |
| I3c | 専用 6 path 以外の走査 hit には captured HEAD の blob 一致を要求する | `_measurement_closure` |
| I4 | 批准側は世代 commit の tree に blob が実在し、worktree が HEAD blob と一致することを要求する | `s8b_ratified_freeze._verify_generation_semantics` |
| I5 | launch certificate は `repository_files` 全列挙を digest の preimage に含むが、保存するのは digest だけ。「certificate 以前に削除された痕跡は原理的に検出不能」は §5-viii の既知限界として既記 | `build_launch_certificate` |

I1・I2 が「走行前は repo に無いこと」を、I3・I4 が「生成・批准時は repo に在り commit 済みであること」を
要求する。同じ artifact について同時には満たせない。

## 2. 親 brief の誤りと訂正 (段 3 の敵対相談が指摘)

- 「v1 freeze の generator pin が現物と乖離しているから、同 file の編集は関門でない」は推論として
  不成立。乖離は実測事実だが、v2 candidate は captured HEAD の同 file bytes を記録するので、
  他の束縛経路を確認しない限り一般化できない。本 wave は同 file を編集しないので実装 blocker には
  ならない。
- 「untracked なら走査対象」は過剰。`--exclude-standard` で除外されないものだけが対象。
- 「再配置した earlier run は HEAD 一致が要る」は過剰。要求されるのは専用集合外に**実際に出た
  hit** だけである。

## 3. 段 3 の中心所見 (レンズ sol、real・採用)

退避先が呼出し引数である限り、部分復元 API が無くても cherry-pick は再現する。

> 同一 env・proto8 の適格 run A、B があり A が古く、床値投影が `F_A ≠ F_B` とする。A を bundle X に
> 退避 → B を別の新規 bundle Y に退避 → Y 全体を復元 → B を candidate に指定する。A は列挙されず、
> 選択判定は B を最古として通す。candidate の `floor_source` と `floor` は A / `F_A` から
> B / `F_B` へ変わる。bundle の改竄も部分復元引数も要らない。

これに対し親は「退避先を固定導出し、引数でも環境変数でも差し替えられなくする」を採った。D475 の
先例と同形であり、選択の口を API から構造的に消す。

## 4. 段 6 の must-fix 2 件 (レンズ sol、いずれも closed)

1. `git rev-parse --git-common-dir` が呼出し元の環境を継承するため、`GIT_DIR` 等で退避先が分岐する。
   → 導出に使う環境から Git の配置・探索・設定系変数を除去し、有効な別 repository を指定しても
   導出先が変わらないことを検査する node を足した。
2. 旧 bundle を `TemporaryDirectory` 配下へ退避していたため、公開 rename と巻戻し rename が連続で
   失敗すると cleanup が唯一の累積 bytes を消す。
   → 退避先を自動 cleanup の外の耐久 path にし、二重失敗時はその場所を例外本文で名指しして残す。

レンズ luna は GO (nit 1 件)。その nit — 新設 test file が検索パス補正の前に `orchestrator` を
import する — は親が実測して実欠陥と確認した (`env -u PYTHONPATH python3 <file>` が
`ModuleNotFoundError` で rc=1)。fix で閉じた。

## 5. 残余 (主張しない限界)

- filesystem を直接操作して bundle を差し替える攻撃は検出できない。共有 admission 台帳が既に
  宣言している残余と同じ類である。
- 除去する Git 環境変数は列挙方式であり、包括的無効化の保証ではない。現行の迂回変数を確認した
  わけではない。
- 公開・巻戻しの二重失敗後、累積 bytes は耐久 path に残るが正規位置への復旧は手動である。
- 退避は全 proto8・不適格・未完成 run を含む。**退避後に clean scan が緑になることは、その痕跡を
  消してよかったことの証明ではない。** 消した後の再起動の扱いは、発火条件付きの次の一手として worklog に残した。

## 6. 変異台帳

- harness: `tools/mutation_harness.py` (`--runner-mode dispatch --detached`)
- runner argv: `python3 tools/run_tests.py orchestrator/tests/test_s8b_floor_evacuation.py
  orchestrator/tests/test_s8b_holdout_freeze.py::test_restored_namespace_restores_candidate_inputs
  orchestrator/tests/test_s8b_holdout_freeze.py::test_restored_namespace_rejects_later_eligible_run -rf --force-dispatch`
- 実装は段 4 で事前登録 (M1〜M9)、段 6 の real 所見ぶんを fix 前に追加登録 (M10・M11)。

### 6.1 probe (期待 node 収集。全件 SURVIVED 登録)

- 対象 commit: `01a8d34fb` (fix2 前)。結果 sidecar sha256: `15dfb33d36a9429391fb33bc0f0cfec4bae7ebe0b33f1eec52deedcca633b8bc`
- baseline PASSED。11 変異中 10 件が赤 (登録と不一致 = 想定どおり)、**M1 だけが真に生存**。
- M1 の生存は等価変異でも他層の mask でもない。上書き不在を pin する node が推測した名前しか
  見ておらず、新しい名前の上書き口を検出できなかった。同 node を AST 構造検査へ再照準した
  (commit `99af814c3`)。**初回結果は消さずにここへ残す** (`DW-M02`)。

### 6.2 本走

- 対象 commit: `99af814c3`。結果 sidecar sha256: `6d52d43dbc4a757d76efe2e6986e1fbc9924d0516306c2fc71b625c41b6ebe3a`
- **baseline PASSED・11/11 KILLED・SURVIVED 0・期待 node 完全一致・全 anchor 一致数 1。**

| id | 変異 | 殺した node 数 | 注入 diff sha256 (先頭 12) |
|---|---|---|---|
| M1 | `bundle_root` へ環境変数の上書き口を足す | 1 | `aeb8c45890ef` |
| M2 | 退避が既存 bundle の run 集合を累積しない | 3 | `94f4c5ef216a` |
| M3 | 退避後に空 namespace directory を残す | 3 | `4f1aaf60b497` |
| M4 | 退避がコピー後の path・hash 照合を省く | 1 | `b195eb0aec5d` |
| M5 | 再配置が最古の run を落とす | 6 | `56efd48760e2` |
| M6 | `_validate` が manifest と payload の照合を省く | 3 | `0cac090b3f70` |
| M7 | 再配置が既存 destination へ merge 公開する (2 置換) | 1 | `74cbff8281e7` |
| M8 | 内容 hash を定数にする | 6 | `f286e085f080` |
| M9 | 再配置が最新 run だけを残す | 5 | `3d8109b6a728` |
| M10 | `bundle_root` の git 呼出しが Git 環境変数を継承する | 1 | `880e90e3e287` |
| M11 | 旧 bundle を自動 cleanup 配下へ退避する | 1 | `2961f0757f0a` |

**過剰決定の明記** (`DW-M03`): M5・M8 (6 node)、M9 (5 node) はどの gate が捕まえたかを単独で
切り分けられない。冗長 gate を含む変異として記録し、単独の検出力証拠には数えない。
M9 が `test_restored_namespace_rejects_later_eligible_run` を殺していることが、cherry-pick 口の
閉塞を candidate 生成の実物で pin している直接の証拠である。

## 7. 工数

codex 子 9 本。plan 186 秒 / 6 call、consult sol 137 / 6・luna 124 / 5、author 874 / 27、
review 85 / 5・114 / 5、fix 341 / 30、focus 92 / 3、fix2 375 / 25。
計算ノード job は変異 probe 12 走と本走 12 走、runner argv の所要実測 1 走 (72 秒)。
