# 段 1 brief — [T-659] activation 発行→配備の分裂窓 (設計 wave)

## scope
- 成果物は**裁定パッケージのみ** (quiesce/drain + atomic deployment の最小設計案と推奨)。本番コード・テストは編集しない (ユーザー指示。実装は [T-657] の land 後の次弾)。
- 置き場: `output/insights/2026-08-09_t659-activation-deploy-window/` + spool fragment (worklog)。段 4 で「実装しない」を裁定し 4→7→8→9。変異免除、受入全走は実施。

## 確定済みユーザー裁定 (前提)
- [T-657] = T-139 裁定後、前提 2 件 (silo 歴史解決・floor protocol 再発行) を揃えてから活性化 (未活性、head=1 のまま)。
- [T-658] = 見送り (receipt の全書込み口配線は防御的堅牢化)。本 wave で復活させない。
- [T-627] = land 済み (世代遷移述語 = (generation, contract hash) 同一入力束縛、entry 318)。
- 研究最優先: 防御的堅牢化は既定で見送り、最小形。

## 実測済みの事実 (probe_split_window.py、temp copy 上、live 不変)
- 発行後・head 未更新: fresh load は `activation head serial 不一致: expected=1 observed=2` で fail-closed (A)。
- head 更新後: 受理 (B)。逆向き窓 (定数先行・record 未配備) も fail-closed (C)。**fail-open 経路なし**。
- record (live directory) と head 定数 (env_contract.py) は**どちらも git tracked** — 同一 commit に収めれば git 配備は commit 粒度で atomic。窓は (i) 発行 tool 実行〜commit の working tree 上、(ii) commit 後〜全 process 再起動、の 2 つ。
- 既存 process は `_AUTHORITY_SNAPSHOT` (PID 単位 cache、fork 時 reset) で旧 head 続走。consumer は campaign 層のほぼ全 driver + t126 driver + probe。
- 発行 tool は handoff 文で「同一 commit + 全 process 再起動」を人間に指示するのみ。機械強制なし。

## 提案の骨子 (P 採番 = 親 provisional、攻撃対象)
- (P1) atomic deployment: 発行 tool が head 定数の書き換えまで同時に行い (source edit)、「発行済み・未 commit」状態を単一 tool 実行内に閉じる。commit は従来どおり人間/親。tracked 2 点の同一 commit は check (ai-provenance 同様の事後監査 or pre-commit 検査) でなく**手順書 + 発行 tool の出力照合**に留める (最小形)。
- (P2) quiesce/drain: 機構を作らず**手順型**を既定とする — 活性化手順に「発行前: 走行中 campaign/harness の不在確認 (受入 lease と同型の排他 + pgrep)、配備後: 全 process 再起動の確認」を置く。receipt には activation_serial が既に載る ([T-627] 系) ため、混在 evidence は provenance で識別可能 — land 側の機械拒否は実需 (混在の実害) が出るまで見送り。
- (P3) 順序: 最小実装 ([P1] tool 改修 + runbook 手順) は [T-657] の実活性化より**前**に land する必要があるかを裁定に含める (ユーザー指示は「[T-657] の land 後の次弾」— [T-657] land = 裁定・前提整備の land であり、実活性化 = record 2 発行の前に本機構を入れる読みで整合するか要確認)。

## 実測訂正 (erratum、段 2 投入後の親追測。段 3 レンズはこちらを正とする)
- (P2) の「receipt には activation_serial が載るため混在 evidence は provenance で識別可能」は**不正確**。`activation_serial` は process-local receipt (`AuthorizedContract`) と `execution_guard.py:75-78` の突合までしか届かず、**durable evidence には載らない** ([T-658] 見送りの帰結)。
- **[erratum 2 で再訂正、段 2 プランの指摘を親が一次資料で確認済み]** durable 側の世代識別子は execution receipt の `contract_sha256` (execution_guard.py:204-222 の build_receipt) である。`evidence_contract_sha256` は s8c 事前登録 evidence 文書の hash (s8c_preregistration.py:37-40) であり env 世代識別子ではない。事後識別が効くのは「契約が実際に変わった env の、receipt を持つ成果物」に限られ、据置 env (D245 が許す) や receipt の無い書込み口は activation state の新旧を区別できない。

## 追補 2 (段 2 走行中の親観測。段 3 レンズはこちらも正とする)
- **並行 wave `dev-wave-t657-t660-g2-activation` が稼働中** (brief = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s1-brief.md`)。[T-657] の実活性化 (record `00000002.json` 発行 + head 定数の同一 commit 更新 + 既存テストの新 head 追従 + [T-660] 検出力確認) を実装しており、「活性化 commit・silo 解決・floor 再発行・pin 更新は同一 wave branch で完結してから land」を不変条件に持つ。
- 帰結 1: **(P3) は事実で解決** — 初回活性化は本設計の機構なしに手動の同一 commit 手順で行われる (ユーザー逐語「実装は [T-657] の land 後の次弾」と整合)。本設計の対象は **serial ≥ 3 以降の将来の活性化** (次の較正世代、floor 再発行サイクル等) の反復可能な手順/機構である。
- 帰結 2: 裁定パッケージは t657-t660 wave の手動手順を「1 回目の実測」として引用し、そこで露出した手間・危険点を設計根拠にできる (land 後に確定)。
- 帰結 3: 本 wave の成果物は t657-t660 の編集面 (silo_ladder_rung1 系、env_contract 系テスト) と交差しない。land 順は lease と fold が直列化する。段 2 プランの P3 節は本追補で部分的に stale — 段 4 で親が supersede する。

## 不変条件
- fail-closed 方向を弱めない (規律 2)。head の exact pin (serial + state hash) を保つ。自動 reload・「観測した head を信じる」系の設計は不採用。
- 診断の構造化 (expected/observed) を保つ (規律 3)。
- [T-658] 見送り裁定・D60 (role runtime launcher の別物性、entry 319) と矛盾する案を出さない。

## 成果物影響 (DW-G05)
- 実装しない/放置の場合: certified 選択・受理集合・数値は現時点で不変 (activation 未発生)。[T-657] 実活性化の当日に、fresh fail-closed と旧 head 続走の混在を人手だけで捌くことになり、活性化前後の evidence 帰属は receipt の serial でしか追えない。

## 分割方針
- 段 2: codex read-only 1 本がプラン起草 (file:line 粒度、上記 P1〜P3 への対案含む)。
- 段 3: 敵対 2 本 (sol / luna)、レンズ分離: A = 設計の正しさ攻撃 (fail-open 化・窓の見落とし・pin 弱化)、B = scope/最小性攻撃 (防御的堅牢化への肥大、既裁定との衝突、docs/byte 予算)。
- 受入環境: Pegasus、runbook の受入 lease + dispatch recipe (worklog 319 と同一作法、背景投入)。
