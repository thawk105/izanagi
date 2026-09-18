---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-18
wave: dev-wave-t2686-recovery-codex
seq: 1
---

## {{D:exact-state-union-walk}}. exact-state の候補取得を遅延 union walk へ束ね、証拠の照合規則は維持する

**決定:** 同一assessment内でmain tipに一致しない要求pathだけを登録し、full-historyのunion logから
path別候補を初出順で得る。mergeの親別entryはcommit単位で合併し、各pathは従来と同じlimit+1件まで
照合する。正証拠優先（D2123）、tree再確認、closed-world負判定、spool receipt、deadlineは変更しない。
nameはbytesで保持し、rename/root/gitlinkの表示設定を固定する。入力域はraw diff由来の正規化tree path。

初回走査の上限は(limit+1)×path数。上限まで読み、必要prefixが揃わなければ同じGit/deadlineで一度だけ
無制限走査し結果を置換する。log.follow=trueまたはargv path部64KiB超では従来per-pathを遅延実行する。
64KiBはpath部の予算で残りを固定argv/environment等に残すための閾値であり、旧s4の
「固定費を足しても128KiBの半分未満」は算術誤りとして訂正する。閾値自体は受理述語を変えない。

**理由:** 起票時のclosure/introduced-states律速は差引推定で、旧profileの直接計測では合計約2.3秒、
assessment約372秒の主な待ちはpath logだった。この標本で優先順位を変更したのであり、closure改善一般を
無益としない。既存の証拠範囲を減らさずGit processの重複を減らす局所変更とする。

**主張の限界:** 正常完了した候補列・payloadの同一性を実測範囲で検査する。全DAG/全configの同一性や
時間内完走集合の保存、時間の非退行は証明しない。片側だけtimeoutする入力はあり得る（D2106と同じ区別）。
timingのwalk秒数は初回unit elapsedにも含まれるので加算しない。fallbackでは要求されたpathだけを数える。

**採らない案:** first-parent等で候補を減らす、any-path/観測証拠を正証拠へ昇格する、timeoutや候補上限を
緩める、汎用cache/並列化/新gateを足す、赤を期待値変更で消す。観測wrapperはdiffとlogを区別する。
