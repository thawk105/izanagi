# [T-213] 再定義の設計パッケージ — 計算ノードから使える検査用隔離 clone の供給

- wave: `dev-wave-t213-redefine` (背景 job、fresh context)
- branch: `worktree-dev-wave-t213-redefine` / 基準 main: `67175e1a` → 記録時 `77e099e3`
- 実装 anchor: **なし (実装しないと裁定)**
- 統制する裁定: worklog (235) [T-213] — 再定義の方向を確定し、6 件の設計を推奨付きで起草して返す
- 前段の一次資料: `output/insights/2026-08-05_t213-shared-scratch-blockers.md` (前 wave (229) の逐語)
- 本 wave の一次成果物 (repo 外): `/work/1/SFC/tanab/dev-wave-jobs/t213-redefine/`
  (brief、段 2 草案、段 3 敵対 2 本、段 4 裁定、probe)

---

## 0. 観測の三分 (前 wave の一般化しすぎを避けるため)

段 3 の両レンズが独立に、親 brief が単発観測を強い前提として並べていると指摘した (A9/B13)。
採用し、本文の主張を次の 3 種に分ける。**この区別を跨いで引用しないこと。**

| 種別 | 意味 | 本書での扱い |
|---|---|---|
| **[コード]** | 現 HEAD のコードから決定論的に従う事実。読めば誰でも再現する | 設計の根拠にしてよい |
| **[観測]** | この機体・この時刻の 1 回の実行結果 | 動機の裏付けにはなるが閾値の根拠にしない |
| **[仮定]** | まだ確かめていない設計上の前提 | 裁定で潰すか、pilot で確かめる |

---

## 1. 出発点 — 前 wave が確定したこと

前 wave (229) は「隔離 clone を共有 FS へ移す」だけでは目的を達成しないと確定した。本 wave は
現 HEAD `67175e1a` でその前提を取り直し、いずれも**現存**することを確認した。

- **[コード]** `.gitmodules` は `url = https://github.com/thawk105/ccbench`。
  `update_submodules_no_fetch()` は URL を絶対 path か `file://` に限る (`git_state.py:494-496`)。
  本 worktree で直接呼ぶと `RUNTIME_IO_FAILURE` を送出する (親の直接実行)
- **[コード]** 隔離 clone は `--no-local --no-checkout` (`git_state.py:99`) で modules cache を持たない。
  checker と同一手順の clone で `_preflight_submodule(["orchestrator/tests"], ".")` = **rc=14**
  (親の直接実行、`modules_cache_exists=no`)
- **[コード]** `run_tests.py` は submodule preflight (`:924`) を site 判定 (`:928`) より前に通す
- **[観測]** 上記 clone の所要は login node の `/tmp` で **11.7 s** (前 wave の同種観測は 6.60 s、
  `/work` は 17.95 s)。共有ノードのため外乱を含む。**この値から timeout 閾値を導かない**

### 本 wave で新たに判明したこと

- **[コード] 新事実 A**: bootstrap gate は `git config --file .gitmodules --get-regexp`
  (`git_state.py:79`) で**作業木の `.gitmodules` そのもの**を読む。したがって `.git/config` の
  per-clone override も `url.<base>.insteadOf` も**この gate を満たさない**。
  選択肢は「tracked bytes を書き換える」か「gate 側に登録経路を足す」かに絞られる
- **[コード] 新事実 B**: submodule は**入れ子**である。`external/ccbench/.gitmodules` に
  `third_party/shirakami` (HTTPS) がある。最上位だけ解決しても閉包は閉じない
- **[コード] 新事実 C**: supervisor は **fake child 専用**である (`worker.py:34` の
  `dev-waves-fake/v1` handshake、D74、`output/dev-wave-supervisor/README.md`)。
  real child の開放は [T-079] で据え置き
- **[コード] 新事実 D**: `validate()` は `replay_run()` + `status()` だけで (`daemon.py:1451-1453`)、
  `checks.json` 等の成果物を読まない。**「成果物に書けば検証される」は現状成り立たない**
