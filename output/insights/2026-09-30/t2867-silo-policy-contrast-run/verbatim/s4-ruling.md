# [T-2867] 本走 wave 段 4 裁定 (親、2026-09-30)

段 2・3 は軽量版で省略 (DW-C00)。brief の (P1)〜(P3) を親が採用する。

## 1. 裁定

- (P1) 採用: 未実走部品 (score job・参照 job・進化×IR の実走) は、v1 cohort の前に試験版文字列
  `silo-policy-contrast-test-2026-09-29` の「進化×IR 1 系列 (score まで)」と「参照 1 本」で確かめる (以下「前走」)。
  理由: 系列台帳は作成時の submit checkout の path と HEAD を束縛し、job はそれと自分の HEAD の一致を要求する。v1 の系列を走らせてから
  欠陥が出ると、その系列には修正を当てられず欠測となり、§7.4 の手順 2 で比較が判定不能になる。前走で欠陥が出れば Codex author で最小修正し、
  v1 の checkout はその修正 commit から作る。費用は約 2 node 時間 (計算確認済みの 61〜70 node 時間に対して小さい)。
- (P2) 採用: 48 系列 + 参照 3 本を回す駆動 loop は repo の外 (job dir) に置き、Codex author が書く。driver・台帳・起動器・親・round tool は変えない。
  loop の raw SHA-256 を発効束に書き、逐語を insight の `verbatim/` に `.md` で残す。
- (P3) 採用: submit checkout 16 本 (AI worktree 容器の外、detach・submodule・hydrate・lock)、同時に進める系列 16 (参照を含む)、LLM 親 4、
  組を系列番号順に開き、組の中は巡回ラテン方格の順。参照 job は batch b の最初の組の前に開く。
- walltime: job1 1800 / eval 900 / score 2700 / reference 3600 秒 (事前登録 §12.1 の案)。
- 変異 matrix: repo の実装面の差分はゼロ (loop は repo 外) なので免除 (DW-S04)。loop の正しさは、実装子の自己試験 (偽の qsub・qstat・起動器・親)、
  段 6 review 1 本、前走での親の実走 (dogfood) で確かめる。
- LLM 親の環境: loop は親を起こすとき、`CLAUDE*`・`CLAUDECODE`・`AI_AGENT`・`ANTHROPIC_*` の変数を全部外した環境で起動する
  (この session の session ID・messaging socket・effort が親へ漏れないようにする)。従量経路の変数があれば loop は起動を拒否する。

## 2. 駆動 loop の仕様 (plan v2)

置き場: 実装子の worktree の `scratch/t2867_contrast_runner/contrast_runner.py` と `test_contrast_runner.py`。親が repo 外へ写して使う。
標準 library だけ。Python 3.10。

### 2.1 入力

`contrast_runner.py run --config <config.json>`。config (親が書く、runner は変更しない):

```json
{
  "schema": "t2867-contrast-runner-config/v1",
  "root": "<abs>",                 // ledgers/<name>/, evidence/<name>/, rounds/<name>/a<a>/, runner-state/ を作る
  "archive_root": "<abs>",         // 起動器 submit の --archive-root <archive_root>/<name>
  "cohort": "...", "version": "...", "pin": "6810666",
  "model": "claude-opus-5-5", "settings": "<abs json>",
  "expected_head": "<40 hex>",
  "checkouts": ["<abs>", ...],
  "walltime_s": {"job1": 1800, "eval": 900, "score": 2700, "reference": 3600},
  "schedule": [{"arm": "reference", "series": 1}, {"arm": "llm-cpp", "series": 1}, ...],
  "max_active_series": 16, "max_llm_parents": 4, "poll_s": 60
}
```

系列名 `<name>` = `<arm>-<series>` (例 `llm-cpp-1`、`reference-1`)。

### 2.2 起動時の検査 (どれかに失敗したら何も投入せず rc=2)

- config の schema・key・型、arm は `llm-cpp|llm-ir|random-ir|evo-ir|reference`、schedule の (arm, series) に重複なし。
- 全 checkout が実在し、`git rev-parse HEAD` == expected_head、`git status --porcelain --untracked-files=no` が空。
- 環境に `ANTHROPIC_API_KEY`・`ANTHROPIC_AUTH_TOKEN`・`CLAUDE_CODE_USE_BEDROCK`・`CLAUDE_CODE_USE_VERTEX` があれば拒否。
- `runner-state/runner.pid` に生きた別 runner があれば拒否 (自分の pid を書く)。

### 2.3 1 周 (poll_s ごと)

1. `qstat` (引数なし) を 1 回呼ぶ。rc≠0 または見出し行 (`RequestID`) が無ければ、この周は job の終了を判定しない (不在と読まない)。
   行頭の `<数字>.nqsv` を走行中の集合とし、記録した request ID がそこに無ければその job は終わった。
