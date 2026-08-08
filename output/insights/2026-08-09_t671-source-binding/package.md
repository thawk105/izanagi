# 裁定パッケージ — [T-671] 汎用 certified producer の source binding + t530 件 6 (campaign id 分裂) (2026-08-09)

wave = `dev-wave-t671-source-binding` / branch = `worktree-dev-wave-t671-source-binding`
逐語 = 同ディレクトリの `verbatim/` (段 1 brief・段 1 実測 A/B・段 2 プラン・段 3 レンズ A/B・段 4 裁定)

**本 wave は実装していない。** ユーザー裁定 (2026-08-09 rulings2 件 1)「[T-671] = 設計 wave 起票を承認。
t530 wave の裁定パッケージ件 6 (campaign id 分裂、[T-657] 直結) と束ねてよい」に従い、
設計択一だけを返す。本番コードの編集はユーザー指示により禁止されていた。

---

## 何が問題か (1 段落)

certified な選択結果・材料レポート・試行台帳は「どの環境契約 (contract) で測ったか」を
`contract_sha256` と activation record の hash で名乗る。しかし **その契約を読み込み・解釈・強制する
Python コード自身の bytes は、どこにも束縛されていない**。silo と qualification は独立に 2 つの機構で
loader を code identity へ入れているのに、汎用 certified 経路 (campaign loop の COMMIT、材料レポート、
WAL) は 1 つも呼ばない。同時に、中断中の [T-530] は契約 hash を campaign identity へ入れる設計を
持っており、これが land すると契約世代が変わったとき同じ論理 campaign が 2 つのディレクトリへ
静かに分裂する。両者は同じ軸を持つ — **書込み時点の ambient な現在値を焼くのか、権威を最初の
durable write で固定して以後は引き継ぐのか**。

---

## 実測した事実 (本 wave で測定。反実仮想と一般化は次節へ分けた)

### A. source binding の非対称 (実測、file:line で再現可能)

1. **silo は 2 module を live bytes で束縛する。** `silo_ladder_rung1.py:254-277`
   `_runtime_module_paths()` に `env_contract.py` (:263) と `env_contract_activation.py` (:264) を含む
   閉集合。`runtime_modules_binding()` :280-287 が `sha256_file()` :246-251 で hash し、
   receipt の `bindings.runtime_modules_sha256` (:2416, :2438, :2519) と submit document の
   `binding.runtime_modules` (:4456) へ残す。検証は `verify-result` (:4817, :4838) →
   `validate_current_bindings()` :3517-3539 で fail-closed。
2. **qualification は同じ 2 module を git blob で束縛する (独立実装)。**
   `orchestrator/qualification/contract.py:38-76` `REQUIRED_CODE_IDENTITY_PATHS` (:64-65)、
   `series_identity()` の `preimage["code_identity"]` (:485, :528-530)、検証は
   `qualification/identity.py:112-144` が `git cat-file blob <commit>:<path>` と exact 照合。
   **silo と共通 helper を持たない。**
3. **どちらも loader 2 本より広い閉包を束縛している。** silo は activation JSON・execution guard・
   calibrator・verifier 群を、qualification は pipeline・build admission・guard・site policy を含む。
4. **汎用 certified 経路は 1 つも束縛しない。** campaign loop の認可 (`loop.py:61-89` →
   `execution_guard.py:107-170`) が見るのは `contract_sha256` と `activation_serial` /
   `activation_state_sha256` だけ (`execution_guard.py:44-104`、:77-78 と :96)。
   材料レポート (`layer3_report.py`) は `env_contract` を参照すらしない。WAL の
   `source_bytes_sha256` (`wal.py:792-902`) は genome の source を指す。
   `build_admission.py` は `env_contract` を import しない。
5. **唯一 loader bytes を見る層は generic 経路へ未配線。**
   `certified_writer_preflight.py:85-126` `_verify_loaded_repo_modules` は import 済み module 全部を
   commit blob と照合するが、呼ぶのは `tools/pegasus/t126_qualification.sh:101` と
   `floor_campaign.sh:83` の投入前 preflight だけ。
