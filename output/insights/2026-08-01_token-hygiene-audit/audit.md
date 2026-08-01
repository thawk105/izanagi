# トークン衛生監査 — claude 子 / codex 子の model・reasoning 経済 (2026-08-01)

発端: ユーザー依頼「claude, codex ともにエージェント呼び出しの際に不必要に高位モデルを呼んだり
不必要に深い推論でトークンの無駄遣いが起きていないか」。

前回の同型監査は `output/insights/2026-07-19_agent-model-economy-audit.md` (13 日前)。
本監査はその**差分と追跡**に重心を置き、以後に追加された面と、承認済み是正の適用状況を実測した。
運用経済の記録であり、CC 合成実験の結論ではない。

- 実測環境: worktree `.claude/worktrees/dev-wave-token-hygiene` (branch
  `worktree-dev-wave-token-hygiene`、base = local main)、host `pegasus02` (Pegasus login)、
  `claude 2.1.220` / `codex-cli 0.146.0`
- 独立検証: codex `gpt-5.6-sol` / `reasoning=high` / `sandbox=read-only` 1 本
  (事実性・過大表現・網羅性の 3 レンズ)。**判定 NO-GO、BLOCKER 1 / HIGH 7**。
  親の草案 4 件が反証され、全件を一次資料で照合して採用した。逐語は
  `verify-output.md`
- **max を選ばなかったのは本監査の主張との一貫性**であり、この選択自体を観測対象として記録する。
  結果として `high` 1 本で BLOCKER 1 + HIGH 7 を得た (n=1 の逸話であり、`max` との比較ではない)

## 1. 実測した child 起動面の全量 (19 面)

### 1.1 Claude 子

| # | 面 | model | effort | 検証機構 | 稼働 |
|---|---|---|---|---|---|
| C1 | `.claude/agents/*.md` 13 role | opus 10 / sonnet 3 | high 10 / medium 3 | static: `spec.py:45,297` が 5 key 必須 + `check_codex_agents` 悉皆 gate / launch-time: `guard_agent.py:78` は **model の存在だけ** | 合成ループ休止中 |
| C2 | ad-hoc `Agent` tool | 呼出し側が明示 | **per-call の指定手段なし** | `hooks/guard_agent.py` が model 未指定を拒否 (hook 自身は `:116` で fail-open) | live |
| C3 | Workflow `agent()` | `opts.model` | `opts.effort` | `tools/check_workflow_models.py` (standalone advisory、hook 未配線。model 欠落 NG / effort 欠落 WARN) | live |
| C4 | `s6_proposal_rounds.call_headless` (`:327`) | 既定 `opus` / canary `haiku` | `high` ハードコード | 凍結計測器 | 凍結 |
| C5 | `s8b_prediction_runner` (`:1102`) | selector-8b frontmatter = opus | `--effort high` 固定 | frontmatter を `:1019-1022` で assert、`modelUsage` の opus slug を `:1189` で検査 | 凍結 |
| C6 | `tools/dev_waves` supervisor | `--model` 必須 + 運用者供給 `allowed_models` に照合 | `--effort` 必須・**値域検査なし** | 形のみ | **fake-only / real 未開放 (D74)** |
| C7 | 親セッション既定 `~/.claude/settings.json` | `opus[1m]` | **`xhigh`** | なし (repo 外) | 常時 |

`~/.claude/agents/` は空、repo の `.claude/settings.local.json` に model / effortLevel の
上書きなし。よって C7 がセッション既定の唯一の供給源である。

### 1.2 codex 子

