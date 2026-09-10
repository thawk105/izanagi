# [T-2124] D1387 — S-1 の epoch gate だけを歴史 purpose へ移す

wave: `dev-wave-t2124-s1-epoch-historical` / branch `worktree-dev-wave-t2124-s1-epoch-historical`
一次資料: `docs/decisions.md` の D1387 (ユーザー裁定)、その前提 D1366。
背景: `output/insights/2026-09-01_t2060-current-closure-unknown/` (T-2060 が裁定へ送った所見)。

## この wave が変えたもの

`orchestrator/campaign/s1_report.py` の `_campaign_verifier_epoch_from_lock_bytes` 1 関数だけ。

1. 中央 gate へ渡す purpose を `CERTIFIED_ACCEPTANCE` から `HISTORICAL_RAW` へ移した。
2. 中央 gate は `HISTORICAL_RAW` のとき記録診断を無条件に返すため、その手前に
   `state == "E0"` の局所拒否を置いた。
3. その拒否が生きていることを、**実 production 関数を通る**負例で固定した。
4. 可用性 gate が実際に外れたことを、v2 lock + 現行閉包取得失敗の正例で固定した。

`replay.load_landscape`、`s8b_oracle_report` の epoch 証拠、`artifact_admission.py` の中央 gate、
`require_persisted_certified_commit`、拒否時の投影は**すべて無変更**である。

## 受理・拒否の変化は 1 点だけである

| 入力 | 変更前 | 変更後 |
|---|---|---|
| v1 lock (authority 不在) | `E0 / v1-authority-absent` で拒否 | 同じ |
| 正しい v2 / E1、現行閉包が取得できる | 受理 | 同じ |
| **正しい v2 / E1、現行閉包が取得できない** | **`E1-stale / current-closure-unavailable` で拒否** | **`E1 / recorded-closure` で受理** |
| malformed lock、記録 commit / blob 不整合 | purpose 判定前に拒否 | 同じ |
| exact 型でない purpose | `TypeError` | 同じ (中央 gate 呼出しを残した) |

この 1 行だけが D1387 が明示的に許した緩和である。段 3 のレンズ A が
`_require_verifier_epoch_for_purpose` の全分岐を列挙し、これ以外の緩和が混入していないことを
実物で確認した。

## 実測で分かったこと

### 依頼文が名指した file に対象機構が無かった

依頼文は「対象は `orchestrator/campaign/s1_direct_comparison.py` 周辺」と書いていたが、
同 file 1353 行に `epoch` の出現は **0 件**である。epoch gate は `s1_report.py:302-310` にある。
段 3 の両レンズが実経路でも確認し、`s1_direct_comparison.py` に epoch 判断の別形は無いこと、
同 module の非 dry-run producer が通す live binding 検証は certified producer admission であって
歴史 report reader の purpose とは別軸であることを示した。

### E0 拒否は、この wave まで実関数の位置で pin されていなかった

`test_s1_report.py` には module 全体に掛かる autouse fixture があり、
`_campaign_verifier_epoch_from_lock_bytes` を固定 E1 の lambda へ差し替えている。
既存の E0 負例 `test_non_e1_campaign_is_structured_and_wal_is_not_read` も、
同関数自体を monkeypatch して**合成した例外**を投げていた。
つまり「E0 なら拒否する」は、production の decode・v1 判定・E0 導出のどれも通らずに緑だった。

本 wave は同 node を実 callee 経由へ直した。dispatcher は block1 の lock bytes だけを
module import 時に保存した production 関数へ渡し、例外は実関数が投げる。
`_fixture` が書く lock は `{"fixture": "s1", "role": role}` だけで `schema_version` も
`authority` も持たないため、production decoder 上の正真正銘の v1 である。

### 親 brief の実測が 1 件、過大一般化だった (段 3 の両レンズが独立に捕らえた)

親は「`output/campaigns/` の 30 directory 全件が v1 lock。よって本変更は既存 30 件の
S-1 出力を 1 byte も変えない」と書いた。census の数値自体は正しかったが、結論が誤りである。

- S-1 report が読むのは 30 件ではなく、freeze と `ROLES` (4 件) と与えられた `--output-root` から
  `layout_for` が決める **4 campaign** だけである。
- `output_root` は repository 外の正規 root も受理する。そこに記録 binding が正しい v2 lock が
  あれば、変更前は拒否され変更後は受理される。**出力は変わる。**
- 再生成すれば `generated_at_head` が現 HEAD になるため、実装差分と無関係に bytes は変わる。

**訂正後の主張:** repo 内 official root の canonical S-1 campaign 4 件はいずれも v1 lock であり、
それらに対する epoch 判定は変更前後とも `E0 / v1-authority-absent` 拒否である。
tracked な `output/reports/s1_direct_comparison/report.json` が変わらないのは
**本 wave が producer を走らせないから**であって、再生成が byte-identical だからではない。

### scope 文字列を test に literal で書くと、稼働中の別 wave と衝突する

段 2 のプランは、拒否 reason の envelope 全体を exact dict で比較し、
`identity_scope` / `excluded_scope` を literal で固定することを提案した。
段 3 のレンズ B がこれを不採用と判定し、親が採用した。理由は 2 つある。

