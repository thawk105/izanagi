# 段 4 裁定 — [T-677] 失敗診断の中継到達

親裁定。real/refuted、採否、scope、プラン v2、変異事前登録を確定する。

## 撤回・訂正する親 brief の主張

- **(P2) の「tracked test file 150 件はすべて `orchestrator/tests/` 配下」は誤り** (lensA#10)。
  `output/insights/2026-08-03_t361-t362-cluster-probes/driver/test_run_probes_evaluator.py` と
  `tools/task_runs/` 配下が反例。正しくは「`pytest.ini` の `testpaths = orchestrator/tests` が
  定める canonical acceptance の収集集合」に限定される。canonical 走行の結論は変わらないが、
  全称主張は撤回する。
- **実測 2 は「launcher 診断が消えた」実測ではない** (lensA#8)。当該 110-failure ログの
  short summary に `test_codex_worker_launch` は無い。正しくは
  「**generic な中継切り詰めは再現済み。launcher 固有の診断消失は推論**」。
  算術自体は正しい (`523,987 - 458,452 = 65,535`、`458,452 / 523,987 = 87.493%`。
  65,535 は `_utf8_tail` が文字境界で 1 byte 戻る挙動と整合)。
- **不変条件「失敗ごとに node id と診断本体を構造化して残す」は 49 KiB 予算と両立しない**
  (lensA#1)。「**代表 failure の本体 + 全 failure の正確な省略会計 + 完全ログへの耐久参照**」へ
  弱める。耐久参照は新規実装を要しない — dispatcher が既に
  `[Pegasus dispatch] receipt を <path> へ保存しました` を出し、receipt の
  `scheduler_logs.stdout.path` が全文ログを指す。
- **不変条件「生成中の例外」は「通常例外」へ狭める** (lensA#4)。`BaseException`
  (KeyboardInterrupt / SystemExit) は握らず伝播させる。
- 押し出し閾値は実測 artifact に限れば **156 件目** (lensB#1)。行長は無上限なので、
  現行案の根拠は「`pytest_unconfigure` 後に pytest の summary が無いこと」へ限定する。

## 所見の裁定

| # | 出典 | 裁定 | 措置 |
|---|---|---|---|
| A1 | 全件保存は予算と両立しない | **real** | 不変条件を上記へ弱める。receipt path を耐久参照として記録 |
| A2 | `terminalreporter.stats` は差し替え可能な表示カテゴリ | **real** | `pytest_runtest_logreport` / `pytest_collectreport` で `report.failed` を独立 stash |
| A3 | xdist internal error / pre-item crash は report が無い | **real・scope 外** | 保証対象外と明記し裁定パッケージへ |
| A4 | wrapper の `yield` 例外を握り潰す構造 | **real** | `yield` を catch の外へ。`finally` 内で `return` しない。`BaseException` 伝播。sentinel 例外の再送出テスト |
| A5 | E2E が恒真ゲート | **real** | `selected>0`、実 nodeid、末尾 sentinel、全 account 値を独立 oracle で検算 |
| A6 | 全層を通らない・relay は best-effort | **部分 real** | E2E を `_relay_scheduler_logs` へ in-process 結合。主張は「正常 relay 経路で末尾に残る」へ狭める。PBS job 実走は scope 外 |
| A7 | `\| FAILED` が変異 harness の偽 node になる | **real・最重要** | 内部 excerpt prefix を `> ` にし、`FAILED ` で始まる行を無害化。consumer テスト必須 |
| A8 | launcher 固有の実測不足 | **real** | brief 訂正済み。E2E payload に 16 KiB + 末尾 `truth_summary` sentinel を使う |
| A9 | representative 変異が fixture 次第で緑 | **real** | 予算を飽和させる複数 source fixture を固定。変異 (e) 単独帰属を撤回 |
| A10 | top-level `tools` import が plain-runner を壊す | **real** | 失敗検出後の lazy import + `ImportError` で fail-open |
| A11 | plain-runner harness / allowlist が未定 | **real** | 新規 test file に `__main__` 自走 harness を付ける |
| B1 | 閾値 156 vs 157 | **real (nit)** | 記録を訂正 |
| B2 | E2E が `-p` で conftest を強制ロード | **real** | `-p` を外し、`orchestrator/tests` 配下の実 conftest 自動 discovery を通す |
| B3 | prefix/frame 後の実中継 bytes | **到達欠陥としては refuted** | `_utf8_tail` は `_prefix_relay_lines` の**前**に効く (`dispatch_compute.py:768,776`) ので到達保証は不変。表示 bytes の会計だけ E2E で併記 |
| B4 | ASCII 主張と UTF-8 会計の矛盾 | **real** | canonical renderer を先に定義。非 ASCII / C0 / DEL / backslash を escape。`source_bytes` と `rendered_bytes` を別会計 |
| B5 | xdist worker crash・実並列度 | **A3 と同件・scope 外** | 裁定パッケージへ |
| B6 | SIGKILL / OOM / walltime / rc=16 | **real・scope 外** | 保証を「pytest セッションが完走した場合」に限定し裁定パッケージへ |
| B7 | nested subprocess の cleanup 未契約 | **real** | `start_new_session=True` + timeout 時 process group TERM/KILL + descendant 消滅検査 |
| B8 | より安い代案の比較なし | **real (nit)** | 下表で裁定 |

## 代案比較 (B8 の裁定)

| 案 | 到達保証 | 欠点 | 裁定 |
|---|---|---|---|
| producer 側 rich digest (本案) | pytest 完走時に成立 | 変更面が増える | **採用** |
| relay 予算の増量 | 不成立 — 後続出力に上限が無い | sanctioned control plane を変更 | 却下 |
| dispatcher でマーカ抽出 | 成立するが Pegasus 経路のみ | control plane 変更。local 走行・変異 harness に効かない | 却下 |
| 完全ログ path だけ中継 | 人間の二段操作が要る | 既に receipt 経由で存在する。単独では診断が届かない | **併用** (新規実装なし) |
| 一行固定 marker | per-failure 本体と会計を失う | 原因帰属に足りない | 却下 |

## 確定 scope (プラン v2)

編集面は 2 ファイルだけ。dispatcher・production・`run_tests.py`・`pytest.ini` は無編集。

### 1. `orchestrator/tests/conftest.py`

- `pytest_runtest_logreport` / `pytest_collectreport` で `report.failed` の report を独立に stash する
  (`terminalreporter.stats` に依存しない)。
- `@pytest.hookimpl(wrapper=True, tryfirst=True)` の `pytest_unconfigure`。`yield` は digest 用
  catch の**外**。post-yield の `finally` で出力し、`return` しない。`BaseException` は伝播。
- xdist worker (`hasattr(config, "workerinput")`) は無出力。
- 失敗 0 件なら builder も writer も呼ばない (緑走行で 1 byte も足さない)。
- 予算: digest 総量 = `DEFAULT_FAILURE_RELAY_LIMIT_BYTES * 3 // 4` = 49,152 bytes。
  1 failure excerpt 4,096 rendered bytes、1 block 5,120 bytes、frame/account 予約 1,024 bytes。
  **relay 定数は失敗検出後の lazy import で取り、`ImportError` なら無出力で fail-open**。
- canonical renderer: 出力は ASCII のみ。非 ASCII は `\xNN`/`\uNNNN`、C0・DEL・backslash も escape。
  `source_bytes` (元 UTF-8) と `rendered_bytes` (escape 後) を別会計。
- **excerpt 行頭は `> `** (`_strip_relay_prefix` が剥がさない)。escape 後に
  `FAILED ` で始まりうる行は無害化して出す。
- 選択順は xdist 到着順に依存しない安定順。予算超過分は
  `omitted_manifest_sha256` (nodeid/when/source_bytes/sha256 の canonical JSON Lines の SHA-256) へ畳む。

### 2. 新規 `orchestrator/tests/test_pytest_failure_digest.py`

`__main__` 自走 harness を付ける (`test_plain_runner_coverage.py` 対策)。

| 対応 | 内容 |
|---|---|
| (a) | 代表 failure の nodeid と longrepr **末尾** が digest に残る。head-only 化で赤 |
| (b) | 緑・skip・xfail・非 strict xpass・0 collected で無出力。worker で無出力。**非空 stats を与える** |
| (c) | 予算と省略会計が厳密。**予算を飽和させる複数 source fixture** で representative tier を固定 |
| (d) | **E2E**: `-p` なしの実 conftest 自動 discovery。大量失敗 + 大量 captured 出力。payload は 16 KiB + 末尾 `truth_summary` sentinel。`selected>0`・実 nodeid・sentinel・全 account 値を独立 oracle で検算。開始マーカ以降 < 64 KiB、stdout が終了マーカで終わる。`start_new_session=True` + timeout 時 process group TERM/KILL + descendant 消滅検査 |
| (e) | digest 予算が `DEFAULT_FAILURE_RELAY_LIMIT_BYTES` の 3/4 に束縛。既存 literal test は無編集 |
| (f) | 通常例外は fail-open (rc 不変)、`BaseException` と inner hook 例外は伝播 (sentinel 再送出) |
| (g) | **consumer**: digest を含む stdout を `mutation_harness._failed_nodes` に通し、excerpt 中の decoy `FAILED a.py::b` が抽出されない。raw / `\| ` 1 段 / `\| \| ` 2 段の三形で抽出集合が不変 |
| (h) | **relay 結合**: (d) の実 stdout を `dispatch_compute._relay_scheduler_logs` へ in-process で通し、digest 全体が中継後にも残る。prefix/frame 後の bytes も併記 |

## 裁定パッケージ候補 (scope 外・ユーザーへ返す)

- **U1**: xdist worker の internal error / pre-item crash では `failed`/`error` report が存在せず
  digest が空になる (A3/B5)。`pytest_internalerror` と `pytest_testnodedown` を別診断項目として
  取り込むか、既存 xdist summary を正本と定めるか。
- **U2**: SIGKILL・OOM kill・PBS walltime 打ち切り・pytest 起動前 rc=16 は pytest hook の到達
  範囲外 (B6)。job wrapper 側の durable checkpoint / partial-log path を作るかどうか。
  本 wave の保証は「**pytest セッションが完走した場合**」に限定して記録する。
- **U3**: relay は best-effort で BrokenPipe / relay error を握る (A6)。真の「確実」を要求するなら
  dispatcher 側の耐久経路が要る。

## 変異事前登録 (DW-M01 / DW-M08)

production 無編集の**テスト・harness 強化 wave**。変異位置は新規 conftest コードなので、
変更前 HEAD には存在しない。よって DW-M08 に従い、各変異について
**新テスト集合 (赤期待) と変更前 HEAD のテスト集合 (緑期待)** の双方を走らせ、
新テストだけが検出する差分を示す。すべて受理集合を変えない
**diagnostic sensitivity pin** として記録し、kill には数えない。

| ID | 変異位置 (新規 `orchestrator/tests/conftest.py`) | 1 行変異 | 新テストの期待赤 | HEAD テストの期待 |
|---|---|---|---|---|
| M1 | digest 予算定数 | `* 3 // 4` を relay 全量へ | (c), (e) | 緑 |
| M2 | excerpt 抜粋 helper | tail slice を head slice へ | (a), (d) | 緑 |
| M3 | excerpt 行頭 prefix | `> ` を `\| ` へ | (g) | 緑 |
| M4 | 会計行 | `omitted_bytes` を常に `0` | (c) | 緑 |
| M5 | worker guard | guard を反転し controller で return | (d) | 緑 |
| M6 | 例外境界 | `except Exception` を `except OSError` へ | (f) | 緑 |
| M7 | 失敗収集 | `report.failed` stash を `stats["failed"]` 参照へ | (b) | 緑 |

単一理由性: M1〜M7 はいずれも新規コードの単一箇所であり、同じ入力を拒否する層は前後に無い
(既存テストはこの digest の名前・marker・会計・hook 順を一件も検査していない)。
M1 について、lensA#9 の指摘どおり
**「dispatcher の relay limit を縮める」変異は既存 literal test も赤にするため (e) 単独の
検出力へ帰属できない**。よって M1 は producer 側定数の変異に限定して登録する。

## 段 5 分割

編集面が 2 ファイルで相互依存するため、実装子は 1 本。
