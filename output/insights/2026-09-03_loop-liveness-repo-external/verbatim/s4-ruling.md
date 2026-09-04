# 段 4 裁定 — 親が real / refuted、採否、scope、plan v2 を確定する

親は両レンズの決定的な主張を 1 件ずつ現物で検算した。以下の「親の検算」はレンズの報告ではなく、
親が自分で走らせて得た結果である。

## 結論

- **単位 A: 採用する。ただし prefilter を NFKC 正規化 source に対して行う形へ変更する。**
- **単位 B: scope を縮小して採用する。登録簿と全走査メタ gate は作らない。**
  対象は既知 4 file の module-local な内容 guard だけとする。
- **5 分問題そのものは本 wave では解決しない。** 律速は最長単体 node であり、本 wave は触れない。
  D312 に従い「何から何へ / 残る律速 / 次に何を削るか」の形で報告する。

## 親が現物で検算した事実

### (M1) NFKC — レンズ A の A-1 は正しい

`layout.ｅxploration_campaign_layout(x)` (全角 `ｅ` U+FF45) は、生 source に ASCII の
`exploration_campaign_layout` を**含まない**のに、`ast.parse` 後の `Attribute.attr` は
NFKC 正規化されて `exploration_campaign_layout` に**なる**。`Name` 形でも同じ。
したがって**「字句 marker は AST 発見の必要条件」という親 brief の論証は破れている。**
親 brief `(P3)` は **refuted**。

### (M2) NFKC 正規化 prefilter で必要条件が回復し、効果もほぼ変わらない

| 経路 | 187 file の所要 | 反例を捕まえるか | 発見集合 |
|---|---:|---|---|
| 無 prefilter (現行) | 1.718 s | — | 7 件 |
| 生 source prefilter | 0.247 s | **捕まえない** | 7 件 |
| **NFKC 正規化 prefilter** | **0.285 s** | **捕まえる** | 7 件 |

NFKC 版でも **83.4% 削減**。正規化の追加費用は 0.038 秒。**修正は成立する。**

### (M3) 構文検査の検出力低下は 3 module 分で、代替 gate は保留中

campaign 186 module のうち test suite の source で名前が挙がるのは 183。残る 3 本
(`p2_5`, `s6_amendment_20260713_fence`, `s6_proposal_rounds_power`) は自分の file 以外
どこからも名指しされていない。レンズ A は「別の campaign 全体 syntax gate は確認できなかった」と
書いたが、**親は `test_campaign_import_invariant.py` がそれに当たり、`ast.parse` の失敗を
`AssertionError` にすることを確認した。ただし同 file の 6 node は `growth_test_holds.py` で
恒久保留されており実走しない。** したがって検出力は本当に失われる。失う範囲は 3 module 分。

### (M4) 保留登録簿の件数 — 親の 61 もレンズ B の 50 も違う

`"<file>.py::<test>"` 形の literal を数えると **53 件、distinct 52 件**。
親が最初に使った `grep -c "::"` は 61 を返したが、これは `::` を含む行を数えており過大。
**件数は本裁定の結論に効かないので、成果物では「約 50 件」と書かず、
権威は `tools/hold_inventory.py` の出力とする。**

### (M5) `output_snapshot_ignores.py` の動的依存 — 型は real、深刻度はレンズ B の記述より低い

レンズ B は `output_snapshot_ignores.py:73-111` が
`git rev-parse --git-path info/exclude` と `git config --get core.excludesFile` の返す path を
`expanduser()` して bytes を読むことを指摘した。**これは正しい。字句走査では原理的に見つからない。**

親が現物を確認した結果:

- `core.excludesFile` は**未設定** (rc=1)。よって現在この source は読まれない。
- `.git/info/exclude` は**空でなく 10 行**あり、`**/.claude/worktrees/` などを含む。
- **しかし `_rule_candidates` (`:121-140`) は `b"**"` を含む規則を捨て、静的前置が `output/` で
  始まる規則しか採らない。10 行はすべて `**` を含むため、現在の寄与は 0 件である。**
- 不在時は `_optional_rule_bytes` が `b""` を返すので、**file を消しても現行テストの挙動は変わらない。**

したがって「`.git/info/exclude` の掃除で全 wave が落ちる」は**現行コードでは成立しない**。
危険なのは削除ではなく、`output/` で始まり `**` を含まない規則を
`.git/info/exclude` か global gitignore へ**追加**した場合である。
**レンズ B の所見は型としては real、記述された深刻度は refuted。**

