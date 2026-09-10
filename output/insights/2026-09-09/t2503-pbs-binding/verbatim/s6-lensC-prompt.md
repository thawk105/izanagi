単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding

必読事項の射影:

- `/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s5-impl.diff` — レビュー対象の実装差分 (逐語)。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s4-adjudication.md` — 親の段 4 裁定。**変異事前登録 (B-057) を含む**。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s5b-author-out.md` — 実装子の報告。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py` — 適用後の現物。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py` — 適用後の現物。読めなければ即停止。

## 依頼

あなたはレンズ C = **正しさと検出力**の敵対レビュー子である。実装を守るのではなく攻撃せよ。
コードを編集してはならず、commit してはならない。所見が無い項目は「所見なし」と書いてよい。

## 攻撃面 (各項目に「real / refuted」と根拠の file:line を付ける)

1. **事前登録した変異が本当に殺されるか。** 段 4 裁定の M1〜M5 を 1 件ずつ机上で適用し、
   期待 node の集合が**完全に**一致するかを判定せよ。
   - M1: `repo_pbs = repo_root / _RUNTIME_PBS_RELATIVE_PATH` → `_BOUND_RELATIVE_PATHS[1]`
   - M2: 同 → `_BOUND_RELATIVE_PATHS[0]`
   - M3: 比較条件を `if False:` にする
   - M4: 例外文言を `"runtime PBS mismatch"` にする
   - M5: `runtime_hashes["runtime_pbs_spool"]` の引数を `repo_pbs` にする
   期待 node が裁定と食い違うなら、正しい期待 node を根拠つきで示せ。
   **裁定の期待 node が誤りである可能性を必ず検査せよ。**
2. **単一理由性 (DW-M01/M03)。** 各変異について、赤理由が 1 つに絞れるか。
   前後・内側に同じ入力を拒否する層が無いか。過剰決定 (複数の gate が同時に赤にする) が
   あれば real 所見にせよ。
3. **恒真・過剰決定。** 追加された 2 つの test のうち、実装のどの行も通らずに緑になる経路が
   あるか。特に helper の assert が先に落ちて test の本体が実行されない条件を構成せよ。
4. **fixture の脆さ。** helper が作る git repo と環境が、次の条件で壊れないか検査せよ。
   実 hostname が `compute-test.example` と偶然一致する、`tmp_path` が repo 配下になる、
   `GIT_DEFAULT_HASH` が sha256 の環境、`init.defaultBranch` 警告、`safe.directory` 制約、
   `core.hooksPath` の global 設定、`realpath` が symlink を解決して `expected_root != repo_root` になる、
   `assert not runtime_pbs.is_relative_to(repo_root)` の Python 版依存。
5. **揮発 payload の焼き込み。** 期待値に working tree の hash、実 hostname、実 job id、
   実行時刻など揮発する値が入っていないか。
6. **規律 2。** 実装がどこかで正しさゲートを緩めていないか。例外文言、`runtime_sha256` の key 集合、
   tuple の値と順序、他の関門 (job id / commit / dirty / nodefile / login node 拒否) が
   差分前と意味的に同一であることを確認せよ。
7. **実装子の報告の裏取り。** 「tuple の値・順序、例外文言、6 件の hash key は不変」
   「編集は 2 file だけ」「129 node green」を差分と現物で検証せよ。誤りは real 所見にせよ。

`docs/failures.md` の型タグ [恒真ゲート] [テスト代表性] [捏造/幻覚] を攻撃面に含めよ。

## 制約

- read-only sandbox。**pytest を実走しなくてよい**。静的検査で足りる。
  実走していないものを「緑」「赤」と書いてはならない。
- 仮想リスク向けの gate・検査・台帳・一般化の追加を推奨しない。scope 外の real 所見は
  「scope 外」と明記して裁定候補として返せ。
- 所見には**成果物影響** (放置すると certified 選択・レポート・台帳の値・受理集合・参照が
  どう変わるか) を 1 行で添えよ。書けない所見は nit と明記せよ。

## 出力形式

見出しは H2 (`##`) で統一し、最後に `## 総括` を置く。各所見は「所見 / real か refuted か /
根拠 file:line / 成果物影響 / 提案」の 5 点で書く。結合文字 U+0300〜U+036F を使わない。
予算が尽きそうなら、途中でもこの出力形式どおりに結論を書いて終われ。無出力が最悪である。
