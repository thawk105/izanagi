# 段 4 裁定 — [T-930] 保留テストの迂回封鎖

親裁定 2026-08-12 21:45 JST。段 2 プラン (`s2-plan.md`)、段 3 敵対 2 本 (`s3-sol.md` STOP /
`s3-luna.md` STOP)、および親の独立実測に基づく。

## 結論 — 段 2 の推奨案 (sentinel + module 単位 refusal) は採らない

**両敵対子が独立に同じ BLOCKER へ収束した** (sol §1 / luna §1): sentinel は
「conftest module が import された」ことしか証明せず、`python3 -c 'import
orchestrator.tests.conftest; runpy.run_path(...)'` で guard が no-op になる。
親も一次資料で確認した — `test_growth_test_holds_contract.py:17` は pytest hook 登録と無関係に
canonical conftest を通常 import しており、「module の存在」と「enforcement の作動」は別事実である。

**採用する設計 = node 単位の call-time 拒否。sentinel も conftest 変更も使わない。**

保留 node の関数本体を、registry 由来の wrapper で置き換える。wrapper は呼ばれた時点で
`IZANAGI_RUN_GROWTH_HELD_TESTS` が exact token かを見て、違えば本体へ入らずに拒否する。

### 親が生死を実測した (2026-08-12 21:40 JST、`probe-nodelevel.sh`、実編集 + 即時復元・復元確認済み)

`test_s8b_repo_scan_invariant.py` の held node 1 件に wrapper を実際に当てて測った。

| 経路 | wave 前 | node 単位 wrapper 適用後 |
|---|---|---|
| A (正規 pytest) | `1 skipped` | **`1 skipped` (不変)**、1 秒 |
| B (`--noconftest`) | `1 passed` 22 秒 | **rc=1 拒否、0 秒** |
| E (自前 `_run()`) | `PASS` rc=0 | **rc=1 拒否、0 秒** |
| 既存 token での解除 | 実行 | **rc=0 実行 (不変)** |

skip が先に効くため wrapper は A では**呼ばれない** — これが「A を bit 単位で変えない」ことの機序で
あり、sentinel のような外部状態を一切必要としない。拒否は本体到達前なので**コストは O(1)** で、
repo 成長に比例しない (22 秒 → 0 秒)。

## 所見の裁定

| # | 所見 | 判定 | 処置 |
|---|---|---|---|
| sol §1 / luna §1 | sentinel = import 存在。G 経路・`-p` preload・偽造で解除 | **real** (独立 2 例) | sentinel を**廃止**。設計変更で根本消去 |
| sol §2 | 同一 process 再入で import-time guard が再実行されない | **real** | call-time 検査により消去 (呼ばれるたびに検査) |
| sol §3 | 非 held の別 test から held 関数を直接呼べる | **real** (wave 前から存在する穴) | call-time 検査により同時に閉じる。scope 内 |
| sol §4 | メタテストが構文結線しか証明しない | **real** | 実挙動 subprocess matrix を必須化 (下記)。ただし **O(1) 制約**を課す |
| sol §5 / luna §2 | alpha は module 単位 hold へ格上げし、現に効いている E 経路を壊す | **real** (親の実測と一致) | node 単位 (= 親 provisional (P2) の beta 側) を採用 |
| sol §6 | reload で sentinel identity が変わり A が collection error | **moot** | sentinel 廃止により消滅 |
| luna §3 | README allowlist / plain runner meta-test が新挙動を表現できない | **moot (alpha 前提)** | node 単位では pytest-only 3 file の挙動は不変 (E で 0 件実行のまま)。README 改訂は不要 |
| luna §4 | A no-op 検査が自分で sentinel を作る | **moot** | ただし「A の証拠は fresh subprocess で取る」は採用 |
| luna §5 | 並行 wave の entry 追加で count/digest 定数が赤 | **real・scope 外** | land 順は先方優先。main 再取り込み後に registry と pin を再読 |
| luna §6 | production hold は scope 外に残る | **real・scope 外** | 本 wave は test 層のみ。報告で production を閉じたと書かない |

親 provisional の帰趨: **(P1) 維持** (B と E の両方が対象)。**(P2) beta を採用** — ただし段 2 が
懸念した harness 侵襲は発生しない (`_run()` は 1 行も編集せず、wrapper が例外を投げると既存の
`except Exception` が ERROR として数え rc=1 になる)。**(P3) 変更** — B は collection error では
なく **test failure (rc≠0)**、E は既存 harness の rc=1。いずれも「静かな rc 0」ではない。

## plan v2 (実装 scope)

1. `orchestrator/tests/growth_test_holds.py`
   - `class GrowthTestHoldBypassRefused(RuntimeError)`
   - `def enforce_held_functions(namespace, module_file) -> tuple[str, ...]`
     registry から当該 basename の held 関数名を取り、namespace の同名 callable を wrapper で置換する。
     **0 件なら `ValueError`** (guard の誤設置検出)。**registry にあるのに namespace に無い名前が
     あれば `ValueError`** (改名・typo 検出)。戻り値は wrap した名前の tuple。
   - wrapper: 呼び出し時に env が exact token でなければ `GrowthTestHoldBypassRefused` を送出。
     診断は literal prefix `IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1` + JSON payload
     (`ensure_ascii=True`、node_id / release_env / release_token を含む)。
     未設定・空・typo はすべて拒否 (A 経路の `pytest.UsageError` は conftest 側に残る)。
   - `functools.wraps` で signature・marker (`parametrize` 等) を保存する。
     **fixture を取る held 関数が opt-in 下で正しく走ることを実装子が実走で確認すること。**
   - **台帳の 30 row・`release_condition` literal・`RELEASE_EXPLICIT_USER_COMMAND_ONLY` は不変。**