なお `core.excludesFile` が未設定でも git 自身は `~/.config/git/ignore` を尊重するため、
この helper は git の実 ignore 集合を過小に見積もる。これは別の忠実度の穴であり本 wave の scope 外。

## real / refuted の裁定

### 採用する must-fix

| # | 出所 | 裁定 | 対応 |
|---|---|---|---|
| 1 | A-1 NFKC | **real** (M1/M2 で親が検算) | prefilter を NFKC 正規化 source に対して行う。bounded fixture に NFKC 正例を必ず入れる |
| 2 | A-3 `Path.exists()` が ENOTDIR/ELOOP も False | **real** | guard は「不在だけ」を skip する形にし、非 directory component・symlink loop は隠さず従来どおり失敗させる |
| 3 | A-3 B-10 2 file の guard 未設計 | **real** | 22 file の requirements、guard 挿入 node、missing/full 対照を具体化する。自走 `_run()` が `pytest.skip.Exception` (BaseException 系) を捕まえない点も直す |
| 4 | A-4 / B-4 全走査 gate は D335 違反 | **real** (両レンズ独立、親も 0.610 秒 / O(file 数) と実測) | **登録簿と 2 本のメタ gate を作らない** |
| 5 | A-5 「2.7 秒は取り残る量」 | **real** | 成果物には「旧見積り 2.7 秒を反証。別測定で saved 0.629 秒 / residual 2.686 秒。数値の一致は同一量を意味しない」と書く |
| 6 | B-1 23.4 pp 試算 | **real** | プランの `27.4% × 85.4%` 試算を成果物から削除する |
| 7 | B-5 D312 三部形式 | **real** | 成果物を「何から何へ / 残る律速 / 次に何を削るか」で固定する |

### scope 外へ出す real 所見 (裁定パッケージでユーザーへ返す)

| # | 内容 | 理由 |
|---|---|---|
| 8 | 全数走査 gate の新設 | D335 の明示例外が要る。人間裁定 |
| 9 | `output_snapshot_ignores.py` の動的 git ignore 依存 | M5 のとおり現行寄与 0。型は real なので次の一手として起票 |
| 10 | 最長単体 node の分割 | 反復間比較を壊さずに並列化できるかの生死確認 (`DW-G01`) から。本 wave の編集面外 |
| 11 | 3 module の被覆穴 | `p2_5` 等が test から一度も名指しされていない。別変更単位 |
| 12 | prefilter 後も傾きは残る (約 1,280 file で元に戻る) | 係数を下げるだけで構造は残る。記録し次の一手へ |

### refuted

- **親 brief `(P3)`「字句 marker は AST 発見の必要条件」** — M1 で破れた。NFKC 版へ置き換える。
- **親 brief `(P2)`「`DW-G03` の独立 2 例は満たす」** — レンズ B が git 履歴で
  dev-wave-jobs 系 2 file は同一作者・同日 (`56ae5e848` / `f24550a01`)、
  B-10 系 2 file は**同一 commit** (`637dafa17`) と示した。
  **「異なる producer/consumer で独立に 2 件」は成立しない。** よって `DW-G03` の
  「単発事故は局所修復か一回限りの migration を既定とする」に従い、**族の制度化を行わない。**
  これが must-fix 4 と同じ結論へ独立に到達している。
- alias import / `getattr` / 文字列結合 / comment 内 marker — いずれも現行 AST 述語でも
  発見されないか安全側の false positive。prefilter 固有の挙動差ではない。
- 正常な完全 input set では assertion の減少は 0 件。
- guard 正例は実体を通る設計になっている。
- 指定された既存 literal (`~/t956-repo/...`, `/home/tester/...`, `/home/u/x`, `/home/role`) の
  inert 判定は現物と一致する。
- レンズ B の「`.git/info/exclude` 消失で受入が落ちる」深刻度 — M5 で refuted。

## plan v2 (実装子へ渡す確定形)

### 単位 A — `orchestrator/tests/test_p3_exploration_namespace.py` のみ

1. `_CAMPAIGN_ROOT` (`:51`) の直後に marker 定数を置く。marker は
   `exploration_campaign_layout` のみ (`run_campaign` / `CampaignLayout` は単独では必要条件でない)。
2. `_discover_campaign_drivers` (`:131-144`) を
   `read_text` → **`unicodedata.normalize("NFKC", text)` に対する marker 判定** → `ast.parse` →
   既存 `_is_campaign_root_creator` の順にする。`campaign_root`、`import_modules`、返却 tuple、
   sort 順は変えない。比較用に keyword-only `use_lexical_prefilter: bool = True` を足す。
