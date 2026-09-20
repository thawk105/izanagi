## 所見

1. **主張:** `.git` を除いた node-local 複製は、現行 suite の collection に失敗する。P1-C は静的に反証できる。  
   **根拠:** module 直下で `git rev-parse HEAD` を `check=True` 付きで実行する箇所がある。
   - `orchestrator/tests/test_t1998_stock_inline_pair.py:63`
   - `orchestrator/tests/test_codex_worker_launch.py:36`
   - `orchestrator/tests/test_t1259_qsub_env_delivery_probe.py:53`

   **親の記述との差:** 「不一致なら local 条件を無効化」では、主たる対照腕を最初から失う。単純に worktree の `.git` ファイルをコピーしても、元の Lustre 上の gitdir を参照しうる。  
   **重大度:** 高  
   **修正案:** 同一 HEAD と source bytes を持ち、Git 管理情報も node-local で解決できる複製方法へ変更する。最初の warm-up で collection 成功と nodeid 集合一致を確認し、失敗した腕の反復には進まない。テスト除外・Git 呼出しの偽装で通してはならない。

2. **主張:** 現行の観測量では CPU・Lustre metadata・memory 帯域の寄与を一意に数値分解できない。  
   **根拠:** brief「弁別の読み方」「P1-B」。source と pyc の配置を同時に変更するため、配置差には metadata、データ読出し、client cache、path 解決などが混ざる。`user+sys` の増加も、memory stall 以外に周波数低下、kernel の競合処理、仕事量増加で起きる。逆に wall と CPU の差には runnable なままの scheduler 待ちも入る。  
   **親の記述との差:** 「local で消える分＝metadata」「CPU 時間増＝memory 帯域」はいずれも十分条件ではない。IPC 低下・cache-misses だけでも帯域飽和を確定できない。process 間で Python GIL／通常の import lock を共有するわけでもない。  
   **重大度:** 高  
   **修正案:** 完了判定を「配置効果・並列度効果と未識別部分の定量化」へ変更する。既存走に context switch、fault、CPU affinity／利用可能 CPU、可能なら周波数・帯域観測を添える。perf 不可時は帰属を未識別のまま残し、3 成分へ強制配分しない。

3. **主張:** 全 deselect の xdist 走と独立48 process 走との差は、受入の「controller 直列＋xdist 起動」の上限にならない。P1-A も成立しない。  
   **根拠:**
   - `tools/acceptance_shards.py:895` は worker ごとに全 item の正規化・割付・digest・shard 選択を行う。独立走では丸ごと欠ける。
   - `conftest.py:1862` は `dist == "loadgroup"` を ledger 読込み条件にする。brief の `-n 48` には `--dist loadgroup` がない。配送は `:2547`、worker 側検証は `:1658`。提示された約118 MB/shard の配送量そのものは、この射影資料では確認できない。
   - `conftest.py:2314` は shard spec 不在・collect-only・選択条件付きの走で early prewarm を開始しない。受入では `:2559` から開始し、worker は `:2516` で完了待ち経路を通る。
   - 全 deselect では `:2567` の controller の nodeid 走査対象が空になり、consumer 不在で prewarm も実行されない（`:920`, `:978`）。完全 collection の hold 検査も `-k` により経路が変わる（`:1972`, `:2180`）。
   - 現行 `pre` の終端は worker 内で記録した時刻の最大値（`acceptance_shards.py:935`, `:1092`）。digest の controller 照合は session 終了時（`:1063`, `:1097`）であり、その全費用を `pre` に含められない。

   **親の記述との差:** 欠けるのは通信だけではない。ledger の配送・検証、割付・再順序化、prewarm との資源競合／待ち、非空 nodeid の配送・照合を測れない。省略と追加費用が混ざる差には上限の保証がない。  
   **重大度:** 高  
   **修正案:** 全 deselect 走は「別 workload の起動較正」と明記し、上限という解釈を削除する。受入 `pre` まで結論するなら、同 checkout・同 plugin・loadgroup・非空の通常 collection を保った対照と、schema 外の測点が必要。conftest／gate の改変で代用しない。

