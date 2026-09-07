# 段 4 裁定 — [T-2198] A-2 / A-6 認証経路の測定 build をオフライン依存へ配線する

親 = claude-opus-5。段 2 プラン (s2-plan.md)、段 3 レンズ A (s3-lensA.md) / レンズ B (s3-lensB.md) を
real / refuted、採用 / 不採用、scope 内 / 外へ裁定し、プラン v2 と変異事前登録を確定する。
段 4 直前に local main を再確認し 12 commit を `--ff-only` で取り込んだ (cf4273f56 → 4b2b8f577)。
取り込んだ範囲に本 wave の編集面はない。

---

## 1. 所見の裁定

### レンズ A (閉じた文法の証明力)

| # | 所見 | 判定 | 採否 | scope |
|---|---|---|---|---|
| A1 | 旧文法と新文法の受理集合は包含関係でなく置換である | **real** | 認識として採用。実装変更なし | 内 |
| A2 | `len(argv) < 10` が新しい最短長 21 と不整合。短い tail は `IndexError` になりうる | **real** | **採用 (must-fix)** | 内 |
| A3 | loader の 6 条件だけでは prefix の意味を固定できない | **real** | **採用 (must-fix)** — A-6 側にも exact literal 検査を足す | 内 |
| A4 | `protocol_sha256` は Python 述語と `_QSUB_ENV_KEYS` を束縛しない | **real** | 事実の記載だけ採用。**一般 gate の新設は不採用** | 記載は内 / gate は外 |
| A5 | golden 張り直しに F36 型の自己参照はない | **refuted** | — | — |
| A6 | 「live pin は 5 箇所だけ」の一般化は偽。grammar 全体の exact dict pin がある | **real** | **採用**。親 brief の誤りとして段 7 で訂正 | 内 |
| A7 | 変異候補に帰属不成立・同値 mutant がある | **real** | **採用**。事前登録を §3 で絞り直す | 内 |
| A8 | 1 key 案が 3 key 案より証明力が強いとは言えない | **refuted (「強い」の主張が)** | 1 key 案を維持。根拠を修正 | 内 |

**A1 の裁定理由。** D1693 の「受理集合を緩めない」は、集合の包含ではなく**閉包の維持**を指す。
新しい期待値は旧期待値の上位集合ではなく別の言語であり、それは裁定文が「期待値を**厳密に**書き直す」と
命じたことの当然の帰結である。旧 protocol の結果が新 protocol で再受理されないことは、
D1693 が既に「過去の認証値は取り直さない」「hash が一致しなくなる旨を明記する」で処理している。
**規律 2 の違反ではない。**

**A4 の裁定理由。** 「同じ `protocol_sha256` のまま Python の述語を書き換えれば受理が動く」は真だが、
これは本 wave が作る欠陥ではなく、認証プロトコル同一性の設計上の**既存の射程**である。
`CLAUDE.md` 絶対規律 7 が明記するとおり、repo 内の挙動検査は gate と検査を同じ主体が変更できる限り
意図的な弱体化への完全な防壁ではなく、**この限界は主張せず明記する**。
本 wave の依頼は「本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」で
あり、`DW-G05` も同じ方向を命じる。**限界を成果物へ 1 段落書き、gate は作らない。**

### レンズ B (実行経路の実在性)

| # | 所見 | 判定 | 採否 | scope |
|---|---|---|---|---|
| B1 | 認証用 `<base>/<name>-src` の生成者が誰もいない | **real** | **採用 (must-fix)**。§2 で入力契約を変更 | 内 |
| B2 | S8b verifier の pin 出所と import | **refuted** | — (親も独立に実測して一致) | — |
| B3 | dependency receipt の観測時点 | **refuted** | プランどおり | — |
| B4 | 条件 gate の全 configure 被覆 | **refuted** | プランどおり 2 箇所で足りる | — |
| B5 | 新 qsub env key で旧 submission receipt が再受理されない | **real** | **採用**。注記へ 1 行足すだけ。実装変更なし | 内 |
| B6 | job-local copy の Git / verifier 機構 | **refuted** | — | — |
| B7 | 3 依存の実サイズ・`/scr` 容量・copy 所要 | **未確定** | **未確定のまま記録**。本 wave では測らない | — |
| B8 | 必須 CLI 引数の呼び手漏れ (`:4548`) | **real** | **採用 (must-fix)** | 内 |
| B9 | 実効層の scope 閉包 (operator 手順と D1693 注記先) | **real** | **一部採用**。§2 の解決で operator 手順は不要になる。注記先は確定する | 内 |

**B2 の裁定理由。** 親が独立に実測した (`s8b_floor_campaign.py:2281-2300` →
`silo_ladder_rung1.third_party_policy` → 共有 `tools/pegasus/policy.json`)。レンズ B と一致。
`fetch_third_party.py` も同じ policy を読むので、hydrate 元と verifier は同じ 3 pin を見る。