| # | 面 | model | reasoning | 検証機構 | 稼働 |
|---|---|---|---|---|---|
| X1 | `DW-S02` 段 2 プラン起草 | `gpt-5.6-sol` | **`max`** | 規律のみ | live |
| X2 | `DW-S03` 段 3 敵対相談 | `gpt-5.6-sol` | `max` | 規律のみ | live |
| X3 | `DW-S05-A` 段 5 実装 | `gpt-5.6-sol` | `high` | 規律のみ | live |
| X4 | `DW-S06-A` 段 6 敵対レビュー | `gpt-5.6-sol` | **未指定** | なし | live |
| X5 | `DW-S06-B` 段 6 fix | `gpt-5.6-sol` (`operations.md:8`) | `high` (段 5 契約の継承) | 規律のみ | live |
| X6 | `DW-S06-C` 焦点再レビュー | `gpt-5.6-sol` | **未指定** | なし | live |
| X7 | `tools/codex_worker_launch.py` (`:2474-2475`) | `--model` 既定 `gpt-5.6-sol` | `--reasoning` 必須・**値域検査なし** | `--sandbox` にだけ `choices`。ただし rollout 記録値と要求値の一致は `:772` で検査 | live |
| X8 | **generic Codex `spawn_agent` 子** | **指定手段なし (親から継承)** | **指定手段なし** | なし | live |
| X9 | `tools/codex_reasoning_ab.py` (`:48,1806-1812`) | `MODEL = "gpt-5.6-sol"` 固定 | `{arm}`、`collect-run` に `max\|high` の allowlist (`:5223`) | allowlist あり | T-181 専用・標準未配線 |
| X10 | `codex_roles/launcher.py` (`:353`) | manifest 固定 | manifest 固定 | **値域 allowlist** `{low,medium,high,xhigh}` | runtime blocked |
| X11 | `codex_roles/spec.py` (`:608-616`) | `{sol, terra}` | `{medium, high}`、opus role は sol/high、verifier は terra/medium (D61) | 実装済み | runtime blocked |
| X12 | `.codex/role-adapters/*.json` 13 件 | manifest から byte 導出 | 同左 | spec の期待バイト一致 | runtime blocked |
| X13 | `.agents/skills/*` (codex 側 skill 入口) | ピンなし | ピンなし | なし | live |

X12 の 13 adapter は manifest の codex 列と**全件一致**しており drift はない (親が独立照合)。

## 2. probe の一次資料

逐語は `probes/cli-effort-failopen.md`。

| probe | 実測 | 射程 |
|---|---|---|
| `claude -p --effort bogus` | `Warning: Unknown --effort value 'bogus' — ignoring it and using the default effort. Valid values: low, medium, high, xhigh, max.` + 本文出力 + **rc=0** | 単発、haiku |
| `claude -p --model not-a-real-model` | エラー + **rc=1** | 単発 |
| `--output-format json` の receipt | top-level に **effort field なし**。`modelUsage` は model / token / cost のみ | — |
| `--output-format stream-json` の `init` event | keys に **effort なし** (`model` はある) | — |
| `claude --help` | `--effort <level> Effort level for the current session (low, medium, high, xhigh, max)` — **既定値の記載なし** | — |
| effort 3 arm の出力トークン比較 (haiku、low / xhigh / bogus、各 n=1) | 326 / 307 / 464 tokens — **arm を分離できず** | **陰性。fallback 先の特定に使えない** |

したがって「不正 effort の fallback 先がセッション設定値 (`xhigh`) か CLI 内蔵既定か」は
**未確認**である。CLI は既定値を文書化せず、実効値をどの出力面にも露出しない。

## 3. `max` と `high` の資源差 (T-181 台帳の再集計)

`output/insights/2026-07-30_t181-reasoning-ab/aggregate-uncertified.json` の
`resource_ledger` 10 run を親が arm 別に再集計した。

| 指標 | high (n=5) | max (n=5) | 倍率 |
|---|---|---|---|
| **推論出力トークン** | 55,184 | 107,932 | **1.96×** |
| 出力トークン計 | 99,774 | 151,762 | 1.52× |
| 入力トークン計 | 20,381,622 | 24,562,854 | 1.21× |
| model 呼び出し数 | 211 | 243 | 1.15× |
| wall 中央値 | 587,285 ms | 915,034 ms | 1.56× |

**射程 (超えて引用してはならない)**: `experiment_complete=false` (replay 未認証)。
run 構成は POS n=6 / NEG n=4 の計 10 (arm 別 5/5)。測ったのは**段 6 focused review の
名指し R-1** であって段 2 起草ではない。非盲検、限定 prompt / snapshot / 期間。
名指し正例の検出は両 arm 3/3 で**劣化は観測されなかった**が、非劣性の証明ではない。
**この比率を段 2 や他段へ外挿してはならない。**

## 4. 所見と裁定

### 4.1 real — ユーザー手番

- **A1 親既定 `effortLevel` が承認値から戻っている。**
  2026-07-19 の承認は `model: "opus"` かつ `effortLevel: "high"`
  (`docs/archive/worklog-phase3-0719.md:83,97`)。当時の追跡台帳は
  **effort を `done`・現物 `effortLevel=high`** と記録し、**model は `unresolved`・現物は fable のまま**
  と記録している (`output/insights/2026-07-19_backlog-triage.md` X6-106/X6-107)。
  現在値は `model: "opus[1m]"` / `effortLevel: "xhigh"`。
  すなわち **effort は一度適用された後に `xhigh` へ戻り、model は後から適用された**。
  戻す裁定の記録は本監査では見つからなかった。
  2026-07-06 協議決着「メインループは日常 `high` / 監査・設計の山場のみ `xhigh`」
  (`docs/archive/worklog-phase3-0702-0713.md:601`) とも整合しない。
  **射程**: これは設定ファイルの文字列であり、各 live session の実効値でも served effort でもない。
  `opus[1m]` は承認文字列 `opus` と exact 一致ではない。
  **AI は repo 外ファイルを編集しないため、確認と変更はユーザー手番。**
  (親の当初草案は「model 適用済み / effort 未適用」と**逆に**書いていた。検証子 R4 が反証し、
  親が X6-106/107 で照合して訂正した。)

