---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-22
wave: dev-wave-t1472-provider-init-indeterminate
seq: 1
---

## 新規

### {{F:mutation-worktree-local-mode-and-resume-file-preconditions}}. `mutation_worktree.py`のlocal mode誤用・resume時の既存file要求が未文書 [手順漏れ]

- 事象: [T-1472] waveの段6変異matrixで、DW-M07を読まずに`--runner-mode dispatch`の既定を
  外れ`--runner-mode local`へ切り替えた (Pegasus queue混雑を疑い、collection段のdispatch
  timeoutを回避する目的)。DW-M07は「runnerの実行経路を変異させるlocalはrunnerが自壊し
  収集段がrc=16になる」と明記しており、実際にlocal mode下でも複数回rc=16の
  collection失敗を再現した (dispatch modeで見えていたのと同型のrc=16のため、当初は
  純粋なqueue混雑と誤認した)。さらに、以下の未文書の制約に連続して遭遇した。
  1. `--resume`+`--attempt-out`は**既存の非symlink通常file**を要求する (新規pathは`--out`同様に
     拒否される)。
  2. 上記1の要求を満たすため空fileを`touch`すると、`Expecting value: line 1 column 1`で
     JSON parse失敗する — 空fileでは救えず、有効な`izanagi-dev-wave-mutation-attempts/v1`
     schemaのJSONが要る。
  3. 既存の有効な`attempt-out`fileを再利用する場合、その`runner_sha256`が現行runの
     runner command (`-- python3 tools/run_tests.py ...`の中身) と一致しないと
     「attempt sidecarのrunner_sha256が現行runと不一致」で中止する — resumeの途中で
     test選択方法 (whole-file指定 vs nodeid個別指定) を変えると発火する。
  4. `--resume`には`--out`自体にも既存の非symlink通常fileが要求される。
  5. `--attempt-out`/`--wrapper-attempt`は`--runner-mode local`では**使用不可**
     (DW-M07には「dispatch専用の同時指定必須ペア」と書かれているが、「local」でも
     単体で指定すると別のエラーで気づく形になっており、"local + 一方だけ" 等の
     組み合わせが初見では判別しにくい)。
  6. `estimated_run_seconds`(spec.json) を過小評価すると、`mutation estimate: N mutation(s) x
     Es + baseline`の合計が`timeout_seconds`と一致・超過した時点で`runner-mode-violation`
     (rc=2) となり、その時点で変異が生成物ファイルに適用されたまま (`dirty
     path=<production file>`) 中断する。復旧は対象scratch worktree内で
     `git checkout --`(このworktreeは隔離ガード対象外なので通常git操作可)。
  7. orphan-hold/runner-mode-violation復旧のため`.izanagi-mutation-worktree`ディレクトリを
     `rm -rf`で直接削除すると、**呼出し元 (親wave) のworktree側の`.git/worktrees/`登録が
     「missing but already registered」で残り**、次の投入が`git worktree add --detach`
     失敗で赤化する。復旧は親wave worktree内で`git worktree prune -v`
     (これも隔離ガード対象外)。
- 根本原因: `docs/dev-wave/mutation.md`のDW-M07は「dispatch既定・local自壊」までは
  明記しているが、上記1〜7の個別の未文書事項までは書いていない。加えて本wave自身が
  DW-M07を読む契機 (条件dispatch15) を見落とした (F461の再発、上記参照)。
- 恒久対応: `docs/dev-wave/mutation.md`のDW-M07へ上記1〜7を追記する案は**段8裁定で不採用**。
  DW-M07は978 bytesで`tools/check_docs.py`のL2単節予算1000 bytesに対し空きが22 bytesしかなく、
  7項目は意味を保ったまま入らない。`docs/skill-self-improvement.md`の
  「予算に収まらなければreferenceへ統合し、それでも意味等価にできなければ変更を止めて
  ユーザー裁定へ返す」「予算値を上げる変更は通常の自己改善に含めず、理由付きの独立審査対象に
  する」に従い、裁定パッケージとしてユーザーへ返す。当面の実体は本エントリ本文の1〜7と
  `--plan-only`による事前確認運用である。
- 再発検知: 変異matrix投入前に`--plan-only`で事前確認する運用と、DW-M07を段6条件15の
  発火時に必ず再読する規律 (本fragment自身がその実例)。

## 再発

### F461

- **再発: 2026-08-22** — [T-1472] wave の段6変異matrixで、`--wrapper-attempt`単独指定
  (`--attempt-out`省略) により同一の `mutation worktree aborted: --attempt-out と
  --wrapper-attempt は同時指定が必要` に当たった。根本原因は、DW-M07 (F461の恒久対応で
  追記済み) を段6の変異matrix投入前に読まなかったこと — 条件dispatch表の条件15
  (「fix後に変異を走らせる直前」) が本waveでも成立していた (段6でfix1を実施済み) にも
  関わらず、走らせる直前の再評価を怠った。
