## 総括

**実装済み・計算ノード未実走**です。[probe/verify_phase_runner.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2807-author/probe/verify_phase_runner.py) を in-place 改版し、untracked のまま残しました。tracked file の差分はありません。commit 操作はしていません。

- 行数: **1785 行**
- 改版前 v2 SHA-256: `c960093de4206d8947b03097bb146ba9e4ee7b43ec6b974cee9d60a4b7609cd5`
- 改版後 SHA-256: `8a44e23875655d24d515d56b9d334e93b2f7a3b6f8646e85d969060022036ce7`

実走した軽量検証:

- `selftest: PASS 120/120 cases`、rc=0。v2 由来49例を更新し、境界・打ち切り・予算・判定順序・束縛・既知結果・identity drift 等を追加。
- AST 構文確認: PASS。
- v2／B-8 helper 全13群の import・属性実在確認: PASS。
- `prerun / calibrate / verify / reverify / summarize / selftest --help`: 全6件 rc=0。
- pytest nodeid の実走は無し。上記は runner 内 selftest の範囲で、親の受入全走を代替しません。

**未実走:** hydrate・checkout・quarantine 適用・build・bench・verifier・圧縮保全／復元・計算ノード経路。所有外 caller・共有 fixture・consumer test への変更波及は**無し**です。

仕様上の差異として明示する点:

- 共有 `choose_extime` は `(3,6,10)` を内部固定しているため、runner 内に同じ選択規則の `(6,10)` 版を実装しました。共有 helper は変更していません。
- 事前登録 §5 の「bench 再生成なし」と依頼の attempt-2 許可は不一致です。明示された依頼に従い、一度の bench retry を維持しました。失敗 attempt は開示し、成功 retry で規約不適合を消しません。

親の login 確認コマンド:

```bash
cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t2807-author
python3.10 -B probe/verify_phase_runner.py selftest
```

試走 argv は以下です。これは指定 author tree を入力にした具体形です。親の投入では `--repo-root` と `--ruling` を実際の detached submit-tree 内の絶対パスへ置換してください。runner は親が job dir へ保全した後に使用します。

```bash
python3.10 -B \
  /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2807-b8-prerun/probe/verify_phase_runner.py \
  prerun --gate g_rl \
  --repo-root /work/1/SFC/tanab/izanagi/.codex/worktrees/t2807-author \
  --third-party-cache /work/1/SFC/tanab/izanagi-thirdparty-cache \
  --scratch-root /scr \
  --output-dir /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2807-b8-prerun/run/prerun/g_rl \
  --ruling /work/1/SFC/tanab/izanagi/.codex/worktrees/t2807-author/docs/b8-final-candidate-longrun-verify-preregistration.md
```

`g_rt` は `--gate` と出力先末尾を `g_rt` に替えた別 job です。試走に `--bundle` は渡しません。