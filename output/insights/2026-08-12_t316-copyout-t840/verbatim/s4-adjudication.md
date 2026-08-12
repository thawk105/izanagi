# 段 4 裁定 — [T-316] R-1 (b)+(c) / [T-840]

親: dev-wave-t316-copyout-t840 manager。入力 = `s1-brief.md`、`s2-plan.md`、`s3-lensA.md`、`s3-lensB.md`、
親の独立実測 (`probe_env.json`、および本書 §0 の追加実測)。

## 0. 親の追加実測 (裁定の根拠。段 3 の後に親が独立に取った)

1. **`artifact_admission` は分類を消費しない。** `orchestrator/campaign/artifact_admission.py:715-785` は
   trigger-machine campaign の binding 特例を除き、構造的に妥当な post-policy campaign を
   一律 `admission_status="admitted"` で返す。coder 由来かどうか、quarantine を通ったかどうかを
   読む経路が無い。→ レンズ A F1 を**支持**。
2. **red / kickoff は現行の正例である。** `orchestrator/tests/test_p3_exploration_namespace.py:313-356`
   (`test_main_public_entry_routes_runtime_layout_and_selector`) は red・kickoff の
   `main(["--allow-coder-derived-build"]) == 1` を期待し、layout と WAL の生成を assert する。
   → 起動前 deny は既存の緑テストを壊し、既存能力を消す。レンズ A F4 を**支持**。
3. **`p3_s4_loop_sort.py` の source pin は歴史記録であり repin 不要。**
   `orchestrator/campaign/t080_freeze_migration.py:88-100` が同 file の SHA を 3 箇所 pin するが、
   照合は `_basis_blob()` → `_blob_bytes_at(commit, path, root)` (`:857-863`) で**固定 commit の blob**
   を読み、working tree を読まない。現行 SHA `602e44fd…` は pin 値 `9b64f34b…` と**既に相違**している。
   → 実装子 B は同 file を編集してよい。`DW-O09` の結論 (凍結 bytes 変化なし) は維持。レンズ A F9 を**支持**。
4. **正常な cache tree に非通常ファイルは無い。** 実在 tree 1,674 entry で symlink 0 / FIFO 0 / socket 0、
   対象 binary は `0o700` / `st_nlink=1`、in-tree `.a` を静的リンク済みで動的依存は system 共有ライブラリのみ。
   → hard-link 拒否と binary 1 本の copy-out は**正常品を過剰拒否しない**。

## 1. 総括裁定

- **A (copy-out 厳格化) = 実装する。** これが裁定 (b) の本体であり、受理集合を縮める純増である。
  ただし主張は「**cache publish 時点の inode 厳格化**」に限定する。
- **C (lexical gate 併置) = 実装する。** docstring のみ。
- **B ([T-840] 機械隔離) = 分割する。** 実装できる部分だけ実装し、
  **裁定の前提を覆す新事実**を添えて残りをユーザー再裁定へ返す (`DW-S04` / `DW-STOP`)。

### B を分割する理由 (承認済み裁定を止める根拠 = 未見の新事実)

裁定は「T-840: 機械隔離」と「T-841: receipt 束縛 (R3-3/R3-9 後)」を**別項として分離**した。
段 3 の 2 レンズが独立に、親が §0-1 で実コード照合したところ、**この 2 つは成果物のレベルでは分離できない**。
「非認証成果物として機械隔離する」を成立させるには、分類を `artifact_admission` /
`layer3_report` / WAL / COMMIT のいずれかが消費しなければならず、それは T-841 の receipt 束縛そのものである。
分類を registry に書くだけでは `admission_status="admitted"` は変わらず、**恒真ラベル**になる (レンズ A F1/F2)。

裁定時点でこの依存関係は提示されていない (2026-08-11 の裁定パッケージ R-2 は
「機械隔離するか、残余のまま台帳に明示するか」の二択として提示し、
機械隔離が T-841 を要することを書いていない)。よって**親は不採用にせず、再裁定へ返す**。