6. **activation 参照は loader 改変を検出しない。** `_state_sha256()`
   (`env_contract_activation.py:130-133`) の入力は activation record JSON 自身のみ。
   `validate_activation_records` (:332-422) が保証するのは chain・registry 一致・serial 連番・
   head pin (`env_contract.py:373-376`) で、すべて data レベル。
   これは [T-529] の設計メモが既に明示していた前提でもある。
7. **既存の source closure 機構はどれも汎用経路を覆わない。** silo / qualification / preflight /
   `known_axes.source_closure` (`s1_known_axes_freeze.py:974-1054`、genome 生成器のみ) /
   FROZEN_MANIFEST (テスト fixture)。
8. **preflight は「ディスク上の bytes」を検査し、「実行中の bytes」を検査しない。**
   `certified_writer_preflight.py:85-100` は import 済み module の `__file__` を読み直す。
   import 後の差し替えは検出できない (構造的な限界。案の優劣を分けない)。

### B. campaign id 分裂の機序 (実測)

9. **main の campaign id に契約は入らない。** `ident.py:125-144` `canonical_preimage()` の
   pre-image は spec_content / ccbench_commit / search_tag / search_config / trial。
10. **t530 branch は契約 hash を id の pre-image に入れる。** `ident.py:52-74`
    `bind_environment_contract()` が `search_config` へ焼き (`model.py:27-28` の共有 wire key)、
    `loop.py:127-134` が `_authorize_measurement()` の戻り (= **その瞬間の current 契約**) を
    束縛してから `campaign_id(cfg)` → layout を確定する。COMMIT 2 口 (`pipeline.py:1028, 1088`) と
    validator (`wal.py:947-985`) も同じ H を要求する。
11. **`lookup()` / `authorize()` は常に activation head の current を返す** (`env_contract.py:606-625`,
    :636-663)。`resolve_by_contract_sha256` (:671-699) は ever-active 解決だが**履歴検証専用**であり、
    `execution_guard._contract_from_authorization` は terminal state の active row しか受理しない。
12. **ambient 直呼びが 15 か所超残る** (`p3_s4_loop.py:752,865,998,1085`、
    `p3_s4_loop_sort.py:197,230,322,430`、`s8a_trigger_sweep.py:288` ほか)。
    lock に固定した契約世代を resume 時に引き継ぐ仕組みは**現存しない**。
13. **書込み前停止は `run_campaign` 内だけでは達成できない。**
    `p3_s4_loop.py:878` が `layout.ensure()` → `ensure_resumable_attempts()` を実行してから
    `run_campaign` を呼ぶ (親が再現)。
14. **読出しは id 非依存だが 2 root で止まる。** `replay.py:89-107` `discover_campaign_dir` は
    prefix glob。同一 slug で 2 root が WAL を持つと `FileNotFoundError` (fail-closed だが可用性破断)。
15. **guided lane は t530 で解決済み。** `guided.py:172-175, 199-201` が
    `require_environment_contract=False`、WAL 側も lock にキーが無ければ検査を skip。
16. **既存 30 campaign は H も `build_admission` も持たない** (実測 30/30)。
    main の `canonical_preimage` は pre-T343 cfg からの id 再計算自体が不可能なので、
    **到達不能は status quo**であり t530 や g2 活性化が開ける穴ではない。
17. **g2 は未活性化** (`env_contract_activations/` は serial 1 のみ)。
18. **D125 決定 (2) の実装は実在する。** `p3_s4_loop_trigger_gating.py:92`
    `_CAMPAIGN_ENV_KEY = "measurement_env"`。したがって
    `docs/orchestrator-design.md`「env は campaign 同一性に含めない」は**既に部分的に破られている**
    (本 wave が作った緊張ではない)。
19. **docs 予算の実測**: core 8,655 / workers 4,526 / mutation 3,689 / operations 8,329 =
    **aggregate 25,199 / cap 25,200 (残り 1 byte)**。`check_docs.py` は現状 rc=0。

### C. 実測ではない — 反実仮想と将来経路 (証拠強度を区別する)

