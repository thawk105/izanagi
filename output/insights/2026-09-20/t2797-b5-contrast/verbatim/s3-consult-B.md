# 結論と検査範囲

**P9 の subprocess 案を、B 消費記録・物理 retry identity・timeout 分類を修正して採ることを推奨する。現状の「seam は2つだけ」「WAL なしなら A のみ」は支持しない。**

全検査は **未実走・静的読解**。pytest、変異 kill、qsub、共有 FS の実機 handshake は実施していない。親が報告した queue・probe・peer job の実測は、今回の独立実測とは区別した。

以下、`plan` は親 job directory の `codex/s2-plan.md`、`追補` は `brief-addendum-1.md`、`V` は同 `verbatim/`。`L` は `orchestrator/campaign/p3_s4_loop.py`、`TJ` は `orchestrator/tests/test_p3_s4_loop_job_contract.py`、`SH` は `tools/pegasus/p3_s4_loop_pegasus.sh`。

# B1 — P9 の「BUILD_START がなければ未投入」は成立しない

- **対象:** 追補:33–35 の A/B 復元。
- **判定:** real。
- **格:** must-fix。
- **成果物影響:** pipeline 投入後・最初の WAL 記録前の中断を A-only と誤計上し、消費した評価機会を返してしまう。

`L:2165` で `run_campaign` に入った後、`loop.py:517` の authorization／claim、`:538` の perf preflight、layout・lock・source 解決を経て、初めて BUILD_START に到達する。したがって **BUILD_START の存在は投入済みの証拠だが、不在は未投入の証拠ではない**。その窓での walltime 打切りは特に区別できない。`V/prereg-s3.md:17–20,41–46` は投入点で B 消費を要求する。

**代案:** P9 を維持し、`L` の既存 `run_campaign` 呼出し直前に、B-5 のときだけ系列台帳へ投入イベントを永続化する最小 seam を足す。通常呼出しは既定 `None` で不変。終了後はそのイベントと WAL を照合する。中断で境界が確定できないものを、無条件 A-only／無料 retry にしない。

これは成功後の加算を禁止するための既存要件であり、汎用 recovery 基盤の新設は不要である。

# B2 — slot 分離だけでは subprocess retry の claim 衝突を避けられない

- **対象:** P1、P9、追補の peer claim 衝突。
- **判定:** real。
- **格:** must-fix。
- **成果物影響:** claim 取得後に失敗した同 slot の retry が、前 process の残存 claim に拒否される。

別 slot の identity 分離は妥当である。しかし `campaign_claim.py:383–386` は release・stale 自動削除を持たず、`:421–433` は既存 claim を O_EXCL で拒否する。別 process が**同じ slot identity**を再取得する retry は、peer と同じ問題を持つ。

`plan:316` の `b5_attempt=0,1,2` はこの問題を解けるが、追補:25 の CLI 案は `b5_slot` しか明示していない。

**代案:** 論理 slot と物理 attempt を分け、両者を campaign identity に束縛する。CLI を増やしたくなければ、物理評価 KEY に cohort／論理 slot／attempt を含め、台帳には論理 slot を別記する。proposal・入力・予定位置は retry 前後で同一にする。claim 削除による再開は採らない。

親からの proposal を待つだけの再 poll は、評価 process の retry とは分ける。

# B3 — P9 は pin 費用で優位だが、「2 seam だけで完成」は反証

- **対象:** P9 と plan の in-process／新 entrypoint 案。
- **判定:** real。
- **格:** should。
- **成果物影響:** author の変更範囲を過小評価すると、authority・B 台帳・session 束縛の一部が未接続で残る。

P9 は既存 `p3_s4_loop.main` を使うため、新 coder entrypoint の登録を避けられる。`materializer_admission.py:152`、`test_p3_build_authority_cli.py:71,688–705`、`test_p3_exploration_namespace.py:416–429` が根拠である。新 module から `run_campaign` を直接呼ばなければ、caller 数2も維持できる。

一方、必要な変更は slot key と resolver 転送だけではない。

- B1 の投入点記録。
- B2 の物理 attempt 分離。
- `L:3145–3151` の coder opt-in 必須条件に、正規の machine mode を接続。
- `bench_max_rounds=3` の明示束縛を採るなら、その B-5 限定接続。
- fresh 評価でない skip を成功復元へ流さない処理。

`L:2175–2179` は現状、skip を `_resolve_duplicate` へ渡す。親側が既存 WAL を当該 subprocess の新しい成功と誤認しない対応が必要である。