## 2. 所見の裁定表

### A (copy-out) — すべて real、scope 内、採用

| 所見 | 判定 | 裁定 |
|---|---|---|
| B/A-3 親 dir の path-based `os.makedirs` | real・blocker | **採用**。承認済み root fd から component を `openat` 相当で辿る。既存の `orchestrator/campaign/durable_root.py` に anchored root があるなら**再利用**し、第 2 機構を作らない |
| B/A-4 leaf の symlink・FIFO・hardlink・mode 検査不足、stale cleanup が symlink を追う | real・blocker | **採用**。`O_NONBLOCK\|O_NOFOLLOW` → `fstat` → `S_ISREG` / `st_nlink==1` / 特権 mode bit 拒否。`_clear_stale_build_dir` は `lexists` 基準へ |
| B/A-1 publish が create-only でない | real・must-fix | **部分採用**。保持した parent fd 経由の `os.rename` + rename 直前の no-follow 再照合まで。**Python 3.10 stdlib に `renameat2(RENAME_NOREPLACE)` が無いため directory の create-only 原子性は主張しない**。残余として明記。legacy への per-digest claim 新設は scope 外 (backlog) |
| B/A-5 環境 flag の fail-closed | real・must-fix | **採用**。`os.name` / 必要 constant / `os.supports_dir_fd` を起動時に検査し不足なら拒否。親実測でこの環境では発火しないので、`monkeypatch.delattr` の負制御 (`orchestrator/tests/test_check_codex_output.py:158` の先例) を**必須**とする |
| A/F5 TOCTOU 負制御が差し替える path が違う | real・must-fix | **採用**。負制御は source staging ではなく **clean destination entry** を copy 後・hash 後に差し替える形にする |
| A/F8 失敗時 cleanup matrix 未定義 | real・nit | **採用**。gate failure では staging と clean candidate の**双方を破棄し claim だけ残す**。exact failure matrix をテストで固定 |
| B/A-6 hit 時に member 集合を検査しない | real・must-fix | **部分採用**。hit 時の **no-follow 読み**は採用。**member allowlist の hit 時強制は不採用** — 旧実装が作った既存 cache entry を全件無効化し、正しさの穴でないのに大量再 build を強制する (規律 4)。cache contract を docstring で明文化し、残余として台帳へ書く |
| A/F6・B/A-2 実行時 binary identity まで届かない | real・**scope 外** | **不採用 (返す)**。fd-to-exec の束縛は R3-4 の sandbox execution receipt / T-841 の領分。本 wave の主張を「cache publish inode の厳格化」に限定する。安価な部分だけ採用: **publish する binary は `0o500`** とし、正例で実行可能性を確認する。これを security boundary と称さない |

### B ([T-840]) — 実装する部分

| 項目 | 裁定 |
|---|---|
| 単一 registry の typed 拡張 | **採用**。`materializer_admission.MATERIALIZER_ADMISSION_REGISTRY` に site kind (`DIRECT_MATERIALIZER` / `CODER_ENTRYPOINT`) を加える。**第 2 registry を作らない**。`NON_ADMISSIBLE_MATERIALIZERS` と `non_admissible_materializer()` の出力 schema は変えない (成果物 schema drift 回避) |
| A/F2 `QUARANTINE_GATED` は恒真ラベル | real・blocker → **採用 (設計変更)**。**`QUARANTINE_GATED` という status を新設しない**。実際の `DiffQuarantineResult.passed` を観測しないラベルに quarantine を名乗らせない。既存 2 status のままとし、coder entry point は kind で区別する |
| **未登録 site からの coder authority 発行を fail-closed で拒否 (runtime)** | **採用。これが B の実体である。** 現存する全 entry point を登録するので**受理集合は 1 件も縮まない** (過剰拒否ゼロ)。新規の未登録 issuer だけが機械的に落ちる純増の閉包 |
| A/F3 AST 閉包の走査 root が閉じていない | real・must-fix → **採用**。走査母集合を `orchestrator/campaign/**` 固定から **tracked Python 全体**へ拡げ、除外は exact registry にする。`output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/smoke_driver.py` は低位 helper を直接使う実在 issuer なので、**歴史 fixture として exact 除外に登録**し、その事実を台帳に書く (黙って走査外にしない) |
| B/B-3 runtime を一次防壁、AST を補助へ | **採用**。registry の runtime 消費を一次、AST 閉包を補助監査とする。authority 経路上の `getattr` / `importlib.import_module` による動的解決は拒否する |
| B/B-2 token が site に束縛されない | **部分採用**。site を **process-local な authority object へ束縛**する。`ADMISSION_SCHEMA` / receipt body / WAL body / cache preimage は**変えない** (T-841 非越境)。同一 process の caller が issuer を直接呼べる限界は `build_admission.py:4-13` のまま残し、認証境界と称さない |