- 「g2 活性化後に dirty loader で certified 成果物が作られる」は**未観測の将来経路**である。
  現時点で g2 は未活性化であり、汎用 certified 経路の loader drift を発火させる計測は存在しない。
- **loader 束縛の欠落は g2 固有ではない。** 同じ穴は現在の g1 でも成立している
  (`output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/` の lock・WAL・
  layer3_report はいずれも loader authority を持たない)。**g2 活性化は発覚の契機であって発生条件ではない。**
- 分裂の必要条件に「未完了 campaign」は**入らない** (段 3 レンズ A が親の一般化を訂正)。
  t530 は旧 root を探す前に current H で id を確定するため、g1 campaign が terminal でも
  g2 で同じ論理入力を再実行すれば新 root ができる。
  「g2 活性化 → t530 land」の順序でも、無束縛 root と H 束縛 root が両方 WAL を持てば 2-hit になる。
  **成果物の形として「分裂」と「断絶」は区別できない。**

---

## 裁定を求める択一

### R1 — 束縛する source 閉包をどこまでにするか (争点 A の中核)

**この問いが本 wave で最も攻撃された点である。** 段 1 brief は「silo と qualification という
独立 2 実装があるから `DW-G03` (族一般化には独立 2 例) を満たす」と書いたが、段 3 の 2 レンズが
独立に反証した — `DW-G03` が要求するのは**同型欠陥が異なる producer/consumer で 2 件再現すること**
であって、既に binding を持つ実装が 2 つあることではない。親はこれを **brief の誤りとして訂正した**。
かつ silo も qualification も loader 2 本より広い閉包を束縛しており、「exact 2-path」への縮約に
根拠がない (実測 3)。

- **(a) loader 2 module のみ** (`env_contract.py` + `env_contract_activation.py`)。
  実装最小。ただし契約を**強制する** `execution_guard` / `loop` / `pipeline` / `wal` が dirty でも
  「clean な commit 由来」を名乗れる (レンズ A-01・B-03)。この場合、成果物が主張してよいのは
  「契約 loader の bytes が記録 commit と一致する」だけであり、**「certified 経路が source-bound」と
  名乗ってはならない**。
- **(b) enforcement 閉包まで広げる** (loader 2 本 + `execution_guard` / `loop` / `pipeline` / `wal` /
  `ident` / `artifact_admission`)。qualification の `REQUIRED_CODE_IDENTITY_PATHS` と同じ考え方。
  閉包の維持コスト (ファイル追加のたびに更新) が増え、閉包自体が drift する。
- **(c) qualification の既存 exact set を汎用経路でも再利用する。** 新しい閉包定義を作らない。
  ただし qualification 用に選ばれた集合が汎用 campaign にとって過不足かは未検証。
- **(d) repo commit 1 本だけを記録し、個別 file hash を持たない。** 最小。dirty tree の検出は
  preflight に委ね、durable ref は commit だけにする。

**親の推奨: (a) を選ぶなら主張を (a) の範囲へ限定すること、実際に「certified 経路の source binding」を
名乗るなら (b) か (c)。** どれを選ぶにせよ **R7 (発火計測を先に作る) が前提**である。

### R2 — 争点 B の停止方式

- **(a) identity と authority を分離する (段 2 の R-B2、段 2 の推奨)。** 契約 hash を campaign id の
  pre-image から外し、`campaign.lock` の authority 欄へ置く。resume 時に pinned 値と current を
  比較し、不一致なら durable write より前に停止する。世代を跨いで続けたいときは明示 `trial`。
- **(b) t530 の H 入り id を維持し、lineage 事前 scan で停止する (R-B3)。** t530 の golden id を保つ
  最小案。**既知欠陥**: 並行起動で両者が 0-hit を見て別 layout を各々 atomic acquire しうる
  (lineage 全体の lock が無い、レンズ A-11)。
- **(c) 旧世代での resume を許す (R-B1)。** pinned H で historical-resume 専用 authority を発行する。
  **これは受理集合の拡大である** — 引退した契約で新しい certified 計測を許すことになるため、
  親は選べない。採用するなら「旧 calibration / attestation を現マシンへ再適用してよい」という
  独立の裁定が要る。
