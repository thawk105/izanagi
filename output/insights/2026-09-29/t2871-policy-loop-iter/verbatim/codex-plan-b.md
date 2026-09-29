## 総括

**案 1 を推奨します。** 既存の系列 campaign dir に `loop_state.json` と `policy_history.jsonl` を残し、pair の候補と stock だけを iteration 番号入りの別 campaign identity で測ります。同じ submit checkout と out_root を使い続けられ、job ごとの claim は one-shot のままです。

現状は [driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:574) が系列と計測に同じ cfg・layout を渡します。2 本目は同じ claim leaf で拒否されます。さらに、claim だけを回避しても [WAL の terminal variant skip](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/loop.py:763) により stock 対照が欠けます。両方を解くには、**iteration ごとに計測 identity と WAL を変え、同じ pair 内では候補と stock の identity を一致させる**必要があります。

## 案の比較表

| 観点 | 案 1：系列 layout と iteration 別計測 layout | 案 2：job ごとに別 out_root | 案 3：B-5 型の測定点 identity と系列履歴 |
|---|---|---|---|
| (a) claim | iteration ごとに別 leaf。各 leaf の one-shot 性を維持 | out_root ごとに同名 leaf。one-shot 性は維持するが、[異なる out_root 間では claim による排他がない](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/campaign_claim.py:383) | 測定点ごとに別 leaf。候補と stock を別 identity にすると現行の同一 authorization session を共有できないため、**pair を一測定点と定義する**必要がある |
| (b) stock skip | pair ごとに新しい WAL。候補と stock は同じ計測 WAL に入り、前 job の stock は skip 対象外 | 新しい out_root の WAL は空。skip を回避 | pair を一測定点にすれば回避。候補と stock を個別測定点にすると現行 session 契約に不適合 |
| (c) 系列状態 | 既存の系列 dir 一か所。walltime 起点、iteration、self_history を共有。critic digest は当該計測 WAL から作り系列 dir に置く | 前 job の tree から状態と digest 材料を転送する手順が必要。出所が複数 tree にまたがる | 系列履歴の置き場を別途定義する必要がある。案 1 と同じ系列 dir を選べば実質案 1 |
| (d) login 操作 | `emit-coder-input` と `record-reject` は従来の系列 cfg・dir を参照。preview も不変 | login 操作のたびに現行 tree と転送先を選ぶ必要がある | 系列 dir を明示して login 操作を接続する改修が必要 |
| (e) 変更面 | driver、焦点 test、runbook。指定された非変更 file に触れない | driver に状態の取込み・転送元選択を追加し、checkout 運用も変更 | 案 1 と同等以上。測定点の単位を誤ると session 設計にも波及 |
| (f) 2 process 結合検査 | 同じ out_root で 2 回起動し、別 claim leaf・別 WAL・単一系列状態を確認できる | 2 out_root と状態転送の fixture が必要 | pair 単位なら案 1 と同型。個別測定点なら既存 session と衝突 |
| (g) runbook | 同じ checkout で直列に 2 job。各 job の計測 dir を読む箇所だけ更新 | job ごとの checkout 作成、状態転送、参照元管理が増える | 系列 dir と測定点 dir の対応を毎回扱う。pair 単位なら案 1 と同型 |
| (h) 既存 A・B | 系列 cfg の identity を維持するため既存 dir を読み替えない | 旧 tree を系列の正本として扱い続けるか、移すかの選択が必要 | 既存 dir を系列 dir とするなら維持できるが、それは案 1 |

## 推奨案と理由

計測 cfg は系列 cfg の `search_config` に、driver が系列 `loop_state.iteration + 1` から得た整数 key、例えば `policy_iteration` を加えて作ります。operator の argv から番号を受け取りません。[`default_cfg`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:121) 自体の系列 identity は変えず、bootstrap と r2 にも key を加えません。

候補と stock の二つの `run_campaign` 呼出しには**同じ計測 cfg**を渡します。[authorization session](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/loop.py:139) は campaign identity、protocol digest、out_root を束縛するため、stock だけ別 identity にすると拒否されます。当該 pair の critic digest は当該**計測 campaign の admitted WAL**から生成し、critic が読む従来の系列 dir の `silo_policy_loop_digest.txt` に出力します。候補の `_result_history` と stock の `_stock_result` も計測 WAL を読みます。系列の履歴と budget は系列 layout を読み書きします。

## 推奨案の変更計画 (file:line)

- [driver:121–143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:121)：系列 cfg から `policy_iteration` 入り計測 cfg を作る小さな helper を追加する。`default_cfg` の既存 identity、bootstrap、r2 は維持する。
- [driver:228–278](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:228)：`_result_history` に計測 layout を渡す。既存の outcome・verifier digest の射影は変えない。
- [driver:365–430](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:365)：pair の `run_stock_control` と `run_one_iteration` に同じ計測 cfg・layout を渡す。`ensure_resumable_attempts` と `_stock_result` も計測 layout に合わせる。二つの `run_campaign` 呼出し本数と gate 順序は維持する。
- [driver:433–477](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:433)：`drive_iteration` は系列 layout の state から次番号を決め、state・history は系列 layout、評価・admitted view は計測 layout に振り分ける。digest の出力先だけ系列 layout とする。`stopped-before` は計測を認可せず既存の counter を維持する。
- [driver:574–678](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:574)：pair 分岐で state を一度読み、同じ次番号の計測 cfg を候補・stock に配る。候補例外後の stock も同じ cfg・session を使う。`emit-coder-input`、`record-reject`、bootstrap、r2 の系列 cfg 選択は変えない。
- [焦点 test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:599) と [runbook §1(f)(g)・§3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/docs/phase3-silo-policy-runbook.md:98) を更新する。`loop.py`、`campaign_claim.py`、`p3_s4_loop.py`、job body は変更しない。