### B ([T-840]) — 実装せず裁定へ返す

| # | 返す項目 | 理由 |
|---|---|---|
| Q1 | red / kickoff を**廃止**するか、**実行可能だが認証されない lane** として残すか | 起動前 deny は §0-2 の既存正例を壊し、診断 WAL の受理集合を縮める。設計択一であり親が決めない (レンズ A F4) |
| Q2 | 分類を `artifact_admission` / `layer3_report` / WAL / COMMIT へ束縛して**真の成果物隔離**にするか | §1 のとおり T-841 の receipt 束縛を要する。同じ裁定が T-841 を「R3-3/R3-9 後」としているため、本 wave へ密輸しない (レンズ A F1、レンズ B B-1) |
| Q3 | calibrator の任意 binary path (`orchestrator/calibrator/cli.py:124-154,774-855`) と shell materializer の扱い | 別系列の認証済み成果物 intake であり Python inventory 外。本 wave 対象外と明記 (レンズ A F7) |
| Q4 | 旧実装が作った既存 cache entry (extra member を含む) を拒否・再発行するか | 上記 B/A-6。正しさの穴ではなく費用の問題 (規律 4) |
| Q5 | fd-to-exec 束縛、build 子孫の終了保証、floor/oracle の store/resume 束縛 | R3-4 / host-security 系の別裁定 (レンズ A F6、レンズ B A-2) |

## 3. 親の provisional 裁定の確定

- **(P1) 支持 (限定付き)。** shared build-cache namespace への production publish は
  `buildcache.py:851` (v2) と `:992` (legacy) の 2 本。calibrator は**別 namespace の別系列**であり
  P1 の主張範囲外とする (Q3 へ)。
- **(P2) 支持。** 親実測 §0-4 が実行可能性まで確認した。ただし精密化: untrusted staging から
  copy するのは **binary 1 本だけ**で、metadata は host-generated とする。
- **(P3) 反証を受理。** registry 単独では隔離にならない。§2 の「未登録 site の fail-closed 拒否」へ
  再照準し、成果物隔離そのものは Q2 として返す。
- **(P4) 未確認 → 段 6 で親が実測して確定する。** 静的な検査可能性はあるが、実走・変異帰属は未確認。

## 4. 変異事前登録 (`DW-M01`、実装前登録)

各変異は「同じ入力を拒否する層が前後に無いこと」を実装後 (段 6 の `DW-M07` anchor 再検証時) に
コードで確認する。確認できないものは登録せず実効 gate へ再照準する。

