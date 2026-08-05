# [T-522] 段 4 裁定 — plan v2 と変異事前登録

## 1. 所見裁定 (real/refuted・採否・scope)

### レンズ A (正しさ境界)

| # | 判定 | 採否 | scope | 裁定 |
|---|---|---|---|---|
| A1 「全 Pegasus 拒否」の射程過大 | **real** | 採用 (文言のみ) | 内 (文言) / 外 (穴の閉鎖) | 保証を「**正しく LOGIN/SUSPECT と判定され、現行 parser が実行 target と認識した綴り**の全拒否」に狭めて brief・docs・test docstring へ書く。`python3 -c` / cwd / symlink / 未解析 launcher の残穴は F121 で既に [T-518] へ起票済みであり本 wave では閉じない |
| A2 単調性と異常時縮退の非両立 | **real** | 採用 | 内 | 異常時 DENY を採る。単調性 (D175 決定 6) の射程を「**valid canonical registry の正常系**」に限定し、registry 異常時の縮小は意図的な fail-closed として新 decision に記録する。fail-open は規律 2 違反であり選択肢にしない |
| A3 loader 返値の postcondition 未検証 | **real** | 採用 | 内 | wrapper 内で返値型を最小再検証し、**registry 確定と `_SANCTIONED_PATHS` 導出を同じ try に入れる**。`None`/list/scalar entry/例外を投げる Mapping を注入して実 subprocess rc=2 を固定する |
| A4 symlink/race/byte cap | **real** | 採用 (縮小) | 内 | `os.open` に `O_NOFOLLOW`/`O_CLOEXEC`、**fd に対する `fstat` で regular 確認と size cap (1 MiB)**、同一 fd から bounded read。祖先 symlink と二 checkout fixture は対象外 (repo root の信頼は前提) |
| A5 README checker が site を表せず inline へ逃げられる | **real (blocker)** | **採用 = 設計変更** | 内 | plan §F の command 解析を**廃止**し、**宣言表方式**へ置換する (下記 plan v2 §B-4)。B3/B4/B5 も同じ変更で閉じる |
| A6 grandfather の未実測性が固定されない | **real** | 採用 | 内 | 投影表の evidence 列を **kind ではなく exact 文字列**にする。`evidence_kind()` 写像は廃止し面を減らす |
| A7 exact-24 と synthetic fixture の衝突 | **real** | 採用 | 内 | production validator は「非空・全 entry schema 適合・class 閉集合」まで。**exact 24 と class 内訳は test 側の独立 golden** に置く (B9 と同一裁定) |
| A8 検出力の名称が過大 | **real** | 採用 | 内 | 各検査の docstring と worklog に検出力を明記。projection 等値検査をデータ完全性の証拠に数えない |
| A9 変異の帰属不成立 | **real** | 採用 | 内 | 各変異で admission 固有 finding の exact prefix と件数を assert。matrix に一次検出器と巻き添えを分けて記録 |
| A10 綴り族 corpus 不足 | **real** | 採用 (縮小) | 内 | local-ok 5 本 × 正規化綴り (`./` 前置・内部 `//`・末尾 slash・repo 内 absolute) の受理 bit を**変更前の値の literal golden**として固定する。69 綴り全体の再構築は行わない |
| A11 計測主張の一般化 | **real** | 採用 | 内 | 「warm microbenchmark では単純 JSON load が起動時間の 3.3%」まで弱める。断定しない |

### レンズ B (射程・整合・運用)