2. 走っている LLM 親 (Popen) の終了を回収する (rc と stdout 末行の outcome を記録)。
3. 系列ごと (schedule 順): job も親も走っていない系列だけを扱う (起動器・台帳を触るのはこの時だけ)。
   a. `python3 -B tools/pegasus/silo_policy_contrast_launch.py status --ledger <L>` (cwd = 系列の checkout) を呼ぶ。rc≠0 → attention。
      status は終了条件を台帳に 1 度書く。台帳の `events/` に `series-end` があれば終了として記録し checkout を解放する。
   b. `next_unit` が `dead-job` → attention (自動で投げ直さない)。
   c. `next_unit` があれば `... launch.py submit --ledger <L> --evidence-root <root>/evidence/<name> --archive-root <archive_root>/<name>
      --walltime <walltime_s[kind]> --submit`。kind は `job1|eval|score|reference`。stdout から request ID (`(\d+)\.nqsv`) を取る。
      rc≠0 または ID が取れない → attention。
   d. `next_unit` が無く終了もしていない:
      - `random-ir`・`evo-ir`: `... launch.py generate --ledger <L>` を同期で呼ぶ (timeout 900 秒)。rc≠0 → attention。
      - `llm-cpp`・`llm-ir`: LLM 親待ちの列 (FIFO) に入れる。
      - `reference`: attention (起きないはずの状態)。
4. 親の枠 (max_llm_parents − 走行中) だけ、列の先頭から親を起こす: a = 台帳の `open_opportunity` があればそれ、無ければ `next_opportunity`
   (checkout の `orchestrator/campaign/silo_policy_contrast.py` を import して読む。書かない)。
   argv = `python3 -B tools/pegasus/silo_policy_contrast_parent.py --ledger <L> --a <a> --out <root>/rounds/<name>/a<a>
   --settings <settings> --model <model> --checkout <checkout>`、cwd = checkout、`start_new_session=True`、stdout/stderr は
   `<root>/rounds/<name>/parent-a<a>-<n>.log` (n は同じ a の起動回数。親の `--out` dir の中には置かない)。
   列には同じ系列を二重に入れない。環境は §1 のとおり `CLAUDE*`・`CLAUDECODE`・`AI_AGENT`・`ANTHROPIC_*` を除く。
   親の rc≠0 → attention。rc=0 なら次の周で 3a から続ける (429 の保留は親の中で 900 秒おきに再開するので runner は何もしない)。
5. 新しい系列を開く: `runner-state/pause` が無く、開いていて終了も attention もしていない系列数 < max_active_series、空き checkout がある間、
   schedule の次の項目を順に 1 つずつ `... launch.py init --ledger <root>/ledgers/<name> --checkout <C> --cohort --arm --version --pin --series`。
   rc≠0 → attention (その項目で開くのを止め、以後の項目も開かない)。schedule の順を飛ばさない。
6. `runner-state/pause` があれば 3c・3d・4・5 の新規行動をしない (走行中の job・親は回収する)。

### 2.4 attention と終了

- attention: `runner-state/attention.jsonl` に 1 行 `{ts, name, kind, detail}` を足し、その系列には以後何もしない (checkout も解放しない)。他の系列は続ける。
- 全 schedule 項目が開かれ、各々が終了か attention で、走行中の job・親が無ければ `runner-state/done.json` (系列ごとの終了理由と attention の要約、非空) を書いて rc=0 で終わる。
- 行動はすべて `runner-state/actions.jsonl` に 1 行ずつ (ts、name、行動、argv、rc、request ID、a、outcome、stdout/stderr の末尾 2 KB)。
- 状態 `runner-state/state.json` (原子的に書く): 系列ごとの checkout・走行中の request ID・走行中の親 (pid・a・起動時刻)・attention・終了。
  再起動時はこれを読み、記録された親の pid が生きていれば (/proc の cmdline に parent script の path を含むとき) 走行中として pid で追い、
  消えたら rc 不明として 3a から続ける (台帳が真実)。記録された job は qstat で追う。
- SIGTERM/SIGINT: 新規行動を止め state を書いて rc=0 で終わる。走行中の親・job は殺さない。
- `contrast_runner.py status --config <config.json>`: state・attention 件数・終了数・走行中の job と親を 1 つの JSON で表示 (読むだけ)。

### 2.5 試験

`test_contrast_runner.py` (unittest、標準 library だけ、合計 30 秒以内)。偽の `qstat`・`qsub` (PATH の先頭に置く shell)、偽の checkout
(git init した一時 dir に偽の `tools/pegasus/silo_policy_contrast_launch.py`・`silo_policy_contrast_parent.py` と、実物の
`orchestrator/campaign/silo_policy_contrast.py` の写し) で、少なくとも次を確かめる:
開く順が schedule どおりで上限を守る、1 系列に同時に 1 job、親の同時数の上限、qstat 失敗の周に job を終わったと読まない、
dead-job と rc≠0 が attention になり他の系列は続く、pause で新規行動が止まる、親の環境に `CLAUDE*`・`ANTHROPIC_*` が無い、
全終了で done.json、再起動で走行中の job を二重投入しない。
