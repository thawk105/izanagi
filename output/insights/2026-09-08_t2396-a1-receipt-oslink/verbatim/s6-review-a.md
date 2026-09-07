## 所見

### 所見 1: 宛先確認と staging 撤去の間の競走で、最後の link を依然として削除できる

- 深刻度: 致命的
- must-fix か nit か: must-fix
- 根拠 (`file:line`): [paper_story_a1_paired.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink/orchestrator/campaign/paper_story_a1_paired.py:865):865-898、[s4-adjudication.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2396-a1-receipt-oslink/artifacts/s4-adjudication.md:17):17-20,112-117
- 事象の並び:

  1. `os.link` により staging と destination が inode I を指す。
  2. 最初の parent fsync が完了する。
  3. cleanup が `destination.lstat()` を実行し、destination が inode I であることを確認する。
  4. 直後に第三者が `unlink(staging)`、`rename(destination, staging)` を実行する。inode I の最後の名前は staging になる。
  5. cleanup の次の `staging.lstat()` は regular fileかつ inode I と判定する。
  6. `os.unlink(staging)` が最後の link を削除する。
  7. 二度目の parent fsync も成功し、publisher は例外なく成功する。
  8. [paper_story_a1_paired.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink/orchestrator/campaign/paper_story_a1_paired.py:3304):3304-3315、3408-3409、4324-4326、4413-4415 の全 caller が成功終了しうる。

- 放置時の成果物影響: submission では3 jobが参照する group receipt が消えて bench 開始不能となり、completion では materialize が参照を解決できず、certified 選択結果と材料レポートは受理されず、試行台帳には intent や job 成果だけが残る。
- 提案: destination の事前 `lstat` を増やすだけでは閉じない。宛先確認と unlink の間に writer が入れない排他契約を設けるか、開いた inode と回復用 link を保持して unlink 後に destination を再検証し、消失時には bytes を名前付きで保存して専用例外にする必要がある。少なくとも `destination.lstat()` の返却直後に上記移動を注入する負例を追加する。
- 推測か実証か: コード上の syscall 順と成功終了は静的に実証できる。実機で競走が発生する頻度は未実測。

### 所見 2: A-1 の同一 inode 移動テストは `os.link` seam を通らなくても緑になりうる

- 深刻度: 中
- must-fix か nit か: nit
- 根拠 (`file:line`): [test_paper_story_a1_job_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink/orchestrator/tests/test_paper_story_a1_job_contract.py:2643):2643-2675
- 事象の並び:

  1. テストは `os.link` を monkeypatch するが、呼出し回数を記録しない。
  2. publisher を「canonical staging 作成直後に `PaperStoryError` を送出する」実装へ壊す。
  3. `with pytest.raises(PaperStoryError)` は成立する。
  4. staging は expected bytes のまま残るため、`preserved` と bytes の assert も成立する。
  5. monkeypatch した同一 inode 移動 seam は一度も通っていない。

- 提案: link 呼出しを記録して厳密に1回を要求し、例外型も `_PublishedReceiptCleanupError` に限定する。所見1の `destination.lstat` 後の競走は別テストとして追加する。
- 推測か実証か: このテスト単体を通る具体的な変異を静的に実証できる。ほかの正例テストまで含む全 suite が緑になるという主張ではない。

### 所見 3: link 後の最初の parent fsync 失敗は公開済み専用例外を通らない

- 深刻度: 中
- must-fix か nit か: nit
- 根拠 (`file:line`): [paper_story_a1_paired.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink/orchestrator/campaign/paper_story_a1_paired.py:926):926-940、3304-3314、8722-8734
- 事象の並び:

  1. `os.link` が成功し、`published=True` になる。
  2. line 927 の `_fsync_directory` が `OSError` を送出する。
  3. `finally` の staging cleanup が成功すると、元の生の `OSError` が再送出される。
  4. `_run_submit_v3` の `_PublishedReceiptCleanupError` と `PaperStoryError` の両 catch を通過する。
  5. `main` も `PaperStoryError` しか捕捉しないため、公開済みであることを示す管理された診断ではなく traceback になる。
  6. 投影されたテストは、最初の fsync のこの分岐を注入していない。

- 提案: link 成功後の fsync 失敗を「公開済みだが durability 不明」の専用 `PaperStoryError` 系へ変換し、v3 では failure receipt を書かない catch に含める。最初の fsync だけを失敗させる submit と completion の負例を追加する。
- 推測か実証か: 生の `OSError` が catch を通過することは静的実証。crash 後に directory entry が残るかは filesystem 依存なので推測。

### 所見 4: 事象順テストは `_fsync_directory` 内の実 fsync 消失を検出しない

- 深刻度: 低
- must-fix か nit か: nit
- 根拠 (`file:line`): [test_paper_story_a1_job_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink/orchestrator/tests/test_paper_story_a1_job_contract.py:2713):2713-2751、[paper_story_a1_paired.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink/orchestrator/campaign/paper_story_a1_paired.py:8071):8071-8079
- 事象の並び:

  1. テストは `_fsync_directory` 全体を event recorder に置換する。
  2. 実装から line 8077 の `os.fsync(fd)` を削除しても、recorder は従来どおり `fsync` event を記録する。
  3. `link -> fsync -> unlink -> fsync` のリスト比較は緑のままになる。
  4. したがって呼出し削除と順序入替えは殺すが、実際の directory fsync 性は固定しない。