- **[コード] 新事実 E**: wave worktree の置き場は `_expected_worktree_path`
  (`git_state.py:414-420`) が `<repo_root>/output/dev-wave-supervisor/runtime/<run_id>/worktrees/wNNN`
  に**ハードコード**している。`--runtime-dir` を渡しても既定 runtime 側に作られる
- **[観測]** 本 worktree の `git submodule update --init` は github から clone して成功した。
  `--no-fetch` 方針は網の有無ではなく**構造的な選択**である。ただしこれは pegasus02 から
  当該 URL への 1 回の成功にすぎない

---

## 2. 段 3 敵対レビューの結果 — 2 本とも NO-GO

段 2 の草案 (codex `gpt-5.6-sol`、`reasoning=max`、read-only) に対し、異なる 2 レンズ
(A: 正しさ防壁と信頼境界 / B: 実効性・到達可能性・運用) を並列で当てた。
**2 本とも NO-GO**、blocker 級 13 件。**4 組が独立に同型を指摘**した。

| 独立に一致した所見 | 内容 |
|---|---|
| A1 / B5 | cleanup 前に封をする `checks.json` へ cleanup 後の `residue_count=0` を書く順序は因果的に成立しない |
| A2 / B4 | 閉鎖述語を成果物に書いても `validate` / `export` が読まないので恒真になる (新事実 D) |
| A8 / B2 | 提案 pilot は `DW-G01` の生死実験ではなく、新 production subcommand を先に作る逆順 |
| A9 / B13 | 親 brief が単発観測を一般化しすぎている (→ §0 で採用) |

親が一次実行・コード読解で裏取りした主要所見:

| # | 所見 | 親の裏取り |
|---|---|---|
| A3 | `pytest.ini` は trust root 外。after-SHA が `addopts = --collect-only` を入れれば、真正な compute 実行のまま全テスト未実行の rc=0 になる | `pytest.ini` 冒頭が「4 ゲートは環境変数 `PYTEST_ADDOPTS` しか読まず ini の addopts を構造的に見ない」と明記。`trust_root()` の pathspec は `tools` と `orchestrator/tests` のみ (`git_state.py:954-960`) |
| A4 | compute 上の被検査コードが `result.json` を先に作れる | `_job_run` は cwd=repo_root で子を起動した後に `O_EXCL` で `result.json` を書く (`dispatch_compute.py:547-612`)。login 側は submission dir の result・log・marker だけを見て scheduler の終了状態と突き合わせない (`:1650-1690`) |
| B1 | supervisor は fake child 専用 | 新事実 C |
| B3 | 草案の新 WAL event は許可 event 外で必ず拒否される | `EVENT_TYPES` は 8 種で `verification_evidence_persisted` を含まない (`ledger.py:56-65`)。既存 `observation_recorded` / `side_effect_prepared` / `side_effect_observed` はある |
| B12 | `RepositoryLease` は runtime dir ごとの lock なので、同一 repo に別 runtime を与えた 2 supervisor が排他を迂回する | `RepositoryLease.acquire(layout, ...)` (`ledger.py:1398-1405`) |
| B14 | `.checkouts` の control-name skip 追加は現行 grammar では挙動を変えない | `_ID_RE = [A-Za-z0-9][A-Za-z0-9._:-]{0,127}` (`schema.py:320`) — 先頭ドット名は元から run と見なされない |

### 前 wave 所見 A5 の機序を訂正する (erratum)

前 wave は「custom runtime と `discover_runs()` の namespace 衝突」と記録した。**機序が違う。**
真の機序は新事実 E — `--runtime-dir` を渡しても wave worktree が既定 runtime 側に作られ、
そこに WAL の無い run ディレクトリが生えることである。`.checkouts` のような名前は
grammar 上もともと run と見なされない (B14)。是正すべきは名前の skip ではなく path のハードコードである。

---

## 3. 裁定パッケージ — 8 件 (ユーザー裁定待ち)

依存順序は §4 に示す。各件の「択一」はユーザーが選ぶためのものであり、
本 wave は推奨を書くだけで採用しない。

### 件 1 — T-213 の完了条件

