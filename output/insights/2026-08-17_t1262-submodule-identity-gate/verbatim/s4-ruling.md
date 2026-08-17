# 段 4 裁定 — [T-1262] submodule の内容同一性 gate

親裁定。2026-08-17 01:55-02:10 JST。base = 3a4c3d43 (main 取り込み済み、対象 2 file は無変更)。

## 0. 契約の宣言 (A9 が要求した択一の決着)

**この gate が保証するのは「initialized submodule の worktree bytes が、pin された commit の
canonical checkout の bytes と 1 byte も違わないこと」である。** clean filter を通した等価性では
ない。したがって:

- 照合は **raw bytes** で行う (git を起動せず Python で `sha1(b"blob %d\0" + bytes)`)。
- 変換 checkout (`eol` / `ident` / `working-tree-encoding` / smudge filter) を生む attributes と
  config は、内容照合より**前に** fail-closed で禁じる。禁じたうえで raw 照合するので、
  A9 が指摘した「raw は正当な変換 checkout を拒否する」経路は定義上存在しなくなる。
- object format が `sha1` であることを検査する (A9 の 3 点目)。実測: 現行 pin は `sha1`。

## 1. 所見の裁定

### 採用 (real、scope 内)

| # | 所見 | 裁定 | 対応 |
|---|---|---|---|
| A3 / B3 | path-aware hash は clean 等価 gate であって exact-byte gate でない | **real** | §0 のとおり raw bytes を確定。プランの CRLF 受理正例は**削除**し、CRLF worktree は**拒否**の node にする |
| A2 | closure 無効時、`refs/replace` で HEAD 表示を保ったまま全内容を差し替えられる | **real** | helper の全 git 呼び出しに `--no-replace-objects` を付ける。`_submodule_worktree_state` の `rev-parse HEAD` にも付ける |
| A1 | closure 無効時、index に無い ignored file を submodule 内へ足せる | **real** | helper 自身が submodule worktree の非 directory file 集合を列挙し、`index path ∪ {".git"}` と一致することを要求する (nested submodule worktree と `.git` の中は降りない)。closure の有無に依らず効く |
| A5 | `admin_dir` を両辺 `resolve()` するので期待 admin path の symlink 化を束縛できない。`--git-common-dir` 未検査 | **real** | 期待 admin path の**全成分**が symlink でないことを要求し、`--git-common-dir` も snapshot 内かつ admin dir と一致することを要求する |
| A6 (symlink 部分) | 中間 directory の symlink 化で final component の `lstat` を騙せる | **real** | 各 tracked path の全成分について symlink を経由せず repository 内に留まることを要求する |
| A4 / A11 / B5 | 内容照合より前に repo config 由来の外部 program が起動しうる。P3 の `submodule.*` 拒否は冗長かつ不足 | **real** | P3 を **key 名の allowlist** へ格上げする。snapshot と全 initialized submodule の **local config** を対象とし、closure の有無に依らず適用する。allowlist 外の key は `RC_SNAPSHOT` で拒否。`submodule.*` も `core.fsmonitor` も `filter.*` も `core.autocrlf` も `include.path` も自動的に落ちる |
| A10 / B4 | source 側に full 内容照合を掛けるのは境界の取り違え | **real** | source には marker / admin / common-dir / config allowlist を要求し、**full 内容照合は destination だけ**に掛ける (プラン推奨と一致) |
| A8 | 提案 node には主要検査を外しても緑になる帰属穴がある | **real** | §3 の変異事前登録で closure 無効枝・再帰・source 側・config allowlist の各 mutant を登録する |
| B7 | 影響する既存 node はプランの 5 件より広い (synthetic 12 + real fixture 17) | **real** | 焦点走に B7 の列挙を含める |
| A7 | 攻撃面は「実効回避 / 既存検査済み / 単独では無効」の 3 種 | **real** | 記録。sparse-checkout の正当利用を拒否する件は、実 snapshot が sparse でないため無害と判定 |

### 採用 (real、記録の訂正のみ・実装影響なし)

