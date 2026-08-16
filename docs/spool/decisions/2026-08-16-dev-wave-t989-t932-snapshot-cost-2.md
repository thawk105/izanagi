---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t989-t932-snapshot-cost
seq: 2
---

## {{D:snapshot-base-narrow-transfer}}. snapshot base は BASE 閉包だけを転送し、upload-pack の受理方針に依存しない

**決定:** `tools/codex_reasoning_ab.py` の `_build_snapshot_base` は、実 repository 全体を
clone してから seal で捨てる形をやめ、`git init` →
`git pack-objects --revs --stdout`(BASE 固定 commit) → `git index-pack --stdin --fix-thin` →
`git update-ref` の 4 操作で **BASE 閉包だけを転送する**。
`git fetch` に生 SHA を渡す案は採らない。

**理由:**
- 旧構造は全履歴をコピーしてから `repack -Ad` で固定 commit 到達分だけを残していた。
  転送も repack も commit 数に比例するのに、残す量は固定である。
  親の実測 (静かな窓、3 走中央値) で root seal 26.30 秒 → 0.33 秒、
  `_build_snapshot_base` 35.02 秒 → 10.31 秒になった。
- `git fetch` に生 SHA を渡す案は同等に速いが、upload-pack が「到達可能な生 SHA の want」を
  受ける挙動に依存する。元 repository に `uploadpack.allowAnySHA1InWant` /
  `allowReachableSHA1InWant` の設定は無く、文書上の既定は false である。
  親も子も rc=0 の一意な理由を確定できなかった。`pack-objects` は upload-pack を経由せず
  source の object database を直接歩くので、この不確実性を構造的に持たない。
- 転送方式を変えても closure の観測値は 1 つも変わらない
  (reason 0 件 / object 8,209 / commit 834 / `.git` 35,132 KB /
  commit-graph 不在 / 残留 pseudo ref 0 件、9 走 + 改修後 1 走で一致)。

**却下した選択肢:**
- `git clone --local` の hardlink — snapshot 先が別 filesystem のため hardlink は成立せず、
  git は copy へ fallback する。速度が変わらない。
- shallow clone — `.git/shallow` を残す。snapshot は自己完結でなければならない。
- 現状維持 + 保留 — 共有 module fixture は consumer が 1 本でも走れば丸ごと構築されるので、
  保留を足しても構築費は 1 円も減らない。

## {{D:closure-check-rejects-shallow}}. snapshot の closure 検査は非空の shallow 境界を拒否する

**決定:** `_one_git_closure_reasons` の `closure_paths` へ `shallow` を足し、
非空の `.git/shallow` を reason にする。既存 6 種 (reflog / replace refs / alternates /
http-alternates / grafts / packed-refs) と同じ扱いとする。
受理集合を縮小する変更なので、正常 snapshot が reason 0 件で通る正例と、
shallow を置くと単一の reason が出る負例を対で置く。

**理由:**
- `.git/shallow` は seal も verifier も列挙しておらず、`git fsck` も shallow 境界を
  正当な履歴端として扱う。HEAD・working tree の hash・ref を変えないまま
  **commit 数だけ減らした snapshot を `git_object_closure.base_only=true` のまま通せる**
  唯一の経路だった。
- 本 wave の中心的な主張が「object 閉包が固定 commit の閉包と同一」である以上、
  その主張を機械検査を通り抜けたまま偽にできる経路を残せない。1 行の fail-closed で塞げる。
- 転送方式の変更自体は shallow を作らない。既存の穴であり、本 wave が広げたものではない。

**却下した選択肢:**
- 新設テストの assert だけで済ませる — 新設 node は synthetic repository を見るだけで、
  production の verifier が実 snapshot を受理する経路は塞がらない。
- lstat 基底への全面移行 — dangling symlink の抜け道は `shallow` に固有ではなく
  既存 6 種と共通なので、別裁定へ送る。本決定の射程を広げない。

## {{D:growth-hold-keeps-the-last-running-gate}}. 成長比例の保留は、その防壁を守る最後の走行 node には掛けない

**決定:** 恒久保留 (D335) の対象を選ぶとき、**保留すると当該防壁を守る既定走行 node が
ゼロになる**場合は保留しない。費用の比例源が別軸で除去できるなら、そちらを先に行う。
保留しなかった事実と理由は保留一覧へ書き、ユーザー提示に含める。

**理由:**
- 本 wave では共有 module fixture の consumer 17 本のうち 14 本が既に保留済みで、
  残り 3 本を保留すれば構築費は消えるが、clean な `verify_snapshot` を呼ぶ既定 node が
  ゼロになる。失うのは closure reason 集合の全部と forbidden object 検査、
  sandbox / Git 環境 scrub の検査である。規律 2 は性能のために検査を消すことを禁じる。
- 提示された比例軸 (session corpus) の親実測は 0.13 秒であり、
  35 秒を占めていたのは同 wave で除去した別軸だった。**0.13 秒の軸のために
  防壁を消す取引は成立しない。** 軸ごとの実測なしに保留を決めてはならない。
- module scope の fixture は consumer が 1 本でも走れば丸ごと構築される。
  部分保留は検出力だけを削って費用を残す純損失になる。

**却下した選択肢:**
- 3 本とも保留して費用を消す — 上記のとおり防壁が全滅する。
- 2 本だけ保留する — 残り 1 本が fixture を構築するので費用は下がらず、検出力だけ減る。
- 保留せず費用も放置する — 比例源を別軸で除去できたので不要。

## {{D:mutation-expected-nodes-must-be-runnable}}. 変異の期待赤 node は、既定で走り、かつ失敗として記録できる node に限る

**決定:** 変異事前登録の `expected_nodes` には、(a) 恒久保留などで既定 skip されない node、
(b) 変異時に **error でなく failure** として記録される node、
(c) `xdist_group` に属さない node だけを使う。
いずれかを満たせない性質は、満たす node へ実効 gate を再照準するか、
登録せず親の直接実測で裏を取って記録する。

**理由:**
- 保留が広く効いている repository では、子が挙げた期待 node が skip され、
  変異は必ず SURVIVED になる。本 wave の初回登録は 6 件中 4 件がこれに該当した。
- 共有 module fixture を壊す変異は consumer を **error** にする。変異 harness の
  失敗 node 抽出は短縮要約の `FAILED ` 行しか読まないので、error だけの走行からは
  node を 1 件も取り出せず PARSE_ERROR になる。
- `xdist_group` に属する node は、collection 空間では接尾辞を持たず、
  失敗要約では `@<group>` 接尾辞を持つ。harness の事前検査は前者を要求し、
  突き合わせは後者を要求するため、**両方を同時に満たす記述が存在しない。**
- 3 条件はいずれも「変異が生きているのに緑に見える」方向へ倒れるので、
  事前に排除しないと変異検査そのものが無意味になる。

**却下した選択肢:**
- 保留を一時解除して走らせる — 解除条件はユーザーの明示命令のみである。
- 期待 node を空にして SURVIVED 期待にする — 検出力の主張ができない。
- harness 側を先に直す — 受理集合を変える改修であり、本 wave の scope 外。別途起票する。