**代案:** **P9＋上記の小さい seam**。新 module は系列管理を所有し、既存 CLI は単回評価を所有する。in-process を採る場合も private 関数十数個の public alias 化は不要で、`plan:109–121` 型の委譲窓口一つに集約する。ただし authority 発行経路の追加費用は残る。

Python 起動・checkout の追加費用は計測対象とする。追補:37 の「数十秒」は独立に裏付けられておらず、build 区間15秒を process 起動費用の測定値にはできない。

# B4 — job body 拡張は成立する。既存 pin が一斉に赤になるわけではない

- **対象:** P5、旧 argv、TJ、EXIT trap。
- **判定:** refuted — 「別 file が必須」「既存 pin が全面更新になる」という懸念。
- **格:** —。
- **成果物影響:** 旧呼出し本文を保持すれば、旧経路の argv と rc 契約を維持できる。

`SH:596–621` の前に B-5 分岐を置き、そこで系列 driver を一度だけ起動して終了すればよい。

```bash
if [[ "$b5_requested" == true ]]; then
  b5_rc=0
  "$PY" -B -m orchestrator.campaign.b5_generator_contrast \
    "${b5_argv[@]}" || b5_rc=$?
  exit "$b5_rc"
fi
```

`SH:154–156` の EXIT trap は終了 rc を捕捉する。この形は `set -Eeuo pipefail` と両立し、旧 fixture／proposal／stock 分岐へ落ちない。候補 reject の CLI rc=0 と系列成立は別なので、系列 driver 自身が台帳から終端 rc を決める必要がある。

**author が触るべき箇所:**

| 箇所 | 必要な対応 |
|---|---|
| `SH:95–96` | B-5 LLM だけ proposal-path 必須を除外 |
| `TJ:266–269` | その条件を含む pin へ更新 |
| **`TJ:698–704`** | 同じ逐語を置換する既存変異も更新。plan の列挙漏れ |
| `TJ:519–526` | 旧 module 呼出し3箇所は維持。B-5 の1箇所を別に検査 |
| `TJ:548–582` | B-5 env 判定と driver 分岐を stage order に追加 |
| `TJ:1866–1915` | 旧 argv・呼出し数・失敗時 rc の期待値を保持 |
| 新 B-5 shell test | 4 mode 各1起動、非零 rc の trap 転記、旧経路不実行を検査 |

B-5 を追加しただけでは、旧 module を数える `TJ:522` は赤にならない。stage-order test も旧 marker の順序を保てば通る。**新経路を検査対象へ追加しなければ、通過しても B-5 の保証にはならない。**

別 file 案は旧 pin への影響を減らせるが、preamble・依存物供給・reservation・trap の複製と新登録が増える。今回の規模では既存 file 拡張を支持する。

# B5 — 3時間 PBS pin と8時間 CLI override は整合するが、既存 test は8時間を証明しない

- **対象:** P8、walltime pin、launcher。
- **判定:** refuted — 「3時間 pin が8時間要求を禁止する」。
- **格:** —。
- **成果物影響:** PBS 行を保持したまま、実 allocation の walltime を reservation に束縛できる。

`TJ:181` は script の3時間行を pin する。一方、`SH:292–321` は `qstat` の実制限から deadline を計算する。`dispatch_compute.py:4018–4024` に CLI `-l elapstim_req=...` の先例もある。親提示の `13465.nqsv` は CLI 優先の既知証拠として扱える。

ただし `TJ:1275–1277` の test stub は10800秒固定である。既存緑から8時間の reservation 束縛を主張できない。

**代案:** PBS pin は維持。launcher argv の28800秒相当と、job の `qstat` 観測値の転送を別々に検査する。

また `plan:479–485` の env 組立には、**qsub への環境輸出方法を明記すべき**である。`subprocess(..., env=...)` だけから job への継承を推定せず、`tools/pegasus/README.md:427` のように必要変数を `-v` で渡す。dry-run はこの最終 argv まで表示する。これは **real／should** の設計欠落で、放置すると計算ノードで必須 env 不足の早期終了になりうる。

# B6 — 原因不明の45分無応答を機械故障に固定してはいけない

- **対象:** P4、追補:53–54。
- **判定:** real。
- **格:** must-fix。
- **成果物影響:** 生成器の空出力・停止・不明な失敗が無料 retry に化け、A 消費と機械欠測の分類が変わる。

共有 FS の同一 directory 内で一時 file を完成させてから rename する方式は、外部ネットワークを必要としない。`plan:455–459` の **proposal は a、評価結果は k** も妥当である。

