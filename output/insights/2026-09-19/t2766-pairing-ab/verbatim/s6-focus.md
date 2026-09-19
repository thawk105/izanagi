## 所見対応表

静的レビューです。pytest・selftest・測定は実行していません。集計器の SHA256 は指定どおり `4ca646b32fa98bd3d7cb8971f776bbe0d8a8942187c39fa924a0762d36c73935` でした。

以下、**集**＝[t2766_ab_analyze.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2766-pairing-ab/probe/t2766_ab_analyze.py)、**起**＝[run-measure.sh](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2766-pairing-ab/run-measure.sh)。行番号は修正後のものです。

| 所見 ID | 判定 | 根拠行・引用 | 残る差分 |
|---|---|---|---|
| A-must2 | **closed** | 集197–218：連続 scope を unit 列へまとめ、`"second_unit": sequence[1]` と `second_item_in_worker_sequence` を分離。553–570に partner／非partnerの正負例。 | なし。実行列の復元という限定もある。 |
| A-should4 | **partial** | 集395–405：`duplicate run number`、`run number gap` を拒否。356–387：期待順序と slot を検査し、有効対だけ `valid_count += 1`。 | 番号順は検査するが、記録された投入時刻との一致・実際の時間的隣接性は検査しない。欠番等は除外表ではなく集計全体のエラーになる。 |
| A-should5 | **closed** | 集128–133：ソート後の要素ごとに `math.isclose(... rel_tol=1e-9, abs_tol=1e-9)`。183–190：cardinality 別の head 比較と partner 比較。571–596：許容／拒否境界例。 | 許容差内の cost 差は区別しない、という固定された精度限界。 |
| B-M1 | **closed** | 起41–42：`exec 9>`、`flock -n 9`。門番開始は59行、同期実行は83行、保存は91–138行、終了は140行。 | 同じロックを使う launcher 間の通常動作について成立。ロックを使わない直接投入まで排除する仕組みではない。 |
| B-M2 | **closed** | 起17で tip 固定、73–76で投入直前照合、87–88で終了後採取。集282–287：前後 SHA と厳密な整数の dirty=0 を要求。820–821：測定 tip のCLI指定必須。 | 前後観測間に変更して元へ戻す操作や、ignored ファイルの変化までは検出しない。 |
| B-M3 | **regressed** | 起26–29：既存確認・`mkdir -p`・pid保存がロックより前。42行：ロック拒否時に同じ RUN へ `measure.done=94`。集395–427：残った番号付きディレクトリを走として取り込む。 | 新設されたロック拒否経路が未投入 attempt を系列へ混入させる。同一 NN/条件の同時起動では既存確認も競合する。詳細は後述。fix 前後の系列・12走上限の扱いも未固定。 |
| B-M4 | **partial** | 起100–103：必須成果物を複製して hash 比較。131–132：相対 `session` と boolean `copy_ok`。集295–307：保存成否・相対パス・全3 shardを検査。 | 起139–140は依然 `echo "$rc"`／`exit "$rc"`。子rc=0なら複製失敗でも成功終了する。JSON生成失敗も終了コードへ反映しない。 |
| B-S1 | **closed** | 集83で testcase `time` を保持、203で unit ごとに加算、224–227で `ledger_max_units` と `measured_longest_units` を分離。 | 実測値はJUnit testcase時間の合計。workerの律速性そのものを証明する値ではない。 |
| B-S2 | **closed** | 集21–22：`初期配布の送信順ではない`。208・215–218：unit列、2個目のunit、2個目のitem、同一unit内かを別出力。 | なし。送信時刻・prefetchの観測とは扱っていない。 |
| B-S3 | **closed** | 起23–25で閾値固定、55行：`leaders <= lmax and l1 < l1max`。8行で検索対象を限定、135–136で閾値・検索式を保存。 | 観測対象外の直接投入や、実行中の共有FS負荷を制御した証拠にはならない。 |
| B-S4 | **partial** | 親裁定 HANDOFF:10で `output/pegasus-dispatch/` を例外化。起46の `git status --porcelain ...`、集285–287で許容外dirtyを除外。 | 実際の制御ディレクトリの残置・ignore状態を各走で記録していない。Git cleanだけでは、output走査を含む同一入力の証明にならない。 |

**A-must1 の裁定：条件付きで妥当。** 「局所検査」と明記して測定へ進む判断は可能ですが、A/B実受入の緑は「実 shard 選択を含む A/B selected・digest 同一性の統合検査済み」の代替にはなりません。README本文は今回の射影にないため、記載完了は未確認です。

## run.json 契約と前後照合

**通常の保存完了経路では、要求されたフィールドの名前・型・意味は一致しています。**

