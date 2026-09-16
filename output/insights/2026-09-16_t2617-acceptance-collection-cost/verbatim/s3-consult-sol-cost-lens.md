## 所見

### 1. plugin の per-item 費用は親の見積もりの 2 倍。ただし、秒数の支配性は未確定

- **主張:** `_canonical_item` は各 worker で全 item に **2 回**適用される。
- **根拠:** `tools/acceptance_shards.py:901` → `records_from_items` → `:791` が第 1 周、`:906` の `by_identity` 作成が第 2 周。各回で `:762` の `Path.resolve()`、`:769` の marker 列挙、nodeid 正規化を行う。23,970 item・48 worker なら **2,301,120 回の resolve**。3 shard 全体なら約 690 万回である。
- **親の記述との差:** brief §5.6 の約 115 万回は半分。また、`:917` と `:919` の digest はそれぞれ全 records と selected に対するもので、**同じ digest の重複計算ではない**。重複しているのは `:916–917` の records payload 構築。
- **重大度:** 高。小規模な短縮候補の優先順位が変わる。

各 worker の主要処理は次のとおり。

| 処理 | worker あたり | 48 worker あたり |
|---|---:|---:|
| 全 suite の pytest collection | 1 回 | 48 回 |
| 全 item の canonical 化 | 2N 回 | 96N 回 |
| `allocate` | 1 回 | 48 回 |
| duration ledger の読込み・JSON parse | 1 回 | 48 回 |
| 全 records digest / selected digest | 各 1 回 | 各 48 回 |

`allocate` は再ソート、file/group 閉包構成、全 node の重み参照を行う（`:325–461`）。**plugin 内の反復する filesystem 操作では canonical 化が第一容疑者**だが、回数だけで execnet や import より秒数が支配的とは断定できない。

### 2. 「差 38 秒」は同条件比較による残差ではない

- **主張:** 56 − 18.23 ≈ 38 秒を、追加処理の正味費用として配分してはいけない。
- **根拠:** login の独立 collection は plugin spec を除去する（`tools/run_tests.py:1422–1424`）。受入側は plugin・xdist を載せる（`:1495–1507`）。さらに、指定 session `8259cf7fff14f3387347ab25a65a379c` の実 report を確認すると、全 shard の `observed_universe` は **24,020 件**で、brief の単独対照 **23,970 件**と一致しない。
- **親の記述との差:** host、実行形、時間境界に加え、比較集合も違う。18.23 秒を「56 秒のうち説明済みの部分」と扱うことも未立証。
- **重大度:** 高。

第 4 の候補は、**loadgroup 時だけ有効になる collection 後処理と worker 設定配送**である。`conftest.py:2207–2218` は閉包検証・suffix 処理・所要秒による並べ替えを行い、`:1810–1816` は loadgroup を有効条件にする。duration ledger は controller から worker へ配送・検証される（`:1622–1644`, `:2337–2345`）。これは単なるテスト module の重複 import と区別すべき費用である。

### 3. `disp` の「99.995% 確定」は分母が違う

- **主張:** 確定しているのは **prewarm barrier 内では receipt が支配的**ということ。`disp` の同率の帰属ではない。
- **根拠:** 指定 session の現物は以下だった。

  | 指標 | 秒 |
  |---|---:|
  | shard-0 `pre` | 56.212744 |
  | shard-0 `disp` | 28.438556 |
  | `barrier_s` | 31.321979 |
  | `receipt_memo_s` | 31.320317 |

  marker は同 session の `shard-0/dispatcher.log:26`。collection 境界は worker 時刻の最大値（`acceptance_shards.py:1075–1092`）だが、prewarm は個々の collection 完了通知から起動できる（`conftest.py:2359–2423`）。最終 worker の収集完了前と重なる。
- **親の記述との差:** 約 **2.883 秒**の差を無視している。これは重なりと barrier 後の処理の差であり、重なりそのものの精密値でもない。
- **重大度:** 高。

### 4. receipt helper の内側は、この判断に必要

- **主張:** T-2616 に実装を委ねても、内訳調査を閉じる理由にはならない。最低限、**lock 待ち／resolver／cache 管理**を分けるべき。
- **根拠:** 計時は `conftest.py:896` から始まり、module 取得、`:899` の real-repo lock 取得も含む。memo 内には HEAD 取得、cache path 構築、別の `flock`、resolver、古い cache の掃除、保存がある（`real_repo_receipt_memo.py:531–578`, `:452`）。
- **親の記述との差:** 「helper の時間 ≒ production の Lustre 走査時間」は未証明。既存 report の lock interval は取得後の保持時間であり、この controller prewarm の待ち時間を説明しない（`conftest.py:1480–1493`）。
- **重大度:** 高。

全面的な resolver の内部解析までは不要。しかし上記三分解は、早期起動で隠せる時間と、production を触らず減らせる時間を判定するために要る。

### 5. bytecode が「温」とする証拠は不足