| ID | 対象 | 変異 | 単一理由 | 期待 |
|---|---|---|---|---|
| M1 | A: leaf open | allowlisted binary の open から `O_NOFOLLOW` **だけ**を外す | leaf symlink を拒否しないこと | KILLED |
| M2 | A: leaf 種別検査 | `stat.S_ISREG()` 判定を落とす | FIFO / directory を通すこと | KILLED |
| M3 | A: hard link | `st_nlink == 1` 検査を落とす | hardlink を通すこと | KILLED |
| M4 | A: 親 component | 中間 component の dir-fd 走査を `os.makedirs` の path-based へ戻す | 中間 symlink を通すこと | KILLED |
| M5 | A: 同一 fd 束縛 | hash / fsync を destination fd でなく **pathname 再 open** へ戻す | destination entry 差し替えを検出しないこと | KILLED |
| M6 | A: publish 集合 | metadata を host-generated でなく **staging からコピー**へ戻す | 偽 metadata を通すこと | KILLED |
| M7 | A: 環境 contract | flag 不足時の fail-closed を silent degrade へ戻す | 非対応環境で無防備に通ること | KILLED (負制御 = `delattr`) |
| M8 | A: cache hit | hit 時の no-follow 読みを path-based へ戻す | 旧 entry の symlink 差し替えを通すこと | KILLED |
| M9 | B: runtime 閉包 | 未登録 site の fail-closed 拒否を素通しへ戻す | 未登録 issuer を通すこと | KILLED |
| M10 | B: AST 走査 root | 走査母集合を `orchestrator/campaign/**` 固定へ戻す | 走査外 issuer を見逃すこと | KILLED |
| M11 | B: 除外 registry | exact 除外を prefix 一致へ緩める | 除外が広がること | KILLED |
| **M12** | **過剰拒否の正例** | deny 側を強めて `st_nlink == 1` を `st_nlink == 0` にする | 正常品を落とすこと | KILLED (正例が赤くなる) |
| **M13** | **wave 前の実コード形** | v2 publish を wave 前の逐語 (`os.rename(staging, bdir)` 丸ごと) へ戻す | 丸ごと publish を通すこと | KILLED |

M13 は「検査を新設する wave で、禁止したい形を wave 前の実コードが使っていたなら、その逐語と同型の
変異を 1 件登録する」規律に従う。M12 は受理集合を縮小する wave で承認外の過剰拒否を検出する正例。

**診断 pin (kill でなく `DW-M08` の diagnostic sensitivity pin として別枠記録):**
現時点で該当なし。段 6 で受理集合を変えない pin が出たら別枠へ移す。

## 5. plan v2 (段 5 へ渡す確定形)

段 2 プランを基礎とし、§2 の裁定を上書き適用する。変更点は次のとおり。

1. `QUARANTINE_GATED` status を**作らない**。site kind で区別する。
2. red / kickoff を**起動前 deny しない** (Q1 の回答待ち)。registry には登録するが runtime の deny は
   「**未登録 site**」に限る。
3. AST 走査母集合を tracked Python 全体へ拡げ、除外を exact registry にする。
4. 親 component の dir-fd 走査、rename の parent fd 経由、環境 flag の fail-closed を追加。
5. publish する binary の mode は `0o500`。
6. hit 時の member allowlist 強制は**しない**。no-follow 読みだけ。
7. 失敗時は staging と clean candidate の双方を破棄し claim だけ残す。
8. 主張は「cache publish inode の厳格化」に限定し、host-security boundary / certified safety /
   完全な成果物隔離を主張しない。

## 6. 所有分割 (段 5)

段 2 プランの分割をそのまま採る。重複所有なし。

- **実装子 A**: `orchestrator/campaign/buildcache.py`、`orchestrator/campaign/coder_effect_gate.py`、
  `orchestrator/tests/test_buildcache_v2.py`
- **実装子 B**: `orchestrator/campaign/materializer_admission.py`、`orchestrator/campaign/build_admission.py`、
  `orchestrator/campaign/p3_kickoff.py`、`orchestrator/campaign/p3_s4_red.py`、
  `orchestrator/campaign/p3_s4_loop.py`、`orchestrator/campaign/p3_s4_loop_sort.py`、
  `orchestrator/campaign/p3_s4_loop_trigger_gating.py`、`orchestrator/campaign/p3_autonomous_workload_trial.py`、
  `orchestrator/tests/test_p3_build_authority_cli.py`、`orchestrator/tests/test_p3_exploration_namespace.py`

`durable_root.py` を再利用する場合、実装子 A の所有へ加えるかを実装子 A の報告で確認する
(編集が必要なら親が所有を追加裁定する)。