- 提案: `_fsync_directory` は置換せず、`os.fsync` を委譲型 spy にして directory fd の2回の fsync と順序を観測する焦点テストを追加する。
- 推測か実証か: 投影されたテスト本文について静的実証。現在の production helper 自体には実 `os.fsync` が存在する。

## 境界別の照合

- A-1: `published=False` では line 865 の宛先分岐に入らず、staging identity のみで cleanup する。既存先拒否テストも staging 不在を要求するため、誤って宛先 identity を要求する退行は検出できる。ただし `destination.lstat` と `os.unlink(staging)` が原子的でなく、所見1が残る。
- A-2: v3 は `_PublishedReceiptCleanupError` を広い `PaperStoryError` より先に捕捉し、`submission-failure.json` writer を通さない。legacy submit と両 completion caller は専用例外をそのまま上へ返し、failure receipt writer を呼ばない。最終 CLI 境界では message を stderr に出して rc 2 にするため、silent success ではない。狭義の cleanup failure 分岐は成立するが、所見3の link 後 fsync 例外は別経路として残る。
- create-only: 完成名の作成箇所は `os.link(staging, path, follow_symlinks=False)` のみである。`FileExistsError` とそれ以外の `OSError` はどちらも `PaperStoryError` となり、成功扱いの分岐はない。`published=False` cleanup は destination を操作しないため、安定した parent という裁定済み境界では既存 bytes を変更しない。
- 部分公開: submission と completion の両方で、canonical bytes の全 write と file fsync が `_exclusive_write_bytes` 内で完了した後にだけ final link を作る。completion の v3 と legacy の両 callerも共通 publisher だけを使用する。write/fsync 失敗で partial staging が残る既知問題は裁定 B-1 の scope 外であり、partial final は作らない。
- 事象順: 成功経路の production は line 917,927,897-898 の順で `link -> destination parent fsync -> staging unlink -> parent fsync` になっている。テストも回数だけでなく event 列全体を比較する。ただし実 fsync の存在には所見4の盲点がある。
- `_PublishedReceiptCleanupError` の参照は定義、publisher での生成、v3 の専用 catch、焦点テストに限られる。途中で成功値へ変換する箇所はない。

## 既存7テストの弱体化検査

| テスト | 守る性質 | 静的照合 |
|---|---|---|
| `test_m1_submission_receipt_is_complete_before_final_path_is_visible` | 完成済み canonical staging からのみ公開 | rename seam を実 link seam へ置換し、呼出し1回と staging 撤去を追加。緩和なし |
| `test_m2_submission_receipt_publish_is_no_replace` | 既存 bytes 不変と空き先成功 | regex は `no-replace` から既存 prefix 全体へ強化。両分岐に staging 不在を追加 |
| `test_m3_submit_rejects_existing_completion_before_intent_and_qsub` | completion 既存時に intent と qsub より前で拒否 | `pytest.raises`、intent 不在、qsub 0回を維持 |
| `test_m4_submit_rejects_existing_stdout_before_intent_and_qsub` | stdout 既存時の事前拒否 | 期待 message、intent 不在、qsub 0回を維持 |
| `test_m5_submit_rejects_existing_stderr_before_intent_and_qsub` | stderr 既存時の事前拒否 | 期待 message、intent 不在、qsub 0回を維持 |
| `test_m6_submit_accepts_clean_evidence_namespace` | clean namespace の受理 | rc 0、qsub 1回、intent と receipt の存在を維持 |
| `test_m7_submit_creates_missing_durable_base` | durable base 不在時の正例 | base 作成、qsub 1回、intent と receipt の存在を維持 |

期待値の反転、assert 削除、skip、xfail、例外許容の拡張は既存7本にはない。追加 completion 負例の広い `pytest.raises(PaperStoryError)` は、exact 英語 message を pin しない裁定 A-6 に沿う。完全な恒真テストは見つからないが、個別の seam 未通過変異は所見2、fsync 実体の変異は所見4のとおり生存する。

## 受理集合の変化

| 事象 | 実装前 | 実装後 | 裁定 |
|---|---|---|---|
| submission で `RENAME_NOREPLACE` が `EINVAL`、同じ場所の hard link は成功 | 拒否 | 受理 | 本 wave の中心目的として承認済み |
| completion で final の `O_EXCL` create は成功するが hard link は拒否される filesystem | 受理 | 拒否 | submission/completion 共通 hard-link publisher の採用に伴う承認済み変更 |
| final 不在だが現在 PID の completion staging `.c-<pid>` が既存 | completion を受理しうる | staging create で拒否 | 裁定 B-4 で既知かつ次 cycle 送り |
| link 成功後の staging cleanup failure | post-publish cleanup 自体がなかった | final を残して非ゼロ | 裁定 A-2 が明示的に承認 |
| 公開後に destination が不在または別 inode | 対応する hard-link cleanup 経路なし | staging を残して拒否 | 裁定 A-1 が承認 |
| destination identity 確認直後に destination を staging へ移動 | 対応する post-publish cleanup なし | receipt を消したまま成功しうる | 未承認。所見1 |

既存 final、symlink、directory entry への公開は引き続き拒否され、通常の `FileExistsError` 分岐で既存 bytes を変更する受理拡大はない。

## 総括

must-fix は次の1件です。

- 所見1: destination identity 確認後の競走により、cleanup が公開済み receipt の最後の link を消して成功終了できる。

A-1 の不変条件が閉じていないため、この実装をこのまま受け入れてはいけません。pytest は実行しておらず、緑は主張しません。