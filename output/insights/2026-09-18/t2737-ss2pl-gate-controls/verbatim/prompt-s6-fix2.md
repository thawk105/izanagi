単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe

## 継承する契約

`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/s5-author-prompt.md` の「probe の契約」「禁止」「出力形式」と `s6-fix1-prompt.md` の継承契約を**全文そのまま継承**する (読めなければ即停止)。tracked file を編集しない。commit / `git add` / stash / branch 操作をしない。patch 2 本は変更しない。

## 必読

- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe/probe-t2737/t2737_gate_probe.py` — 対象 (warm-up の呼び出し、`run()` 内 `ident == 'warm-up'` の枝)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe/orchestrator/campaign/buildcache.py` — 756-771 (`_canonical_fetchcontent_base`: `FETCHCONTENT_BASE_DIR` は **既存の non-symlink directory かつ canonical path** を要求)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe/tools/pegasus/probes/t316_sandbox_backend_probe.py` — 1895-1905 (`base.mkdir(exist_ok=True)` → `base.resolve(strict=True)` の先例)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/receipts/probe-result-1.json` — 計算ノード job 1 の受領証。`warm_up.error` に実際の traceback (`BuildCacheError: FETCHCONTENT_BASE_DIR は non-symlink directory 必須`)。JSON は `python3 -c` で key を絞って読む

## 所見と fix (1 件)

**所見 F2 (real、親の計算ノード実測 07:25 JST、request 5036.nqsv):** probe の warm-up は `fetchcontent_base_dir=str(attempt / 'fetchcontent')` を渡すが、その directory を作っていないので helper が入口で `BuildCacheError` を投げ、warm-up が 0.02 秒で内部例外になった。結果、warm 系 cell 全部が `preprocess-failed` (config.h 不在) になり (iii) の対が取れない。

fix の内容:
1. warm-up の直前に `base = attempt / 'fetchcontent'; base.mkdir(exist_ok=True); base = base.resolve(strict=True)` (t316 と同形) を入れ、`kwargs['fetchcontent_base_dir'] = str(base)` にする。receipt の `warm_up` に `fetchcontent_base_dir` の実 path と、helper 呼び出し前に `os.path.isdir` / `islink` / `realpath == abspath` を検査した結果を残す。
2. **`--selftest` に F2 の負例と正例を足す**: `prepare_masstree_fetchcontent` の入口検査 `buildcache._canonical_fetchcontent_base` を (a) 不在 path で呼ぶと `BuildCacheError` になること、(b) probe が作る形 (mkdir → resolve) の path で通ることを、`tempfile.TemporaryDirectory` 内で検査する (helper 本体は呼ばない。tmp を使うので selftest の「tmp 不要」の但し書きを README で更新する)。
3. README-probe.md の該当箇所を更新 (F2 の事実、fix、selftest 項目数)。login で `--selftest` を再実走し rc と PASS 数を報告。login-precheck の再実走は不要 (warm-up は login では呼ばれない)。

## 出力形式

`## 総括` (必須): (1) 変更行、(2) selftest rc と PASS 数 (新項目名)、(3) F2 の closed / partial、(4) 成果物 4 点の新しい sha256 と byte 数、(5) 走らせていないもの。