4. **主張:** 温い prefix を新設する測定は、現行受入の cache 状態を再現しない。  
   **根拠:** brief「不変条件」「測定行列」、T-2617 §3.1・§9。dispatcher は `PYTHONDONTWRITEBYTECODE=1` を既定にする（`dispatch_compute.py:1853`）。  
   **親の記述との差:** pytest の assertion rewrite cache は cacheprovider と別物であり、`-p no:cacheprovider` はその無効化ではない。prefix 対応版では rewrite cache も prefix に移るが、当該環境の実装・読出し成功は射影資料から未確認。新 prefix を温めると、checkout 内の欠落・陳腐化した pyc を読む受入との差を消してしまう。  
   **重大度:** 中  
   **修正案:** warm-up では書込み禁止変数を **unset** する（文字列 `"0"` は許可指定にしない）。同一 interpreter・pytest・絶対 source path で通常／rewrite cache の利用を確認する。現行 checkout cache のままの N=1 対照を1走置き、温 prefix の結果とは分ける。

5. **主張:** 「同時開始 shard 群は全部72〜76秒」は提示データと矛盾し、反復2回の根拠にもならない。  
   **根拠:** `pre-recent-27-shards.txt:6` からの `8d490116` は、約2.3秒以内に3 shard が開始し、`pre=61.6 / 60.9 / 60.9`。`:1` の同時開始2 shard も `61.6 / 66.2`。ファイルには27行ではなく **29行**ある。T-2617 §1.1 の0.3秒は1 session の3 shard 間差で、反復誤差の推定ではない。  
   **親の記述との差:** 高い群だけを抜き出した一般化になっている。session digest は checkout 同一性の証明ではなく、欠測 shard・他 job・時間帯も未統制。ABBA は任意の共有負荷変動や cache の履歴効果を除去しない。  
   **重大度:** 中  
   **修正案:** P1-D/E の根拠を撤回し、ノード間同時性は未検証仮説として残す。N の順序も前半／後半で反転し、N=1 または48の参照条件を前後に置く。client stats は当該 client の観測であり、MDS 全体の負荷や他ノードの同時性を直接証明しないと明記する。

6. **主張:** 測定する wall の区間と出力負荷が統一されていない。  
   **根拠:** brief「scope」「測定行列」は `/usr/bin/time` による process 全体の wall と「独立48の最大 wall」を使う。一方、独立 `--collect-only -q` は大量の nodeid を出力し、全 deselect xdist とは出力量も終了処理も違う。  
   **親の記述との差:** process ごとの最大所要は、起動ずれを含む「最初の開始→最後の終了」と同じではない。stdout を Lustre のログへ出せば、測りたい読取り競合へ診断自身の書込みを混ぜる。  
   **重大度:** 中  
   **修正案:** process 別所要と cohort 全体の開始／終了時刻を両方採る。計時走の stdout/stderr は node-local の個別ファイルへ統一し、job 後に転送する。nodeid 比較は warm-up 出力を再利用し、collection 区間と process 全体を区別する。

7. **主張:** 「checkout を汚さない」の対象範囲と、環境設定を行う場所が不足している。  
   **根拠:** generic は空の環境 allowlist・clean 環境（`dispatch_compute.py:155`, `:1661`）で、cwd は repo 固定（`:1841`）。通常の dispatch 保存先は `repo/output/pegasus-dispatch`（`:3624`）で、`:3700` からディレクトリを作る。  
   **親の記述との差:** login 側だけで設定した prefix／AUTO_RECORD 等は generic へ配送されない。local 腕も script 内で `cd` しなければ元 checkout を測る。また「tracked tree が clean」と「checkout 配下への書込みゼロ」は異なる。  
   **重大度:** 中  
   **修正案:** 環境設定と腕ごとの `cd` を compute 側 script に明記する。dispatcher の運用記録と測定子の書込み禁止を区別し、ログ保存先を具体化する。既存 dispatcher の規律を変更する新 gate は足さない。

8. **主張:** 前提読取り script は universe を取得できず、欠測 worker を含む `disp` の完全性も確認していない。  
   **根拠:** `read_pre.py.txt:44` は存在しない候補 field を読む。実体は `report["observed_universe"]` の list（`acceptance_shards.py:1165`）。`:40` は first-start 欠落を黙って除外する。timeline の workers は観測された実行／lock 情報から構築され、起動 worker 全員の名簿ではない（`acceptance_shards.py:1147`）。  
   **親の記述との差:** 出力は全行 `universe=None` なので、26,040件という前提はこの script では裏付けられない。部分欠測では観測された最小 first-start が真の最小より遅くなりうる。なお、今回の timestamp は明示的な `+09:00` 付きで、時差誤りは確認できない。  
   **重大度:** 中  
   **修正案:** universe は list 長と nodeid 同一性を読む。first-start の有効／欠測数を併記し、`cf` 欠落時の `:.1f` 例外も避ける。naive timestamp を読む場合だけ生成側 timezone を明示する。