**推奨**: 「実 izanagi 由来の disposable clone に対し supervisor を 1 wave 走らせ、active 段の
fixed check が隔離 clone 内で submodule を持ち、計算ノードへ dispatch され、その証拠が
**再起動後も検証できる**」を完了条件とする。置き場の移設は手段であり完了条件ではない。

**必須の付帯条件**: 述語を成果物へ書くだけでは足りない (新事実 D)。**述語を消費する validator を
同時に設計し**、terminal 遷移・`validate`・pilot 判定の三者が同じ validator を呼ぶ。
これを欠くと規律 3 が禁じる「謳うだけで発火しない保証」になる。

### 件 2 — supervisor の submodule bootstrap 権威

**推奨 (a)**: tracked `.gitmodules` は書き換えず、operator が管理する **local mirror registry** を
supervisor profile の権威にする。gate は「登録済みの exact mapping かつ**承認済み gitlink SHA**」だけを通す。

- 許可する commit を候補側の gitlink から採ってはならない (自己選択 pin になり D16 の pin 再承認を迂回する)
- **再帰**が要る (新事実 B)
- **mirror の producer を同時に決める** — 誰が network から取り、どう検証し、いつ凍結するか。
  決めなければ受理集合が「repo の bytes」ではなく「記録されない operator の状態」に依存する

**択一**: (b) tracked `.gitmodules` を書き換える — 現行 gate をそのまま通せるが、upstream との
共有物へ機体固有事実が入り、入れ子側も別途書き換えが要る。
(c) gate を HTTPS 一般許可へ緩める — `--no-fetch` の供給鎖固定を撤回する。

**受理集合の変化 (推奨 (a) の場合)**: 現在は絶対 path / `file://` だけが通り、それ以外は
mirror の有無に関係なく落ちる。変更後は「登録済み exact mapping + 承認済み pin + mirror に object 実在」が
新たに通り、未登録・不一致・pin 不在・入れ子未登録は落ちる。入れ子の URL すり替えは**現行より狭まる**。

### 件 3 — 隔離 clone への submodule 供給

**推奨 (a)**: 件 2 の registry mirror から、隔離 clone ごとに modules cache を独立 materialize する
(network なし、`--no-hardlinks`、再帰)。`_preflight_submodule` は**緩めない**。

**択一**: (b) `--recurse-submodules` — network 供給の復活。
(c) `--reference` / alternates — 供給元の GC・改変に隔離 clone が依存し、`--no-local` の分離が崩れる。

### 件 4 — dispatch 依存の trust closure と site 権威

**推奨**: `orchestrator/campaign/__init__.py`、`site_policy.py`、`dispatch_compute.py` を trust root に
入れる。site は **routing site と execution site を型分離**して両方を成果物に残し、「単一権威」と称さない
(A7: compute 子は `run_tests.py` を site 引数なしで起動するため、子側でもう一度 `current_site()` を呼ぶ)。
site policy は audited bytes から実行し、その SHA を観測記録と trust entry の双方へ束縛する (B11)。

**注意**: これは**十分でない**。件 8 の穴 1 がある限り、trust root を広げても真正な compute 実行のまま
全テスト未実行の rc=0 が作れる。

### 件 5 — compute 実行の attestation

**推奨**: 次の順に固定する。

1. raw request / receipt / marker の **bounded bytes を W 配下へ複写** (digest だけでは再検証できない、A6)
2. digest と observed projection を **既存 `observation_recorded`** で WAL へ束縛 (新 event を作らない、B3)
3. cleanup を実行
4. **別の成果物・別の WAL 記録**で cleanup 結果を残す (二相、A1/B5)
5. terminal completed は第二相の後だけ許す

qsub は非冪等な副作用なので、既存の `side_effect_prepared` → qsub → `side_effect_observed` の枠へ載せる
(B7)。これにより SIGKILL 窓で「PBS job は生きているが台帳に無い」状態を scavenger が裁定できる。

**注意**: attestation の強度は件 8 の穴 2 に上限を切られる。receipt が真正でも、被検査コードが
結果チャネルを先取りできる限り「実行された」以上のことは言えない。