| # | 判定 | 採否 | scope | 裁定 |
|---|---|---|---|---|
| B1 配線テストが `hooks` 欠落で skip | **real** (実測確認済み: `test_hooks.py:1760` の `skip`) | 不採用 | **外** | admission registry ではなく hook 配線 gate の問題。**裁定パッケージへ返す**。本 wave は「S3 が保証するのは docs/data の同期であって防壁の実配線ではない」と明記する |
| B2 check_docs 側 `SystemExit` 未対策 | **real** | 採用 | 内 | import・load・全呼出しで `BaseException` を finding 化し、`sys.modules` と `sys.dont_write_bytecode` を復元。`SystemExit(0)` 変異を両側のテストに入れる |
| B3 fenced-only の逃げ道 | **real** | 採用 | 内 | A5 の宣言表方式で閉じる |
| B4 変数合成での迂回 | **real** | 採用 (縮小) | 内 | 宣言表方式に加え、**README の fenced block 内で `pegasus/` を含むのに `tools/pegasus/` literal を含まない行を赤**にする |
| B5 site 推定の偽陽性 | **refuted-by-redesign** | — | 内 | command 解析を廃止したため消滅する |
| B6 `tools/README.md` が正反対の記述 | **real** (実測確認済み: `tools/README.md:28-31`「分類 registry も gate も存在しない」) | 採用 (本文修正のみ) | 内 (本文) / 外 (閉集合化) | 本 wave で本文を正す。living doc 領域の閉集合化は**裁定パッケージへ** |
| B7 `reason`/`primary_gate` 非同期 | **real** | 部分採用 | 内 (射程明記) / 外 (散文同期) | 投影表は (path, class, **exact evidence**) の 3 列とし、`reason`/`primary_gate` の散文同期は**裁定パッケージへ**。S3 の保証射程を「class と evidence の同期」と明記する |
| B8 CommonMark 表境界 | **real** | 採用 (縮小) | 内 | 投影表の cell は**単一 backtick literal のみ**許可し、`\|` を含む行・code span 崩れは赤。orphan 判定は「header+separator に属さない `\|` 開始行」に厳密化しテストを付ける |
| B9 exact-24 の永久条件化 | **real** | 採用 | 内 | A7 と同一裁定 |
| B10 land 原子性 | **real** | 採用 | 内 (一括 land) / 外 (過去 commit 方針) | JSON・loader・hook・checker・docs・tests を**同一 commit・同一 tested tip** で land する。過去 commit へ戻したときの防壁方針は**裁定パッケージへ** |
| B11 受入の `python3 -c` が規範外 | **real** | 採用 | 内 | login では `py_compile` と `check_docs` までに留める。loader の実呼び出し検証は `run_tests.py` 経由 (計算ノード) のテストだけで行う |
| B12 計測主張 | **real** | 採用 | 内 | A11 と同一 |

## 2. plan v2 (確定仕様)

### A-1 正本 JSON `tools/pegasus/admission_registry.json`

- 形式: `{"schema_version": "pegasus-admission-registry/v1", "entries": {path: {class, reason, primary_gate, evidence}}}`
- UTF-8 / BOM なし / LF / 2-space indent / `ensure_ascii=False` / 末尾 exact 1 LF
- key 順は `schema_version`, `entries`。entry key 順は `class`, `reason`, `primary_gate`, `evidence`。path は昇順
- 24 entry の 4 field を `hooks/guard_bash.py:183-328` から**一文字も変えずに**移す
- **canonical bytes の SHA-256 pin は置かない** (予測値の焼き込みは F27 型の罠になる)。
  代わりに全 24 entry の 4 field を `test_hooks.py` の独立 literal golden で固定する

### A-2 loader `tools/pegasus_admission_registry.py` (`tools/pegasus/` の外)

- 外に置く理由: `test_bash_pegasus_execution_inventory_is_synchronized` が `.py` を無条件に実行体と数え、
  subtree 内に置くと 25 件目として registry 同期が壊れるため (段 2 の指摘、親が実測確認)
- 公開面は `REGISTRY_RELATIVE_PATH` / `AdmissionRegistryError` / `load_admission_registry(repo_root)` の 3 つ
- 読み込み: `os.open(O_RDONLY|O_NOFOLLOW|O_CLOEXEC)` → `os.fstat` で regular 確認と 1 MiB cap →
  同一 fd から bounded read → UTF-8 decode → duplicate key 検出付き parse → schema/path/class 検査 →
  canonical 再 serialize 一致確認
- **validator は exact-24 を要求しない** (非空・全 entry 適合・class 閉集合まで)
- 全件検査を終えるまで mapping を公開せず、**部分成功を返さない**
- 失敗はすべて `AdmissionRegistryError` に正規化する

### A-3 `hooks/guard_bash.py`

- literal registry (183-328 行) を wrapper 呼び出しへ置換する
- wrapper は `spec_from_file_location` で `<repo_root>/tools/pegasus_admission_registry.py` を exact path import。
  `sys.dont_write_bytecode` と `sys.modules` を try/finally で復元する
