# [T-2392] 正式系列の起点入口を CLI へ足すか — D1775 の条件判定と最小実装

- wave branch: `worktree-dev-wave-t2392-genesis-cli-entry`
- 起点 main: `cc9bba523`
- 実装 commit: `29b05b024` (subcommand)、`f0d2ad43e` (テストの単独理由化)
- 裁定: **足す** (D1775 の停止条件は発火しない)

## 何を決めたか

D1775 は「正式系列を開始する production の起点入口を CLI へ足す」と決め、例外として
「**着手前に、既存の orchestrator / producer 経路で起点の commit・argv・入力・lifecycle が
記録されるかを read-only で確かめる。記録されているなら足さない**」を付けた。

本 wave はこの 4 項目を実測した。結果は **commit=偽 (厳密に読む場合) / argv=偽 / 入力=真 /
lifecycle=真** であり、例外の前件 (4 項目の連言) は成立しない。よって主文どおり足した。

## 実測 (read-only、local main cc9bba523 上)

### 不在の確認 (道具: `git ls-files`)

追跡 file の権威一覧を使い、他セッションの worktree (`.codex/worktrees/`) と submodule を
構造的に除外して数えた。

- 追跡 `*.py` 806 件。test を除いて `create_attempt_registry_genesis` を含むのは 4 file:
  `attempt_registry_core.py` (core 定義)、`trial_registry.py` (8c facade 定義 + core への 1 呼出し)、
  `s8b_attempt_registry.py` (8b 側の別 registry / 別 profile)、
  `s8c_preregistration_evidence.py` (C03 の必須関数名集合の**文字列**であり呼出しではない)。
  → **8c facade の非テスト caller は 0 件。**
- `*.py` 以外の追跡 file の hit は docs / insights の散文のみ。実行体は 0 件。
- CLI の subcommand は `register` と `accept` のちょうど 2 つ。
- 正本 path `output/s8c-preregistration/attempt-registry.jsonl` は disk 不在・git 未追跡。
  正式系列は未開始である。

### 4 項目の判定

| 項目 | 判定 | 根拠 |
|---|---|---|
| 入力 | **記録される** | 起点行が `freeze_id` / `manifest_path` / `manifest_sha256` / 全 slot (`prereg_generation` 付き) / 再試行可能理由を保持する (`attempt_registry_core.py:1506`)。受入は起点の manifest digest を受領証と照合し (`s8c_acceptance_receipt.py:1632`)、slot 射影を再導出して一致を要求する (同 1660)。 |
| lifecycle | **記録される** | production driver `p3_autonomous_workload_trial` が slot 予約・観測開始・終端を駆動し、process 同定と開始時刻を残す。受入が射影を再導出する。 |
| argv | **記録されない** | `main(argv)` は `parse_args` するだけで保存先が無い。receipt schema・registry 行・CLI 出力のいずれにも raw argv の field が無い。**既存 2 入口も同じ**なので、同層への追加では改善しない。 |
| commit | **記録されない (厳密に読む場合)** | 下記。 |

### commit 束縛が「導入 commit」を束縛していないこと (段 3 sol が発見、親が現物で確認)

受入は起点が git に commit されていることを要求するが、束縛されるのは
**「起点 1 行の blob を含む任意の commit」**であって「起点を作った commit」ではない。

- 全史走査 `_assert_attempt_registry_history_append_only` は、blob が前 commit と同一のとき
  strict-prefix 検査を掛けない (`s8c_acceptance_receipt.py:1898` の
  `if previous is not None and canonical != previous and (...)`)。
- `_blob_at_commit(root, prereg_content_commit, path)` は P に genesis-only blob が在ることしか
  見ず、P が導入 commit かを見ない (同 1638)。

**反例:** commit G が起点を導入 → registry を変えない無関係な commit K → K を内容 commit `P` として
使う。この履歴は正式な発行経路をそのまま通り、receipt に残るのは K であって G ではない。

なお受入の attempt 検査そのものは恒真ではない。P/C の食い違い、P に blob が無い、
prefix が継承しない、P 時点が起点 1 行でない、final terminal の欠落・重複・report hash 不一致は
いずれも赤になる (負例テストは `test_s8c_acceptance_receipt_v2.py:1132/1158/1182/1199/1268`)。