### 件 6 — 共有 FS 残骸の回収と custom runtime

**推奨**: 隔離 clone を `D/.checkouts/<id>/` に置き、lease + 有界 scavenger で管理する。
**同時に `_expected_worktree_path` のハードコードを解く** (新事実 E — これが custom runtime 問題の実機序)。

付随して裁定が要る点:

- worktree・submodule checkout の bytes / inode を accounting へ入れる (現在 `max_run_bytes` は
  worktree を意図的に除外している、B9)
- 別 host / 再起動後 boot の `FOREIGN_LEASE` からの回復手順 (B8)
- 同一 repo に複数 runtime を許すなら、repo identity に対する global lease を runtime とは独立に置く (B12)

### 件 7 (新設) — pilot の形

**推奨**: 新しい production subcommand を先に作らない (`DW-G01` 違反)。
**既存の fake child (`orchestrator/tests/test_dev_waves_fake.py`) と 100 行以内の使い捨て driver で、
実 izanagi の disposable clone に対し 1 wave を走らせる**のが最小の生死実験である。

- **real child の開放 ([T-079]) は不要**。pilot が試すのは child ではなく、供給・信頼・dispatch・
  証拠・cleanup という infrastructure である。ここは前 wave も本 wave の草案も取り違えていた
- 二段階に割る。**段階 1** = 既存 production 関数だけで supply / trust / dispatch を通す使い捨て probe。
  **段階 2** = fake child による supervisor 1 wave の E2E
- 正式 pilot を作る場合も、pilot が通した bytes と land 候補 bytes の同一性を記録する (A8)

### 件 8 (新設・T-213 の scope 外) — trust root の 2 つの穴

いずれも**現行 main に存在する**穴で、T-213 とは独立に効く。T-213 の前提にせず別タスクとして起票する。

1. **制御面が trust root の外にある**: `pytest.ini` は trust root の pathspec の外にある。
   after-SHA が `addopts` を足せば、4 ゲートは環境変数しか読まないため素通りし、
   全テスト未実行の rc=0 になる。**推奨**: trust root を「ファイルの正の列挙」から
   「Python module origin と制御ファイルの閉集合」へ広げる設計として起票する
2. **compute の結果チャネルを被検査コードが先取りできる**: `_job_run` は cwd=repo_root で子を起動し、
   その後 `O_EXCL` で `result.json` を書く。子が先に同名ファイルを作れば trusted 側の書込みは失敗し、
   login 側は残った内容と真正 marker・会計だけを読む。**推奨**: 被検査コードが書けない結果チャネル
   (親 wrapper 所有) を設計する

### 予算の閉包 (件 1〜7 に共通する設計要件)

レンズ B が deadline の全体像を洗い、どの区間にも検証・cleanup の reserve が無いと指摘した (B6)。
実装時は次の式を満たすことを submit 時に検査する。

```
total_timeout > preflight + worker上限 + passive + 2×(clone+供給) + local checks
              + dispatch(tests) + dispatch(provenance) + 証拠 fsync + cleanup + margin
```

内側 (dispatcher) の deadline は外側 check の残時間から導出し、内側が必ず先に終わるようにする。
**閾値は §0 の [観測] から導かない** — 上限・margin・内外関係から事前登録する。

---

## 4. 推奨する依存順序

```
件 8 (独立に起票。T-213 をブロックしない)

件 7 段階 1 (使い捨て probe)
  → 件 2 (bootstrap 権威 + mirror producer)
    → 件 3 (再帰供給)
      → 件 4 (trust closure / site 型分離)
        → 件 6 (置き場・lease・worktree path のハードコード解消)
          → 件 5 (attestation 二相 + qsub write-ahead)
            → 件 7 段階 2 (fake child で 1 wave E2E)
              → 件 1 の完了条件を validator で判定
```

---

## 5. 本 wave の射程

段 4 で「実装しない」と裁定した (`4→7→8→9`)。実装差分が無いため、**変異 matrix と受入全走は
本 wave の射程外**であり、`DW-M01` の変異事前登録も行っていない。docs 記録のみ。

コード・テスト・機械設定は 1 byte も変更していない。
