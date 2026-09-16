---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2647-b10-tail-downstream
seq: 1
title: [T-2647] B-10 静的 backoff 右 tail の集団判定を両論文系列の入口へ渡した (docs のみ、branch worktree-dev-wave-t2647-b10-tail-downstream、実装面ゼロ・変異 matrix 免除・受入 child-green)
---

## 本文

- **依頼が挙げた carry の前提は既に stale だった。** 「本走を投入する」は 2026-09-15 の完走で
  済んでおり、依頼本文自身がそれを織り込んでいた。本 wave は投入も測定もしていない。
- **段 2 plan 1 本 + 段 3 敵対 2 レンズ (sol = 過大主張、luna = 接続漏れ)。所見は real 8 件・
  refuted 1 件。2 レンズは割れず補完的だった。** 最重要は luna の「図表・材料への接続という完了
  条件を入口注記へ縮めている」で、cohort を明示した判定表を insight へ置き両入口から指す形へ直した。
  次に重いのは sol の「事前登録 §3 が要求する throughput の費用併記が落ちている」。
  逐語と裁定は `output/insights/2026-09-16/t2647-b10-tail-downstream.md` §6 に凍結した。
- **refuted 1 件。** 「worklog fragment の `title:` が `[` 始まりで YAML として不正」という所見は、
  レンズが `yaml.safe_load` という**実際の consumer でない道具**で検査したものだった。
  `tools/spool_fold.py` の `_parse_frontmatter` は正規表現 `([a-z]+): ([^\n]+)` で読む。
  引用符を付けると fold が生成する worklog 見出しへ `"` が混入するので採らなかった。
- **子が親 brief の誤りを 3 つ訂正させた。** (1)「既測は 1000 マイクロ秒まで」は探索走
  (2000 / 4000 / 9999 マイクロ秒) を落としていた。(2) 図を作らない根拠に挙げた「両系列の最新版が
  図の新規作成・昇格をしない」は backoff 版だけの、しかもその版自身についての記述であり、
  後続 wave を制限しない (結論は維持し根拠を差し替えた)。(3) stale 対象を §8 の 2 文に縮めていたが、
  本体 2026-09-14 版では 5 箇所である。
- **数値は下流文書の孫引きにせず、原成果物を直読して作った。** 親が `jq` と `awk` で
  group report の json / dat を読み、18 区間すべて `declining`・局所平坦 0・
  `saturation_location` は 3 workload とも `null` を確認した。throughput の 5 反復平均は
  段 3 のレンズが独立に計算した 6 値と完全一致した。
- **素材:** 09-15 cohort の集団 verdict は `not-observed-in-any-workload`。言い方は事前登録 §4.5 の
  固定表現「この事前登録の述語では、表現可能域である 9999 マイクロ秒までに飽和を観測しなかった」に
  限る。`performance_certified: false` は動いておらず、当時の実行全体の独立監査も未実施である。
  2026-09-16 の再導出で 3 成果物が byte 一致したことは、その監査の代わりにならない。
- **2 本目 cohort の地位 (D2050) には触れていない。[T-2647] も B-10 も閉じない。**
  09-15 cohort を描いた図は存在せず、作るなら置き場所の系列契約と新図種の完成要件を先に解く必要が
  ある (insight §4)。
- **受入 attempt を 1 本空費した。** `tools/dev_wave_submodule_init.py` が
  `OK: submodules initialized` / rc=0 を返し開始 gate も通ったのに、3 段目の
  `external/ccbench/third_party/shirakami/third_party/googletest` が未初期化のまま残り、
  attempt 1 が `stage=preflight-submodule-ready rc=2` で終端した。
  `git submodule update --init --recursive` で解消した。
- **検査:** `python3 tools/check_docs.py` は違反なし。`python3 tools/spool_fold.py --dry-run` は
  `status=planned`。`python3 tools/check_ai_provenance.py` の full 監査は rc=0 (計算ノードへ
  dispatch、request 1199.nqsv)。受入全走 attempt 2 は `child-green` で
  24,070 passed / 68 skipped、`red_nodeids` と `flake_nodeids` はいずれも空、
  tested main `d97c423bd` / tested tip `3d1904fd4`。

## 次の一手差分

### carry

- [T-2647]