しかし「45分応答がない」は通信障害の証拠ではない。親の死亡、LLM の未完了、空出力後の通知漏れ等を区別できない。`V/prereg-s3.md:35–46` は機械故障を限定し、分類不能の無料 retry を禁止する。ここは `plan:461` の方が追補より正確である。

**代案:**

- 空出力／schema 不合格は `.rejected.json` で A 消費を閉じる。
- 通信・供給障害が確認できる場合だけ、同じ操作を追加2回まで待つ。
- 原因不明は分類不能欠測として終了する。
- 親が死亡しても job 自身の deadline で台帳終端を書き、非零で終了する。
- request に対応する proposal・sidecar・実入力をそろえてから公開する。複数 file の rename 全体が atomic だとは扱わない。

通常の終了なら EXIT trap が働くが、scheduler の強制 kill まで終端 JSON の生成を保証しない。開始イベントと scheduler 証拠による事後記録を残す。

# B7 — 待機費用と8時間の成立性は分ける必要がある

- **対象:** P4、P8、4 job 配置。
- **判定:** real。
- **格:** should。
- **成果物影響:** LLM 待機で allocation を使い切り、16 session 完走前に系列欠測となる。

48 core の allocation 換算では、45分待機は36 core-hours、3回待機は108 core-hoursである。通常仮定の10手番×5分でも約40 core-hoursを待機へ使う。CPU 実使用量とは区別して記録する。

`plan:513` が認めるとおり、8時間は45分×3回を多数回繰り返す最悪ケースを吸収しない。さらに A-only reject があれば LLM 提案機会は10回を超える。

**代案:** poll 自体の期限に加え、既存 reservation の残時間で新しい待機・評価を開始できるか判断し、終了記録の余裕を残す。これを新たな系列3600秒制限にしない。

配置比較は次のとおり。

| 配置 | 利点 | 費用・契約 |
|---|---|---|
| 系列16 sessionを1 job | queue 待ちを系列1回に集約。stock と初回評価の同 job が成立 | LLM 待機で node を占有 |
| 1評価1 job | LLM 手番中の node 待機を削減 | 適応的な評価ごとに queue／起動待ち。stock・score を含めれば「×11」だけでは総費用にならない |
| stock だけ先行 job | 初回入力を早く作れる | `V/prereg-s5.md:38` の stock と初回評価の同 job に反する |
| block stock 別 job | 系列とは独立に5 sessionを取得可能 | 別 job を禁じる記載は§5.4にない |

**「系列全体を必ず同 job」は、§5.4 の逐語そのものより強い設計である。** 明示要求は開始 stock と最初の評価の同 job。後続分割案を検討する余地はあるが、今回の試走では費用と比較条件を親が固定する必要がある。

block-stock 先行は、較正済み経路の所要を53枠の内側で把握できる点で支持する。46 run／143 req は4 node同時開始の保証にはならない。4本同時投入と同時実行も別である。

# B8 — 53枠の算術は妥当。所要推定を実測 max と呼べない

- **対象:** brief:35–41,63、P8、DW-O13。
- **判定:** 根拠不足 — 8時間での完走、115秒の適用域。
- **格:** —。
- **成果物影響:** 暫定見積りを本走上限の根拠に転用すると、費用裁定の根拠が不足する。

`3×16+5=53≤60` は正しい。遅延しても新系列・代替探索・追加 stock を発行しなければ、時間超過それ自体は論理 session 上限を増やさない。品質 round と認可された同 slot retry は物理回数として別計上する。

ただし今回の指定資料からは、115秒について候補・trace・測定数・分布 max への参照が得られない。gen_S の86400秒は受付制限であり、所要予測ではない。

K2 round3 の `README.md:65–84` は69秒だが、bench は2 repで、同文書は前巡432秒との差も示す。較正済み1M／48／5 repの session 分布へそのまま外挿できない。`docs/dev-wave/operations.md:104` は母集合・regimeを併記した実測 max への倍率を要求する。

**代案:** 8h／3hを試走の暫定管理値と明記する。正常・失敗・retryを含む session 所要、最大値、job Elapse、cache・rounds・LLM待機を取得し、本走上限はその後に決める。打切り観測を正常完走の max と混ぜない。

# B9 — pin 閉包には plan 未記載の検査面がある

- **対象:** 新 module、entrypoint、新 test、job body。
- **判定:** real。
- **格:** should。
- **成果物影響:** 実装が正しくても既存閉包検査で落ちるか、新経路が検査対象から漏れる。

検索で追加確認した面を含め、author の対象を次に固定すべきである。

