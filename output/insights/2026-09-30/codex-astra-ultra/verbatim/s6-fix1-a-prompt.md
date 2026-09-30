単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 6 レビュー B (所見 RB-1 が本 fix の対象): /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s6-review-b.md
- 段 5 の自分の報告 (前回の変更内容): /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s5-author-a.md

作業する worktree (cwd、書込みはここだけ): /work/1/SFC/tanab/izanagi/.codex/worktrees/astra-ultra-unit-a (前回と同じ木・同じ branch)。

# 役割と所有

あなたは dev-wave 段 6 の fix 子 (Codex role=author、単位 A) である。**sub-agent を spawn しない (collaboration tool を使わない)。**
段 5 の実装子契約をそのまま継承する (所有 path・検査と報告の義務・テストを甘くしない・変更前の受理/拒否挙動の明記)。
編集してよい path: tools/check_docs.py、orchestrator/tests/test_check_docs.py (本 fix で触るのはこの 2 file だけ)。docs は編集しない。自分では commit しない。

# やること

親が段 6 で docs を縮約し、L1.5 の実 footprint を旧予算 9,696 bytes 以内に収めた (wave 側 commit 4af3c92b2)。したがって段 5 で入れた
予算の引き上げを取り消し、**base 3cb51f201 の値へ厳密に戻す**。対象は段 5 で変えた次の 6 箇所だけ (他の段 5 の変更は残す):

- tools/check_docs.py: `DEV_WAVE_L1_5_BYTES_MAX = 9_788` → `9_696`
- orchestrator/tests/test_check_docs.py:
  - `assert check_docs.DEV_WAVE_L1_5_BYTES_MAX == 9_788` → `9_696`
  - `_grow_test_layer_to(root, "L1.5", 9_789)` → `9_697`
  - `"l1_5": ("L1.5", 9_789, "L1.5 unique footprint 9789 bytes")` → `("L1.5", 9_697, "L1.5 unique footprint 9697 bytes")`
  - `10_625 if target_layer != "l1" else 9_788` → `9_696`
  - `assert layers["L1.5"] <= 9_788` → `9_696`

これは既存テストの期待値を段 5 以前の値へ戻すことであり、期待値の緩和ではない。反転・skip・削除はしない。
`git diff 3cb51f201 -- tools/check_docs.py orchestrator/tests/test_check_docs.py` に 9_788 / 9_789 が 1 件も残らないことを確認して報告する。
この木の docs は wave の縮約をまだ持たないので、この木で check_docs を走らせると L1.5 footprint 超過 (9793 > 9696) と effort pin 5 件が期待赤。

# 出力形式

markdown。「## 変更」「## 確認 (grep・構文・実走した範囲)」「## 期待赤と回帰」「## 総括」。
