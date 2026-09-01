# [T-2124] S-1 の epoch gate だけを歴史 purpose へ移す — dev-wave handoff

- wave: `dev-wave-t2124-s1-epoch-historical`
- branch: `worktree-dev-wave-t2124-s1-epoch-historical`
- worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical`
- base (着手直前の local main): `28ebff456b9f57a927854950b5030fa77aec6529`
- 背景 job / worktree 隔離 (DW-O20 成立)。本 handoff は repo 外。
- 一次資料: `docs/decisions.md` の D1387 (ユーザー裁定)、その前提 D1366。
  背景 `output/insights/2026-09-01_t2060-current-closure-unknown/`。

## 段 1 brief

**scope.** `orchestrator/campaign/s1_report.py` の epoch gate 1 関数
(`_campaign_verifier_epoch_from_lock_bytes`) の purpose を `CERTIFIED_ACCEPTANCE` から
`HISTORICAL_RAW` へ移す。同時に `E0 / v1-authority-absent` の拒否を局所に明示して残し、
負例テストで固定する。`orchestrator/campaign/replay.py` (`load_landscape`)、
`s8b_oracle_report.py` の epoch 証拠、`artifact_admission.py` の中央 gate は**一切触らない**。

**確定済みユーザー裁定.** D1387。3 消費者のうち S-1 だけを移す。replay は exact 型と証拠
capability に束縛されており緩めると規律 2 に触れる。oracle は根拠が一次資料に無い。

**成果物影響 (DW-G05).** 放置すると、S-1 report の certified gate は将来の v2 lock に対して
作業ツリーが汚れているだけで `current-closure-unavailable` を出し、記録された証明の鎖とは
無関係な理由で歴史標本を拒否し続ける。D1387 はこれを S-1 の purpose の誤りと裁定した。

**不変条件 (規律 2 を緩めない).**
1. `E0 / v1-authority-absent` の拒否は生きたまま残る。負例テストは**実関数を通す**。
2. `require_persisted_certified_commit` (`s1_report.py:352`) の保存済み COMMIT 証拠検査は無変更。
3. `artifact_admission.py` は 1 byte も変えない。`replay.py`・`s8b_oracle_report.py` も同様。
4. 拒否時の投影 (`_rejected_epoch_projection`、`campaign_verifier_epoch_rejected` reason) は無変更。

**成果物の形.** `s1_report.py` の局所差分 1 箇所 + `orchestrator/tests/test_s1_report.py` の
負例 1 本と正例 1 本 + 変異 matrix + worklog / insight fragment。docs 本文の新設はしない。

**分割方針.** 変更面が 2 file と小さいため段 5 実装子は 1 本。受理集合が変わり正しさ防壁に
触れるため**軽量版にはしない** — 段 2・3 と段 6 の敵対レビュー 2 本を省かない (DW-C00)。

### (P1) 親の provisional 裁定・攻撃対象

E0 拒否は `_campaign_verifier_epoch_from_lock_bytes` の**局所**に置く。
`artifact_admission` に第 3 の purpose や wrapper を新設しない (D1366 が却下した選択肢)。

### (P2) 親の provisional 裁定・攻撃対象

「可用性 gate が実際に外れた」ことの正例は、v2 lock + `ContractLoaderBindingError` を強制した
状態で gate が拒否しないことで示す。v2 lock は実 artifact に 0 件なので合成 fixture になる。
この合成が機構を通っているか (両層 stub で恒真になっていないか) が攻撃対象。

## brief 前の実測 (引数の前提を 1 つ覆した)

- **F-A: 依頼文の対象 file が違う。** epoch gate は `orchestrator/campaign/s1_report.py:302-310`
  にある。`s1_direct_comparison.py` には `epoch` の出現が **0 件** (1353 行全走査)。
  依頼文の「対象は s1_direct_comparison.py 周辺」は `s1_report.py` を指すものとして読む。
- **F-B: 保存済み campaign 30 件はすべて v1 (authority 不在)。** `output/campaigns/` の 30
  directory 全件で `campaign.lock` に `authority` key が無く、記録 epoch は
  `E0 / v1-authority-absent` になる。つまり**既存成果物にとって唯一到達する経路は E0 拒否**であり、
  可用性 gate (`capture_contract_loader_binding`) には 1 件も到達していない。
  本変更は既存 30 件の S-1 出力を 1 byte も変えない。
- **F-C: 既存の E0 テストは実関数を通っていない。**
  `test_non_e1_campaign_is_structured_and_wal_is_not_read` は
  `_campaign_verifier_epoch_from_lock_bytes` 自体を monkeypatch する。さらに module 全体に
  autouse fixture `_certified_epoch_fixture` が同関数を固定 E1 へ差し替えている。
  よって E0 拒否は現状**実関数の位置では pin されていない**。負例テストは autouse fixture を
  解除し実 callee を名指しする必要がある。
- **F-D (DW-O09 pin 閉包): `output/reports/s1_direct_comparison/report.json` は tracked かつ
  byte pin 対象。** `docs/paper-story/figures/fig4_s1a_9pair_direct_comparison.provenance.json`
  が sha256 `491ad38dbabc4a9d57fc7a0ae5a4f5b37f67a5862712e158a9cc34e8552fa725` で束縛し、
  現物と一致する。この report は `campaign_verifier_epoch` field を**持たない** (gate 導入前の
  `generated_at_head 24202e27` 生成物)。`test_s1_9pair_figure_provenance.py` は照合するだけで
  再生成しない。**本 wave は producer (`s1_report.main`) を走らせない** (DW-O10)。
  それ以外に `s1_report.py` の bytes を pin する manifest / generator source hash は無い。
  `docs/freeze-permanent-design-s2.md` の W-d writer / consumer registry は path 登録であり、
  file を消さず増やさない本変更では不変。
- **F-E: 稼働 wave との編集面重複なし。** 32 worktree を committed 差分と未 commit dirt の
  両方で走査した結果、重なるのは `artifact_admission.py` の 2 本 (T-733 の
  `dev-wave-t733-source-closure-transitive` と `t733-author`) だけ。その差分は scope 文字列と
  docstring のみで gate 論理を変えず、本 wave は同 file を編集しない。
  `s1_report.py` / `test_s1_report.py` は重複 0。
- **F-F: 先例あり。** `HISTORICAL_RAW` の宣言は `layer3_report.py:551` と
  `p2_2_report.py:133` に既存。新設パターンではない。

## dev-wave 改善候補

(段 8 で一度だけ裁定する。現時点の記録:)

- 候補 1: 依頼文が名指した file に対象機構が無く、別 file (`s1_report.py`) にあった。
  `DW-S01` は「変更面は分類でなく実アンカー表で渡す」と定めるが、**依頼文の名指し file 自体が
  実測で外れる**型は明記が無い。段 1 の実測義務に「依頼文の名指し対象を識別子で実測して確かめる」
  を含めるかを段 8 で検討する。

## 進捗

- 2026-09-02: 段 1 実測完了 (F-A〜F-F)。worktree 作成へ。
