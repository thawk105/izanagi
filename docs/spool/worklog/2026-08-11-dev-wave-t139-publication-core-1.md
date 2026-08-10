---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t139-publication-core
seq: 1
title: 公表手続きの新 core を起草した ([T-139]) — 裁定 B4 (a) の別 study を段階 1 で返し、上流に「d=1.0 では適格な J が存在しない」を発見した (docs のみ、実装差分ゼロ、受入 8245 passed / 20 skipped / 532.78 秒 / rc=0、branch worktree-dev-wave-t139-publication-core)
---

## 本文

- **起票根拠 = 裁定 B4 (a) (2026-08-10 /rulings)。**一次控えは
  `dev-wave-jobs/rulings-inbox/2026-08-04-rulings-session-5rulings.md` §60。
  「公表の検定手続きの正本を、現 core を書き換えない新しい core を起こす別 study で凍結する」。
  本 wave はその草案を起草し、**凍結はユーザー承認へ返した** (段階 1、`authority: none`)。
  裁定 R5 (a)+(d) が「文言修正は将来の別 study の core 起こし時に」と書いていた正分母 guard も、
  本 core が正本を持つ形で回収した。
- **実装差分ゼロ。**コード・テスト・script・機械設定を 1 つも追加・変更していない。
  差分は `output/insights/` と `docs/spool/` だけである。したがって `DW-S04` の免除規定
  (実装差分ゼロの変異 matrix) に該当し、**変異 matrix は登録も走行もしていない。**
  変異させる gate も受理集合も存在しないことを段 4 で確認した。
- **受入は免除しなかった。**判定証拠 = 実 repo の `output/insights` を読むテストが複数実在する
  (`orchestrator/tests/test_artifact_admission.py`、`test_frozen_artifacts.py`、
  `test_check_docs.py` 等を grep で実測)。したがって全走した。
- **受入 lease に 125 回の claim (約 62 分) を要した。**取得後に local main を取り直したところ
  **48 commit 遅れ**ており、待ち手の中で `--no-ff` merge してから投入した (親へ戻さない)。
  release は land の終端で行う。
- **凍結境界を守った。**現 core (`ac939af4…`)、追補 A 再発行版 (`f7db96ce…`)、追補 B 草案の
  bytes をいずれも変えていない。commit 前に pin (`test_t139_preregistration_binding.py` の
  `BlobRef`) と実 blob の一致を親が実測した。
- **敵対検証は 5 本 + 再レビュー 2 巡。**段 3 の 2 レンズがどちらも NO-GO (blocker 2 件 / 9 件)、
  段 6 のレビュー 2 本も NO-GO (4 件 / 5 件)、焦点再レビュー第 2 巡 NO-GO (残 4 件)、
  第 3 巡で **GO (残 0 件)**。
- **親の暫定判断が 1 件倒れた。**「Holm は closed testing の shortcut だから検出力で劣らない」は
  **誤り**である (相関を使う有効な局所検定を持つ closed testing の方が強い)。
  結論 (Holm 採用) は維持し、理由を「任意の依存に耐え、必要なのは marginal `p` 値の妥当性だけ」へ
  差し替えた。
- **親自身が草案に入れた数値誤りを 2 件、レビューが捕えた。**どちらも「書いた本人には正しく見える」型で、
  静的レビューでしか出ない。
  1. stress check の縮退枝を `6×6` 標本共分散の特異性で判定していた。`J ≤ 6` では rank が
     高々 `J−1 < 6` なので**必ず**特異になり、`J = 4, 5, 6` の 108 セルが手続きを 1 度も試さないまま
     `x = 0` で通過する恒真な gate になっていた (2 レンズが独立に指摘)。
  2. 厳密不等式の境界を切り捨てた値 (`0.0144150`) で閾値として書いていた。真の境界は
     `α* = 0.014415014983…` であり、`α_pub = 0.01441501` は書いた閾値を超えるのに条件を満たさない。
     等式で定義し、丸めるなら切り上げ側 (`0.0144151`) を使う形へ直した。
- **レンズ間の食い違いを 1 件、親が裁定した。**stress check の seed が source core の digest を
  含むことについて、レンズ A は refuted (blob identity は不変)、レンズ B は real
  (erratum 適用後の effective core と食い違う) と判定した。**B を採った** — 乱数 stream の
  domain separator に provenance の意味を持たせない方が安全である。seed から digest を外した。
- **親が独立に計算して得た事実 2 件** (どちらのレンズも明示していない形。repo 外 probe で実測)。
  1. `α_pub > α* = 0.014415014983…` のとき、候補 `J = 4, …, 13` の**すべてで**
     `q_primary(J, 0.025) > c_B(J, α_pub)` である。したがってその条件下では、
     **Holm と同時区間の非整合は primary が pass しない枝でしか起こらない**
     (primary が pass すれば 6 成分すべての下限が正で Holm も第 1 段で全棄却)。
  2. 上流の設計問題 (下記)。
