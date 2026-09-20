## 所見 (R-1 …)

静的照合の結果、**数表の取り違えは見つからなかったが、限定の継承・変更関数の説明・記録の量化語に修正が必要**。以下では、レビュー対象 results を「稿」、本 wave の `output/insights/2026-09-20/t2792-a1-sized-attempt2/README.md` を「insight」と略記する。

**R-1 / 対象: 稿 §3 冒頭、README 追加行 / 主張:** attempt-0001 の限定20件を「そのまま」継承できない。

根拠: attempt-0001 稿の L-A1S-4 は「attempt-0001 が 1 本あるだけ」、L-A1S-16 は「bnode107〜109」を含む。attempt-0002 の `receipt.json` は bnode035 / 039 / 040。現行の但し書きは L-A1S-18 と L-A1S-20 しか読み替えていない。L-A1S-4、10、18、20という参照番号自体は正しい。

放置時の影響: **attempt-0002 の限定として、旧 attempt の本数・測定 node を誤って継承する。**

分類: **must-fix**。

是正案:

> 「attempt-0001 稿の L-A1S-1〜L-A1S-20 は、attempt-0002 についても番号の対応する内容がそのまま成り立つ」
> →「attempt-0001 稿の限定を参照する。ただし L-A1S-4 は本稿 L-A1S2-4、L-A1S-16 の測定 node は bnode035 / 039 / 040、L-A1S-18 は図なし、L-A1S-20 の時刻は本稿 §2.5 として扱う。旧稿の本文・判定は変更しない。」

README の「限定 13 件を attempt-0001 稿の 20 件に加える」も、

> →「限定13件を記載し、attempt-0001 稿の限定は本稿 §3 に明記した読み替えの下で参照する」

とする。

**R-2 / 対象: 稿 §1.5・§4.3・§5.5、README 追加行、insight §1・§2.2 / 主張:** git hunk header を変更行の所属関数として扱っている。

根拠: 指定 commit 間の driver 差分と AST を照合した。追加関数は `_exact_v3_rerun_authorization`、`_rerun_authorization_digest`、`run_authorize_rerun`。既存関数の変更は `_assert_no_prior_v3_bench_start`、`_run_submit_v3`、`_exact_materialization_destination`、`_run_materialize_v3`、`_parser`、`main`。稿が列挙する `_v3_group_intent`、`_attempt_intent_path`、`create_materialization_destination`、`run_materialize` 自身には変更がない。差分量は **143行追加・3行削除**。

放置時の影響: 測定経路の変更範囲を説明する証拠が、実際の変更関数と食い違う。

分類: **should**。

是正案:

> 「hunk の所属は」以降の関数列挙
> →「変更行は定数、追加した `_exact_v3_rerun_authorization` / `_rerun_authorization_digest` / `run_authorize_rerun`、既存の `_assert_no_prior_v3_bench_start` / `_run_submit_v3` / `_exact_materialization_destination` / `_run_materialize_v3` / `_parser` / `main` にある。」

> 「認可 gate の 143 行」
> →「認可 record の生成・照合、submit・materialize への接続、CLI 分岐の143行追加・3行削除」

「推定量・分類・測定関数自身に変更がない」は確認できた。ただし「測定値に影響しない」と同義ではない。§4.3 の当該文は、

> →「測定・統計関数自身に変更行がないことを静的に確認した。実行時の等価性は検証していない。」

とする。

**R-3 / 対象: insight §1 項1 / 主張:** 「stdout / stderr はいずれも空」の対象が不明で、3 job を含む読みでは偽。

根拠: `MANIFEST.tsv` の job stdout は write-heavy 885、balanced 875、read-heavy 881 bytes。stderr は557 / 556 / 556 bytes。`completion.json` も各ファイルの非空内容に対応する digest を持つ。

放置時の影響: 完走記録が job ログの不在を誤って伝える。

分類: **should**。

是正案:

> 「stdout / stderr はいずれも空、failure 受領証なし。」
> →「3 job の scheduler stdout は885 / 875 / 881 bytes、stderr は557 / 556 / 556 bytesである。」