### 4.2 real — 構造的 (回避策しかない)

- **A2 per-call で effort を指定できない子が 2 系統ある。**
  (i) Claude の ad-hoc `Agent` tool: 本セッション harness の呼び出し schema は
  `description / isolation / model / prompt / subagent_type` だけで **`effort` を持たない**。
  `hooks/guard_agent.py:104` も同じ前提を書く。
  (ii) codex の generic `spawn_agent` 子: D54 の再監査が
  「`spawn_agent` schema には custom profile を明示選択する field がなく、`task_name=auditor` 等は
  generic child の名前を変えるだけ」「省略した surface は親から継承される」と確定している
  (`docs/decisions.md:2053-2062`)。**model も reasoning も呼び出し側から選べない。**
  → 緩和は 3 つだけ: (a) model/effort をピンした named role を使う、
  (b) Workflow `agent()` の `opts.model` / `opts.effort` を使う、(c) セッション既定を下げる。
  A1 が効くのはこの (c) の経路である。
- **A3 Claude CLI の `--effort` は fail-open で、実効値の attest 経路がない。**
  不正値は warning + **rc=0** で既定へ落ちる。対して `--model` は **rc=1** で fail-closed。
  effort は JSON result にも stream-json の `init` にも現れず、`--help` に既定値の記載もない。
  **これは `docs/failures.md` F56 (codex 側で `model_reasoning_effort="ultra"` が rc=0 で通る) の
  Claude 側同型である。** fallback 先の実体は §2 のとおり**未確認**。

### 4.3 real — 潜在 (現在のトークン消費はゼロ)

- **A4 `tools/dev_waves` の model / effort 検証が非対称。**
  model は運用者供給の `allowed_models` に literal 照合される (`daemon.py:222`) が、
  effort は非空 ASCII (`daemon.py:226`) と `_EFFORT_RE` の形 (`schema.py:830`) だけ。
  さらに `daemon.py:1685` は要求値 effort を profile 記録へ書くのに、子 receipt の
  `CLAUDE_RESULT_ALLOWED_FIELDS` (`receipt.py:22`) に effort が無く照合できない。
  **ただし D74 により本層は fake child 限定で real `claude -p` の起動経路が存在しない**
  (`worker.py:1` = "Bounded, fake-only child process worker"、`docs/decisions.md:2955,2959,2991`)。
  よって**現在のトークン消費への因果はない**。意味を持つのは D74 (6) が未消化として挙げる
  「real 開放前のユーザー裁定 (real child の settings・hook 必須政策)」への入力としてである。
  (親の当初草案は本項を live な浪費源として書いていた。検証子 R3 が反証し、親が D74 で照合して訂正した。)

### 4.4 real — 契約の穴

- **A5 段 6 の 2 段が reasoning 未指定で、歴史運用が `max` と `high` に割れている。**
  `DW-S06-A` (敵対レビュー) と `DW-S06-C` (焦点再レビュー) はいずれも reasoning を書いていない
  (`docs/dev-wave/workers.md:45-64`)。実績は両方に散る —
  `max` 側 = `docs/decisions.md:2645,2648`、`2026-07-26_t106-t107-parser-authoritative.md:149`、
  `2026-07-26_t098-selector-lp-reject.md:146` ほか。
  `high` 側 = `2026-07-27_t128-t080-fixture-scan-inflation.md:91`、
  `2026-07-28_t157-resolve-duplicate-identity.md:37` ほか。
  **これがユーザーの懸念に最も直接に当たる実測である** — 契約が沈黙している段で、
  記録上およそ半々の割合で最深の `max` が選ばれている。
  (親の当初草案は「実運用は一貫して high」と書いていた。親自身が待機中に反例を実測して訂正し、
  検証子 R10 も独立に反証した。)
