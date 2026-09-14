単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260914

必読事項の射影: 下記の絶対パスを読む。**読めなければ即停止し、読めなかった path を報告せよ。**
この停止規則は下記に列挙した射影 file にだけ掛かる。お前が自分で探した path が不在でも、
それを理由に検査全体を打ち切ってはならない (その path は「不在」と記録して先へ進め)。

- /home/SFC/tanab/.claude/jobs/eb641176/tmp/wave-paper-story-20260914/prompt-plan.md
- /home/SFC/tanab/.claude/jobs/eb641176/tmp/wave-paper-story-20260914/plan-out.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260914/docs/paper-story/README.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260914/docs/paper-story/2026-09-05.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260914/output/insights/2026-09-07_t2364-paper-story-a2-certification/certification.json
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260914/output/insights/2026-09-08_t2411-paper-story-a6-certification/certification.json

この段では commit・push・file の書き込みを行わない。成果は最終メッセージの本文だけで返す。
pytest・build・測定は走らせない (sandbox に書込可能 tmp が無い)。静的な読解と照合だけでよい。
予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## レンズ A — 正しさ境界と、古い記述の引き写し

お前のレンズは **「正しさの緑が性能の主張へ染み出していないか」「訂正すべき古い記述を引き写して
いないか」「一次資料が言っていないことを言っていないか」** である。
`prompt-plan.md` (親 brief) と `plan-out.md` (段 2 の plan) の両方が検査対象である。
**plan を守ってはならない。親 brief 自身も、親が段 1 で自分で測った値とその一般化も、攻撃対象である。**

## 背景 — 親が書こうとしている新版

親は `docs/paper-story/2026-09-14.md` を、2026-09-14 時点の正典全体から**全項目再導出**して足す。
最新版は 2026-09-05 で、その §8 と §9 は「採用構成を現行環境の正式 protocol で測った判定は無い」
「性能を測った workload そのものでの採用静的 backoff の certification は 3 workload とも無い」と書く。

その後、正典側で次が確定した (親の実測。疑ってよい)。

- A-2 の attempt `t2364-20260907b` (2026-09-07) が outer `observed-positive`。
  4 cell すべて `source_binding_status=bound`、stock cell は `src_token=stock`、adopted cell は非 `stock`。
  rr5 adopted 3,987,794 / stock 2,438,295 (effects 0.6354846316791036)、
  rr50 adopted 4,297,929 / stock 3,756,230 (effects 0.14421348000521794)。
  4 cell とも correctness `certified` (legacy 1 回 + performance 5 回)。
- A-6 の attempt `a6-20260908b` (2026-09-08) が outer `reject`。
  rr95 stock 10,088,796 / adopted (fixed 2 µs) 9,505,248、effects −0.057841193339621455。
  2 cell とも correctness `certified`。
- T-2557 / T-2589: balanced の stock-inline 対を 2026-09-13 に正式測定し 2026-09-14 に `accepted`。
  improvement_percent 11.225375361916456。再測定していない。

## 親の暫定裁定 (攻撃対象)

- **(P1-a 改訂)** 親は段 1 で「A-2 は A 群の残件のまま」と書いたが、D1645 の逐語
  「正しい identity で取り直した attempt が出るまで A-2 の結論を外す」を読み直した結果、
  **新 attempt がその解除条件を満たす**と考えを改めた。したがって新版では A-2 の新 attempt の
  結論を論文素材として使う。**旧 attempt の結論と fig5 の用途制限は D1936 項21 により期限なしで残す。**
- **(P1-d)** 但し書き 2 (性能 workload そのものでの採用静的 backoff の certification が無い) は、
  A-2 と A-6 の新 attempt により **3 workload とも外れる**。ただし残る限定は
  (i) L01 の point-key trace、(ii) D1257 の「correctness 側の argv は独立記録されていない」、
  (iii) `compile_out_evidence_scope` の「artifact hash 単独では compile-out の証明にならない」の 3 つ。
- **(P1-e)** 新旧環境で符号が 3 workload とも一致した (旧 +38.3 / +11.3 / −6.6、
  新 +63.5 / +14.4 / −5.78) ことは書いてよいが、**再現判定ではない**と明記する。
- **(P1-b)** balanced stock-inline 対の `accepted` は但し書き 1 (A-1) を外さない。

## 探させたいもの

1. **一次資料が支えない断定。** 上の各値・各判定について、親が一次資料を超えて言っている箇所。
   特に「certified」の対象・射程、`observed-positive` の意味、A-2 と A-6 を 1 つの主張へ束ねること。
2. **正しさの緑の染み出し。** 4 cell / 2 cell の correctness certified を、性能の文・表・要約へ
   持ち込んでいないか。`certified` は実際に build された bytes についての判定であって、
   要求した構成が build されたことを含意しない (F707) という規律が保たれているか。
3. **古い記述の引き写し。** 最新版 (2026-09-05) から新版へ運ばれる記述のうち、2026-09-14 時点で
   偽になっているもの。特に §2 (f)、§4 の図の表 (fig6 が増えている)、§5、§6、§7、§8 の A/B/C 群、
   §9 の 7 種の表。**「不変」と書かれた項目こそ疑え。**
4. **規律 7 の破り。** 旧 attempt の判定を取り消していないか。前後比較として読ませていないか。
   逆に、旧判定を無効化しないことを口実に新しい事実を書き落としていないか。
5. **親の一般化。** 親が自分で測った値 (certification.json の field、worklog の記述) から、
   母集合や射程を超えた一般化をしていないか。
6. **D12 の境界。** `observed-positive` を研究の成功宣告へ拡張していないか。
   逆に `reject` を研究の失敗宣告へ拡張していないか。

## 出力形式 (この見出しをそのまま使う)

## 所見

各所見を次の形で書く。番号 / 対象 (親 brief か plan か、どの節) / 主張 / 一次資料の path または D 番号 /
確度 (高・中・低) / 是正案 1 文。**確度の根拠を必ず書け。**

## 親の暫定裁定への評価

(P1-a 改訂) (P1-b) (P1-d) (P1-e) のそれぞれについて 同意 / 不同意 と、不同意なら一次資料を指した対案。

## land 可否

GO / NO-GO と、その理由を 3 行以内。

## 総括

10 行以内。最も重い所見 1 件を名指しする。