- **主張:** cache directory の entry 数だけでは、有効な cache を全 worker が読んだとは証明できない。
- **根拠:** 計算 dispatch は `PYTHONDONTWRITEBYTECODE` を既定で `1` にする（`tools/pegasus/dispatch_compute.py:1633`）。launcher にも対応がある（`tools/acceptance_launcher.py:68–77`）。既存 cache の読込みは禁止しないが、Python tag、pytest assertion rewrite 用 cache、source の更新との整合を entry 数は示さない。
- **親の記述との差:** 「#3 に近い」は仮説。冷条件の約 40 CPU 秒も、そのまま受入 wall の削減量にはできない。
- **重大度:** 中。

### 6. 最長テストの床が動かなくても固定費削減は有効

- **主張:** P1-D の「床は動かない」は、何もしない根拠にならない。
- **根拠:** 指定 session の shard-0 では、実行・終了処理を固定した反実仮想として、

  ```
  pre だけゼロ : 307.112 − 56.212744 = 250.899 秒
  disp だけゼロ: 307.112 − 28.438556 = 278.673 秒
  両方ゼロ    : 307.112 − 84.651300 = 222.461 秒
  ```

  他 shard の実測 wall は 223.144 / 211.758 秒なので、この走では shard-0 だけ両区間を消しても最遅は **223.144 秒**になる。
- **親の記述との差:** 5 分近傍の走に対しては意味が大きい。一方、高負荷時まで保証する策ではない。
- **重大度:** 高。

## 帰属の判定

**現時点では、38 秒の数値内訳も、(a)〜(c) の秒数上の支配順位も確定できない。** 静的に確定できるのは、48 重の全 collection、96N 回の canonical 化、worker ごとの割付・ledger parse・digest、および追加の loadgroup 処理である。48 並列の総 CPU 時間を wall に足してはいけない。

**既存成果物だけでの完全分解はできない。repo 外 probe を加えれば、新しい同条件走の分解はできる。** 過去の 38 秒を一意に復元することはできない。

親が行う観測は、次の順が費用対効果に優れる。

1. **比較条件を揃える。** 同じ revision・worktree・Python/pytest/xdist・環境・全 nodeid 集合を固定する。計測は計算ノードで、既存 runner 経由。48 worker の本観測には `--collect-only` を使わず、通常の全走を観測する。
2. **既存出力を回収する。**
   - JUnit の session 開始・wall。
   - report の collection 境界、worker の初回・最終 test 時刻。
   - `IZANAGI_MEMO_PREWARM_V1` の barrier・receipt・oracle 時間。
   - `IZANAGI_EFFECTIVE_SCHEDULER_V1` で実効 scheduler を確認。
   - `IZANAGI_ACCEPTANCE_SHARD_ARTIFACTS_V1` で成果物を対応付ける。
   - `login-collection.log` で独立 collection の command・集合を照合する。
   
   後ろ三つは識別・整合確認用であり、bootstrap 時間の計測行ではない。
3. **repo 外の一時診断 plugin を controller と全 worker に載せる。** 配送されていることを PID・worker ID で先に確認する。report schema は触らず、外部ログへ単調時計と CPU 時間を記録する。
   - worker 起動要求、OS process 起動、worker 設定完了、collection 開始・終了。
   - `records_from_items`、`allocate`、第 2 canonical 周回、payload/digest、conftest の前後処理。
   - per-item ログは出さず、関数単位の集計にする。
4. **外部 profiler／syscall 観測を補助に使う。** `resolve` に伴う metadata 操作、import・rewrite、CPU 実行と待ちを区別する。全 worker の詳細 syscall tracing は擾乱が大きいため、代表 worker の別走で確認する。
5. **prewarm は同じ probe で三分解する。** real-repo lock の要求・取得、memo lock の要求・取得、resolver の入退場、cache 掃除・保存を記録する。barrier 開始・終了と最後の worker collection 完了を同じ時間軸へ置く。
6. **未計装の対照走と比較する。** 48 worker の時間を合計せず、最後の collection 完了へ至る経路と controller の直列処理を見る。逐次・並列・I/O の相互作用は独立項として残し、無理に 38 秒へ割り振らない。

これは D1729 の「受入 report の field を足さない」を守る。診断走は、未計装走との一致・擾乱確認なしに性能改善の証明として扱わない。

## lever 表

「集合不変」だけでは受理集合不変の証明にならない。nodeid・marker・閉包・失敗条件・独立再導出を保つことが必要である。

