---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-15
wave: dev-wave-t856-verified-oracle-verdict
seq: 1
title: judge_combined を封印 token 専用にし oracle 側の未封印経路を閉じた — 恒真な検査を 5 件除去して再導出へ畳み、生存した変異 1 本が検出力の穴を実測で暴いた (コード、branch worktree-dev-wave-t856-verified-oracle-verdict)
---

## 本文

- 起点は 2026-08-12 /rulings の [T-856] 択 (a) 確定。judge 側 oracle verdict が未封印で、
  schema と holdouts の形だけ満たす手書き verdict が combined 結論へ到達できる状態だった。
  裁定は「既存 `VerifiedPrediction` pattern の複製で安い」という見立てだったが、
  **段 2 のプランがこの見立てを否認した** — 型と manifest sha の照合だけでは、正しい公開 sha を
  転記した median 改竄が通る。D304 が既に決めた「公開 pin との比較は転記で満たせる」と同型である。
  親は再導出まで行う案へ裁定を差し替えた ({{D:oracle-verdict-seal-by-rederivation}})。
- **複製元も差し替えた。** 裁定文が挙げた `VerifiedPrediction` は素の公開 dataclass で直接構築でき、
  封印穴を一型先へ移すだけだった。同じ s8b 族の `VerifiedManifest` は closure の seal object で
  直接構築を機械拒否する。択 (a) をより強く満たす同方向の実装であるため、後者を採った。
- **段 3・段 6 の敵対レンズが計 4 巡で 20 件を出し、うち production の実穴 5 件を閉じた。**
  最重要は次の 3 型で、いずれも「反射操作を使わない通常の Python 操作」で成立していた。
  (a) 発行済み token の内包 dict を item 代入で書き換えると combined 結論を任意に変えられる、
  (b) `__eq__` が常に真を返す `str` subclass で spec 束縛を迂回できる、
  (c) `__getitem__` を上書きした `dict` subclass で canonical hash を一致させたまま
  schedule 射影に偽値を読ませられる。境界の引き方を {{D:seal-trust-boundary-by-reflection}} で確定した。
- **恒真な検査を 5 件除去した。** loader 後の schema 再確認・marker 再確認・top-level exact key・
  holdouts 構造検査は全文書 canonical 比較に包含され、verifier 内の `VerifiedManifest` exact-type
  検査は `project_verified_manifest_schedule` の同一検査に包含される (親が実測で確認)。
  冗長 gate は変異の単一理由性を壊すため置かない。
- **refuted:** 親 brief の「certified 選択の値そのものが変わる」は過大だった。combined verdict を
  読む tracked な下流 consumer は現行 tree では同 file の CLI だけで (8b 本走が未実施で下流が
  未配線)、実際に変わるのは `8b-combined-verdict/v2` の 3 条件・結論値・`oracle_floor_exceeded` である。
  レンズ B が指摘し、親が受け入れて訂正した。
- **refuted:** 親が事前登録した変異 M01 は当初「型 guard だけ除去」で、それだけでは
  `oracle.document` が `AttributeError` になり受理集合が広がらない偽の KILLED になるところだった
  (段 6 の 2 レンズが独立に指摘)。guard 除去と unwrap 緩和の 2 置換累積へ再登録し、
  親の in-memory probe で「生 `OfficialVerdict` だけが fail-open になる」ことを実測してから登録した。
  duck-typed wrapper 側は別変異 (M05) を新設して 1 対 1 に分離した。
- **scope 外と裁定して実装しなかったもの 3 件。** (1) observations 層の封印 — oracle と
  observations を同時に偽造する攻撃は残るが、D304 が観測側 seal を「権威の設計判断を伴う」として
  明示的に scope 外に置いている。(2) `_write_create_only` の書き込み途中失敗で partial output が
  残る件 — 本 wave が触っていない既存 helper。(3) 反射操作経由の迂回 — 明記済みの信頼境界外。
  いずれも新規タスクとして起票を諮る。
- **エージェント工数と異常:** codex 子 11 本 (plan 1・consult 2・author 1・review 4・fix 3)。
  異常 3 件。(iii) 変異 scratch を `rm -rf` で消したところ、git の worktree 登録に
  「登録済みだが実体が無い」残骸が残り、次の変異走が rc=125 で起動前に落ちた。
  これは land を全 wave 分止める型でもある。`git worktree prune --dry-run` で対象が
  自分の 1 件だけであることを確認してから prune した (他 wave の worktree 10 件は無傷)。
  `mutation_worktree.py` は中断時に container を保持する設計なので、後片付けは
  `rm -rf` でなく prune を伴う必要がある。
  残り 2 件は次のとおり。(i) 段 6 レビュー 1 本が `evidence_status=invalid` で不受理。子は完走して
  8,388 bytes 相当の所見を出していたが、成果物として数えられないため保全して親が独立に裏取りし、
  以後の子 prompt に出力量上限を明記した。以後の 4 本はすべて受理された。
  (ii) 最終焦点レビューの 1 本が上流分類器に「サイバーセキュリティ上のリスク」として弾かれ
  出力ゼロ・rc=1 で終わった。防御目的を前面に出し攻撃語彙を減らした prompt で再投入した。