## 本 wave の実質的な純増 — provenance ではなく入力構築の保証

`create_attempt_registry_genesis` は `manifest_sha256` を**独立した引数**として受け取り、
`_SHA256_RE.fullmatch` の形式検査しかしない (`trial_registry.py:2494`、正規表現は 115 行)。
manifest 本体を読んで照合しない。起点は create-only の不可逆な成果物なので、
食い違う hash を渡すと誤りは受入まで残る。

追加した `genesis` subcommand は `load_trial_manifest` を通して manifest bytes から digest を
導出する (同関数は `sha256` を返す、821 行)。これは既存 `register` 入口が
`append_trial_registration` 内で使うのと同じ helper である (1741 行)。
**誤った digest を不可逆な起点へ焼き付ける前に拒否できるようになった。**

一方で、追加した入口も **schema を変えない限り actor・時刻・実行 code 版・argv・真の導入 commit を
記録しない**。本 wave はこの穴を塞いでいない。

## 実装

- `orchestrator/campaign/trial_registry.py`: `main` に第 3 subcommand `genesis` を追加。
  引数は `--manifest` / `--repo-root` / `--freeze-id` / `--prereg-generation` / `--slots-file` の 5 個。
  `--manifest-sha256` は導出するため足さず、`--registry` と `--retryable-failure-reasons` は
  既存の正本 path・閉集合を使うため足さない。既存 2 入口は無変更 (差分は追加のみ、削除 0 行)。
- `orchestrator/tests/test_trial_registry.py`: 正例 1・拒否例 7 を既存 file へ追加。
  **新規 test file を作らない**ため、自走 harness の登録も受入所要台帳の新規行も不要で、
  main 取り込み時の台帳競合も起きない。

## 検査

| 走行 | 結果 |
|---|---|
| 新テスト単独 (`-k genesis_cli`) | 8 passed |
| 変更 test file 全体 (fix 前) | 248 passed |
| 変更 test file 全体 (fix 後) | 248 passed |
| consumer 17 file (参照関係で列挙) | 2421 passed / 8 skipped |
| AI provenance 全史監査 | rc=0 |
| 非帰属赤 3 件の単独再走 | 3 passed (9.04s、非再現) |

### 受入の経緯 (3 attempt、いずれも実装の赤ではない)

- **attempt 1**: `stage=postcheck rc=70`。post-claim merge は成立 (`ba92db94c merge main`、
  main `2995cc728` を取り込み) したが、走行中に main が 6 commit 進んで branch が遅れ fail-closed。
  テスト子は未起動 (`raw_child_rc=null`)。実体は `_behind_count != 0`
  (`tools/dev_wave_wait.py:3882`) だが、診断行は `reason: terminal-postcheck` としか出さない。
- **attempt 2**: 完走。**21976 passed / 68 skipped / 3 赤**。3 件とも `trial_registry` を
  1 箇所も参照しない file (`test_codex_worker_launch.py` 1 件、`test_t1259_qsub_env_delivery_probe.py`
  2 件)。実行ノードの loadavg は **65.1**。内訳は launcher の rc 期待に対する timeout 1 件と、
  `git ls-files --others --exclude-standard -z` が 30 秒 timeout する setup 失敗 2 件。
  → 同一 tip で 3 件を単独再走すると **9.04 秒で全部緑 (非再現)**。環境由来と確定。
- **attempt 3**: 再び `stage=postcheck rc=70`。
- **attempt 4〜6**: postcheck は通過し全走したが、毎回**別の**非帰属 test が赤 (codex launcher 系 / 変異 harness /
  `campaign.lock` を 32 件と数える共有状態 test)。3 file とも `trial_registry` を 1 箇所も参照しない。
  lock 数はその後 main・wave 側とも 32 件で一致しており、一過性だった。
- **attempt 7**: **緑。21990 passed / 68 skipped / 赤 0、rc=0、receipt 発行。**

### 変異 matrix

事前登録 (実装前、`verdict.md`) の 4 変異。置換対象が 4 件とも一意であることを実測してから走らせた
(`manifest_sha256=manifest.sha256,` は file 内に 6 箇所あるため、genesis 分岐の呼出し全体を anchor にした)。

