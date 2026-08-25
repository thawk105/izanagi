---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1726-freeze-rederive
seq: 1
title: [T-1726] 受入 receipt verifier を ratified legacy freeze の条件再導出へ昇格し、[T-1727] の世代交代を裁定した (コード + テスト、branch worktree-dev-wave-t1726-freeze-rederive、変異 matrix = baseline PASSED・5/5 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- **段 3 の敵対相談が親 brief の成果物影響を覆した。** 親は「標準 verifier の緑だけで受理され
  論文 B-3 の certified 選択を決めうる」と書いたが、現 checkout では全 receipt が構造的に
  `certifying=false` へ固定され、`layer3_report` は `certifying is True` を要求する。
  誤値 receipt が現在の成果物の値を決める到達可能経路は無い。穴は潜在的で、
  certifying を有効化する将来世代で発火する。裁定 (昇格する) は覆らないが、記述を訂正した。
- **段 2 のプランは実装不能だった。** ratified legacy freeze を検証対象 repository から読む設計は、
  凍結 artifact を複製しない正当な receipt 生成経路を `legacy-read` で拒否する。
  レンズ B が編集禁止の正例を名指しして実証した。権威 root を verifier 自身の checkout へ
  分離して回避した ({{D:receipt-freeze-rederivation-authority}})。
- **追加予定の照合 1 本が恒真だった。** レンズ A が、expected arm binding digest の照合は
  既存 gate と expected content digest 一致から決定論的に従うと指摘した。足さない裁定にした
  ({{D:receipt-gate-no-tautological-assert}})。謳うだけで発火しない assert は
  変異検査で偽の KILLED を生む。
- **段 6 レビュー A の最重 must-fix は本 wave 由来でなく、consumer にも届かなかった。**
  `VerifiedAcceptanceReceipt` は gate 外で生成できるが、唯一の consumer が通す
  `require_current_verified_receipt` は再検証結果を返すため偽造した中身は届かない。
  親が一次資料で確認し scope 外へ回した。
- **段 6 レビュー B の must-fix は 2 分割した。** 例外契約の破れ (import 失敗が
  `AcceptanceReceiptError` でない型で漏れる) は指定 2 file で閉じるため採用。
  副作用のない軽量 authority leaf の新設は編集面を超えるため裁定パッケージへ回した。
  親の実測では module 単体 import は 0.034 秒・stdlib のみで軽量契約は保たれており、
  重い連鎖は v2/v3 検証時だけの 0.334 秒だった。
- **焦点再レビューが fix 1 巡目の F1 を partial と判定した。** 条件の数値は独立に固定されたが
  descriptor 全体が固定されておらず shared-oracle が残っていた。
  descriptor は 10 値の小さな構造だったため、全体を literal で等価比較させる fix 2 巡目で closed にした。
- **[T-1727] を裁定した。** v4 へ上げず、旧 v2/v3 artifact を固定 V1 authority の legacy として
  読み続ける。明示的失効は採らない。3 条件付きで {{D:receipt-legacy-generation-conditions}} に記録した。
- 子の工数: codex 9 本 (plan 1・consult 2・author 1・review 2・focus 1・fix 2)。
  すべて `launcher_rc=0`・`gpt-5.6-sol`・`effort=xhigh`。
  段 5・段 6 の実装子と fix 子はいずれも pytest を実走できず (Pegasus dispatch `rc=16`、
  login node の cgroup 上限)、実走はすべて親が代替した。
- 変異 matrix の運用で 3 件詰まった。いずれも変異と無関係である。
  (1) 共有木の事後検査が `rc=125` — 観測 root に共有 checkout が入り走行中に別 wave が触れた。
  `--source-repo` へ独立 clone を渡して構造的に断った。
  (2) その clone の submodule 初期化が `protocol.file.allow` の既定で拒否された。
  (3) 収集段が `rc=16` — 同時刻の `qstat -Q` は gen_S に 101 件 (QUE 35 / RUN 47 / HLD 17) で、
  scheduler 混雑だった。中断した走行の container が fresh 走を塞ぎ、台帳未作成のため
  `--resume` も使えず、新しい `--scratch-root` で再投入した。
- 逐語と実測は `output/insights/2026-08-26_t1726-freeze-rederive/`。

## 次の一手差分

### 完了

- [T-1726] `s8c_acceptance_receipt.py` を ratified legacy freeze から条件を再導出する
  verifier へ昇格し、positive control (自己整合した誤値 descriptor の拒否) を置いた。
  remaining: none
  base: fbb4816f772753d99e88306dfe23f4eeec53d9d0a6822c2bf821a024c35803a0
- [T-1727] schema 世代交代を裁定した。v4 へは上げず、旧 v2/v3 artifact を固定 V1 authority の
  legacy として読み続ける。条件は {{D:receipt-legacy-generation-conditions}}。
  remaining: none
  base: 423d73a4257755ea3d7770c30fd3d6ddd48548066b2ba1de59e3c8f4fc9fd78b

### 新規

- {{T:receipt-v4-before-authority-change}} **P2・新規**: 受入 receipt を v4 へ上げ、
  freeze の path・hash・generation を serialized binding へ載せる。
  {{D:receipt-legacy-generation-conditions}} の条件 3 により、
  `V1_FREEZE_SHA256` の差し替え、`HOLDOUTS` / `DERANGEMENT` の改訂に**先立って**必要になる。
  巻き込む pin は `test_reflux_originless_compatibility.py` の receipt key 集合 baseline と
  `test_trial_registry.py` の receipt 期待値。
- {{T:receipt-measurement-head-binding}} **P2・新規**: receipt が名乗る `measurement_head` を
  ancestor / registry 記録 head へ束縛する。現状は標準 verifier が受け取った値をそのまま
  再導出の基点にする。条件再導出は measurement_head に依存しないため誤条件は通らないが、
  レポート・台帳の参照が無関係な commit を指しうる。
- {{T:receipt-empty-cell-descriptor-proof}} **P2・新規**: `cells=[]` と C02 reason 保持の
  組み合わせで、実行 descriptor が不在のまま expected digest の自己申告を verified receipt に
  できる構造を塞ぐ。`test_partial_receipt_cannot_drop_c02_reason_without_descriptor_proof` の
  設計意図と一体のため、受理集合の形を含めて設計し直す必要がある。
- {{T:shared-arm-authority-leaf}} **P2・新規**: producer / issuer / verifier が共有する
  副作用のない軽量 authority leaf を新設し、`trial_registry` の受入経路に残る
  legacy freeze との断絶を閉じる。併せて `s8c_acceptance_receipt` が v2/v3 検証時に
  引く 36 module の import 連鎖を切る。
