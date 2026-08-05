実装は指定 3 ファイルだけに閉じ、commit・docs 編集・qsub/qstat は行っていません。計算ノード実走が必要な項目は、継承契約に従って `partial` としています。

### F1〜F7 対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| F1 compile argv | `partial` | ycsb object を exact-one 選択し、`result.cc` / `util.cc` も検査: [probe.sh:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.sh:50)、実 argv 由来 summary: [probe.sh:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.sh:96)、正例・欠落・重複 fixture: [probe.sh:265](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.sh:265)。self-check 緑だが実 compile DB は未実走。 |
| F2 liveness 起点・終端 | `partial` | worker-local の最初の `TxExecutor::begin()` で起点固定: [patch:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control.patch:69)、[patch:114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control.patch:114)。固定 `[0,1500ms)` / `[1500,3000ms)`、3秒以後無出力: [patch:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control.patch:88)。patch dry-run 緑、本体未実走。 |
| F3 status fail-open | `partial` | main、dependency、third-party、CCBench の status rc を空判定前に確定: [PBS:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:74)、[PBS:165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:165)。PBS 未実走。 |
| F4 commit 束縛 | `partial` | `RUN_COMMIT` 一回固定・clean拒否: [PBS:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:29)。5 blobをcommitからbundle化: [PBS:95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:95)。実行中PBS hash照合: [PBS:120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:120)。commit後PBS未実走。 |
| F5 pin 閉包 | `partial` | 共通のpin/clean/replace-ref/index-bit/shallow/alternate検査: [PBS:152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:152)。third-party tracked snapshot: [PBS:239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:239)。CCBench gitlink照合と非archive snapshot: [PBS:256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:256)。依存E2E未実走。 |
| F6 閉表・state | `partial` | EXIT trap による atomic terminal state: [PBS:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:40)。性能開始marker: [probe.sh:468](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.sh:468)。correctness/liveness/true/false/post states: [probe.sh:409](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.sh:409)、[probe.sh:448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.sh:448)、[probe.sh:559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.sh:559)。科学的falseはrc=0。PBS未実走。 |
| F7 副次診断 | `partial` | TPSを先にprimaryへ確定: [probe.sh:498](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.sh:498)。診断失敗は`NA`と理由のみ: [probe.sh:506](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.sh:506)。実benchmark log未実走。 |

F2 の seam は `TxExecutor::begin()` です。YCSBではrunnerのstart barrier解放後、各試行の処理開始時に必ず呼ばれるため、走行開始に十分近く、成功commitより前の時点を保証します。

### 変更と波及

- [patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control.patch:1): transaction試行起点の固定2窓。
- [driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.sh:1): 3 source compile receipt、state閉表、TPS/診断分離。
- [PBS](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:1): commit bundle、pin閉包、atomic EXIT state。

callerには、新たに `IZANAGI_T139_PREREGISTRATION_RELATIVE_PATH` が必要です。値は統合commit内の、basenameが `s4-adjudication.md` である事前登録文書を指す必要があります。現在のrepo外 `s4-adjudication.md` のままではPBSは意図どおり拒否するため、親の段7統合が必要です。

consumer側では `compile-argv.tsv` がarm単位からarm×source単位へ、`diagnostics.tsv` が理由列付きへ変わり、`state/phase.tsv` と `state/terminal-state.tsv` が追加されます。共有fixture・docs・policy・submodule本体は未変更です。

F3と同型で追加修正した箇所は、main/dependency/third-party/CCBenchのstatus取得、nm countのread failure、副次診断の`sed` failureです。

### 検査結果

- driver / PBS `bash -n`: rc=0
- CCBenchコピー `/tmp/t139-patch-dry-run.4lauqy` への `patch -p1 --dry-run --forward`: rc=0
- `probe.sh --self-check`: rc=0
  - verdict 正例 accepted / 負例 rejected
  - row構造 正例 accepted / 負例 rejected
  - liveness 正例 accepted / 負例 rejected
  - 4 transaction entry JSON accepted
  - ycsb entry欠落 rejected
  - ycsb entry重複 rejected
- `git diff --check`: rc=0
- 最終status: 指定3ファイルのみmodified

未実施:

- `python3 tools/check_docs.py`
- `python3 tools/check_codex_agents.py`
- CCBench build、実compile DB/nm/liveness、dependency/PBS E2E、benchmark、pytest
- qsub/qstat、commit、provenance監査

`hostname=pegasus02` であり、`check_docs.py` はrunbook上login側`unknown`、build/test/benchmarkも計算ノード専用です。qsub禁止との両方を守るため実行しておらず、緑とは報告しません。

想定回帰は、事前登録文書のcommit内配置と新envが未設定なら投入が拒否されること、PBS spool bytesがcommit blobから変形される環境ではhash照合で拒否されること、compile/diagnostics/state TSVの手動consumer更新が必要なことです。またC++本体build未実施のため、patchのコンパイル回帰余地は残ります。一時copyはsandboxが削除操作を拒否したため `/tmp/t139-patch-dry-run.4lauqy` に残っています。

## 総括

F1〜F7のroot causeに対するコード修正と指定の軽量検査は完了しました。`regressed` と判定した所見はありません。ただし計算ノード実走が禁止された実装子契約に従い、7件とも最終状態は `partial（実装済み・E2E未実走）` です。