| 検査 | 判断 |
|---|---|
| `test_campaign.py:5418,5433,5500,5524` | direct `run_campaign` を増やさなければ2／総数22／raw総数18を維持 |
| `test_p3_exploration_namespace.py:416–429` | 既存 L の layout11、run_campaign2を維持。新 coder entrypoint 案では契約追加が必要 |
| `test_p3_b4_wiring_probe.py:329` | import閉包49。L→B-5 の逆 import を作らない |
| `test_official_perf_closure.py:495–535` | 実際の条件式を検査する。core／report／shellで該当すれば inventory 更新 |
| **`test_campaign_import_invariant.py:883,931`** | 新 campaign CLI の import／bootstrap 形も検査対象。相対 import＋main guard の形に注意 |
| **`test_pegasus_tools.py:540–558`** | SH の third-party source 解決逐語と出現数も pin |
| **`test_p3_build_authority_cli.py:95–140,688–705`** | 新 test で独自 authority issuer を増やしても閉包に掛かる |
| **`TJ:698–704,939–951`** | pin 本体だけでなく、その断片を置換する既存変異も保持 |
| `admission_registry.json:112–116` | 同 SH 拡張なら既存登録は維持。新 login launcher の分類は別途必要 |

新 test の `__main__` harness は `TJ:1928–1934` に合わせ、subprocess は `-B`／`PYTHONDONTWRITEBYTECODE=1` を使う。後段の実走は `tools/run_tests.py` 経由とする。

**代案:** pin 数を先に書き換えて緑にするのではなく、実装の call／import 面を確定してから必要な inventory だけ更新する。

# B10 — consumer と計時は plan にある。削りすぎると依頼未達になる

- **対象:** A2、P7、verifier wall、較正・verify 配線。
- **判定:** refuted — 「plan にこれらがない」。
- **格:** —。
- **成果物影響:** いずれも明示されており、欠落ではなく接続と報告範囲の問題である。

`plan:370–414` に解析 consumer、`:438–451` に job から固定構成を使う driver、`:515–534` に費用採取がある。shell に較正 flag の文字列が出なくても、B-5 driver が各 slot CLI へ必ず渡せば配線は成立する。検査も最終 slot argv／identity／WALまで見るべきである。

P7 の「n=1だから対不足」は不十分で、plan の反証と追補:49を支持する。pilot は `not-applicable-pilot` とし、少なくとも次を出す。

- A/B、論理 session・物理 attempt・品質 round 数。
- stock／endpoint／score、fallback、anomaly、品質・機械欠測。
- stock5件の記述 CV。
- session 所要の分布と max、build、bench、trace＋verify区間。
- job Elapse総和、queue待ち、LLM手番・待機費用。

追補:45–47 の **trace＋verifier区間として報告する**案は、依頼の括弧書きに沿う合理的な縮約である。ただし `pipeline.py:2130,2177–2178` の通り、隣接 verify record の差には周辺処理も入る。失敗 rep に `verify_done` がなければ、欠測／打切り区間として示し、既完了 rep で補完しない。

純 verifier 計時 adapter は今回は削除候補。既存 WAL 差分を純 verifier 秒と改名することは不可。

# B11 — 本走統計は scope 内。合成 test は実データ接続の代用ではない

- **対象:** A2 の exact permutation／Holm。
- **判定:** refuted — 「本走未認可だから統計実装も要求外」。
- **格:** —。
- **成果物影響:** pilot 記述だけに削ると、§10の解析 consumer 実装が未完了で残る。

`V/prereg-s10.md:21` は score／floor／6比較／判定順を実装対象に含める。2^12＝4096通りの列挙自体は小さく、計算費用より欠測・fallback・対形成の意味を誤る費用の方が大きい。

`plan:414` の13/4096、79/4096等の固定例は、実装自身から期待値を作らない限り有用である。ただし合成配列だけでは、実台帳から正しい対・block・attemptを作ることを保証しない。

**代案:** 純粋な統計関数と判定順を今回実装し、pilot 台帳から記述報告までの接続も検査する。本走データでの妥当性を実証したとは言わない。

pilot記述＋判定順の骨格だけへ縮小するなら、未実装の統計部品を明記し、**(α)完了とは報告しない**ことを親裁定にする。

# B12 — 変異 matrix は方向がよいが、帰属と恒真性は未証明

- **対象:** plan:556–577。
- **判定:** 根拠不足。
- **格:** —。
- **成果物影響:** 全体 suite が赤になっても、要求された単位自身が負例を検出した証拠にならない。

具体的には次を修正すべきである。