9. **主張:** 配置差を staging の効果上限へ転用する算術には条件が欠けている。  
   **根拠:** brief「弁別の読み方」。T-2617 §3.3 は、既存の `56−18≈38秒` を同条件差分ではなく、成分へ配分してはいけないと明記している。  
   **親の記述との差:** local 化で得た差には source・pyc・Git・cache 状態の変更が含まれる。staging／warm-up 費用を払う層も異なり、48 process の page cache 共有により N=1 の差を48倍できない。plugin の過去の単独 CPU 差も、48並列時の wall 差を保証しない。  
   **重大度:** 中  
   **修正案:** 「当該 N・当該 cache 条件での配置差」として報告する。複製と warm-up の所要を別記し、受入全体の短縮見込みは適用回数・償却条件付きにする。過去の38秒へ新しい差分を足し込まない。

## 測定行列の修正版 (差分だけ)

- **置換:** `.git` 除外 rsync を、同一 HEAD・source bytes と有効な node-local Git 管理情報を持つ複製へ変更。複製所要も記録する。Git 情報の容量が未確認なので staging 時間は現時点では見積れない。
- **前倒し:** 既存 warm-up を collection 成功・nodeid 集合比較に兼用する。追加走なし。件数一致だけには退行させない。
- **追加:** Lustre／現行 checkout pyc／prefix 未設定の N=1 を1走。温 prefix との差を確認するため、既存値から概算20〜90秒。
- **置換:** N を単調増加させず、前半と後半で順序を反転。ABBA だけで時間交絡を除去できたとは判定しない。
- **追加:** 同じ N=48 の参照腕を job 前後に計2走。時間変動の検出用で概算2〜4分。外部 Lustre 負荷の原因同定には使わない。
- **削除:** 全 deselect xdist 差を「controller 費用の上限」とする判定。2走を残すなら、起動較正という限定された目的に変更する。
- **置換:** 「3仮説の配分確定」を「配置／並列度の応答と未識別部分の定量化」に変更。受入 `pre` の分解を必須とするなら、通常受入経路を保つ対照設計を先に確定する。
- **追加走なし:** process 別・cohort 別時刻、fault／context switch、利用可能 CPU、計測可能な client stats を既存走へ付随記録。ログは node-local に保存する。

## 見つからなかったこと

- `git`、`.git`、`/work/`、`/home/`、`output/`、module 直下の呼出しを grep／AST で確認した。絶対 path 定数は見つかったが、それだけで collection 時に外部資料を読むとは断定できない。Git 不在による失敗は上記3箇所で具体化できた。
- **nodeid 集合比較の欠落はない。** brief は既に件数と集合の双方を要求している。
- `workers` が dict なのに list と誤読する欠陥はない。script は両方を扱う。今回の timezone 解釈にも具体的な誤りは見つからない。
- 現行 generic 経路では sidecar 継承の穴はない。dispatcher が除去する（`:1848`）。conftest の書出し条件は AUTO_RECORD ではなく SIDECAR（`:2734`）だが、現経路では到達要因が除かれる。ledger 読込み・配送から ledger ファイル更新も見つからない。
- 指定資料に記された範囲では、受入の集合縮小・worker 数変更・report schema 拡張・verifier 弱体化を実装する計画はない。診断内の集合比較自体を新しい恒久 gate と扱う理由もない。
- entry 1218 の file 別計測、T-2786 の base 構築を再測定する計画はない。ただし N=1／48 の総 collection 比較は T-2097 と重なる。今回の純増は同 checkout・計算ノード上の配置対照と N 応答である。

## 総括

高は **3件**。判定は **修正後 GO**。  
最重要は、観測された差を3原因へ一意に配分できるという完了判定の撤回である。  
実行面では `.git` 不在を直さなければ local 腕が失敗し、xdist 全 deselect 差から受入の上限も出せない。  
上記を修正すれば、改善実装・恒久 gate・台帳を追加せず、有効な診断として実測に進める。