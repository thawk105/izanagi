---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2321-b10-value-errata
seq: 1
title: [T-2321] B-10 記録値を規律 7 の追記訂正で直した — 「24 反復」は表の本規模 18 / campaign 全体 22 (帯 1346.9-1465.6 秒は高 commit 13 件) に範囲を分け、「5 時間 5 分」は WAL / scheduler.stderr の記録境界の秒表示差で位置づけたが区間は未同定のままで、既存但し書き「本規模 3 反復を含む」の適用限界を 7 箇所へ追記 (docs のみ、branch worktree-dev-wave-t2321-b10-value-errata、変異 matrix 免除 = 実装面差分ゼロ)
---

## 本文

- ユーザー依頼は「[T-2321] (P3、entry 1262) B-10 の記録に残る値の誤りを規律 7 の追記訂正 (削除 0 行) で直す
  (docs のみ) — 『24 反復』(road-and-balanced README 2 箇所と設計文書 §4 blockquote) は一次資料 verify_done=22
  (legacy 4 + performance 18)・本規模 18 と一致しない。22 と 18 は集計範囲が違うので一律置換にせず範囲を書き分けて
  訂正する。あわせて『5 時間 5 分』の計測区間を一次資料 (request 965996、Elapse 20950 秒。Elapse をそのまま計測区間と
  見なさず WAL / journal の時刻で区間を確定する) から確定する。[T-2202] の『誤りのまま』但し書きは凍結物なので
  書き換えず訂正は追記で行う。着手直前の local main から fresh worktree を作る。規律 2 を緩めない。本題の追記訂正
  だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **閉じた。** 一次資料は `output/insights/2026-09-18/t2321-b10-value-errata/README.md` (逐語は同 `verbatim/`)。
  編集は 7 file・8 箇所の純挿入 (+72 行 / 削除 0)、既存行と T-2202 の但し書きは 1 byte も変えていない。
- **「24 反復」はどの範囲にも対応する記録が無い値だった。** campaign `ed8a676b` の WAL (33 行) を親が直接数え、
  `verify_done` 22 = 初期確認 (legacy) 4 + 本規模 (performance) 18、全件 serializable / certified=true /
  `payload.anomalies` 0、abort 0。表 (本規模) の「24 反復ぶん」「全 24 反復が certified」は 18 に、campaign 全体の
  22 は範囲付きで併記した。段 3 レンズ A が「帯 1346.9-1465.6 秒は高 commit 3 変種の 13 件 (5+5+3) で 18 件全体の帯
  ではない (`602b4ce9c788` は 401.7-427.4 秒)」を追加指摘し (real)、設計文書 §4 と README に書き分けた。
- **「5 時間 5 分」は WAL / scheduler.stderr のどの記録境界とも一致せず、計測区間は引き続き未同定である。**
  scheduler.stderr: Started 09-02 01:07:49 JST / Ended 06:56:55 / Elapse 20950S / `Terminated`。WAL: 3 変種目の
  認証確定 05:40:56 (Started から 16,387 秒 = 4 時間 33 分 07 秒)、4 変種目 `292d58f1dad8` の本規模 verify_done
  06:06:15 / 06:28:42 / 06:52:31 (17,906 / 19,253 / 20,682 秒)、Ended まで 20,946 秒 (Elapse 記載と 4 秒差、理由は
  資料から特定できない)。レンズ A が Created・Started・WAL 33 件・Ended の 36 時刻・630 組を epoch で検算し、
  18,300 ± 30 秒に入る区間は 0 件。campaign dir に journal は無い (`runs/` は `wal.jsonl` のみ)。
- **親の brief は「5 時間 5 分 = 撤去判断時の走行中 qstat 観測での request 経過時間 (06:11〜06:13 頃)」と断定して
  いたが、段 3 の両レンズが独立に「証拠より強い」と退けた (A-1 / B-2、real)。** 同時代記録 (archive 1187) の
  「経過 18,196 秒」と整合する仮説には留めたが、両値の観測時刻・起点・丸め方は特定できず (差 104 秒)、当時の qstat
  逐語も残っていない (投入証拠の qstat-f は投入直後 Elapse 3S の 1 回のみ)。追記の見出しは「記録境界の時刻差と、
  旧『5 時間 5 分』の未確定範囲」にし、「確定」の語を使わなかった。
