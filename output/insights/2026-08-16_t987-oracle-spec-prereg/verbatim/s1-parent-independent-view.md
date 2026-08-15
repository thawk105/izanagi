# 親の独立見解 — 段 2/3 子の出力を読む前に固定

固定時刻: 2026-08-15 23:47 JST (段 2 プラン子は起動済み・未完了、出力未読)
根拠はすべて現 HEAD (330f67d0) の一次資料。docs の記載は根拠にしない。

## 1. n の導出に関する親の結論 (brief の (P1)(P2) を親自身が訂正する)

brief 起草時、親は a12 stress-check の J を replicate 数 n と同一視し、
「a12 は J∈[4,13] の包絡を与える」「精度係数 q(J)/√J の平坦化点が n=8」という
導出を (P1)(P2) に書いた。**この導出は配線と結びついていない。**

- `s8b_oracle_judge.py:159-345` の `judge_oracle` が実際に行う集約は
  **median of medians → configuration 間の argmax** であり、
  tie 判定は `value == maximum` の **float 完全一致**である (`:317-325`)。
- a12 が模擬している判定式は
  `mean - q*sqrt(s/J) > 0` (`stress-check-simulation.json` の `false_pass_rule.formula`) で、
  **平均・標本分散・q(J) を使う下側信頼限界**である。**配線されている規則ではない。**
- したがって q(J)/√J の平坦化は、現行 judge の受理挙動を一切支配しない。
  a12 から n を導けるのは、集約規則を a12 の規則へ**再凍結した場合に限る**。
- `judge_oracle` の docstring 自身が
  「この集約規則はまだ再凍結されておらず、実測開始前に明示的な再凍結が必要である」と
  宣言している (`s8b_oracle_judge.py:167-170`)。

**訂正後の親の立場:** a12 は n の下限も上限も与えない。a12 が与えるのは
「別の判定規則のもとで J∈[4,13] なら false-pass 率が α₁ の 15.6% 以下に収まる」という
**条件付きの安心材料**だけであり、しかも artifact 自身が `pilot_ready=false` /
`a11_empirical_stress_model_only` と宣言している。**承認パッケージで a12 を
n の根拠として提示してはならない。**

## 2. では n は何から導けるか (較正からの導出)

n が現行配線で持つ唯一の統計的役割は、**median of medians の安定度**である。
その安定度が意味を持つのは下流の `s8b_verdict.py` 条件 3 で、
oracle 実測差が per-pair floor を超えるかを判定するときである
(`s8b_verdict.py:14-16`、floor を使うのはこの条件のみ)。

- 素材となる散らばりの実測: pegasus 登録済み較正 2 件の within-run CV = 1.17% / 1.25%
  (`output/env/pegasus/calibration/registered/*.json`)。
  between-run CV は linux-baremetal でのみ実測 (rr5 0.67% / rr50 1.07% / rr95 0.11%) で、
  **rr20・rr80 の between-run 実測は存在しない**。
- 比較先の尺度: floor protocol の `wired_min_rel_floor = 0.03` (3%)。
  ただし `holdout_freeze.json` の `floor` は **null** であり、per-pair floor の実値はまだ無い。
- 正規近似での標本中央値の標準誤差は約 `1.253*sigma/sqrt(n)`。
  sigma = 1.25% を採ると n=4 で 0.78%、n=8 で 0.55%、n=13 で 0.43%。
  3% floor に対する比は順に 26% / 18% / 14%。

**親の候補: n = 8。** 根拠は (i) 上記 SE が floor の 1/5 程度に収まる最小の切りの良い値、
(ii) floor protocol の `n_sessions = 8` と同値で先例整合
(`output/s8b-freeze/floor_protocol.json`)、(iii) 純測定時間 12 cell × 8 × 5 rep × 5 秒 = 40 分。
**a12 は根拠に入れない。** この候補は「正規近似」「sigma を within-run CV で代用」
「floor 実値が未確定」の 3 点で近似であり、承認パッケージにはこの限界を明記する。

## 3. 本 wave 発の新規所見 (entry 511 に無い)

- **N1 (規則の不整合):** a12 の事前登録規則と配線されている judge の規則が別物である (上記 1)。
  entry 511 の承認パッケージは n=8 を草案として出したが導出を示しておらず、
  この不整合にも触れていない。
- **N2 (spec 層が A3-3 を検査しない):** `validate_reviewed_spec` は `build_schedule` を
  呼ぶだけで `_validate_schedule` を通さない (`s8b_oracle_spec.py:123-137`)。
  manifest 層は block を正確に 1 件しか許さない (`s8b_oracle_manifest.py:302-305`)。
  よって複数 block の spec は**承認を通過し、manifest 生成で初めて落ちる**。
  承認手番を 1 回消費してから落ちる形であり、承認の前に落とすべきである。
- **N3 (tie が実質到達不能):** `judge_oracle` の tie 判定は float 完全一致であるため、
  連続値の median of medians では tie がほぼ発火しない。ノイズ内の差でも `unique-best` を
  宣言する。ノイズ耐性は下流の floor 条件だけが担っており、oracle verdict 単体は
  「差が意味を持つか」を判定していない。**これは規律 2 に触れる性質だが、
  C1〜C6 を変えない制約下では本 wave の実装対象ではない。** 記録項として返す。

## 4. contract test 改訂 (B) についての親の独立設計骨子

現状 (`test_s8b_oracle_manifest_contract.py:130-146`) は 2 directory 配下の file 数 0 件でだけ緑。

親案 = **pin 状態で分岐する 2 状態設計**。
- `APPROVED_SPEC_SHA256 is None` のとき: 受理集合は**現状のまま** (2 directory とも 0 件)。
- `APPROVED_SPEC_SHA256` が 64hex のとき: 受理集合は
  「`output/s8b-oracle-spec/` の file 集合が `reviewed_spec.json` **ちょうど 1 件**で、
  その実 bytes の sha256 が pin と一致する」。他の file が 1 つでもあれば赤。
- 広がる範囲 = `0 件 ⊊ {0 件} ∪ {reviewed_spec.json ちょうど 1 件かつ sha256 == pin}`。
  **pin が None の間は 1 byte も広がらない。**
- **恒真化の危険:** テストが pin を読むと、pin と file を同時に書ける実装者にとって
  この検査は「自分で書いた 2 つが一致する」ことしか見ない。
  親案では、pin の値そのものを**別の独立な記録** (承認 receipt) と突き合わせない限り
  恒真である点を、設計の限界として明示する。これを解くのが entry 511 の Q2 (trust root) であり、
  **B は Q2 が未解決のままでは「機械強制された人間承認」を名乗れない。**
- `output/s8b-oracle-manifest-candidates/` は spec と lifecycle が異なる
  (candidate は複数生成されうる作業物、spec は承認済み単一)。**同じ 1 件契約を課さない**。
  親案では candidate 側は 0 件条件を維持し、必要になった時点で別途裁定する。

## 5. 本 wave の推奨結論 (段 4 で再裁定する)

実装差分ゼロで land し、次を承認パッケージとして返す。
n=8 の候補と限界、a12 を根拠から外すこと、N1〜N3、B の 2 状態設計と恒真性の限界。