2. `orchestrator/tests/conftest.py` — **変更しない。** 保留印 (skip marker) は従来どおり conftest だけが
   付ける (制約「同一 node の保留印は 1 つ」を構造的に満たす)。並行 wave との衝突面も増やさない。
3. 保留 8 file それぞれの**全 test 定義の後・`__main__` ブロックの前**に 2 行
   (`import` + `enforce_held_functions(globals(), __file__)`)。
4. `orchestrator/tests/test_growth_test_holds_contract.py` へ検査を追加。
   - **binding (AST)**: registry 由来の全 file が top-level で厳密に 1 回呼ぶ。
     負例 = in-memory source から call を除いて赤になること。
   - **wrap の実在**: registry の 30 node すべてが実際に wrapper 化されている
     (合成 namespace ではなく実 module を import して確認)。
   - **実挙動 subprocess matrix (すべて O(1)・held body を走らせない)**:
     (a) B `--noconftest` → rc≠0 + prefix + `1 passed` 不在、
     (b) E `python3 test_s8b_repo_scan_invariant.py` → rc≠0 + prefix、
     (c) **G 経路** `python3 -c 'import orchestrator.tests.conftest; runpy.run_path(...)'` → rc≠0 + prefix、
     (d) 非 held の別 process から held 関数を import して直接呼ぶ → 拒否、
     (e) **A の正例** 通常 pytest で held node → rc=0 + `1 skipped` + 保留マーカー。
   - **過剰拒否の正例 (受理集合を縮小する wave の必須項、DW-M01)**:
     `python3 orchestrator/tests/test_env_attestation.py` が **`103 passed, 1 skipped` を保つ**
     (0.76 秒、実測済み)。module 単位の過剰拒否へ退行したら赤になる。
   - **解除口が 1 本であること**: 合成 namespace に軽量関数を差して、exact token で本体到達・
     typo で拒否を確認する (実 held body は走らせない)。
   - 期待値の literal は **producer 定数を import せず test 側にハードコード**する
     (producer と consumer の同時退行による恒真化を断つ。worklog 483 の同型再発防止)。

## 事前登録する変異 (DW-M01、実装後に anchor を再検証して本走)

| # | 変異 | 期待 |
|---|---|---|
| M1 | wrapper の env 比較を恒真化 (`!=` → `==` 反転) | B/E/G の実挙動検査が KILLED |
| M2 | 1 file から `enforce_held_functions` 呼び出しを削除 | binding 検査が KILLED |
| M3 | registry に無い関数まで wrap する (過剰拒否) | 過剰拒否正例 (`103 passed, 1 skipped`) が KILLED |
| M4 | wrapper を原関数の素通しにする (no-op wrap) | 実挙動 matrix が KILLED |
| M5 | token 比較を前方一致へ緩める | typo 拒否検査が KILLED |
| M6 | 0 件 namespace の `ValueError` を除去 | 誤設置検出が KILLED |
| M7 | conftest の skip 付与を削除 | A の `1 skipped` が消え、wrapper が A で発火して KILLED |
| M8 | 新テストを wave 前 HEAD 版へ当てる (DW-M08 新旧両走) | 新テストだけが B/E/G を検出する差分を示す |

## scope 外 → 段 4 裁定パッケージでユーザーへ返す

1. **脅威モデルの明示**: 同一 process 内で任意コードを書ける者は `__wrapped__` 直呼び・guard の
   再束縛で必ず回避できる。Python にこれを防ぐ手段はない。**本 wave が封鎖するのは runner の
   起動形**であり、その旨を worklog へ明記する。これ以上の封鎖 (別 process 強制など) を望むかは
   ユーザー裁定事項。
2. C / D 経路の INTERNALERROR (rc=3)。保留は破られていないが診断不能。直すと「repo 外 cwd からの
   走行を成立させる」方向になりうるため触らない。
3. production hold (`freeze_verification_hold.py`) の同型迂回可否 (luna §6)。本 wave は test 層のみ。
4. 並行 wave が entry を追加した場合の count / key digest / row digest 定数の同期 (luna §5)。

## 実装子への必須条件

- Codex `role=author`、`sandbox=workspace-write`。docs 編集と commit はしない。
- **既存テストの期待値を変更しない。** 反転・緩和・skip・削除で辻褄を合わせない。
- 台帳 30 row と `release_condition` literal を変更しない。conftest を変更しない。
- 新しい env / CLI flag / 設定ファイルを作らない。
- 新設する検査は **repo 成長に対して O(1)** であること (成長比例のテストを新設したら本末転倒)。
- fixture / parametrize を持つ held 関数が opt-in 下で走ることを実走で確認する。