- **実測で判明した既存但し書きとの矛盾を追記した (A-2 / B-3、real)。** T-2202 の「いずれの区間でも本規模 3 反復の
  時間を少なくとも含む」は、WAL 末尾まで・request 終了までの区間では確認できるが、Started 起点 18,300 秒という読みでは
  本規模 2・3 反復目の完了 (19,253 / 20,682 秒) より前なので成立しない。旧 bytes は保持し、適用限界だけを各箇所に足した。
- **scope の裁定:** (P1) 「5 時間 5 分」の追記先は担い手全部 = T-2202 が「判定不能」を付けた 6 箇所 + レンズ A が閉包漏れ
  として挙げた `2026-09-02/b10-denominator-270/README.md` §4.1 表 (job 壁時計への帰属を書く、T-2202 の対象外) の
  計 7 箇所。根拠は設計文書 §1 に集約し、他 6 箇所は短文 + 参照 (routing 5)。`docs/paper-story/2026-09-05.md` の
  3 箇所は凍結 snapshot で誤値を肯定していない (「一次資料は 22」) ので触らず、実規模 18 / 全体 22 の範囲は次版が本
  insight から引く。(P5) decisions fragment と D1605 の新 D 訂正は書かない (B-5 採用、routing 2 に該当せず、台帳側は
  [T-2322] の裁定領域)。D1605 理由節の「24 反復ぶん」は T-2322 の列挙に加えた (下の更新)。
- 検査: pin 閉包 (path / sha256 / blob) 0 件、`check_docs.py` 違反なし rc=0、holdout 走査 `conjunction_hits: []`、
  `git diff --check` 緑。実 repo を読む check_docs テスト 3 node (`test_real_repo_clean` 等) の単独実走 (`run_tests.py`、自動判定で
  bounded local = login) は 3 skipped / rc=0 (growth hold `docs_bytes`、opt-in なし。hold 下は走っていないので緑と
  読まず、検査器の直接実走 rc=0 を根拠にする)。変異 matrix は実装面差分ゼロで免除 (DW-S04)。受入全走は land 経路で 1 走 (結果は land の受領証)。
- 工数: codex 子 2 本 (段 3 consult、レンズ A 5 分 20 秒 / B 3 分 16 秒、medium)。段 2 プラン子・実装子・段 6 レビュー子
  なし (`DW-C00` 軽量版、docs-only)。親の実測: WAL / scheduler.stderr の読取と時刻換算、pin 閉包、担い手検索、
  check_docs 1 回、holdout 走査 1 回、挿入 script 1 本 (job dir)。

## 次の一手差分

### 完了

- [T-2321] 「24 反復」3 箇所を範囲別 (表の本規模 18 / campaign 全体 22、帯は高 commit 13 件) に、「5 時間 5 分」7 箇所を
  記録境界の秒表示差で位置づけ (区間は未同定のまま、既存但し書きの適用限界を追記) する追記訂正を 7 file・8 箇所へ
  純挿入した (削除 0 行)。一次資料は `output/insights/2026-09-18/t2321-b10-value-errata/README.md`。
  remaining: none
  base: 851514fd7a655135f162a5279e463f7d6042e1c3152d105f3f780e1f6a0432e1

### 更新

- [T-2322] **P3・ユーザー裁定待ち**: [T-2202] の対象外に残った同じ主張の
  担い手 — `docs/decisions.md` (D1480 / D1485 / D1489 / D1509 / D1554)、archive worklog
  (1186 / 1187 / 1189 / 1190 / 1197-1198 / 1211 / 1223) — に同じ但し書きを付けるか。台帳は
  追記 (新 D または H2 直後の blockquote) でしか書けない。付けないなら記録のみで終端する。
  [T-2321] (2026-09-18) の追記: `docs/decisions.md` D1605 の理由節にも「24 反復ぶん」(訂正値は実規模 18 /
  campaign 全体 22) があり、D1480 / D1489 付近の「5 時間 5 分」と同じく台帳側の担い手である。本裁定の対象に加える。
  base: c18b58e813db07c0d960f7b5c0a0fe7163ce134a0bc756fca06c5d288f68e385
