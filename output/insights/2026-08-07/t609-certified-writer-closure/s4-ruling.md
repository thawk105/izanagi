# 段 4 裁定 — [T-609] certified writer の閉包 (plan v2)

親が段 2 プランと段 3 の 2 レンズを real/refuted で裁定し、plan v2 と変異事前登録を確定する。

## 0. 親 brief の実測の訂正 (親が現物で再確認)

段 2 と 2 レンズが独立に指摘した誤りを、親が自分で読んで確認した。brief の実測台帳を次へ置換する。

| brief 実測 | 裁定 | 訂正後の事実 |
|---|---|---|
| 1 (`None` が site 検査より前) | **real** | `loop.py:66-67` で確定。狭義に正しい |
| 2 (caller 14、契約を渡すのは 2 本) | **refuted** | `loop.run_campaign` の呼出しは 12 module・15 箇所。`t126_driver:540` と `s8b_oracle_driver:1381` は `run_campaign` ではなく `pipeline.evaluate` の直接呼び手 |
| 3 (残り 12 本が同一の実行値) | **refuted** | `sanity_silo.py:52` は `numactl` を渡さない (= `None`)。`p3_s4_loop_trigger_gating.py:560` は compute で既に契約を渡す |
| 4 (配線しても受理集合不変) | **refuted** | `env_contract` は認可用ではなく `pipeline` の build-v2 selector (`loop.py:248-250` → `pipeline.py:515-518`)。legacy と v2 は namespace も検証関数も別 (`buildcache.py:851` vs `:680`) |
| 5 (pipeline の pegasus 強制は qualification 枝のみ) | **real** | `pipeline.py:546` で確定 |
| 6 (`None` 素通りを禁じるテストは 0 件) | **real (部分訂正)** | 0 件は正しい。ただし既存被覆は monkeypatch 1 本だけではなく、required attestation の順序テストもある |
| 7 (floor の最初の書込みは 88 行) | **refuted** | 最初の script 書込みは `floor_campaign.sh:30` の `mkdir "$TMPDIR"`。T126 の 75 行は正しい |
| 8 (凍結 bytes 不変) | **real (一般化のみ refuted)** | `FROZEN_MANIFEST` 23 entry に対象なしは正しい。ただし T126 の `script_identity` / `series_identity` は key 側 pin であり、wrapper 変更で future series ID が変わる |

登録済み較正の active は `753f535a…` (`env_contract.py:267`) であり、brief が挙げた `94a4…` は
登録済みだが current contract の参照先ではない。

**(P1)〜(P5) はすべて全部または一部が反証された。親の provisional 裁定は破棄し、以下で置換する。**
親の一般化が段 3 で覆るのはこれで 5 wave 連続である。

## 1. 中核裁定 — 閉包は `run_campaign` ではなく sink で行う

2 レンズが独立に同じ欠陥を指摘し、親も現物で確認した。**certified を書く実体は
`pipeline.evaluate` であり、`run_campaign` を通らない production 経路が実在する。**

- `s8a_trigger_sweep.py:456-463` — screening 有効時は `run_campaign` ではなく
  `screening_driver.evaluate_candidate()` へ分岐する。同型が `s6_sort_sweep.py:352-359`、
  `backoff_sweep.py:84-94` にもある。
- `screening_driver.py:171` が `evaluate()` を契約なしで直接呼ぶ。
- `s1_direct_comparison.py:626` の既定 `evaluate_fn=pipeline.evaluate` も契約なし。

したがって `run_campaign` の 15 箇所だけを閉じても「certified writer を閉じた」は**偽**になる。
T-609 が名指しした `s8a_trigger_sweep.py:457` の driver 自身が、すぐ隣に第 2 の未防護経路を持つ。

**裁定: 認可の強制点を `pipeline.evaluate` (sink) に置く。** これにより既存 caller だけでなく
将来の caller も自動的に fail-closed になり、AST で caller を数える閉包テストが不要になる。

## 2. plan v2 — 実装する項目 (scope 内)

### A. Python 層 (実装子 A)

- **A1.** `pipeline.evaluate` に必須 keyword-only 引数 `authorization_contract` を追加する
  (既存の `build_context` と同じ形)。欠落・`None`・非 exact 型は、**layout / WAL / build へ
  一切書く前に** `TypeError` で拒否する。
