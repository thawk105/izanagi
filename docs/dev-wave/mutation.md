# dev-wave 変異検査契約

変異事前登録、kill 意味論、harness、fix 後再検証の正本。

## DW-M01 — 事前登録と単一理由性

変異は実装前に登録する。段 4 は B-057、段 6 の real 所見は fix 前。各変異は位置と、同じ
入力を拒否する層が前後にも内側にも無く赤理由が一つに絞れることを実装後に確認し（F820）、
できなければ登録せず実効 gate へ再照準する（F28）。未知 key を持つ spec は起動前に中止。受理集合を縮小する wave は承認外の過剰拒否の
正例も、テスト強化だけの wave は `DW-M08` の新旧両走も登録する。

## DW-M02 — 所見ゼロの裏取り

レビュー所見ゼロを変異なしで緑と数えない。変異が生存したらまず他層の mask と等価変異を疑い、実効 gate へ再照準して両層同時変異まで裏取りする。初回結果は消さず erratum に残す。

## DW-M03 — kill の意味と fixture

kill は受理集合か fail-closed 挙動が期待方向へ変わったときだけ数え、診断文字列だけの赤を kill に
しない。fixture が単一理由か確認し、過剰決定なら単一理由へ差し替えるか、冗長 gate と明記して
単独変異の証拠から外す。

## DW-M04 — 置換と注入実在

置換対象が一箇所でなければ停止し、注入なしを緑と報告しない。同一ファイルの複数置換は累積適用し、
置換ごとに累積後の一意性を assert する。SURVIVED は mutated 内容の diff で注入実在を確認するまで
equivalent としない。両層変異は kill 期待を必ず事前登録する（F33）。

## DW-M05 — 復元と単一走行

変異harnessは`tools/mutation_harness.py`を使う。同toolは元ソースの固定HEAD束縛、起動/復元時の
内容比較、`flock`単一走行、逐次flush、HEAD/spec束縛の`--resume`、signal復元をfail-closedで
強制する（F32）。独自harnessは同等検査を備えると段4で事前登録する。
変異中は親の編集とworktreeへ書きうる子の起動を止める。起動前に総所要を見積り、外側の
実行時間上限内の経路で起動する。この2点はtoolが検証不能な親の自己申告義務。
生存process照合はERE/literalで`\|`を避け、worktree pathで待ち手自身と並行waveの子を除く。
final の待ちは job dir で確定済み本文と検査の準備に充てる（未測定欄・placeholder 禁止）。

## DW-M06 — hang 変異

local hangは`hang_risk`と`hang_timeout_seconds`へ隔離、timeoutはfail-open証拠（F32）。
dispatch短hang値は外側で使わずwalltimeへ委譲。rc=16はkillとせず、既存hold条件時のみhold・変異を残す。

## DW-M07 — fix 後 anchor

source-repoはD1009の独立clone(main=対象commit)。本走前にfix最終commitでold逐語anchor・期待nodeを再検証。
mask再照準・erratumは`DW-M02`で台帳へ。本走は`--runner-mode dispatch`既定、argvへ`--force-dispatch`。
localはspec不問でlogin拒否、runner変異は収集`rc=16`。
`--attempt-out`/`--wrapper-attempt`はdispatch専用必須ペア、後者は正整数。実走は`--detached`。
再投入は両方変更、`--resume`は前回sidecarを新pathへ複写(空file中止、F453)。
KILLED期待のnode空は中止。probeは全件SURVIVEDで観測nodeを集める。
`--spec`/`--out`/`--attempt-out`はcheckout外(rc=2)。outはscratch-rootと同一device(rename条件)。
dispatch外側実効値=max(spec,前段+queue+walltime+grace+回収+cleanupの予算)。不足は理由付き診断、
collectionの既存Q+G gateは元specで維持。有限の余裕は任意の遅延を保証しない。

## DW-M08 — 失敗 node と検出力

harness は rc と失敗 node を毎回記録する。pytest は `-rf`、node 抽出は F71 に従う
（rc≠0 で 0 件は fail-closed 停止）。
**期待 node は完全集合**で、同形式へ正規化した記録 node との完全一致だけを KILLED とする（F33）。
期待 node は login self-run（変異ごとに注入 → 自走 harness → `DW-O19` で復元し sha256 も照合）で
観測し dispatch final を 1 回。適用は自走の node 集合（FAIL + ERROR）が `--collect-only` と一致し
login 実行が許される file に限り、pytest 専用 allowlist・parametrize・conftest / autouse fixture・
環境変数・import 副作用に依存する test は dispatch probe（初回を probe と明記）へ戻す。
受理集合を変えず構造化シグナルだけを pin する変異は kill でなく diagnostic sensitivity pin へ
別枠記録する。テスト強化だけの wave は新旧 HEAD の双方へ変異を走らせ、新テストだけが検出する差分を示す。