3. 発見名の 7 件 literal pin テストを足す。
4. bounded fixture (固定本数、`tmp_path`) で prefilter 有無の発見集合が一致することを、
   **production の `_discover_campaign_drivers` そのものを両設定で呼んで**確かめる。
   fixture には **NFKC 正例 (全角 `ｅ` 版) を必ず含める。** 生 source prefilter なら落ちるが
   NFKC prefilter なら拾う、という差を直接突く。
5. **実 repo を prefilter 有無で二重走査する既定テストは作らない** (D335)。
6. `_DRIVER_CONTRACTS` と `_driver_contract` は変更しない。

### 単位 B — 既知 4 file の module-local 内容 guard だけ

対象と現況:

| file | 束縛先 | 現況 |
|---|---|---|
| `test_t189_oracle_wiring_slice.py` | `/work/1/SFC/tanab/dev-wave-jobs` | 根 directory の有無だけ |
| `test_t1434_t1222_science_slice.py` | 同上 | guard 無し |
| `test_b10_extended_figure_provenance.py` | `/work/1/SFC/tanab/b10-backoff-grid-runs5` | guard 無し |
| `test_plot_b10_extended_backoff.py` | 同上 | guard 無し |

`test_codex_reasoning_ab.py` は既に正しいので**触らない**。これが合わせる先例である。

1. 各 module に `_missing_pinned_*` / `_require_pinned_*` を置き、**その module が実際に読む
   file 集合**を checked-in artifact から導出する (t189 は 4 file、t1434 は 21 file、
   B-10 は 22 file)。
2. **不在 (ENOENT) だけを skip とする。** `Path.exists()` は ENOTDIR / ELOOP でも False を返すので
   使わない。非 directory component・symlink loop・内容不正・SHA 不一致は guard で隠さず、
   従来の verifier に失敗させる。
3. reader-A output だけを読む node は、その 1 file だけを guard する。無関係な file の不在で
   skip させない。
4. `test_physical_rejects_symlink_component` は guard しない (外部内容の実在が前提でない負例)。
5. skip 理由には欠けた relative path を列挙し、「完全な入力集合なら全 assertion が走る」ことを
   明記する。**既存テストの期待値は一切変えない。**
6. 各 module に「root は在るが要求 file が 1 件欠ける → skip する」正例と、
   「完全な集合なら skip しない」対照を置く。root-only guard の偽実装を直接殺す。
7. B-10 2 file の自走 `_run()` が `Exception` しか捕まえない点を直し、
   `pytest.skip.Exception` で非 0 終了しないようにする。
8. **登録簿 JSON も、全 test source を走査するメタ gate も作らない。**

## 変異事前登録 (`DW-M01`)

段 2 の 9 点から、scope 縮小で消えた registry 系 3 点を除き、NFKC 分 1 点を足す。

| # | 変異 | 期待赤 node (exact) |
|---|---|---|
| 1 | marker を `run_campaign` へ変える | `test_campaign_driver_discovery_names_are_pinned`、bounded fixture 等価性、`test_driver_contract_registry_is_exact` |
| 2 | **NFKC 正規化を外し生 source で判定する** | bounded fixture 等価性 (NFKC 正例のみ) |
| 3 | 7 件 pin の `p3_kickoff` を 1 文字変える | `test_campaign_driver_discovery_names_are_pinned` のみ |
| 4 | `_driver_contract` の `contracts[name]` を `.get(name)` へ | 既存 `test_missing_driver_contract_is_hard_failure` のみ |
| 5 | t189 の欠落判定を `not jobs_root.is_dir()` へ | t189 の missing-file guard テストのみ |
| 6 | t1434 の欠落判定を同上 | t1434 の missing-file guard テストのみ |
| 7 | B-10 の欠落判定を同上 | B-10 の missing-file guard テストのみ |
| 8 | t189 `_require_*` の `pytest.skip(...)` を `return` へ | t189 の missing-file guard テストのみ |
| 9 | requirements factory から 1 file を除く | 各 module の requirements exact テスト (期待値を同じ factory から導出しないこと) |

## 分割

編集面が素集合の 2 単位。registry が消えたので単位 B 内の producer/consumer 契約も消え、
分割してよいが、4 file とも同一 pattern のため 1 子に持たせる。

- 単位 A: `test_p3_exploration_namespace.py`
- 単位 B: 上表の 4 file