**B7 の裁定理由。** 本 wave は計算ノードへ投入しないので実測できない。ただし
**同じ機体で同型の copy を既に 2 driver が行っている** (`submit_floor.sh:490-511`、
`p3_s4_loop_pegasus.sh:323-355`) ので、前例のない新規 risk ではない。`DW-G02` に従い
1 cycle 後へ送り、成果物へ「未実測」と書く。推測値を採否の根拠にしない。

**B9 の裁定理由。** §2 の入力契約変更により、operator が渡すのは `fetch_third_party.py hydrate` が
**そのまま作る** `<root>/<name>` になる。operator 手順は変わらないので
`tools/pegasus/README.md` の改訂は不要になり、この所見は消える。D1693 の注記先だけ §2 で確定する。

---

## 2. プラン v2 (確定)

段 2 プランを基礎に、次の 6 点を変更する。それ以外はプランどおり。

### v2-1 (B1): 入力契約を hydrate の実出力へ合わせる

`--third-party-source-root` が受け取るのは **`fetch_third_party.py hydrate` が作る
`<root>/<name>` 配置**とする (`masstree` / `mimalloc` / `googletest`、末尾 `-src` なし)。
`<name>-src` への変換は **job body が job-local scratch で行う**。

```
third_party_root=$scratch/fetchcontent
mkdir "$third_party_root"
cp -a "$third_party_source/masstree"   "$third_party_root/masstree-src"
cp -a "$third_party_source/mimalloc"   "$third_party_root/mimalloc-src"
cp -a "$third_party_source/googletest" "$third_party_root/googletest-src"
```

そのうえで `run-workload --third-party-source-root "$third_party_root"` を渡す。
これは**同じ file の既存 `dependency_prefix` の扱いと同型**である
(`tools/pegasus/paper_story_a2_certification.sh:281-291` が
`cp -a "$dependency_source"/. "$dependency_prefix"/` を既に行う)。
`p3_s4_loop_pegasus.sh:323-355` も `<root>/<name>` → `<name>-src` の同じ変換を持つ。
**新しい producer も新しい operator 手順も要らない。**
build が使う実効綴りは引き続き `<base>/<name>-src` で一意である。

### v2-2 (A2): path token 数を slice の前に明示検査する

`_exact_trace0_configure_argv` で `tail` から位置切り出しをする前に、
`len(tail) >= len(path_prefixes)` を検査し、満たさなければ `CertificationError` を投げる。
冒頭の `len(argv) < 10` は `len(fixed) + len(path_prefixes) + len(ordered_define_tokens)` から
導いた値へ差し替える。**固定値 21 を literal で書かない** (define 個数は policy 由来である)。
短い argv が `IndexError` として collector へ抜ける経路を残さない。

### v2-3 (A3 / A6): A-6 policy にも grammar の exact literal 検査を足す

A-2 側の `test_policy_is_the_exact_literal_four_cell_protocol` (`:1690-1741`) は
grammar 全体を exact dict で固定する semantic pin である。**A-6 側 (`:1839-1855`) は現在
grammar literal を比較していない。** 4 prefix を含む grammar の exact literal 検査を A-6 にも足す。
これがないと、誤った literal と誤った golden hash を同時に書いた commit が緑で通る。

### v2-4 (B8): test caller の範囲を広げる

`run_workload` の直接呼び手は `test_paper_story_a2_certification.py` の
`:4082`、`:4103`、`:4280`、`:4427`、`:4548` の 5 箇所。プランは `:4438` までしか挙げておらず
`:4548` の source-role rejection test を漏らす。**必須引数の追加は 5 箇所すべてに波及する。**

### v2-5 (A4 / B5 / B7 / B9): 成果物へ書く注記を確定する

D1693 が命じる「過去の結果と現行 policy の `protocol_sha256` が一致しなくなる旨」は、
次の 3 箇所へ**追記**で書く (既存記述の書き換えはしない。絶対規律 7)。

1. 本 wave の insight `output/insights/2026-09-07_t2198-trace0-fetchcontent/README.md` (新規)
2. `output/insights/2026-08-24_paper-story-a2-certification/README.md` (末尾へ追記)
3. `output/insights/2026-09-02_paper-story-a6-certification/README.md` (末尾へ追記)

注記に含める 4 点:

- 旧結果は旧 policy hash / 旧 protocol hash に束縛されたまま残り、値は取り直さない。
- 現行 policy の `protocol_sha256` は旧結果のものと一致しない。
- **旧 submission receipt は現行の exact qsub env 契約でも再受理されない** (B5)。
  ただしこれは新しい破壊ではなく、protocol hash と job body hash の変化に既に含まれる。
- `protocol_sha256` が束縛するのは policy document であって、Python 側の述語や
  qsub env の exact 集合ではない (A4)。**この限界は主張せず明記する。**

`docs/paper-story/**` と `docs/paper-story/figures/**.provenance.json` は触らない (凍結された歴史記録)。

### v2-6 (A8): 1 key 案の根拠を修正する

`fetchcontent_path_argument_prefixes` (ordered 4 要素) を採る。根拠は
「3 key より証明力が強い」ではなく、**「同じ閉じた言語を、prefix と name の再合成という
非一意な経路を経ずに表す」**である。producer 定数との食い違いはどちらの案でも
最終の全 argv 一致が拾うので、そこに差はない。