- **codex 子は 3 回とも `tools/run_tests.py` を走らせられなかった**
  (`Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1`、rc=16)。
  親の bounded local は同条件で通る。子は「実装済み・未実走」と正しく申告し、実測はすべて親が行った。
- 実測: wave 前 baseline (`test_s8b_verdict.py` + `test_s8b_oracle_manifest_contract.py`) =
  62 passed。最終形の焦点走 (上記 + `test_s8b_oracle_artifacts.py` + `test_s8b_oracle_judge.py`) =
  **131 passed / 5.39 秒** (Pegasus 計算ノード、tip `e418f9c1`)。
  なお login ノードの bounded local は他 wave が memory 予算を占有すると
  `memory.max / memory.oom.group を走行中に attest できない` で止まるため、
  焦点走は計算ノードへ dispatch した。
- 変異: 固定 commit `e418f9c1` の使い捨て worktree で 6 変異を dispatch 実行し、
  **6/6 KILLED・SURVIVED 0・MISMATCH 0**。M01〜M03・M05・M06 はそれぞれ**ちょうど 1 本**の
  テストだけを落とし、単一理由性が実測で成立した。M04 (正例) だけ 3 本落ちる
  (いずれも正当な token 発行を前処理に含むため)。期待 node は 2 度、実測した失敗集合へ
  再登録した (`DW-M08`)。probe 台帳を消さずに残す (`DW-M02`)。
  台帳は `output/insights/2026-08-15_t856-verified-oracle-verdict/`。
- **変異が 1 本生存し、それが検出力の穴を実測で見つけた。** 最終レビューが
  「`judge_combined` 側の plain JSON 型再検査には専用の実効性テストがない」と指摘したのを、
  親は断定せず M06 を `expected_status=SURVIVED` で走らせて確かめた。結果は **SURVIVED**
  (落ちたテスト 0 件) で指摘は real と確定。**production に欠陥は無く、欠けていたのは
  検出力だった** — canonical hash を保ったまま consumer が読む値だけを変える
  `dict` subclass を、型検査は拒否できるが、それを固定する回帰テストが無かった。
  テストを 1 本足して M06 を KILLED にした (production は変更していない)。
- **受入全走の数値を本文へ書けない構造がある。** `dev_wave_land.py` は wave tip と tested tip の
  完全一致を要求するため、受入は本記録 commit を含む tip で回すしかなく、その結果を後から
  本文へ書き足すと tip が変わって受入自体が無効化される。したがって本エントリの受入証拠は
  land へ渡した受領証であり、受領証が無ければ land は main を 1 bit も進めない。
  数値を本文に載せたい場合は受入を 2 走させる必要があり、lease の TTL を超えるため採らなかった。

## 次の一手差分

### 完了

- [T-856] `VerifiedOracleVerdict` を導入し `judge_combined` を封印 token 専用にした。
  封印は再導出と canonical 型厳密比較で実質化し、5 変異すべてが単一テストで KILLED。
  remaining: none
  base: d4a9997bf5dbdfbdd89059d57d23fa99780bfc4322734e2538122a9c33512791

### 新規

- {{T:oracle-observations-seal}} **P2・新規 (ユーザー裁定待ち)**: oracle verdict の封印は
  単独文書の改竄を閉じたが、observations と oracle を同時に偽造する経路は残る。D304 が
  観測側 seal を権威の設計判断として scope 外に置いているため、本 wave では実装していない。
  択 = (a) observations 層にも封印 token 境界を新設する / (b) 現状維持で主張を
  「単独 oracle 改竄まで」と限定し続ける / (c) [T-657] 権威束設計へ合流させる
- {{T:write-create-only-atomicity}} **P3・新規**: `_write_create_only` は `open("x")` で
  inode を作った後に書き込みが失敗すると truncated JSON を残し、次回実行も create-only の
  `EEXIST` で拒否される。temp へ書いて `os.rename` する二段化で閉じられるが、
  共有 helper のため consumer 全体の受理集合に触れる。本 wave は scope 外とした
- {{T:codex-child-cannot-run-tests}} **P2・新規**: codex 子の sandbox から
  `tools/run_tests.py` が走らない (local 予約台帳を更新できず dispatch へ倒れ、
  `qstat -Q preflight rc=1` で rc=16)。本 wave で 3 回、別 wave でも同型が観測されている。
  子が実測できないと段 5・6 の「緑には実走 nodeid を併記」が常に親へ集中する