- **`BaseException` (SystemExit 含む) を捕捉し、失敗時は `({}, diagnostic)` を返す。import 時に例外を漏らしてはならない**
  (漏らすと process が rc=1 で死に、Claude Code の hook 契約では rc=2 以外は遮断しないので **fail-open** になる。親が実測確認)
- 返値の型を wrapper 内で最小再検証し、**`_SANCTIONED_PATHS` の導出まで同じ try に入れる**
- `_SANCTIONED_PATHS` は local-ok からの導出を維持 (二重表を作らない)
- `_pegasus_admission_entry` の prefix fallback は維持
- `OTHER` / `PEGASUS_COMPUTE` の既存 ALLOW bit は不変

### B-1 runbook §7.0 完全投影表 (新設・親が本文を書き、checker が照合)

`| path | class | evidence |` の 3 列 × 24 行。cell は単一 backtick literal のみ。
registry と (path, class, evidence) の**集合完全一致**を要求する。

### B-2 既存 unknown 表の規則

pegasus path の各行は次のいずれか。それ以外は赤。
- registry class が `unknown`
- class が `local-ok` かつ evidence が `legacy-admitted` で始まり、**同じ行の説明 cell に
  `` `local-ok` `` と registry の exact evidence 文字列がある** (grandfather の明示)

### B-3 既存 実測表の規則

全行の分類 cell が `local-ok`。path 集合 == registry で evidence が `runbook §7.0 実測` の path 集合。

### B-4 手順面 = **宣言表方式** (plan §F を置換)

`tools/pegasus/README.md` に機械検査対象の宣言表を置く。

`| path | 手順上の実行 site | registry class |`

- site 列は閉集合 `login-direct` / `qsub-job-body` / `compute-only`
- `login-direct` ⇒ registry class == `local-ok`。他の 2 値 ⇒ class != `local-ok`
- class 列は registry と exact 一致
- **README 本文 (fence 内外・inline code・通常文を問わず) に現れる registry 既知 path はすべて宣言表に載ること**
- README の fenced block 内で `pegasus/` を含むのに `tools/pegasus/` literal を含まない行は赤
  (実行 target の変数合成・command substitution の禁止)

### B-5 orphan row と表境界

§7.0 内の `|` 開始行は header+separator を持つ表に属すること。`\|` を含む行・code span 崩れは赤。

### B-6 loader の import 方法 (check_docs 側)

`REPO/tools/pegasus_admission_registry.py` の **exact path import** とする。
module 名 import にすると、`test_check_docs.py` が REPO を tmp へ付け替えても実 module を掴み、
「loader 不在 → 赤」の変異が効かなくなる (親が実測確認)。

### B-7 docs 差分 (親所有)

- `docs/pegasus-runbook.md` §7.0: 正本を hook から JSON へ移す / grandfather 追認と [T-520] 後の昇格 /
  投影表の新設 / `submit_silo_ladder_rung1.sh` 行の grandfather 明示 / 孤立行を表へ戻す /
  check_docs の検査対象追記 / **保証射程の明記** (class と evidence の同期であり、`reason`・`primary_gate` の
  散文と防壁の実配線は含まない)
- `tools/pegasus/README.md`: 宣言表の新設 / login direct の `collect_receipt.py` 手順を訂正
  (**この経路は現状 hook が拒否する。計算ノード確保下での実行は実 artifact が無い未実証経路である**と正直に書く)
- `hooks/README.md`: 正本の所在を JSON へ / hook は共有 validator による投影と記す
- `tools/README.md`: 「分類 registry も gate も存在しない」を現状へ更新する

### B-8 受入 (親、login 規範を守る)

- login: `python3 -m py_compile ...`、`python3 tools/check_docs.py`、`git diff --check`
- 計算ノード dispatch: `python3 tools/run_tests.py orchestrator/tests/test_hooks.py orchestrator/tests/test_check_docs.py -q`、
  最終は受入全走
- **`python3 -c` による loader 直接実行は行わない** (B11)

### 所有分離

| 単位 | 編集所有 |
|---|---|
| A | `tools/pegasus/admission_registry.json`, `tools/pegasus_admission_registry.py`, `hooks/guard_bash.py`, `orchestrator/tests/test_hooks.py` |
| B | `tools/check_docs.py`, `orchestrator/tests/test_check_docs.py` |
| 親 | `docs/pegasus-runbook.md`, `tools/pegasus/README.md`, `hooks/README.md`, `tools/README.md` |