親の制御コマンドの出力が空だったという意味なら、実際のファイル名を限定して別記する。「failure 受領証なし」は射影だけでは独立確認できない。

**R-4 / 対象: 稿 §2.7・§5.5 / 主張:** 並記値の出所を旧 results 稿としており、「数値の出所は一次資料だけ」と整合しない。

根拠: §2.7 は「attempt-0001 の値は attempt-0001 稿 §2.1 … から逐語で写した」、§5.5 も旧稿を先に置く。README 系列規則は「数値・日付・判定の出所は一次資料だけ」。今回、旧 leaf の `statistics` と全数値の一致は確認できた。

放置時の影響: 値は正しくても、記載された転記経路が二次資料経由になる。

分類: **should**。

是正案:

> 「attempt-0001 の値は attempt-0001 稿 §2.1 (= 公開 leaf …) から逐語で写した。」
> →「attempt-0001 の値は公開 leaf `output/insights/2026-09-13/paper-story-a1-balanced5-sized/result.json` の `workloads[].statistics` から転記した。attempt-0001 稿 §2.1 とも一致する。」

§5.5 も同じ順序に直す。

**R-5 / 対象: insight §5 検算の説明 / 主張:** 113項目の検査が保証する範囲を広く書きすぎている。

根拠: `draft_check.py.txt` は数値や hash が稿の**どこかに存在するか**を調べる。hash と表の対象行の対応、全 lock・schedule receipt の現物 digest の再計算、mean / h 等の再計算を同 script が全面的に行うわけではない。`known` には一次資料の申告 hash も登録される。一方、`extract-attempt2.md` には再計算・現物比較の別記録がある。

放置時の影響: 「113 ok」を、script が実装していない検証の成功証拠として引用してしまう。

分類: **should**。

是正案:

> 「稿の作成時に30対の生値から再計算した検算 (`verbatim/draft-check-1.txt`、113項目 ok / 問題0)」
> →「生値からの再計算と現物 digest の比較は `verbatim/extract-attempt2.md` に記録した。`verbatim/draft-check-1.txt` の113項目 ok / 問題0は、稿中の値・digest の存在照合と配置比較の出力であり、全表の行への帰属や散文の量化語を保証しない。」

新しい gate や検査の追加は不要。記録の説明を正す。

**R-6 / 対象: 稿 §1.4・§2.5、insight §3 / 主張:** 待ち時間の起点と record 数に不整合がある。

根拠: insight は write-heavy の request 作成を18:11:15、開始を18:11:23と記すが、稿は「他2 job は7秒で開始」とする。`receipt.json` は開始時刻を確認できるものの、request 作成時刻の一次記録は射影にない。また write-heavy と read-heavy の build_start / build_done / verify_done は、各2 armで**各6 record、計12 record**。

放置時の影響: 時系列の起点と件数を誤って伝える。

分類: **should**。

是正案:

> 「他2 job は7秒で開始した。」
> →「他2 job の scheduler start はともに18:11:23だった。」

> 「write-heavy と read-heavy の6 record」
> →「write-heavy と read-heavy の各6 record、計12 record」

「Pre-running のまま5分31秒」も連続観測とは区別する:

> →「balanced の request 作成から開始までの記録上の差は5分31秒。監視では18:12:11〜18:16:12に PRR、18:17:12に RUN を観測した。」

**R-7 / 対象: 稿 §1.4 / 主張:** 認可 self digest の定義に除外 field が欠ける。

根拠: D2178 項2、追補、driver `_rerun_authorization_digest` は `authorization_sha256` 自身を除外する。driver と同じ整形（`indent=2`、末尾改行）で再計算すると `9ccd38c9…` と一致した。

放置時の影響: 読者が record 全体を hash して不一致になる。

分類: **nit**。

是正案:

> 「record 自身の canonical JSON の digest」
> →「`authorization_sha256` 自身を除いた record の canonical JSON の digest」

**R-8 / 対象: 稿 §2.6、insight §6 / 主張:** 将来の図の束縛方式と別 wave の動作を、この記録で確定している。

根拠: 稿は「作るならば本稿を `caption_source` として別途作る」、insight は「次版の全項目再導出 (並走 wave) が本稿と results 表の行から拾う」。依頼逐語は図を scope 外とし、別 wave の実施・情報取得を保証していない。