- **A2.** 認可述語を 1 か所へ集約し、次を全部検査する。
  1. exact `ExecutionEnvironmentContract` 型 (subclass 不可)。
  2. `authorization_contract == env_contract_registry.lookup(authorization_contract.env_tag)`
     — 自作契約を認可に使えなくする。これを入れないと gate は恒真に近い (レンズ A 所見 2、
     レンズ B 所見 2)。
  3. 実行値の完全一致: `env_tag` / `clocks_per_us` / `numactl`。
     `numactl is None` は拒否する (現行の `tuple(numactl or ())` は `None`・`""`・`False` を
     空 tuple へ潰し、pegasus の解決済み `()` と未解決 `None` を区別できない)。
  4. `PEGASUS_COMPUTE` では登録済み pegasus 契約だけを受理する (現行規則を維持)。
  5. build selector `env_contract` が非 `None` なら `authorization_contract` と同値を要求する
     (分離によって新たに生まれる「認可 linux / selector pegasus」の穴を塞ぐ。レンズ A 所見 2)。
- **A3.** production の sink caller を全部配線する:
  `loop.run_campaign` (layout 生成前の早期検査は維持)、`screening_driver.evaluate_candidate`、
  `s1_direct_comparison`、`t126_driver`、`s8b_oracle_driver` (injected `evaluate_fn`)。
- **A4.** `run_campaign` にも必須 keyword-only `authorization_contract` を足す。
  既存の `env_contract` は build-v2 selector のまま**据え置く** (P1 の一斉配線は却下)。
- **A5.** `run_campaign` の 12 module・15 呼出しへ `authorization_contract=lookup(ENV_TAG)` を配線する。
  `sanity_silo.py` は `numactl=list(contract.numactl)` も渡す。

### B. shell 層 (実装子 B)

- **B1.** 両 wrapper の**最初の script 書込みより前** (`floor_campaign.sh:30` の `mkdir "$TMPDIR"`、
  `t126_qualification.sh:75` の `mkdir -p`) に、静的 admission preflight を置く。
- **B2.** preflight helper は **receipt の `source_commit` から `git cat-file blob` で取り出し、
  標準入力で interpreter へ流す**。これにより (i) ファイルを書かない、(ii) wrapper に hash literal を
  埋めない (相互 pin の循環がない)、(iii) 投入時 commit A と現 worktree commit B の drift で
  誤拒否しない。レンズ B 所見 7・10 はこの一手で同時に閉じる。
- **B3.** helper は**薄い CLI adapter に限る**。strict JSON reader・protocol 検証・契約検証を
  再実装せず、既存の `s8b_floor_campaign` の protocol 検証、`qualification.contract.validate_protocol`、
  `env_attestation.load_verified_calibration`、`site_policy.current_site` を呼ぶ。
  private 関数が必要なら public leaf へ昇格させるだけにする (レンズ B 所見 9)。
- **B4.** helper を `REQUIRED_CODE_IDENTITY_PATHS` へ**追加しない**。wrapper 自身が既に
  script identity の対象であり、helper は commit 由来で解決されるため推移的に固定される。
  追加すると既存 v1 series が exact key-set 検査で検証不能になる (レンズ A 所見 8、レンズ B 所見 8)。
- **B5.** preflight が非 0 なら、attempt directory・failure marker・driver を一切作らずに停止する。
  診断は stderr のみ。

### C. 台帳へ書いてよい文言 (レンズ B 所見 6 を採用)

> PBS が job body を開始した後、当該 wrapper が明示的に管理する durable output および scratch を
> 初めて変更する前に、submission / source identity・current registry・protocol / control・
> calibration bytes・compute-site の静的 read-only admission を完了する。qsub 側の receipt / ledger、
> PBS spool / prologue / epilogue、scheduler が作る `$TMPDIR`、filesystem atime、
> full hardware attestation probe の scratch は対象外である。

**「write-zero」「最初の書込み前に契約で保護した」と略してはならない。**

## 3. real だが scope 外 — 裁定パッケージへ返す

いずれも real と裁定するが、承認外の受理集合変更または独立設計を要するため実装しない。

1. **認可の proof chain 永続化** (レンズ A 所見 4、レンズ B 所見 3)。`attestation_mode="none"` では
   receipt が発行されず、campaign identity にも WAL COMMIT にも認可が残らない。さらに T-609 以前の
   無束縛 COMMIT を、認可済みの再起動が terminal として skip できる。閉じるには resume の受理集合と
   campaign identity を変える必要がある。**T-530 が「同じ wave で行え」と言った hash 束縛はこれである。**
2. **書込みを伴わない full hardware attestation** (レンズ A 所見 6、レンズ B 所見 5)。
   `attestation_mode="required"` の実 probe は TSC probe が一時ファイルを作るため、
   preflight に入れると preflight 自身が最初の writer になる。事前ビルド済み probe の別設計が要る。
3. **`site_policy` の誤分類** (レンズ B 所見 4)。`bnode[0-9]+` の hostname だけで compute と判定し、
   NQSV / PBS 証拠を分類条件にしない。CI や別施設のホスト名で誤検出しうる。既存の裁定
   (「計算ノードの権威は bnode hostname と affinity」) を覆すため独立裁定が要る。