素集合。B の実 repo 検査は A と親 docs の land 後に緑になる (B の実装子には「親 docs 未 land のため
赤になる finding 集合」を事前指定する)。

## 3. 変異事前登録 (DW-M01 / DW-M08)

harness は `tools/mutation_harness.py` を使う。各変異は**一次検出器**と**巻き添え検出器**を分けて記録する。
テスト強化 wave なので、docs 変異は新旧両走 (変更前 HEAD 版テストが何も検出しないこと) を示す。

| ID | 位置 | 変異 | 期待赤 (一次検出器) | 巻き添え | 単一理由性の根拠 |
|---|---|---|---|---|---|
| M1 | loader の全件検証 | 部分成功を返す (検証済み entry だけの mapping) | hook 新テスト「registry 破損時に local-ok 5 本を含む全 pegasus direct が LOGIN/SUSPECT で DENY」 | なし | 既存テストは healthy registry しか使わない |
| M2 | hook wrapper の `except BaseException` | `except Exception` へ狭める + loader に `SystemExit(0)` を注入 | hook 新テスト (subprocess rc=2) | なし | 現行 hook には SystemExit を止める層が無い (親が実測: `main()` の except は import 後にしか効かない) |
| M3 | runbook 投影表 1 行の class (docs 一時変異) | `dispatch-required` → `local-ok` | **新 check_docs 投影検査のみ** | なし (既存検査は docs 表を読まない) | **新検査の純粋 control**。変更前 HEAD 版テストは 0 件検出 |
| M4 | README 宣言表 1 行 (docs 一時変異) | 行を削除 (本文の出現は残す) | 新 check_docs「本文出現 ⊄ 宣言表」 | なし | 同上 |
| M5 | runbook 投影表の evidence (docs 一時変異) | `legacy-admitted (未実測)` → `runbook §7.0 実測` | 新 check_docs 投影検査 | なし | grandfather 固定の control |
| M6 | `check_docs.main` の新 checker 呼び出し | 呼び出しを削除 | 新 check_docs テスト群 (検査蒸発 control) | なし | 呼び出しは 1 箇所 |
| M7 | JSON の 1 entry の class (tracked file 一時変異、`DW-O19`) | `unknown` → `local-ok` | hook 独立 golden + 新 check_docs 投影検査 | **両方が一次** | 2 層で検出されるため matrix には「冗長 gate」と明記し、単独変異の証拠から外す (`DW-M03`) |

## 4. 裁定パッケージ (scope 外 real 所見 — ユーザーへ返す)

1. **hook 配線テストの skip (B1)。** `orchestrator/tests/test_hooks.py:1760` は `.claude/settings.json` に
   `hooks` キーが無いと skip する。設定から `hooks` を丸ごと消すと、全 hook が発火しないのにテストは緑になる。
   D30 の再設計期の遺物であり、現在は配線済みなので skip を廃止できる。
2. **`reason` / `primary_gate` の散文同期 (B7)。** 本 wave は class と evidence だけを同期する。
   registry が「入力 cap 未完」とする path の説明を docs 側で「実測済みで安全」に書き換えても検出されない。
   安定 ID (`reason_id` / `primary_gate_id`) を投影する設計が必要かを裁定されたい。
3. **分類 claim を書ける living doc の閉集合化 (B6)。** 今回 `tools/README.md` を手で直したが、
   同じ事実を書ける文書の集合が閉じていないため再発しうる。
4. **過去 commit へ checkout したときの防壁方針 (B10)。** 本 wave 以前へ戻すと新 checker 自体が消える。
   「commit 相対の旧防壁へ戻る」か「外部の最新 hook を維持する」かは未裁定である。
5. **registry 異常時の可用性縮小 (A2 の帰結・報告)。** JSON が壊れる・消える・権限が落ちると、
   現在 login で通っている 5 本 (`dispatch_compute.py` / `fetch_third_party.py` / `submit_certify.sh` /
   `submit_floor.sh` / `submit_silo_ladder_rung1.sh`) も拒否される。安全側だが可用性は下がる。
   これを許容しない場合は別設計が要るため、報告する。