放置時の影響: 現在の結果記録に、未認可の将来設計・未確認の他作業の保証が残る。

分類: **should**。

是正案:

> 「attempt-0002 の図、または2 attempt を並記する図は、作るならば本稿を … 別途作る …」
> →「図の作成と束縛方式は本 wave の対象外である。」

> 「次版の全項目再導出 (並走 wave) が本稿と results 表の行から拾う。」
> →「本 wave は results 表への1行追加までを行った。」

「stale 注記は足していない」自体は、依頼の限定された scope と整合し、欠落とはしない。3本目を認可しないという追補の紹介も scope 内であり、認可の提案ではない。

**R-9 / 対象: brief.md 不変条件、insight §2.1 / 主張:** submit-tree に「投入後1 byte も書かない」という絶対表現が、予定・実績と衝突する。

根拠: brief 自身が materialize の宛先を submit-tree 内の新規 leaf とする。`.complete.json.destination` もその絶対パス。insight は「投入後は1 byteも書いていない」の直後に「materializer の出力だけが増えた」と書く。

放置時の影響: 正当に作成された公開 leaf を、不変条件違反または無書込みとして誤記する。

分類: **should**。

是正案:

> 「submit-tree は投入後1 byteも書かない。」
> →「投入後は submit-tree の既存ソース bytes を変更しない。materialize は指定した新規 leaf に出力する。」

insight も同じ区別で実績を書く。

**R-10 / 対象: 親 brief・裁定、射影資料 / 主張:** 段省略の実質的前提は支持されるが、規則への適合まで検証済みとはできない。

根拠: 差分に実装変更はなく、投入対象・認可・公開先は D2172 / D2178 / 依頼逐語で指定済み。P1 と P4 は支持される。`886c19259` と `ec696308a` が `fec4a8187` の祖先であることも確認した。一方、DW-C00 / DW-S04 の規則本文、裁定 inbox 全体、hydrate 2箇所の実記録は射影されていない。また「差分適用前」とされた `README-results-series-rules.md` には、既に今回の追加行が含まれていた。

放置時の影響: レビューが確認していない規則適合・事前状態まで追認したように読める。

分類: **記録**。

是正案:

> 「起点 local main … に含まれることを … 定数と … 実在で確認」
> →「`886c19259` と `ec696308a` が起点 `fec4a8187` の祖先であることを確認」

射影説明の「差分適用前」は、

> →「追加行を含む射影。追加位置と変更量は `README-row.patch` を正本とする」

と訂正する。P2・P3の未確認部分を理由に、新しい作業や承認 gate を要求するものではない。

## 逐語照合の対照表 (命題 / 稿・README・insight の文 / 一次資料の逐語 / 一致・不一致)

§2.7 は workload と attempt をキーに**各行を分離して**照合した。8数値は mean、h、区間下限・上限、B、baseline mean、sd、planned sigma。**6行×8数値すべて一致**し、classification / breach も一致した。