4. **floor protocol の source-commit 非束縛** (レンズ A 所見 7)。qsub 後に
   `output/s8b-freeze/floor_protocol.json` の `master_seed` を変えても、job 側 dirty 検査は
   `output/` を除外するため検出できず、別 schedule が走る。既存の TOCTOU であり本 wave の
   変更が作るものではない。新規タスク候補。
5. **no-bench verifier sanity の契約束縛の意味** (レンズ A 所見 3)。`sanity_silo` は
   `do_bench=False` で numactl を実際には使わないため、A5 の配線は宣言値の付与に留まる。
   「no-bench の correctness-only COMMIT を計測契約束縛の対象と数えるか」は独立の裁定。
   A5 は認可の穴を塞ぐために行い、**numactl gate が sanity_silo で実効的だとは主張しない。**

## 4. 変異事前登録 (DW-M01、実装前)

| # | 対象 | 変異 | 期待赤 node | 単一理由性の根拠 |
|---|---|---|---|---|
| M1 | 認可述語の欠落/`None` 拒否 | 拒否を消して素通りさせる | evaluate を認可なしで直接呼ぶ負例 | `run_campaign` を経由しない直接呼出しで隔離するため、前後に同じ入力を拒否する層がない |
| M2 | registry 同値検査 (A2-2) | 検査を削除 | 値をずらした自作契約の負例 | 型検査は通る値にする。実行値も契約と一致させるので、他の検査は発火しない |
| M3 | selector 同値検査 (A2-5) | 検査を削除 | 認可 linux / selector pegasus の負例 | 認可側は完全に整合させるので、認可述語の他項では拒否されない |
| M4 | `numactl is None` 拒否 (A2-3) | `tuple(numactl or ())` の falsy 潰しへ戻す | pegasus 契約 + `numactl=None` の負例 | 契約の `numactl` が `()` のときだけ差が出る。他項は一致させる |
| M5 | `PEGASUS_COMPUTE` の exact-pegasus gate | 条件ブロックを削除 | compute + linux 契約 + linux 実行値の負例 | build selector は legacy のまま。heavy-work site gate は compute を許すため他に拒否理由がない |
| M6 | wrapper の preflight 非 0 処理 | 非 0 を無視して継続 | wrapper 結合負例。**観測点は「書込みと driver 起動が発生しないこと」** | 最終 reject は後段 gate でも起きるため、kill 観測点を書込み有無に置く (レンズ A 所見 10) |
| M7 | preflight の位置 | 最初の書込みより後ろへ移す | 順序テスト。観測点は同上 | 同上 |

**正例 (承認外の過剰拒否の検出、DW-M01)**

- P-1: 登録済み契約と一致する実行値の evaluate / run_campaign は従来どおり成功する。
- P-2: 正しい receipt・protocol・calibration・compute site の preflight は通り、後段へ進む。

## 5. 成果物影響 (DW-G05)

- 実装した場合: certified 成果物を書く経路が sink で認可され、認可のない run は
  layout / WAL を作る前に拒否される。受理集合の変化は**縮小のみ** —
  (i) 認可を渡さない run、(ii) 自作・drift した契約、(iii) 認可と selector の不一致、
  (iv) pegasus 契約に対する `numactl=None`、(v) compute 上の linux 契約。
- 実装しない場合: certified 選択結果と proof chain に環境契約へ束縛されない run が混じったまま残り、
  floor / T-126 を「最初の書込み前に静的 admission を通した入口」と数えられない。
- **本 wave では、認可の事実は成果物 bytes に残らない** (§3-1 が scope 外のため)。
  したがって「proof chain に束縛された certified writer closure」とは呼べない。
  worklog にはこの限定を明記する。

## 6. 分割と順序

- 実装子 A = Python 層 (A1〜A5) と preflight helper。
- 実装子 B = shell 層 (B1〜B5) と wrapper テスト。
- helper の CLI 契約 (引数・exit code・stderr 形式) は本裁定で先に固定し、両者を並列投入する。
  B は helper の hash を pin しない (B2) ため、A の bytes 確定を待たない。

### helper CLI 契約 (固定)

```
python3 -I -B - <mode> --repo-root <path> --receipt <path>
   mode = "floor" | "t126"
   stdin = helper source (git cat-file blob <source_commit>:<helper path>)
   exit 0 = admission 合格 (stdout は出さない)
   exit 3 = admission 不合格 (stderr に 1 行 JSON: {"gate": <str>, "reason": <str>})
   exit 4 = 入力不備・環境不備 (stderr に同形式)
   いかなる場合もファイルを作成・変更しない
```

## 7. 停止条件

実装子は、既存テストの期待値を変えなければ緑にできない状況に至ったら**変更せずに報告して止まる**。
とくに、自作契約を sink へ渡して成功を期待する既存テストが見つかった場合は、A2-2 を弱めず、
親へ差し戻す。
