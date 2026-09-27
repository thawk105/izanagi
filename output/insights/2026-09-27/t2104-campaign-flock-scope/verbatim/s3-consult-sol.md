## 所見

1. **must-fix — path 不一致の拒否が認可消費より遅い。** `orchestrator/campaign/p3_s4_loop.py:3181,3216-3232` は B-4 receipt の消費記録を公開してから `run_campaign` に進む。一方、plan の保持 handle 照合は `orchestrator/campaign/loop.py:723-730` に置かれる。注入 layout 等で path が違えば、そこで拒否されても消費は取り消せない。さらに `run_campaign` の環境認可・perf preflight は `:692-723` で照合より先に走る。**成果物影響:** 再試行できない arm が欠測となり、block score・verdict が変わりうる。**推奨:** driver で実行先の authoritative layout と producer の lock path を認可消費前に照合する。`run_campaign` 側の照合も残す。消費記録が存在しないことまで確認する負例を置く。

2. **must-fix — 53/53 の同居実測は flock path の一致を測っていない。** `probe_colocation.py:19-34` は `loop_state.json` のある campaign を母集合にし、同じ root の `runs/wal.jsonl` の有無だけを数える。B-4 に限定せず、実際の `campaign_lock_path` と producer の `_execution_lock_for_root` は呼ばない。`orchestrator/campaign/layout.py:62-68,375-414` では hash に使う root と lock directory の base が別入力であり、producer は `p3_b4_raw_record_producer.py:1329-1343` で root の字面から明示 base を復元する。特に環境 base の正規化、明示 base、symlink・注入 layout で差が出る余地がある。**成果物影響:** driver の flock 中も producer が別 lock を取得し、`terminal-record-absent` を封印しうる。**推奨:** 実 B-4 形の root で driver・`run_campaign`・producer の三つの path を直接比較する負例を置き、本番で許す入力の一致条件を明示する。53/53 は同居実例としてのみ扱う。

3. **must-fix — handle の同一 process 性が設計にない。** plan の path・active・fd・inode 検査は、`fork` 後に継承された handle と fd でも通りうる。`orchestrator/campaign/lock.py:76-89` の flock は fd が指す open-file description に結び付くため、子が継承 handle を渡して自前取得を省けば、親子が同じ所有権で並走できる。子で context を閉じれば親の保持まで解除しうる。既存の `test_campaign.py:3072-3104` は別取得の拒否を検査するが、継承 handle の受け渡しは検査しない。**成果物影響:** 並走中に producer が lock を取得可能となり、欠測・score・verdict が変わりうる。**推奨:** 取得 PID と発行元を handle に束縛し、受け渡し時に現 PID と発行済みの active handle を確認する。解放後・fd 再利用後・fork 子での受け渡しを個別に拒否する test を置く。

4. **should — main の負例が保持期間の終端を証明しない。** plan の main test は最初の事前認可中の probe と、`drive_iteration` spy への同一 handle 引数を確認する。しかし `p3_s4_loop.py:3931-3947` の spy が実 driver を置換すると、checkout 後から checkpoint 完了まで flock が生きているかは未検査になる。**成果物影響:** main 経路で早く解放する変異が緑のまま残り、B-4 記録の欠測を防げない。**推奨:** spy 内でも producer の path と実 `campaign_lock` による競合を確認し、戻り後の再取得成功を確認する。認可・preflight・通常／入口停止 checkpoint の各 probe は到達回数を独立に検査する。

5. **should — 変異表は赤理由をまだ一意にしていない。** `p3_s4_loop.py:2467-2495,2535-2559` には preflight・quarantine の別の拒否層があり、`run_campaign` 受け渡し欠落変異も実体へ到達しなければ二重取得で赤にならない。plan の「重い build 以下を seam で止める」だけでは、各 node が狙った競合で落ちる保証はない。**成果物影響:** 機構を通らない緑、または別 gate による赤を修正の証拠と誤認し、欠測経路が残る。**推奨:** 各変異について probe 到達、実 `campaign_lock`・producer path 使用、失敗例外と同期点を記録し、旧コードでの赤理由を個別に確認する。テスト実走の判定は親が行う。

6. **nit — brief の path 表記は不正確。** `brief.md:18` の `<output_root>/<use_class>/campaign-locks` は `layout.py:51-68,455-463` の式と異なる。明示 `output_root` では `<output_root>/campaign-locks` である。**成果物影響:** 誤った directory で照合 test を作ると、実際の producer 競合を検査できず、B-4 の欠測・score・verdict を守ったと誤認する。**推奨:** brief の表記を実式に合わせる。

## 裁定パッケージ候補（今回の実装 scope 外）

- `p3_s4_loop_sort.py:524` と `p3_s4_loop_trigger_gating.py:1005` にも、認可から checkpoint までの同型の窓がある。事前登録の対象は `docs/phase3-b4-reflux-ablation-preregistration.md:158` の base なので今回の変更対象外とする判断は妥当だが、対象 driver を広げる裁定時には別途閉じる必要がある。
- `p3_b4_raw_record_producer.py:62` の「内側区間しか覆わない」という非保証文は、新しい base 実行の説明としては古くなる。旧記録との区別を付ける更新は別裁定とする。

## 総括

- **P1:** 条件付き賛成。明示受け渡しは再入拒否契約（`test_campaign.py:3072-3083`）と両立するが、発行元・PID・生存の確認が必要。
- **P2:** 賛成。base が事前登録対象。兄弟 driver の窓は裁定パッケージ候補。
- **P3:** 条件付き賛成。提案区間は通常終了・入口停止・例外時の解放を覆える。path 不一致を認可消費前に拒否する条件が欠ける。
- **P4:** 賛成。ただし「競合時は消費前に止まる」は path 一致が前提。
- **P5:** 条件付き賛成。今回 producer を触らない scope と整合するが、新 base の説明としては陳腐化する。
- **must-fix:** ①消費前の path 照合、②三者の実 lock path 一致の検証、③handle の同一 process 性。
- **残る穴:** 53/53 は B-4 flock path の証明ではない。main の保持終端と変異の単一赤理由も、計画どおりのテストが実装・実走されるまで未確定。静的検査のみを行い、テストは実行していない。