---

## 3. 変異事前登録 (実装前に確定。`DW-M01` / `DW-M03` / `DW-M08`)

レンズ A の帰属分析に従い、**帰属が一意に絞れるものだけ**を登録する。
harness は `tools/mutation_harness.py`。baseline 緑を必須とする。

### 登録する変異 (期待 KILLED)

| ID | 変異位置 | 変異内容 | 期待 node (完全集合) |
|---|---|---|---|
| M1 | `paper_story_a2_certification.py` `_exact_trace0_configure_argv` | source prefix 検査を 1 本 (GOOGLETEST) 削除 | 新設 `test_trace0_fetchcontent_prefix_mutations_are_rejected` |
| M2 | 同上 | base と masstree の期待順を交換 | 新設 `test_trace0_fetchcontent_segment_matches_v2_command_order` |
| M3 | 同上 | 最終の `list(argv) != expected` を部分一致へ変える | 既存 `test_trace0_argv_closed_grammar_rejects_unconsumed_tokens[unknown-configure-token]` |
| M4 | 同上 | path token 数の下限検査 (v2-2) を削除 | 新設 `test_trace0_configure_argv_rejects_short_path_segment` |
| M5 | policy loader (`:418` 付近) | 末尾 `=` 検査を削除 | 新設 `test_policy_loader_rejects_each_malformed_fetchcontent_prefix_list` |
| M6 | policy loader | 長さ 4 の検査を削除 | 同上 |
| M7 | policy loader | 一意性検査を削除 | 同上 |
| M8 | `_condition_gate_family_context` prebuild | source dir を 1 本 (mimalloc) 落とす | 既存 `test_paper_condition_gate_is_p_strict_and_precedes_campaign` の exact kwargs 検査 |
| M9 | `_condition_gate_family_context` capture | `configure_args` から source dir を 1 本落とす | 新設 `test_condition_gate_uses_exact_offline_fetchcontent_argv` |
| M10 | 同上 | `configure_args` の順序を入れ替える | 同上 |
| M11 | `run_workload` | staged verifier 呼出しを削除 | 新設 `test_run_workload_verifies_staged_sources_before_condition_gate` |
| M12 | `run_workload` | receipt observer 呼出しを削除 | 新設 `test_official_run_observes_dependency_receipt_after_condition_prebuild` |
| M13 | `run_workload` | 5 値のうち `mimalloc_source_dir` を `run_campaign` へ渡さない | 新設 `test_official_run_forwards_exact_fetchcontent_five_tuple` |
| M14 | submission validator (`:1282` 付近) | 新 qsub env key を exact 集合から削除 | 新設 `test_submission_rejects_missing_or_changed_third_party_source_root` |
| M15 | `paper_story_a2_certification.sh` | `googletest` の copy 行を削除 | 新設 `test_job_body_stages_exact_three_src_suffixed_dependencies` (job contract) |
| M16 | `paper_story_a2_certification.sh` | copy 先の綴りを `<name>-src` から `<name>` へ変える | 同上 |

### 登録しないもの (理由を明記。`DW-M03` / `DW-M08`)

- **golden 4 値 (5 箇所) の書き換え** — 正当な policy 変更でも必ず赤になる冗長 gate であり、
  文法機構への帰属が成立しない。KILL に数えない。
- **`_TRACE0_CONFIGURE_ARGV_KEYS` からの新 key 削除** — loader が assertion 前に落ち、
  policy を読む多数の test が同時に赤になる。帰属不成立 (レンズ A の表)。
- **`-DFETCHCONTENT_FULLY_DISCONNECTED=ON` の受理** — 挿入位置によらず prefix 検査か
  最終全一致のどちらかが必ず拾うため、専用機構への帰属が成立しない。
  M3 の閉包 test で覆われる。
- **loader の nonempty 検査の削除** — 「str かつ末尾が `=`」から論理的に導かれる同値 mutant。
- **`inspect.getsource` の文字列存在検査だけに掛かる変異** — 機構を通らない。
  M8〜M13 はすべて runtime の kwargs / call 順序検査と対にする。

### 実装後に確認する義務 (`DW-M01` の単一理由性、F820)

各変異について「同じ入力を拒否する層が前後にも内側にも無い」ことを実装後に確認する。
確認できないものは登録から外し、実効 gate へ再照準する。SURVIVED は `DW-M04` に従い
mutated 内容の diff で注入実在を確認するまで equivalent と呼ばない。

---

## 4. 段 5 の分割

**実装単位は 1 本**とする。文法・配線・shell・test が同一の argv 契約を共有しており、
分けると契約の食い違いが実装中に発生する。Codex `role=author`、`reasoning=xhigh`、
`sandbox=workspace-write`。親は実装面を直接編集しない。

## 5. 段 6 以降

敵対レビュー 2 本 (レンズ = 受理集合の閉包 / 実行経路と test の帰属)。
変異 matrix と受入全走は免除しない。受入投入は
`tools/dev_wave_wait.py acceptance --lease-optional` を使う。