| lever | 効果見込み | 集合不変か | 受理集合不変か | 規模 | 採否 |
|---|---|---|---|---|---|
| 第 2 canonical 周回を除き、第 1 周の item→record 対応を再利用 | **秒数は測れない**。canonical 呼出しを半減、48 worker で約 115 万回削減 | 全 item を第 1 周で処理 | 同じ正規化・重複検査・marker 検証を残す条件 | 小 | **最優先で効果測定** |
| 同一 file の resolve を collection 内で共有 | **測れない**。item 数 N に比例する resolve を異なる path 数 F に近づける | 全 item は保持 | path・symlink の変化や異常時の拒否を隠さない条件。無条件の証明は未了 | 小〜中 | 上案の次 |
| records payload と既に整列済みの値を再利用 | **測れない**。`:916–919` の重複構築・sort を削減 | 可 | digest の入力 bytes、全検査を保存 | 小 | profile で有意なら採用 |
| `allocate` の CPU・ledger 読込みを効率化 | **測れない**。48 回の JSON parse・全件処理が対象 | 可 | worker ごとの割付再導出、同じ重み・tie-break・異常検出を保存 | 中 | 第二候補。共有の割付 manifest は却下 |
| conftest の ledger 配送用 payload を controller 内で再利用、前後 hook の重複処理を削減 | **測れない**。`:2344` の worker ごとの構築等が対象 | 可 | worker 検証・hold 検証・順序を保存 | 小〜中 | probe で対象を絞る |
| 有効な bytecode／assertion rewrite cache を事前準備 | 温ならほぼ 0、miss 時の受入短縮秒は**測れない** | 同じ source・rewrite 条件なら可 | stale cache を信用せず Python の妥当性確認を維持 | 小〜中 | miss 確認時だけ。準備時間も計上 |
| import・parametrize・plugin 初期化の重複計算を削減 | **測れない**。bootstrap と collection 双方の候補 | 同じ全 item・ID・marker を生成する条件 | assertion rewrite、fixture、hook、例外を保存する証明が必要 | 中〜大 | profiler が特定した箇所だけ |
| prewarm を collection と重ねる（T-2616） | 当該 sample の直接対象は **28.44 秒**。28 走の対象窓は 20.7〜41.1 秒。純減は競合次第 | 全 collection を維持可能 | 同じ snapshot・lock・session 分離・失敗伝播を保つ必要。先行実験は赤あり | 中 | **優先候補、保証済みとは扱わない** |
| memo 内の HEAD/path/cache 掃除・保存を効率化 | **測れない**。production resolver 外にも費用がある | 可 | cache の鮮度・排他・破損拒否・session 分離を保存 | 小〜中 | 三分解後に判断 |
| production resolver の同値な高速化 | **測れない**。helper 全時間を削減余地と数えない | テスト集合は不変 | resolver の受理・拒否、証拠読取りを同値にする証明が必要 | 中〜大 | 本 wave は実装せず、候補自体は閉じない |
| 同じ内容の読込みを事前に行い page cache を温める | 温ならほぼ 0、他は**測れない**。費用の前払いになり得る | 可 | 内容・root・検査を変えなければ可 | 小 | 冷 I/O が支配すると判明した場合だけ |
| 同時走行との資源競合を減らす | **測れない**。CPU/I/O 待ちの実測が必要 | 可 | 同じ実行・gate を維持 | 運用変更 | 診断候補。queue を含む総時間で評価 |
| 何もしない | **0 秒** | 不変 | 不変 | なし | 現段階で探索終了にする案は不採用 |

次は除外する。

- **worker 数・配布順の変更:** D532 の制約に触れるため、本 wave の lever にしない。
- **collection の共有・自 shard 絞り込み:** D711／D1728 に触れる。
- **plugin や assertion rewrite の一括無効化:** 集合が一致しても検出力の保存を証明できない。
- **repo を別 root へ移すだけの案:** 実 repo、HEAD、lock、path を扱う検査の意味が変わる。
- **prewarm 2 本の再並行化:** 現行で並行化済み。oracle 約 0.13 秒に対し receipt 約 31 秒なので主要 lever ではない。
- **テスト開始後への単純な背景化:** 先行 README:86–98 では実行窓増大・赤が記録されており、採らない。

## 短縮の可否 — 1 行の結論

**条件つきでできる：全 collection・既存の拒否条件を保存し、二重 canonical 化の削減と prewarm の重なりを同条件で測れば短縮余地はあるが、全走 5 分以内の保証には足りない。**

## 総括

親の判断は、**P1-E は維持、P1-B の「内訳確定済み」は撤回、P1-C は比較条件を揃えて再測定、P1-D の候補を拡張**とする。実装を増やす前に、外部 probe で主要関数と待ち時間を一度分けるのが最も安い。

5 分への算術は、実行窓が変わらない仮定で次のとおり。

- `pre + disp` の提示範囲は **76.1〜100.2 秒**。
- wall **296.2 秒**から両方を消すと **196.0〜220.1 秒**。
- wall **604.5 秒**から両方を消しても **504.3〜528.4 秒**。**5 分には入らない。**

これらは別走の extrema を使った範囲であり、対応する走の予測値ではない。最遅 shard が shard-0 でなければ、shard-0 の `disp` を全体 wall から引くこともできない。

最長単体 **208〜214 秒**は 300 秒より短い。したがって固定費削減は近傍の走には十分意味がある。しかし **604 秒級の走は、この二区間を全部消しても救えない**。本調査は実装・テスト実行を行わず、静的検査と既存成果物の読取りで判断した。