確定版 (`mutation-ledger-final.json`、HEAD `f0d2ad43e` に束縛、baseline PASSED):
**4 件すべて KILLED、MISMATCH 0、SURVIVED 0、TIMEOUT 0**。期待 node の完全一致も 4 件とも成立。

| 変異 | 内容 | 結果 | 赤になった node 数 |
|---|---|---|---|
| m01-fixed-digest | 導出 digest を固定の形式妥当な定数へ | KILLED | 1 |
| m02-constant-generation | `args.prereg_generation` でなく定数 1 を渡す | KILLED | 2 |
| m03-optional-generation | `--prereg-generation` を optional 化 | KILLED | 1 |
| m04-permissive-json | strict decoder を寛容な `json.loads` へ | KILLED | 3 |

**erratum (初回走行を probe として保存):** 初回 (`mutation-spec-probe.json` /
`mutation-ledger-probe.json`) は m02 が MISMATCH だった。**原因は親の期待集合の誤りであり、
実装の欠陥ではない。** 段 6 fix で世代不一致テストの全 slot を一様に `3` へ揃えたため、
変異が定数 `1` を渡しても先頭 slot で同じ食い違いメッセージが出て、当該テストは緑のまま通る。
親は当初この node を期待集合に含めていた。訂正版 (`mutation-spec-final.json` /
`mutation-ledger-final.json`) では m02 の期待 node を正例・再実行テストの 2 件へ直した。
初回結果は消さず probe として残す。

m04 は初回から期待どおり 3 node (duplicate-key / non-utf8 / non-finite) で一致した。
`[object]` は decoder を緩めても「配列でない」で落ちるため期待集合から外してあり、
この判断も実測で裏付けられた。

## 段 6 レビューの裁定

- **refuted:** 「`load_trial_manifest` は裁定外の validator」— 既存 `register` 入口も同じ helper を
  使う (`trial_registry.py:1741`)。同層の兄弟入口と同一であり新規 validator ではない。
  拒否されるのは受入を通りようがない入力だけである。
- **real・scope 内 (fix 済み):** canonical stdout の自己 oracle、世代不一致テストの過剰決定、
  strict JSON 入力の過剰決定。いずれも本 wave が追加したテスト自身の弱さで、
  変異の単独理由性に直接効くため fix した。
- **real・scope 外 (新規 T へ):** 下記。

## scope 外の real 所見 (実装せず、ユーザー裁定へ返す)

受入契約または registry schema の変更を伴うため、D1769 に従い本 wave では実装しない。

1. 受入は「起点を導入した commit」を束縛していない (上記の反例)。束縛するかは設計択一。
2. `_write_create_only` は `O_EXCL` で作成後、途中の `os.write` / `fsync` 失敗でも作りかけ file を
   消さない (`trial_registry.py:2433-2467`、`finally` は fd を閉じるだけ)。壊れた正本が
   create-only path を占有し再試行を恒久的に塞ぐ。共有 writer で分類受領証経路 (3288 行) も使う。
3. standalone の receipt verifier は `prereg_effective_commit` が実在するか・P の直子か・
   measurement HEAD の祖先かを検査しない (正式 issuer だけが検査する)。
4. standalone verifier は lifecycle の意味を再導出しない。`_assert_git_history_append_only` は
   lifecycle JSON を parse せず、長さと hash を合わせた任意の非空 file を拒否できない。
5. standalone verifier は起点の `manifest_path` を受領証の `manifest_path` と比較しない
   (正式 issuer は比較する)。
6. 起点 schema に作成時刻・実行者・実行 code 版の field が無く、exact-key 検査により追加もできない。

## 手順の欠落 (段 3 luna)

起点を作る**運用手順**は `docs/phase3-8c-preregistration.md` にも
`docs/phase3-s8c-autonomous-trial-runbook.md` にも無い。前者は規範的要件 (§6 前提条件 4) を書くが
手順ではない。コードが要求する順序は少なくとも
「manifest と slots を用意 → 起点を生成 → 起点を含めて `P` を commit → binding のみの `C`」
だが、この起点生成の工程が未文書化である。本 wave は subcommand を足したので、
手順を書く先は用意された。