| 単位 | 単独で検出すべき負例 |
|---|---|
| 重み | 同じ生成関数で作った hash 同士の比較ではなく、固定された独立期待値／改変材料 |
| session上限 | 定数53の比較だけでなく、driverが実際に発行する slot 列と B11／score6 の禁止 |
| A/B | B1 の投入後・WAL前中断。正常終了だけの test では不足 |
| fresh／retry | 同値別slotだけでなく、別process・同論理slotの物理retry分離 |
| handshake | 無応答・明示空出力・証拠付き通信障害をそれぞれ区別 |
| job | static文字列検査に加え、実shell＋stubで1起動・非零rc・旧経路不実行 |
| consumer | producer定数と独立な対・p値・判定順期待値 |

特に `plan:564` の「`check_stop` を呼んだら失敗する spy」は P9 と両立しない。P9 は fresh layout で既存 `check_stop` を通す案であり、呼出し禁止は要件ではない。

**代案:** 「系列履歴の収束／reverse／累積時間によって次の fresh slot が止まらず、B10またはA30まで進む」という挙動を検査する。各変異について、無変異正例→指定単位の test→変異負例の順で記録する。他 test も同時に kill すること自体は問題ない。

# B13 — 削除可能性と残すべき最小実装

- **対象:** brief／plan の過剰実装。
- **判定:** real。
- **格:** should。
- **成果物影響:** 不要な一般化を残すと、試走前の実装・検査費用が増え、削ればよい部品が恒久契約になる。

削除・縮約を勧めるものは次のとおり。

- `plan:322` の全 slot hash8 衝突の事前網羅検査。LLM候補は未生成であり、既存 identity lock照合と当該 attempt の結果対応を利用する。
- 純 verifier 計時の runtime adapter。
- P9採用時の新 coder entrypoint登録と、private 関数群の public alias 化。
- node喪失後も系列を自動復活させる汎用retry／再配置基盤。plan:295の系列欠測で足りる。
- β launcher の複数 workload／複数系列／108系列 schedule 生成。生成器の w・r 引数や本走解析関数まで削る必要はない。
- 本走認可・発効束を自動認定する新 gate。

一方、B/A台帳、同slot追加2回の限定retry、品質欠測、状態継承、fresh評価、解析consumerは依頼にある。これらを「台帳・検査だから過剰」として削ることは反対する。

**根拠:** `V/T-2797-origin.md` の scope、`V/prereg-s10.md:10–21`、`V/prereg-s11-12.md:45–50`、`plan:295,322,532`。

## 総括

**must-fix**

1. **B1:** WAL不在を未投入と断定せず、B消費境界を永続記録する。
2. **B2:** subprocess retry に物理attempt identityを持たせ、残存claimとの衝突を避ける。
3. **B6:** 原因不明の無応答を機械故障・無料retryへ固定しない。

| 前提 | 判定 |
|---|---|
| **P1** | 条件付き支持。slotに加えてcohort／物理attemptを分離 |
| **P2** | 迂回の必須性は反証。P9のfresh layout運用でも停止不適用を実現可能 |
| **P3** | 支持。WAL品質分類とendpoint資格を分け、失敗・欠測を保持 |
| **P4** | 条件付き支持。共有FS handshakeは妥当。timeout分類とallocation残時間処理を修正 |
| **P5** | 支持。既存body拡張が小さい。旧argvを保持し、TJの変異も更新 |
| **P6** | 条件付き支持。100／130全要素一致は未実走。数学的誤差証明とは呼ばない |
| **P7** | 元案を反証。追補のpilot専用記述経路を支持 |
| **P8** | 暫定設定として支持。8時間完走・4node同時開始の根拠は不足 |
| **P9** | **修正採用を推奨。** 新entrypoint案よりpin・登録費用が小さい。現状の2 seam／WALのみ復元は反証。起動費用は未測定 |

**削除候補:** hash8衝突の事前網羅検査、純verifier adapter、新coder entrypoint、公的alias群、汎用retry／再配置、本走108系列launcher、発効自動gate。解析consumer本体は削除しない。

**親裁定が要る事項**

- P9へB投入点記録と物理attempt分離を追加する具体形。
- 原因不明timeoutを分類不能欠測とすること。
- 4 jobの直列／並列配置と、分割する場合の同job契約の扱い。
- 115秒の測定元・母集合と、試走後の実測maxから決める本走費用上限。
- consumerを縮小する場合に、(α)未完了を明示すること。
- author開始前のpeer対象2 fileの再照合。claim修正が着地していれば、その差分を織り込む。