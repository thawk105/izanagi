---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t435-8c-generation-budget
seq: 1
title: [T-435] 8c 事前登録の世代予算条項の改訂内容を確定し、決定先行 wave として land した (docs のみ、branch worktree-dev-wave-t435-8c-generation-budget、実装差分ゼロのため変異 matrix は該当なし)
---

## 本文

- **起票時の stale はもう存在しなかった。** 2026-08-04 に「多世代化の条件を『還流設計の裁定』と
  だけ書いている」として起票されたが、2026-08-15 の `d0fc008c` が §2 / §4 を `G=2` 固定へ
  書き換えて消していた。裁定は 2026-08-25 に再確認されているので有効だが、直す対象は当時と別物である。
  現在残っているのは「正確に `G=2` は機械強制されず起動形の責務である」という、
  D443 (2026-08-16) 以降は偽になった主張のほうだった。
- **段 3 レンズ A が親の暫定裁定を D439 違反として撃ち落とし、wave の形が変わった。**
  親は g11 の `ruling_reference` に D443 を引くつもりだったが、D439 は
  「世代記録の裁定参照に手続の決定を代用する」を却下済みで、理由も
  「その決定は当該改訂の内容を承認していない。改訂の provenance が承認元へ到達しなくなる」と
  一致していた。`docs/decisions.md` に本裁定を記録した決定は無いことを確認し、
  D439 形 2 (決定先行 wave + 改訂 wave) を採って本 wave を決定先行 wave に変えた。
  D443 代用は機械検査を通ってしまうぶん、手続きの空洞化にあたる。
- **両レンズが独立に「保証の射程が強すぎる」を出した。** D443 が束縛するのは
  manifest を伴う registered 起動の**宣言 generation budget** だけで、実際の完遂世代数ではない
  (D443 決定 (4) が partial を受け入れる)。unregistered exploratory 経路にも及ばない。
  親の実測見出しと段 2 プランはこの限定を落としていた。
- **レンズ A: 改訂 proof が条件 11 の検査外の機構を充足根拠に見せる。** 条件 11 の
  `required_evidence` は supervisor と第二層射影の 2 種だけで、D443 の 3 機構がある
  `trial_registry.py` を含まない。明記しない `proof` は束縛されていない事実を昇格させる。
- **レンズ A: 「閉じた還流を強制する」への言い換えは自己矛盾。** 同文書 §4 が
  「閉じているのはキー集合であって情報量の遮断ではない」と自ら記録している。
- **レンズ B が親の pin 閉包の穴を実測で埋めた。** 親は `proof` の逐語だけを検索していたが、
  証拠契約全体の意味 hash が `test_current_evidence_contract_hash_is_frozen` と
  `test_evidence_contract_hash_accepts_non_path_controls` の 3 parametrize に literal で
  pin されており、契約を変えると 4 nodeid が赤くなる。生成閉包として同じ変更単位に入れる。
- **親の記述を 2 件撤回した。** (1) 段 1 brief の成果物影響「層3 材料レポートと proof chain が
  その文言を引く」は静的検索で consumer が存在せず、根拠が無かった。改訂の実効性は
  「監査者が読む現況表示の訂正と、その訂正時点を g11 が不可逆に記録すること」に限られる。
  (2) 親は `evidence_contract_sha256` を raw bytes hash と実測に書いたが、実装は strict JSON を
  canonical 化して domain prefix を付ける意味 hash であり、空白・key 順だけの変更では動かない。
- **親が一度「台帳から落ちている」と報告した [T-315] は誤りだった。** 2026-08-15 の
  棚卸し (entry 555) で正規に見送られ、`docs/phase3.md` の見送り台帳に再訪条件つきで実在する。
  fold の保存則は破れていない。再訪条件 (同一ファイルを触る wave への相乗り) は
  本 wave も後続 wave も満たさないため見送りのまま置く。
- 段 2 プランは g11 の全 field 予測値を出し、レンズ B が production parser で再現して一致を確認したが、
  親は確定値として採らない。決定 (2) の限定で改訂文が変わるため hash は再計算になる。
- 実装差分ゼロのため B-057 の変異事前登録は該当なしとして明示的に見送った。
- 段 8 は F39 と F154 の再発を記録した。F39 は「凍結成果物のファイル全体の hash を pin する
  テスト」が pin 閉包から落ちた件、F154 は「コードで実測した制約の由来決定を引かなかった」件で、
  いずれも既存 F と同型のため新しい F は採らず再発として追記した。
  `docs/dev-wave/**` と command 入口はいずれも byte 予算に余裕が無く
  (`.claude/commands/dev-wave.md` は上限 9,520 に対し実測 9,520)、本文追記はしていない。
- 子の工数: codex 3 本 (plan 1・consult 2)。すべて `launcher_rc=0` / `evidence_status=complete`。
  model call は 50 / 38 / 57、wall は 824 / 704 / 1352 秒。

## 次の一手差分

### 更新

- [T-435] **P2・裁定済み (2026-08-25 /rulings 全件、推奨どおり) → 決定先行 wave 着地済み、改訂 wave 待ち**:
  改訂の内容・変更単位・限界は {{D:s8c-generation-budget-reprereg}} で確定した。残るのは実行だけである。
  後続 wave が同一 commit で次を land する。(a) `docs/phase3-8c-preregistration.md` の §6 条件 11 と
  §6「衝突 (b)」の「残る欠落」段、(b) `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json`
  の条件 11 `proof`、(c) `docs/phase3-s8c-autonomous-trial-runbook.md` の 3 箇所、
  (d) `orchestrator/tests/test_s8c_preregistration_core.py` の証拠契約 hash pin 4 nodeid、
  (e) `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g11.json`
  (`prepare-revision` で発行し `ruling_reference` は {{D:s8c-generation-budget-reprereg}})。
  `DECIDER_VERSION` は v6 のまま bump しない。
  base: e39bfbdea012c20c8feefb2db834be40378a810c1cea630096df7056a8c8f195