| 命題 | 稿・README・insight の文・値 | 一次資料の field・逐語 | 結果 |
|---|---|---|---|
| attempt-0001 write-heavy | mean `1591948.5`、h `23911.502943472762` | 旧 `statistics` の同値、残る6数値も該当行と同一 | 8/8一致 |
| attempt-0001 balanced | mean `448830.1666666667`、h `28351.599461068836` | 旧 `statistics` の同値、残る6数値も該当行と同一 | 8/8一致 |
| attempt-0001 read-heavy | mean `-576749.7666666667`、h `32963.69867738655` | 旧 `statistics` の同値、残る6数値も該当行と同一 | 8/8一致 |
| attempt-0002 write-heavy | mean `1538451.4666666666`、h `41434.211082207854` | 新 `statistics` の同値、残る6数値も該当行と同一 | 8/8一致 |
| attempt-0002 balanced | mean `548138.2333333333`、h `25552.384438113106` | 新 `statistics` の同値、残る6数値も該当行と同一 | 8/8一致 |
| attempt-0002 read-heavy | mean `-560565.6`、h `41746.744315864176` | 新 `statistics` の同値、残る6数値も該当行と同一 | 8/8一致 |
| 分類・breach | 両 attempt 全6行 `resolved-above-floor`、旧 false×3、新 true / false / true | 各 `statistics.classification` / `variance_plan_breach` | 一致 |
| 稿 §2.1 の再計算 | 対差、mean / h / B / 区間が一致 | 全90対の差と arm 生値を照合し、式から再計算 | 一致 |
| 稿 §2.3 | 6 arm の mean / min / max / median / cv | `arms.raw_tps` と `wal_evidence.records[].payload` | 一致 |
| 稿 §2.4、insight §4 | commits 458889 / 510621、481088 / 509412、471051 / 523733 | `verify_done.payload.commits` | 一致。旧 attempt との交換なし |
| 同上 | aborts 105711 / 197048、133860 / 194033、166197 / 200282 | `verify_done.payload.aborts` | 一致 |
| 正しさ記録 | 6件とも anomaly 0、certified、serializable | `anomalies=0`、`certified=true`、`verdict=serializable` | 一致 |
| job 表 | 13220 / 13221 / 13222、035 / 039 / 040 | `job_executions.request_id` / `reservation_binding.host` | 一致 |
| elapsed / CPU | 1050.02 / 321.32 / 847.45秒、9080.502 / 9081.926 / 9108.688秒 | `accounting.elapsed_s` / `cpu_total_s` | 表示丸めと一致 |
| scheduler 終端 | 消失後、state / exit_status 未観測 | `terminal_reason=request-disappeared-after-visibility`、両 `observed=false` | 一致 |
| 認可 | D2172、項2、2026-09-20、source `fec4a818…` | 認可 record の `decision` / `source_commit` | 一致 |
| canonical identity の差 | 指定4箇所だけ異なる | 両 `campaign_binding.canonical_preimage` を構造比較 | 一致 |
| leaf digest・size | result `b7e0518e…` /269786、receipt `98c35cca…` /19393、marker `7ad34232…` /1407 | 現物 bytes から SHA-256 再計算 | 一致 |
| 追補・登録・受領証 | 追補 `0098d4ea…`、登録 `6047eff0…`、completion `11202bf7…`、認可 `8204f975…` | 現物 bytes から再計算 | 一致 |
| durable WAL / lock / schedule の hash・size | 稿 §5.2 の各値 | `result.json` 記録値と `extract-attempt2.md` | 一致。原本現物の独立再読ではない |
| complete 時刻 | `recorded_epoch` 18:30:05 | `receipt.json.recorded_epoch=1789896605` | 一致 |
| 監視終了 | 18:29:14、全request消失 | `watch.log` 最終行 `alive=0` | 一致 |
| 制御コマンド・barrier の mtime | 18:10:34、18:18:44、18:30:06、18:30:21等 | MANIFEST / extract の記録 | 記録間で一致。rc・原本mtime全部の独立確認ではない |
| 限定継承・出所・ログ不在 | 「そのまま」「旧稿から」「いずれも空」 | R-1・R-3・R-4参照 | 要修正 |

insight §5 は丸めた表示値として数値は正しい。「逐語」という見出しは厳密には不適切なので、「公開 leaf の値を表示桁に丸めた」とするのが正確である。

`variance_plan_breach` の説明は実装と整合する。`_statistics_from_signed_differences` は `sample_sd > planned_sigma_tps` を記録し、分類には `_classify_difference(mean, half_width, boundary)` を使う。したがって「breach flag が分類を直接変更しない」は正しい。ただし sd は h を通して分類に影響するため、「分散が分類に影響しない」とは読ませない。稿の括弧説明はこの区別を保っている。計画sigma超過を無効・再走・formal判定に変えていない点も適切。

## 量化語の検証 (問い 2 の各項 / 確認方法 / 結果)