| # | 所見 | 裁定 | 訂正内容 |
|---|---|---|---|
| A13 | M2 は作業木の pin `511c9538` を測っており、実 snapshot が使う `d706650c` ではない | **real** | **実測し直した** (§2 M6)。`d706650c` でも raw 不一致 **0/404**、mode 不一致 0、object format `sha1`、全件 0.124s。`--no-local` clone による実転送 + 新規 checkout で測った |
| A17 | pin 閉包「2 件」は repo 内 schedule だけを数えた値 | **real** | 実測: `/work/1/SFC/tanab/dev-wave-jobs/` 配下に `submodule_manifest_sha256` を持つ file が **293 件** (当該 run だけで 29 件)。**(P1) reject-only を確定させる根拠**になった |
| B11 | 「コード外 tool pin 0 件」は `apparatus-pin.json` が反例 | **real** | 私の DW-O09 探索が F30 の罠を踏んだ。ただし [T-1223] が同 pin を「歴史記録・参照する現行コードなし」と裁定済み (`s4-ruling.md:12,75`、`erratum-f176.md:91`)。実装影響なし |
| A16 | 「copy2 は index stat cache を必ず無効化する」は誤り | **real** | 同一 filesystem では device が変わらず、`core.trustctime=false` 等で ino/ctime が判定材料から外れる構成がある。**本裁定は stat に一切依存しない** (raw hash) ので設計影響なし。M4 の断定を撤回する |
| A18 | 「純増検出力 = 4 vector」は数え方が誤り | **real** | 独立述語は A/C = index↔HEAD、B = worktree↔index、D = marker↔admin の **3 系統**。本裁定でさらに file-set 完全性・成分 symlink・common-dir・config allowlist・replace ref の 5 系統が加わり **計 8 系統** |
| A15 / B9 | 費用「1 秒未満」は未確定 | **real** | raw を採るので `hash-object` の subprocess 費用は発生しない。採用値は §2 M6 の **0.124s / repository** とし、verify の反復回数 (snapshot finish 1 + supervisor precheck 1 + 試行ごと pre/post 2 + final replay 1) を worklog に明記する |
| B2 | 実 snapshot の正例は Shirakami の `--recursive` init を要する | **real** | 記録。本 wave のテストは synthetic + 既存 real fixture node で担保する |
| B10 | 2 件の schedule.json は runtime consumer を持つ | **partially real** | `supervise_pair` / `_replay_manifest` はコードとして読むが、この 2 件を入力にする自動走行は無い。(P1) 採用で無害化 |
| B12 | reject-only は証拠を保存しない | **real** | (P1) を維持し、**proof chain には「検査が通った事実」を保存しない**ことを worklog に明記する |
| B1 / B8 | nit | **real** | 記録のみ |

### scope 外 (real だがこの wave では実装しない → 裁定パッケージへ)

| # | 所見 | 理由 |
|---|---|---|
| A12 / B6 | `collect_run` / `make_packets` / verdict CLI が snapshot を再検証しない | 台帳が **[T-1263]** として別項に立てている。本 wave で実装すると 2 項目が混ざり、受理集合の変化を分けて測れない |
| A6 (hardlink / TOCTOU) | snapshot 外の hardlink alias による時間差改変 | pre/post oracle という既存機構の射程であり、root repo にも同型に存在する。内容同一性 gate とは別の境界 |
| A4 (残余) | system-level git config は `_clean_environment` の射程外 | repo 外の設定であり、本 gate の編集面から届かない |

## 2. 親の追加実測 (裁定の根拠)

**M6 — 実 snapshot が使う CCBench pin での raw 照合 (A13 への回答)**

`git ls-tree 8c8dc5e0(BASE_COMMIT) external/ccbench` = `d706650cdb31e442bef45b9b4216951d4fb40969`。
これを `--no-local` clone → `checkout --detach` した使い捨て木で測った (probe: job tmp `probe_t1262d.py`)。

| 量 | 値 |
|---|---|
| index entry | 405 (`100644`=285 / `100755`=119 / `160000`=1) |
| **raw bytes hash と index blob id の不一致** | **0 / 404** |
| 欠落 | 0 |
| mode (実行 bit・symlink 種別) 不一致 | 0 |
| object format | `sha1` |
| 全件 raw sha1 の所要 | **0.124s** |
| `--no-replace-objects diff-index --cached --quiet HEAD --` | rc=0 |
| nested gitlink | `third_party/shirakami` = `fb14e659` |

**M7 — pin 閉包の再測 (A17 への回答)**

`submodule_manifest_sha256` を含む file: repo 内 2 件 (insight の schedule.json)、
repo 外 `/work/1/SFC/tanab/dev-wave-jobs/` 配下 **293 件** (`dev-wave-t181-certified-rerun` だけで 29 件)。

## 3. plan v2 (確定した実装方針)

`tools/codex_reasoning_ab.py` に次を実装する。**oracle dict へ field を足さない (P1 確定)。**

1. `_submodule_worktree_state` (`:915-981`)
   - `rev-parse HEAD` を `--no-replace-objects` 付きにする。
   - initialized 枝の return 直前で、marker / admin を束縛する:
     `--no-replace-objects rev-parse --absolute-git-dir` と `--git-common-dir` の双方が
     期待 admin dir と一致し、期待 admin path の**全成分が symlink でない**こと。
   - 既存の理由文字列 3 本 (`initialized submodule HEAD/gitlink mismatch` /
     `submodule object store cannot be inspected` / `submodule worktree is not a directory`) は
     一字も変えない。