- **A6 live な codex 起動経路に reasoning の値域検査がない。**
  `codex_worker_launch.py:2474-2475` は `--reasoning` を required にするだけで `choices` がない
  (`--sandbox` にはある)。ただし rollout の記録値が要求値と一致するかは `:772` で検査する。
  **値域 allowlist の参照実装は repo 内に既にある** — `launcher.py:353`
  (`{low,medium,high,xhigh}`) と `spec.py:608` (`{medium,high}`)。
  → [T-189] (択 (a) 裁定済み・実装待ち) の実装コストは低い。

### 4.5 policy 変更提案 (real finding ではない)

- **A7 段 2 プラン起草の `reasoning=max`。**
  これは doctrine 逸脱ではなく**現行の明示 policy** である (`docs/dev-wave/workers.md:5`、
  `docs/decisions.md:2645` が標準ループとして記録)。よって「過剰である」という親の当初判定は
  **格下げする** (検証子 R9)。
  提案の根拠は §3 の資源差 (推論トークン 1.96 倍) だが、**T-181 が測ったのは段 6 focused review
  であって段 2 ではなく、replay 未認証・非盲検・限定 prompt** である。外挿は禁じられている。
  → 実装せず、§5 の裁定パッケージへ。

### 4.6 refuted / 据置

- **A8 named role 13 件**: 既存方針に対する新たな mismatch を**静的に観測しなかった**。
  前回監査の refuted 群 (凍結実験契約、auditor のモデル階層方針例外、tool-less 1 shot) は今回も成立。
  ただしこれは政策判断の追認であって、頻度・品質の再計測ではない (検証子 R13)。
- **A9 codex adapter 13 件**: `runtime_activation.status = "blocked"` で live コスト 0
  (`.codex/agents/README.md`)。現行 spec は `{sol,terra}` × `{medium,high}`、verifier は
  terra/medium (D61)。**「D54 の sol/high 統一」という親の帰属は撤回する** — D54 初版の
  3 role active 裁定は同日再監査で supersede 済み (`docs/decisions.md:2055,2065`、検証子 R12)。
- **A10 過小方向 (難しい仕事に低位モデル)**: 13 named role の範囲では新規 mismatch を観測しなかった。
  `coder` = sonnet に対し `auditor` = opus で「監査側 ≥ 被監査側」の階層方針を満たす。
  X8 / X13 のように tier を選べない面があるため、「全 surface で過小なし」は導けない。

## 5. 裁定パッケージ (ユーザー判断が要るもの)

1. **親既定 `effortLevel`** — `xhigh` のままにするか、2026-07-19 承認値 `high` へ戻すか。
   戻す場合は `~/.claude/settings.json` の手動編集 (AI は repo 外を編集しない)。
   意図的に `xhigh` へ戻したのであれば、その裁定を記録すれば A1 は解消する。
2. **段 2 (`DW-S02`) の `reasoning`** — `max` 据置か `high` へ引き下げか。
   引き下げの根拠は段 6 で測った 1.96 倍の推論トークン差だが、**段 2 での測定はない**。
   選択肢: (a) 据置、(b) 引き下げ、(c) [T-181] の認証再走と段 2 への限定 A/B を先に行う。
3. **段 6 (`DW-S06-A` / `DW-S06-C`) の reasoning を契約へ明記するか、どの値にするか。**
   現状は未指定で運用が max / high に割れている。予算 headroom は
   `docs/dev-wave/workers.md` に 563 bytes ある。
4. **A4 を D74 (6) の「real 開放前ユーザー裁定」項目へ併合するか** — real child の
   effort 値域検査と receipt での照合を、real 開放の前提条件に含めるかどうか。

## 6. 監査自体の品質注記 (正直に)

- 親の草案は 4 件で誤っていた: A1 の適用方向 (逆)、A4 の live 誤分類、A5 の「一貫して high」、
  A9 の D54 帰属。うち 1 件 (A5) は親が待機中に自力で訂正し、3 件は codex 検証子が検出した。
  **前回監査と同じく、製品をまたぐ独立検証だけが捕まえた誤りがある。**
- 親は最初、`--effort bogus` の rc=0 を逐語保存せずに主張していた (検証子 R7)。
  指摘を受けて `probes/cli-effort-failopen.md` に一次資料を保存し直した。
- fallback effort の実体は特定できていない。3 arm probe (haiku, n=1/arm) は**陰性**で、
  この陰性結果も台帳に残す (成功した測定だけを書かない)。
- 本監査は静的照合と軽量 probe だけで、**各 role の呼び出し頻度・品質の再計測はしていない**。
  「変更不要」は前回の政策判断の追認であって、新たな費用対効果の実証ではない。