## 失敗時の挙動

- **候補例外：** 現行の `drive_iteration` と同じく、その iteration の `eval-exception` を系列履歴へ記録し、系列 counter を進める。[pair 分岐](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:643) は同じ計測 identity で stock を試み、最後に候補例外を再送出する。認可前の候補失敗なら stock がその identity の claim を最初に取得し得る。
- **stock 例外：** 候補の counter と履歴は既に残る。候補例外が無ければ stock 例外を送出し、候補例外もあれば現行どおり候補例外を優先する。stock 成功を履歴に捏造しない。stock の成立は当該計測 WAL と job stdout で確認する。
- **`stopped-before`：** 系列 counter は増やさず履歴も追加せず、stock を起動しない。計測 claim を作らない。
- **再投入：** 異常終了後の再投入を「同じ iteration の再測定」とは扱わない。既に state が進んでいれば次番号になり、進む前に process が落ちていれば同じ番号の one-shot claim に拒否され得る。claim を退避しない。

## 焦点 test 計画

[既存の pair・例外・停止 test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:542)を新しい二 layout 契約に合わせる。数秒の結合 test では、親 test が一つの使い捨て out_root と proposal を用意し、同じ driver `main` を **別 process で直列に 2 回**呼ぶ。子 process へ fixture の monkeypatch を持ち込むには、環境変数で指定した小さな `sitecustomize.py` または `python -c` の harness から driver を import してから build・trace・bench だけを差し替える。`_authorize_measurement`、`acquire_claim`、`check_reservation`、authorization session は実体を呼び、Pegasus の reservation・attestation 入力は既存の [authorization session fixture](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_campaign.py:14535) と同じ作り方を子へ渡す。

各子で候補と stock の `run_campaign` 経路を通し、2 子の後に、計測 claim が異なる 2 file、各計測 WAL に候補と stock の attempt、系列 `loop_state.iteration == 2`、系列履歴が 2 行、stock が両回 `certified-stock`、系列 dir の digest が 2 回目の計測 WAL に由来することを確かめる。負例は iteration key を除き、2 process 目が実 `ClaimError` になることを確かめる。実 C++ build や性能測定はこの test に含めない。実行は親が `tools/run_tests.py` 経由で行う。

## 変異の事前登録候補

| 変異 | 焦点 test で落ちるべき条件 |
|---|---|
| 計測 cfg の iteration key を削除 | 2 process 目の claim が衝突 |
| stock に系列 cfg を渡す | 同一 session の identity binding mismatch |
| stock に系列または前回の計測 layout を渡す | 2 回目の stock が skip、または `certified-stock` にならない |
| `_result_history`／critic digest の読取りを系列 WAL に戻す | 2 回目の候補結果・digest の帰属が合わない |
| state・履歴の書込みを計測 layout に移す | 系列 counter 2、系列履歴 2 行、login の self_history が崩れる |

## runbook 書き換え要点

[§1(f)](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/docs/phase3-silo-policy-runbook.md:98) に、同じ submit checkout で pair job を直列に投入し、各 pair の候補と stock は iteration 別の同じ計測 campaign に入ることを書く。walltime の起点は系列 dir の `loop_state.json` のままと明記する。[§1(g)](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/docs/phase3-silo-policy-runbook.md:119) は、critic が読む digest と履歴の場所を従来の系列 dir とし、digest の材料は当該計測 campaign の admitted WAL と明記する。[§3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/docs/phase3-silo-policy-runbook.md:147) の「1 loop campaign あたり pair job 1 本」の制限を、新しい系列／計測 dir の対応と one-shot の説明に置き換える。bootstrap・r2 と login 操作の command は維持する。

## brief との食い違い

brief の「claim を解いても stock が skip される」は、**同じ計測 campaign の WAL を再利用する場合**に正しいです。[skip は campaign layout の WAL を replay](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/loop.py:763)して決まるため、案 1・2・pair 単位の案 3 では回避できます。

「同じ iteration を 2 度測れば ClaimError」は、**同じ計測 identity を再使用した場合**の性質です。現行の [例外処理](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:452)は候補例外でも counter を保存するため、通常の次回起動は次 iteration になり、同じ claim leaf を再使用しません。process が checkpoint 前に落ちた場合などには同じ番号が再選択され、claim が拒否します。

K2 の[別 out_root の先例](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair-resubmit/setup-submit-trees.sh:5)は確認できます。一方、「Pegasus で系列状態を job 間継続した先例が無い」は提示された K2 資料からは全体の不存在まで証明できません。少なくともこの K2 手順は状態継続の実装例ではありません。

## scope 外候補

同じ系列に複数の pair job を並行投入するための counter 予約・直列化、異常終了した iteration の再測定方針、別 out_root 間の排他を担保する台帳は今回追加しません。今回の運用は runbook の同一 checkout・直列投入を前提にします。

この段では読み取り専用の静的検査を行いました。実装・test 実行はしていません。