2. 新規 `_submodule_content_identity_reasons(snapshot, repositories)` を `_index_stage_entries` の後に置く。
   repository ごとに次の順で検査し、理由を**返す** (例外を投げない):
   1. object format が `sha1` であること。
   2. local config の key 名 allowlist。**allowlist は実 builder が書く key を実測して確定する**
      (`git init` + `submodule update --init` + `checkout` が書くもの)。allowlist 外は拒否。
   3. `--no-replace-objects diff-index --cached --quiet --ignore-submodules=none HEAD --` (rc≠0 で拒否)。
      **`git write-tree` は使わない** (封緘済み object store を汚す)。
   4. `ls-files --stage -z` の各 entry について: 全 path 成分が symlink を経由せず repository 内に
      留まること、file 種別と実行 bit が mode と一致すること、`120000` は `readlink` の bytes を、
      `100644`/`100755` は**生 bytes**を `sha1(b"blob %d\0" + bytes)` で index blob id と照合すること。
      `160000` は hash 対象外 (再帰先の repository 自身が検査する)。
   5. worktree の非 directory file 集合が `index path ∪ {".git"}` と一致すること
      (nested submodule worktree と `.git` の中は降りない)。
3. `_git_closure_reasons` (`:1396-1435`) と `verify_snapshot` の `enforce_closure=False` 枝
   (`:1690-1691`) の**両方**から helper を呼ぶ。inventory は 1 回だけ取り、
   `_expected_filesystem_files` へ precomputed で渡す。
4. `_init_submodules_from_local_source` (`:715-762`) は `_submodule_worktree_state` の強化を
   共有するので marker / admin / common-dir が効く。加えて source の local config allowlist を要求する。
   **full 内容照合は掛けない。**
5. oracle dict (`:1706-1726`) は 1 field も変えない。

## 4. 変異事前登録 (DW-M01)

harness = `tools/mutation_harness.py`。各変異は「同じ入力を拒否する層が前後に無い」ことを
確認済みで登録する。帰属は helper 直呼びの node (単一理由) を使い、end-to-end node は統合証拠とする。

| # | 変異 (無効化する検査) | old の形 | 期待 kill node |
|---|---|---|---|
| **N1** | **index↔HEAD^{tree} 照合を外す (= wave 前の実コードの形。`return "initialized", candidate` のまま内容検査を持たない)** | 現行 `:972` の `return "initialized", candidate` 相当 | **空 CCBench 拒否 node** と HEAD^{tree} 外 index entry 拒否 node |
| N2 | worktree raw bytes 照合を外す | 新設 | bytes 改変拒否 node、CRLF 拒否 node、symlink target 改変拒否 node |
| N3 | marker↔admin 束縛を外す | 新設 | rogue admin 拒否 node |
| N4 | `--no-replace-objects` を外す | 新設 | replacement ref 拒否 node |
| N5 | worktree file-set 完全性を外す | 新設 | ignored extra file 拒否 node |
| N6 | admin path 成分の symlink 検査を外す | 新設 | admin symlink 拒否 node |
| N7 | tracked path 成分の symlink 検査を外す | 新設 | 中間 directory symlink 拒否 node |
| N8 | config allowlist を外す | 新設 | post-seal config 拒否 node |
| N9 | `enforce_closure=False` 枝の helper 呼び出しを外す | 新設 | closure 無効での拒否 node |
| N10 | 再帰 (nested initialized) への適用を外す | 新設 | grandchild 改変拒否 node |
| N11 | 実行 bit / file 種別照合を外す | 新設 | 実行 bit 不一致拒否 node |
| N12 | object format 検査を外す | 新設 | (帰属不能なら登録を取り下げ、`DW-M01` に従い実効 gate へ再照準する) |

**過剰決定の回避 (DW-M03):** 攻撃 A〜D の end-to-end fixture は `submodule.<n>.ignore=all` を
**local config ではなく `.gitmodules` (tracked)** に置く。local config へ置くと N8 の
config allowlist と二重に発火し、単一理由性が壊れる。

**正例の登録 (DW-M01「承認外の過剰拒否を検出する正例」):**

| # | 正例 | 主張 |
|---|---|---|
| P-1 | 無改変 initialized submodule が受理され続ける | 受理集合が承認外に縮んでいない |
| P-2 | 受理された snapshot の oracle canonical bytes・`submodule_manifest_sha256`・`manifest_sha256` が本変更の前後で不変 | (P1) reject-only が成立している |
| P-3 | 未初期化 nested submodule を持つ inventory が従来どおり扱われる | 既存の受理形を壊していない |

## 5. ユーザーへ返す裁定パッケージ (scope 外の real 所見)

1. **[T-1263] の中間成果物層。** `collect_run` / `make_packets` / append-verdicts / freeze-verdicts /
   reveal-mapping は snapshot を再検証しない。本 gate は `verify_snapshot` と final replay には
   効くが、receipt・材料 packet・verdict freeze は旧 gate で受理された参照を区別できない。
   **本 wave は「aggregate の final replay までが検証済み」と明記するに留める。**
2. **hardlink / TOCTOU。** snapshot 外の hardlink alias で、pre/post oracle の間だけ bytes を
   変える攻撃は本 gate では塞がらない。root repo にも同型に存在する既存の境界。
3. **system-level git config。** `_clean_environment` は `GIT_*` と user config を除くが
   system config は残る。repo 外の設定であり本 wave の編集面から届かない。
