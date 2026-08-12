# [T-886] rollout 探索の SHA pin 付き label 限定 fast path

wave `dev-wave-t886-rollout-fastpath` / branch `worktree-dev-wave-t886-rollout-fastpath`。
ユーザー裁定 (2026-08-12 第 2 束) **T-886 = (a)** の実装。

## 何をしたか

`tools/codex_reasoning_ab.py` の `_find_rollout` に keyword-only `pinned_label` を足し、
label が `ROLLOUT_SHA256` にあり `SESSION_IDS` の対応と一致するときだけ、
名前 glob → 内容照合 → SHA 照合の 3 段で短絡する。pin 無しの呼出元は全走査のまま。

## 実測 (`beforeafter.json`、順序 counterbalance 2 走)

corpus manifest = **2,973 file / 2.62GB** (測定時刻は同 JSON)。

| label | before (全走査) | after (fast path) | 返り path 一致 | 速度比 |
|---|---|---|---|---|
| POS | 4.144s | 0.0191s | ✅ | 217x |
| NEG | 4.169s | 0.0224s | ✅ | 186x |
| fix2 | 4.147s | 0.0211s | ✅ | 197x |
| author | 4.141s | 0.0202s | ✅ | 205x |
| fix1 | 4.214s | 0.0206s | ✅ | 205x |

**fixture 1 インスタンス分 (5 呼出) = 20.82s → 0.10s。**
逆順走でも before は 4.14〜4.21s で変わらず、cache 温度差では説明できない。

**これは fixture 1 回分であって受入全走の wall ではない。** `benchmark_snapshots` は
`scope="module"` だが xdist worker 間では共有されないため、全走の改善量は worker 数に依存する。

## 効果の機序 (2 度訂正した)

裁定パッケージは効果を「比例走査の除去」と書き、親は段 4 でそれを
「warm metadata walk の係数削減」と訂正した。**どちらも不正確である。**

narrow な `Path.rglob` も同じ tree を最後まで歩くので **walk の費用は before/after で同じ**。
消えているのは**無関係 rollout の open / stream / session_meta candidate parse** である。

- directory walk = 2,946 file で約 17ms、**約 5.5 µs/file** (`glob_scaling.json`、warm cache)
- 全走査の内容 scan = 約 1,500 µs/file
- よって **残る比例項は walk (5.5 µs/file)**。10 倍に増えても glob 側は約 0.17s。
- **cold cache 倍率は未測定・効果不明。** 敵対レンズ 2 本が独立に「提示資料から算出不能」と判定した。

## 等価性と受理集合

- pin 済み 5 label すべてで返り path が全走査と一致 (`beforeafter.json`)。
- 全 corpus 走査 (`divergence.json`、2,945 file) で **form A (名前の id を中身が宣言しない) = 0 件**。
  ただしこれは**当該時点の観測であって不変条件ではない** (F141 型)。同一性の錨は SHA pin である。
- **認可された受理集合の変化は次の 2 方向だけ:**
  1. 非候補 file に同 id を宣言する重複がある入力 — 現行は `RC_SESSION` で拒否、fast path は受理
  2. 非候補 file の病的 bytes による未捕捉例外を観測しない

  **2 は親 brief が当初「重複だけ」と書いて漏らしていた。** 段 3 の敵対レンズ 2 本が独立に反例を
  構成し、うち 1 本が「名前 glob を採る以上は回避不能」と論証した。先行 wave の Q3 で
  ユーザーが同方向を「認める」で確定済みであることを根拠に、親が認可範囲内と裁定した。
- **候補自身の一過性例外の再試行は認可しない。** 段 5 実装は fast attempt 全体を
  `except Exception` で包んでおり、候補自身の内容照合例外まで飲んで読み直していた。
  段 6 レビューが検出し、例外の扱いを 3 区画へ分けた ({{D:fastpath-three-exception-regions}})。

## 副産物として見つけた比例走査 (本 wave では触らない)

- `_find_rollout` の **`thread_id` 経路 (pin 無し)** は、subagent を産んだ親 session を
  `RC_SESSION` で拒否する。述語が `id` と `session_id` の**いずれか**一致なので、
  親 id で引くと親本体 + 全子 rollout がヒットするため。**実 corpus に該当 id が 2 件実在**
  (`019f690c` → 2 file、`019fd52d` → 4 file、いずれも subagent / fork。`divergence.json`)。
  裁定が pin 無し経路の全走査維持を明示しているので触っていない。
- `_scan_session_rows` は `_json_lines` で全 corpus の**全行**を parse する。receipt 検証経路に
  あり、テストでは実 corpus を渡していないため本 wave の律速ではない。

## 検証

- 焦点走 (計算ノード): 実装後 **190 passed / 0 failed**、fix 後 **193 passed / 0 failed**
- 変異 matrix: `mutation-round2.json` = **16/16 KILLED**、生存ゼロ、baseline 54 passed / rc=0
  - `mutation-round1.json` は **probe** (DW-M08)。10 KILLED / 6 MISMATCH で
    **missing はゼロ** — 期待集合が完全でなかっただけで、検出力の不足ではない。
    観測から完全集合を再導出して round 2 を本走とした。
- 段 3・段 6 の敵対レンズ計 4 本の逐語は `verbatim/`。親の裁定 2 通も同ディレクトリ。

## 親が撤回した主張 (記録として残す)

段 4 で 5 件 (`verbatim/stage4-ruling.md` §0)、段 6 でさらに 1 件を撤回した。
機序の記述は上記「効果の機序」が最終形である。