- **(d) 分裂を仕様化し、`discover_campaign_dir` を H-aware にする (R-B4)。** 可用性だけが戻る。
  同じ campaign の未完了台帳が別 root へ静かに移った事実は残る。

**親の推奨: (a)。** ただし R3・R4・R6 の条件付き。

### R3 — v1 (現行) lock の位置づけ

(a) 案が v2 envelope を導入する場合、既存 30 campaign と既存 report を v1 のまま残すことになる。

- **(a) v1 = read-only historical。** 再開を許さない。既存 replay は読めるが追記は不可。
- **(b) v1 = 条件付き resume 可。** どの条件かを明示する必要がある。
- **どちらを選んでも anti-downgrade 規則が要る** (レンズ A-05): v2 の外側 envelope を剥がして
  inner identity を v1 lock として提示すれば campaign id は変わらないため、authority を消した WAL が
  同じ id の v1 として再受理されうる。現行 `artifact_admission.py:487, :637, :699` は
  `build_admission` を持つ v1 を post-policy lane で受理する。

### R4 — D125 決定 (2) の `measurement_env` をどうするか

段 2 は「R-B2 は D13 の env 非 identity 規則を回復する」と書いたが、**これは不正確**である。
`p3_s4_loop_trigger_gating.py:92` の `_CAMPAIGN_ENV_KEY = "measurement_env"` が残る限り、
env は依然 campaign id を分ける (実測 18)。

- **(a) `measurement_env` を保持する** (D125 決定 (2) をそのまま維持)。
  「契約 hash は id に入れないが env tag は入れる」という非対称を明文化する。
- **(b) D125 決定 (2) を supersede し、env も id から外す。** `docs/orchestrator-design.md` の
  規約へ戻る。ただし D125 が根拠にした「Pegasus 実行が同じ campaign root を指す」問題への
  代替策が要る。
- なお t530 件 5 (D125 決定 (2) を decisions 上どう supersede 表記するか、T-343 が既に破っている
  事実を含む) は本件と同じ面を持つ。**R4 と t530 件 5 は同時に裁定するのが自然。**

### R5 — 世代境界の比較粒度

v2 authority は `contract_sha256` に加えて `activation_serial` と `activation_state_sha256` を
記録しうる。一方、resume 前の比較を H だけで行うと不整合が生じる (レンズ A-09)。
activation state hash は**全 env** の `active_contracts` を覆うため、Pegasus だけが g2 へ進んで
Linux が g1 のままでも state hash は変わる。

- **(a) 対象 env の H だけを比較する。** 他 env の活性化で既存 trial が拒否されない。
  ただし記録した full authority digest は不一致のまま残る。
- **(b) activation state 全体を比較する。** 厳密だが、他 env だけの活性化で既存 resume が拒否される
  (受理集合の縮小)。
- **(c) 記録は full、比較は対象 env の H。** 差異を成果物に残しつつ resume は通す。

### R6 — 「durable write より前に停止」を実現する層

`run_campaign` の内部だけを直しても成立しない (実測 13)。

- **(a) 全 certified caller の最初の durable boundary を統一する。** `p3_s4_loop.py:878` のように
  caller 側で `layout.ensure()` する経路をすべて改修する。実装量が増える。
- **(b) `layout.ensure()` / `ensure_resumable_*` の側に authority 検査を移す。** caller を触らずに
  boundary を下げる。ただし authority を持たない正当な呼出し (guided / legacy) の扱いが要る。
- **(c) 「書込み前停止」を諦め、事後に検出して隔離する。** 弱いが実装量は最小。

### R7 — 実装の前提条件 (`DW-G04`)

**段 3 の 2 レンズが独立に一致した最重要点**: 提案されたどの gate も、**現在の production artifact で
正に発火させられない**。既存 30 campaign は H も `build_admission` も持たず、汎用経路の
loader drift を発火させる計測は存在しない。段 2 プラン自身もこれを認めている。