1. **検出力が増えない。** 既存 node はすでに `campaign_verifier_epochs["block1"]` を
   production 定数から取った値と exact dict で比較しており、投影の field 追加・欠落・値変更を
   殺している。
2. **稼働中の T-733 と衝突する。** T-733 は `CAMPAIGN_VERIFIER_EPOCH_SCOPE` の文言を
   exact 24 path から curated exact 62 path へ変えている。literal を書けば、
   正しい S-1 実装でも T-733 が着地した瞬間に本 node が落ちる。

編集面の重複検査 (32 worktree、committed 差分と未 commit dirt の両方) は
`artifact_admission.py` の重複を検出していたが、**本 wave が同 file を編集しない**ため
無害と判定していた。衝突は編集面ではなく **test に焼き込む値**の側から来る。
path の重複だけを見る検査はこの型を捕らえない。

### 残る検出力の穴 (実装せず裁定へ返した)

中央 gate の戻り値を、同じ `state="E1"` / `reason_code="recorded-closure"` を持つが
**別の有効な 64 桁 SHA** の `CampaignVerifierEpoch` へ差し替える変異は、
現在のテスト全部を通り抜ける。負例は E0 で先に終了し、他の S-1 node は autouse fixture が
実 callee を通さない。

これは本 wave が作った穴ではない (変更前は実 callee を通るテストが 1 本も無かったため
同じ変異が同じく生存した)。実在欠陥でもない。よって依頼文の
「仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」に従い実装せず、
裁定パッケージとして返した。閉じるには正例へ assert 1 本を足せばよい。

## 変異 matrix

probe (全件 `SURVIVED` 期待で観測 node を回収) → 本走の 2 段で回した。
どちらも `--runner-mode dispatch` / `--force-dispatch` の計算ノード経路。
runner argv は `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_s1_report.py -q -rf`。

- 束縛 HEAD: `f238bc6217cb32847758c1e47054ee9cbe919559` (実装 commit)
- baseline: `PASSED` / rc=0 / failed_nodes 0 件 / 32.0 秒
- 本走 spec sha256: `371f84f16f5bde86623b6d24e025f77cc95e8ac4e5bc1e78368fefc2beeccadc`
- probe spec sha256: `070f2fde2b89f48d9a3036edd0b37e1e432b09b831875f79aa6ad399d6a71304`

| # | 変異 | 結果 | 検出した node (完全集合) |
|---|---|---|---|
| M1 | 局所 E0 `raise` を削除 | KILLED | `test_non_e1_campaign_is_structured_and_wal_is_not_read` |
| M2 | purpose を `CERTIFIED_ACCEPTANCE` へ戻す | KILLED | `test_v2_epoch_gate_is_historical_when_current_closure_is_unavailable` |
| M3 | 中央 gate 呼出しを削り `return recorded.diagnostic` | KILLED | 同上 |
| M4 | E0 で `ArtifactAdmissionError` を投げる | KILLED | `test_non_e1_campaign_is_structured_and_wal_is_not_read` |

本走 summary: `KILLED 4 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0 / PARSE_ERROR 0`、
`matching 4 / registered 4`。**4 件とも 1 node ずつで検出**され、単一理由性 (同じ入力を拒否する層が
前後に無く、赤理由が 1 つに絞れること) を probe の観測で実測により確かめた。

段 4 の事前登録は plan が挙げた 5 件目 (`_rejected_epoch_projection` の field 変更) を外して 4 件で
凍結した。同変異は本 wave の変更箇所ではなく既存 node がすでに殺すため、DW-M01 の単一理由性を
満たさない。段 6 のレビュー B が同じ判定を独立に出した。

erratum (段 6 で判明): 段 4 で凍結した「最初に赤になる assert」の**散文**が M1 / M2 で不正確だった。
M1 は WAL 読取禁止の assert が先に発火して `schedule_ledger_invalid` へ変換され、
最初に赤になるのは `reason["code"]` の比較である。M2 は 4 assert のいずれでもなく、
実 callee 呼出し行での未捕捉 `CampaignVerifierEpochRejected` で node が error になる。
**期待 node の完全集合は不変**であり、本走はその凍結集合と完全一致した。

## 親の実測 (受入以外)

- 焦点走 `orchestrator/tests/test_s1_report.py` — 27 passed (248.20 秒)
- 焦点走 `orchestrator/tests/test_ccbench_spawn_sites.py` — 18 passed (20.06 秒)
- 変更・新設した 2 node の単独走 (`-k "historical or non_e1"`) — 2 passed (75.33 秒)
- 三軸語の機械走査 — 権威 CLI (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`) で
  rc=0。本 wave の新規 file に conjunction hit 0 件、defang 不要。
- AI provenance 全史監査 — 新規違反なし

## 一次資料

- `s1-brief.md` — 段 1 brief と親の実測 (F-A〜F-G)
- `s4-adjudication.md` — 段 4 裁定、plan v2、変異事前登録、gate の禁止と通る正例
- `s6-adjudication.md` — 段 6 裁定 (レビュー 2 本)、erratum
- `verbatim/` — 子の出力逐語 (plan、相談 2 本、実装、レビュー 2 本)
- `mutation-*.json` — 変異 spec と走行結果