- **上流に重い設計問題を発見した (裁定 C-1 として返す)。**追補 A `a10` の
  `L_J = max(0, 1 − Σ_k p_k(J))` と `a11` の `q(13, 0.025) = 3.449997` のもとで、
  `d⁻ = 1.0` (裁定 U4 が「引き下げない」と定めた下限) では最小成分の失敗確率が
  `0.42372 > 0.20` になるため、**候補 `J = 4, …, 13` のどれも `L_J ≥ 0.80` を満たさない**
  (`L_J ≤ 0.57628`)。必要条件は `d⁻ ≥ 1.2210`、6 成分が同水準なら `1.5623` が要る。
  **凍結済み文書の問題であり本 wave では直せない。**なお `d⁻ = 1.0` で「全候補で `L_J = 0`」と
  書いたのは過大で、第 2 巡の指摘を受けて `L_J ≤ 0.57628 < 0.80` へ訂正した。
- **新 core を承認しても本走は解禁されない** (裁定 C-2)。source core の
  `main_admission: requires_addendum_a_and_b` が要求する追補 B は source core に従属する文書であり、
  新 core に従属する追補 P はそれになれない。段 2 プランがこれを最初に指摘し、
  段 6 が「現 B と追補 P が同じ公表 entry を二重予約する」形になることを追加で示したので、
  予約所有者の択一を C-2b として独立の問いに切り出した。
- **probe を repo へ入れかけて撤回した。**検算 script 4 本を `output/insights/.../probe/` へ
  複写した直後に、[T-317] の裁定 (probe は所在を問わず実装面であり repo へ入れない。repo 外の
  運転 script は親可) に反すると気づき、commit 前に削除した。probe は wave artifact directory に
  残し、出力値だけを逐語と package へ転記した。
- **peer 通知を 2 回受け、いずれも local main の読み直しの契機にだけ使った** (待機・検査省略の
  根拠にしていない)。1 回目は wave 途中で `909914ef` を ff-only 取り込み、2 回目は受入待ちの
  最中だったので lease 取得後の merge にまとめた。
- 承認パッケージの正本 = `output/insights/2026-08-10_t139-publication-core/package.md`
  (C-1、C-2、C-2b、C-3、C-4、C-5)。草案の正本 = 同ディレクトリの `publication-core.md`。
- **段 8 の自己改善候補 1 件は、実装せず起票へ回した。**`DW-S04` の変異免除規定は
  「実装差分ゼロの**「実装しない」裁定**の変異 matrix だけ」と書いており、成果物が docs で
  実装差分がゼロの wave (本 wave がまさにこれ) に当てはまるかを親が段 4 で迷った。
  明確化を試みたところ `docs/dev-wave/**` の **L1 unique footprint が 10,647 bytes** となり
  予算 **10,625 bytes** を **22 bytes** 超えて `check_docs` が拒否した。
  短縮のため「「実装しない」裁定」を落として「実装差分ゼロの wave」へ一般化すると予算には収まるが、
  それは**変異検査 (正しさ防壁) の免除範囲を一方的に広げる**変更にあたるため、
  `docs/skill-self-improvement.md` の「正しさ防壁・裁定境界の変更は実装せず裁定パッケージへ送る」に
  従って実装しなかった。`docs/dev-wave/core.md` は変更していない。

## 次の一手差分

### 更新

- [T-139] **P1・公表 core 草案を起草済み → ユーザー裁定 6 問待ち (C-1 / C-2 / C-2b / C-3 / C-4 / C-5)**:
  裁定 B4 (a) に従い公表手続きの新 core を段階 1 で起草した
  (`output/insights/2026-08-10_t139-publication-core/publication-core.md`)。
  未調整 `p` 値 = 片側 `t` (統計量は `a10` と同一)、多重調整 = Holm、同時区間 = Bonferroni 片側
  同時下限 (Holm と一致しないことを明記)、正分母 guard = `qualification_status` の逐語複写、
  非正規性は解消せず 360 セルの事前固定 stress check は診断、追補の閉集合は `p01`〜`p03`。
  **凍結していない。本走の投入は依然不可** (B8 (a) は不変で、加えて C-2 のとおり新 core だけでは
  `main_admission` が閉じない)。**新たな blocker: `d⁻ = 1.0` では適格な `J` が存在しない** (C-1)。
  裁定 Q-A〜Q-E (367)、B4 (a) / B8 (a) (373) は不変。
  正本 = `output/insights/2026-08-10_t139-publication-core/package.md`
  base: a59df3904ae743296d5baa6eb48e8dc63e6fdf6b968582bafa7a4816da1bc9ba

### 新規

- {{T:dw-s04-zero-diff-exemption}} **P3・ユーザー裁定待ち**: `DW-S04` の変異免除規定が
  「実装差分ゼロの「実装しない」裁定」と書かれており、成果物が docs で実装差分ゼロの wave に
  当てはまるかが曖昧である。「実装差分ゼロの wave」へ一般化すれば曖昧さは消え予算にも収まるが、
  変異検査の免除範囲を広げる変更なので裁定を要する。現状のまま明記だけを足す案は
  `docs/dev-wave/**` の L1 予算を 22 bytes 超える (10,647 > 10,625)。