- **(a) 発火計測を先に作る。** 実装 wave の第 1 段を「loader drift が layout / WAL より前に拒否される」
  「記録 commit blob 不一致を admission が拒否する」の 2 本の決定的テストにし、それが赤で落ちることを
  確認してから production を書く。
- **(b) 核となる vertical slice だけ実装し、周辺 (report v4 / historical reader / caller 閉包) は
  実 artifact が出るまで延期する** (レンズ B-10、D205 の線引き)。
- **(c) 設計メモに留め、実装しない。**

**親の推奨: (a) + (b) の併用。**

### R8 — 順序 (T-657 活性化 / t530 land / 本件実装)

- **T-657 の g2 活性化は止めなくてよい。** 現在 t530 は未 land、g2 は未活性化、H 束縛の production
  campaign は 0 本なので、争点 B の発火条件は成立しない。並行 wave
  (`dev-wave-t657-t660-g2-activation`) を待たせる必要はない。
- **ただし t530 の land は R2 の統合まで保留する必要がある** (レンズ B-06)。t530 は旧設計
  (H を id へ入れる) の未 land commit 3 本を抱えており、これが先に land すると分裂条件が成立する。
- **争点 A には無保護期間がある** (レンズ A-10)。loader 束縛の欠落は g1 でも成立しているため
  (実測 C)、「活性化前に閉じる必要はない」は「いつ閉じてもよい」を意味しない。
  活性化から R1 実装までに生成された certified 成果物は authority なしで固定される。
- **選択肢**: (a) 上記のとおり T-657 先行・t530 保留・A は最初の g2 汎用 certified 出力より前 /
  (b) A も活性化の前提条件へ昇格させる (T-657 を待たせる) / (c) t530 を先に land し、
  R2 (a) か少なくとも (b) を t530 へ統合してから活性化する。

---

## 本 wave が新たに見つけた、別 ID で起票すべきもの

- **caller inventory 検査の部分的恒真性** (レンズ A-04、親が再現)。
  `orchestrator/tests/test_campaign.py:2513` の `direct_sinks` 側は
  `assert any(... for call in calls)` (:2553) なので、`authorization_contract` keyword を持つ
  呼出しが同ファイルに 1 本あれば、他の呼出しは keyword なしでも通る
  (`expected_run_calls` 側は `all(...)` で正しい)。また `expected_run_calls` は固定 dict + `ast.Name`
  照合のため、新規ファイル・alias・attribute 呼出しを検出しない。
  **成果物影響**: 新規または別形態の writer が authority なしの COMMIT を書いても、閉集合検査は緑のまま。
  これは既存 gate の弱点であり [T-671] の所有ではないため、**新規タスクとして起票する**。

## t530 パッケージの他項目との重複 (二重起票しない)

- レンズ A-06 (raw reader / freeze / offline report が proof chain を迂回する。
  `s1_known_axes_freeze.py:221,263`、`s1_report.py:329`、`s8b_oracle_report.py:1275`) は
  **t530 件 2 と同一面**。本件の source binding を実装しても、これらの consumer は
  authority なしの COMMIT を certified 材料として採用しうる。
- レンズ A-07 (S8b private lock が `{manifest_sha256, block_id, campaign_id}` だけを atomic acquire し、
  同 layout へ certified COMMIT を書く。`s8b_oracle_driver.py:979, :989, :1356`) は
  **t530 件 3 と同一面**。
- **したがって R1〜R8 をすべて実装しても「proof chain が全経路で完結した」とは名乗れない。**

## 実装時の前提条件 (設計択一ではないが、実装 wave が先に決めるもの)

- **Layer3 report の参照 domain と field 名** (レンズ A-12・B-07、D75)。現行
  `_report_primary_refs` (`layer3_report.py:161, :178`) は WAL / whiteboard だけを再導出し、
  `source_refs` との exact bijection を要求する。schema (`layer3_schema.json:21`) も `wal|wb` のみ。
  authority ref を足すなら、既存 `source_ref` / `source_refs` と型・意味が衝突しない exact 名を
  先に確定する。