| 項目 | 確認方法 | 結果 |
|---|---|---|
| seed・group_bits・物理順が3 workloadとも一致 | 両 result の schedule `document` を workload ごとに比較。4 fieldと12 blockの arm順を照合 | 確認。bitsは `[1,0,0]` / `[1,1,0]` / `[1,0,1]` |
| driver以外8本がbytes同一 | `source_binding.files` の集合・blob oid・working SHA-256を比較 | 記録上、8本すべて一致。driverだけ異なる |
| driver hunkが測定関数にない | 指定commit間の実差分と関数ASTを照合 | 関数自身の変更なしは確認。所属関数一覧はR-2の誤り。実行時等価性は未確認 |
| benchが balanced → read-heavy → write-heavy の直列 | schedule各60 repの最小開始・最大終了を比較 | 確認。18:18:44.891〜18:22:07.514、18:22:07.529〜18:25:29.863、18:25:29.879〜18:28:51.988 |
| schedule_wall_sが階段状 | schedule記録値を比較 | `202.64248350803973` → `404.9508861489594` → `607.0667186549399`。確認 |
| 階段の原因がlock待ち | 上記時間と登録済みlock規則を照合 | 整合する。ただし待ち時間の個別計装値はなく、全差分をlock待ちに帰属する厳密な内訳は本レビューでは確認できない |
| baseline CVが3本とも大きい | 全6 armを生値から再計算しWAL値と照合 | 確認。0.03227476 > 0.00590914、0.01604910 > 0.00621295、0.00886818 > 0.00495579 |
| write-heavy baseline pair 0が最大 | raw値の順位とscheduleの先頭repを照合 | 最大2730303、次点2522961、差207342。最初の物理repであることも確認 |
| 全180標本が整数 | 全6 arm×30値の整数性を確認 | 確認。JSON型はfloatでも値は整数 |
| stdout 875〜885 bytes | MANIFESTとcompletionの対象path・digest対応 | 記録上確認。本文全体は本レビューでは読んでいない |
| verify 11〜13秒 | extractの build_done→verify_done のepoch差 | 11.153〜12.589秒。概数として整合 |
| settled | 両 result の schedule `settled` | 新0.0380859375 /1.6103515625 /0.0、旧0.02734375 /0.0234375 /2.25732421875。全件true、threshold 4.0 |
| 5分31秒・他2本7秒 | receiptの開始時刻、insightの作成時刻、watch | 331秒の算術は整合。request作成の一次記録は射影外。「他2本7秒」はR-6 |
| hydrateのpin一致・detached/clean・再投入不在の全履歴 | 射影された資料の範囲を確認 | これらを全面的に独立確認する資料は不足。本レビューでは確認できない |

## 判定しないの線 (問い 3)

稿 §0・§2.7・§3、README 行、insight は、A-1充足・formal昇格・再現性・安定性・性能優劣を肯定する結論を出していない。

「符号は同じ」「分類は6 cellとも同じ」は一次資料で確認できる観察であり、直後に再現判定との区別がある。「認可済み独立再現」は D2172 が定めた観測目的の呼称として使われている。insight の「同一配置の反復は成立した」も、続く seed・配置の一致という意味では裏付けられるが、より明確には「登録した同一配置で測定された」とするのがよい。

§2.7 には実際に6行の並記表があり、必要な値を読める。「判定しない」の反復によって並記が欠落する問題はない。attempt間の差・比・合成区間は作られていない。

追補・事前登録・旧 leaf・旧稿・fig9・figures README、および実装面について、今回の `git diff HEAD` に変更はなかった。旧判定を強めたり弱めたりする変更も認めない。ただしR-1の継承表現は修正が必要。

README patch は results 表末尾への1行追加であり、版の履歴表への登録ではない。append-only・attempt-0002単独稿という単位は依頼と整合する。数値の出所についてはR-4を直す必要がある。系列規則には図 provenance からの転記という一般文も残るが、今回のユーザー指示は図なし・一次資料からの単独稿を明示しており、図や一般規則変更を追加する理由にはしない。

## 総括

**数値・分類・配置の中核は確認できた。must-fix はR-1。** R-2〜R-9の説明・出所・量化語も、凍結前に修正するのが適切。

段2・3・5省略の実質的前提である「設計択一なし・実装変更なし・今回の受理集合変更なし」は差分と裁定に整合する。review 1本の規則根拠、hydrate、外部状態の全履歴は、本レビューの確認範囲に含めていない。

ファイル変更、pytest、実測は行っていない。