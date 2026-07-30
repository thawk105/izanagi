# [T-182] model routing 限定 shadow pilot — 逐語・receipt (凍結、2026-07-29)

親の裁定要約は `docs/worklog.md` 2026-07-30 (68)。分析の正本は
`output/insights/2026-07-29_t182-model-routing-shadow-pilot.md`。
**本 wave に実装差分はない** (段 4 で「実装しない」と裁定し `4→7→8→9` を辿った)。

| ファイル | 役 | sha256 (凍結時) |
|---|---|---|
| `s1-brief.md` | 段 1 brief (親) | `aaa98d8086608e3d57d4cb9d20adefeb072a8a6d0e688e218fbba7e5466d9def` |
| `s2-plan.md` | 段 2 プラン起草 (codex) | `6b698cc5f28754d05121a849c9871340bfcc44cce35b3bd481b5a5da9e8b42a7` |
| `s3-consult-a.md` | 段 3 敵対相談 A (実験妥当性レンズ) | `98f2f6dae1ec3cc7988b2c569240fb5eb06facb67d191b2c8fe55f859825dffa` |
| `s3-consult-b.md` | 段 3 敵対相談 B (gate 実効性レンズ、**authoritative**) | `c0e1077400248594d86a91c25a1ae3f248e0f6caab7c6898f6b28ec6ae60ee17` |
| `s3-consult-b-shadow-luna.md` | 段 3 レンズ B の **shadow arm 1** | `9110f9d2ec45cb1141f6888139f72e61c2cc29a5b5548c5cce64dca09c3734e2` |
| `s3-consult-b-shadow-mini.md` | 段 3 レンズ B の **shadow arm 2** | `c90ca2567318f7e018095a93b2141981b88a8542544bd77346c895c512b9612c` |
| `s3-consult-b-prompt.txt` | **3 arm 共通の凍結入力** | `8975a1fb2065626dbe3aa37f8474aabf94c95ef7257b13149949d57bf9722784` |
| `s4-adjudication.md` | 段 4 裁定 (親、実装しない) | `b179fd0d0327970a1aae27147f12bfb7c7a6668e3cac1b7793df5d7bcb244a67` |
| `probe-summary.md` | 段 1 生死確認の要約 (親) | `4a634a7a0c3b52746cf8155b8a8cac309a8a9cec15007081752e705f78e3b594` |
| `probe-receipts.json` | 段 1 probe の全 receipt | `bae89015a4ec99b3d55d953b53605b0ac7774fc946fb7f000d686892dd312b65` |
| `stage3-receipts.json` | 段 1 + 段 3 の全 receipt (凍結時点) | `e56aa37c0f3d72350ba5aab72f5ac008a46fb1af06c3385f225ec0263c10ee2b` |

## arm の同定 (session_id)

| arm | session_id | model / reasoning | prompt_hash |
|---|---|---|---|
| authoritative (レンズ B) | `019faded-eab5-7a43-b843-1a61b2d45c91` | `gpt-5.6-sol` / max | `02f8f550583d…` |
| shadow 1 | `019faded-eaa8-77a1-bd77-88689d3301aa` | `gpt-5.6-luna` / max | `02f8f550583d…` |
| shadow 2 | `019faded-eaa5-7890-89e4-804c14cb26c3` | `gpt-5.4-mini` / xhigh | `02f8f550583d…` |
| レンズ A (比較対象外) | `019faded-eaa8-7990-9460-77f3be1c4287` | `gpt-5.6-sol` / max | `d933d64e27ff…` |
| 段 2 planner | `019fad…` (`stage3-receipts.json` 参照) | `gpt-5.6-sol` / max | — |

**shadow 2 arm と authoritative arm の `prompt_hash` が一致している**ことが、同一凍結入力で
比較したことの機械証拠である。ただしこの hash は空白正規化後の値であり、byte 同一性の証明では
ない (限界は分析正本の「凍結入力の束縛の限界」を参照)。

## 起動条件

- 段 2 / 段 3 の全 arm: `codex exec -s read-only -C <本 wave の worktree>`。
  model と `model_reasoning_effort` だけが arm 間で異なる。
- 全 arm が `tools/check_codex_output.py` rc=0、ラッパの `.done` rc=0。
- read-only sandbox のため子はテストを実走していない。非実走は緑と数えていない (`DW-O05`)。

## 段 1 probe に含まれる不可用 model の session

`gpt-5.4-nano` (`019fadd3-c15a-79e1-8783-f083061d4e3d`) と
`gpt-5.1-codex-mini` (`019fadd3-c19c-7a12-bbf0-ded998aed815`) は 400 で拒否されたが、
rollout には session が残り receipt の `model` は要求 slug のまま、
`model_calls=0` / `cli_reported=0` である。これが分析正本の指摘する fail-open の一次資料。