| フィールド | launcher出力 | 集計器の扱い |
|---|---|---|
| `condition` | 起127：文字列 A/B | 集279–281：値とディレクトリ末尾を照合 |
| `tip_sha` / `tip_sha_after` | 起128：文字列 | 集282–284：両方をCLI測定tipと照合 |
| `dirty_lines_before/after` | 起134：整数 | 集285–287：`type(...) is int`、値0 |
| `pair_slot` | 起127：整数 | 集363–366：存在時に厳密な整数・期待slotを照合 |
| `rc` / `env` | 起133：整数／文字列値の辞書 | 集288–294：rcとA/B opt-inを照合 |
| `session_dir` / `copy_ok` | 起131–132：成功時 `"session"`／`true`、失敗時 `null`／`false` | 集295–306：成功条件を要求し、失敗は無効化 |
| `session_dir_origin` | 起132：元パスまたはnull | 表示用。集計元には使わない |

`session_dir=null` は保存失敗の記録として整合しており、契約不一致ではありません。`measurement_tip` は表示用で、判定の正本はCLI引数です。

ただし、**投入前停止では `run.json` 自体が生成されません**。また、JSON生成のPythonが失敗しても起139–140が子rcを返します。通常走のフィールド契約は一致しますが、全終了経路の記録契約は閉じていません。

## 直列化・順序・新たな欠陥

**fd 9 の継承自体は問題ありません。** launcherはロックを取得してから門番を開始し、同期的な `run_tests.py` の終了後も成果物保存までfdを保持します。子がfdを保持する間、次のlauncherを拒否する動作は直列化の意図に一致します。`flock -n` なので、次走は待機ではなく終了コード94で拒否されます。これは計算ノード上のジョブへロックfdがそのまま転送されることを意味しません。

新たな欠陥は**ロック前のRUN作成**です。

- 別NNの重複起動でも、ロック拒否された未投入RUNが残ります。集395–427はこれを無効走として取り込み、12走枠と隣接対の構成に含めます。「測定走上限12」と未投入attemptの関係が未定義です。
- 同じNN/条件の2本が起26の存在確認をともに通過すると、`mkdir -p` は両方成功できます。敗者が同じ `measure.pid`、`chain.log`、`measure.done` に書き込み、実行中の勝者の記録へ干渉できます。

ロックをRUN作成より前に取得し、新規ディレクトリ作成を原子的に拒否できる形にする必要があります。未投入停止をどこへ記録し、測定番号・上限へどう数えるかも固定が必要です。

**「無効対はslotを消費しない」は、段4の「無効対は同順序で追加」と一致します。** 例えば初回AB対が無効なら、

`01-A,02-B〔slot1・無効〕 → 03-A,04-B〔slot1〕 → 05-B,06-A〔slot2〕 → 07-A,08-B〔slot3〕`

となります。集769–776にも同型の検査があります。親は各対の有効性を確認してから次slotへ進む必要があります。

一方、手入力NNと実投入順の一致は未検算です。例えば実際には `02-B`、`01-A` の順で完走させても、集計器は番号で並べ直してABとして扱います。投入・終了時刻との照合が必要です。また、段4:48のfix後取り直しについて、旧系列を保存したうえで新tip系列をどう開始し、上限を共有するかは残っています。

## warm-up の評価

[run-warm2.sh](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2766-pairing-ab/run-warm2.sh:11) は `PYTHONDONTWRITEBYTECODE=` をexportし、collect-onlyを実行します。dispatchのallowlistに同変数があり、requested envの適用後に [dispatch_compute.py:1855](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2766-pairing-ab/tools/pegasus/dispatch_compute.py:1855) が `setdefault(..., "1")` を行うため、**空文字が既定値で上書きされない方式は成立**しています。

共有FS上の同じソース・互換Python/pytestから使えるpycを事前生成する方式として、A/B片側だけを温める構造ではありません。countファイルは391を確認しました。うちpytest書換364という内訳は依頼本文の情報で、countファイル単独では再確認できません。

ただし、次の限定があります。

- pycの存在は、A/Bのpage cache・fixture等を含む同じwarm状態の保証ではありません。
- collect-onlyのbytecode生成を理由に受理集合が変わる経路は、指定資料では確認できません。ただし、実selectedのA/B同一性をこのwarm-up記録が証明するわけではありません。
- **測定走で同変数が未設定であることは、launcher単独では保証していません。** 起30–36はpairing変数だけを整理し、83行は環境を継承します。warm-upを別スクリプトとして実行したexportは親へ逆流しませんが、測定起動元に空文字があれば継承され、computeの既定 `"1"` は効きません。起82の記録も `IZANAGI_` のみです。

測定launcherで同変数を明示的にunsetし、その状態を記録すれば、「測定走には渡さずcompute既定1」という契約を閉じられます。

## 総括

対象11件は **closed 7件／partial 3件／regressed 1件**。A-must1の裁定評価は別枠です。

**NO-GO。** 主な投入前修正は、ロック前RUN作成による記録衝突・未投入attempt混入の解消と、複製／JSON保存失敗の非ゼロ終了です。併せて、実投入順の照合、未投入停止・fix後系列の計数規則、測定時bytecode環境の固定を閉じる必要があります。