# [T-241] 計算ノードの LLM transport — 実測で前提が覆り、実装せず裁定へ戻した wave

2026-08-01 / branch `worktree-dev-wave-t241-abc-pilot` / dev-wave (実装差分なし)

## 一行

T-241 の「A/B/C live pilot を Pegasus 計算ノードで再開する」は、**numactl でも LLM 到達性でもなく、
D108 が定めた実行場所契約と `_site_admits_measurement` の Pegasus 拒否で塞がっている**。その途中で
「計算ノードは外部 network 不可」という記録済みの事実が**誤り**であることを実測し (proxy 経由で
Claude CLI は通る)、これが D108 決定 (1) の前提の一部を覆すため、親は独断で実装せずユーザー再裁定へ戻した。

## 読む順

| ファイル | 中身 |
|---|---|
| `s1-brief.md` | 段 1 brief。**過大表現 3 件を含む**。訂正は `s4-adjudication.md` の「親 brief の訂正」 |
| `s2-plan.md` | 段 2 codex プラン (read-only、`gpt-5.6-sol` / max)。凍結 `agent_provenance` の見落としを親 brief に対して指摘 |
| `s3-lens-a-isolation.md` | 段 3 敵対レンズ A (隔離契約・正しさ防壁)。逐語 |
| `s3-lens-b-tautology-scope.md` | 段 3 敵対レンズ B (受入の恒真性・consumer 取り残し・scope 欠落)。逐語 |
| `s4-adjudication.md` | 段 4 親裁定。real/refuted 一覧、実測表、**ユーザー裁定パッケージ (択一 3 件)** |
| `evidence/` | 生の実測 |

## evidence の索引

| ファイル | request / node | 何を示すか |
|---|---|---|
| `probe-876527.txt` | `876527` / bnode002 | DNS は不通、素の `claude -p` は rc=0 |
| `probe-876528.txt` | `876528` / bnode002 | 算術 nonce 正答 3 秒、proxy 変数 2 件の存在、`python3` が 3.9 |
| `probe-876529.txt` | `876529` / bnode002 | **決定実験**。full env=成功 / driver の allowlist=`ENOTIMP` 172 秒 / allowlist+proxy=成功 |
| `probe-876729.txt` | `876729` / bnode002 | toolchain 棚卸し。`g++-13` 不在、gflags/glog 不在 |
| `control-876813-*` | `876813` / **bnode145** | 8c driver 実走 (no-build)。rc=2、3 cell とも `planner-invalid` |

## 注意 (この記録を後から読む人へ)

- 支持されている事実は **lowercase `http_proxy` / `https_proxy` の 2 変数**に限る。大文字版と
  `no_proxy` の意味論は未測定である。
- 「https が proxy で通るなら FetchContent / git clone / pip も通る」へ読み替えてはならない。
  実測したのは Claude CLI 1 本だけである。
- `control-876813` は bnode145、probe 群は bnode002 で、別 allocation である。同一ノードでの
  before/after 対照ではない。
- 実装差分がないため、変異 matrix と受入全走はこの wave の対象外である。