- **脅威モデルの明示**: 全案に共通して、preflight 系の検査は「ディスク上の bytes」であって
  「実行中の bytes」ではない (実測 8)。import 後の差し替えは検出できない。
  防ぐなら out-of-process の署名 / attestation が必要で、これは D205 の範囲を超える。
  **成果物には「accidental / dirty checkout と履歴の取り違えまでを防ぐ」と書くべきで、
  「悪意ある in-process 改変を防ぐ」と書いてはならない。**
- **docs 予算** (実測 19): `docs/dev-wave/**` へ規範文を足す実装は aggregate 残り 1 byte に阻まれる。
  **[T-664] が「依頼された 2 経路 (陳腐化ルール削除・テスト化) では予算が空かない」と確定させた**
  (経路 A = 削除候補ゼロ、経路 B = `DW-O23` の 449 bytes 1 件のみで同 wave の親は非推奨)。
  したがって本件の実装が規範文を要求するなら、前提は [T-664] ではなく **[T-313] の実装**である。
  規範文を必要としない形 (コードと計測だけで閉じる) を選べるなら、この前提は外れる。
  本パッケージ自体は `output/insights/` で予算対象外。

---

## 共通の設計原則 (2 争点は同型である)

段 2 が提案し、親が採用した 1 文:

> **ambient な current 値は、最初の durable write の authority を解決するときにだけ使う。
> その exact identity を atomic lock へ固定し、resume は記録された authority を先に読んで
> current と一致しなければ書込み前に停止する。歴史 consumer は current の live 状態ではなく、
> 記録された commit / activation chain を検証する。**

この原則は次の 3 つを同じ構造で防ぐ。

1. source を編集した後に、過去の artifact が current-live 不一致で壊れること (silo 型 live hash の弱点)。
2. 活性化の後に current H が別 id を作ること (争点 B)。
3. lock 作成後に ambient 値が変わり、同一 WAL へ異なる世代の record が混ざること (t530 が閉じようとした穴)。

---

## 却下した案 (再提案しないこと)

- **契約文・docs pin・運用宣言だけで「source-bound」「resume-pinned」と名乗る案。**
  実 producer の bytes / H を拘束しない。[T-665] 段 3〜4 が同型の案を否定している
  (契約文を足すだけでは docs pin と同じ強度で、解こうとしている問題の再演)。
- **loader hash を自己申告するだけの案。** COMMIT の field は増えるが、live bytes ↔ commit blob の
  write gate と独立 consumer が無ければ受理集合は変わらない。
- **source binding を `search_config` へ入れる案。** loader を編集するたびに campaign id が分裂し、
  争点 B を source 側で再現する。
- **`ever_active` 解決をそのまま historical write authorization とみなす案 (親の provisional P2)。**
  履歴検証と新規計測許可の混同であり、現行 guard の current-only gate を実質的に弱める。
  **段 2 が親の裁定を反証し、親が撤回した。**
- **silo 型 live hash を汎用化する案 (R-A3)。** 採用後の成果物が次の loader 編集で歴史検証不能になる。
  qualification の commit-backed 方式より弱く、凍結成果物の原則にも合わない。
- **既存 30 campaign や既存 v2/v3 report を新 schema へ再生成する案。** 凍結 bytes と歴史受理集合を
  不必要に変える。

---

## この wave の証拠の状態 (隠して引用してはならない)

- **実測はすべて本 wave で取った** (repo 実読、`check_docs.py` 実走、byte 集計、既存テストの逐語確認)。
  実測・反実仮想・一般化を上の A / B / C 節で分離してある。
- **本番コードは 1 行も編集していない** (ユーザー指示)。テストも追加していない。
- **段 3 は 2 レンズとも NO-GO** (A = sol / must-fix 11・nit 1、B = luna / must-fix 7・nit 3)。
  親は 1 件 (A-04 を [T-671] の must-fix とすること) を scope 外へ、
  2 件 (親自身の brief P1 の `DW-G03` 解釈、実測 B の「未完了」条件) を**親の誤りとして訂正**した。
- **変異 matrix は免除** (`DW-S04` の実装差分ゼロ条項)。**受入全走は免除していない。**
