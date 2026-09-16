# [T-2125] 段 1 brief — 歴史閲覧が現行 policy 照合で塞がる問題

## 研究前進

論文図・材料レポートの再生成経路 (`tools/plotting/plot_s1_9pair.py`、
`orchestrator/campaign/p2_2_report.py`、`orchestrator/campaign/layer3_report.py`、
`orchestrator/campaign/b10_backoff_static_tail_formal.py`、`orchestrator/critic/digest.py`、
`orchestrator/critic/online_digest.py`、`orchestrator/campaign/replay.py`) は、過去の campaign を
`CampaignReadPurpose.HISTORICAL_RAW` で読む。ところがこの閲覧は、campaign lock に記録された
build admission policy が**現行 policy と等しいこと**を要求している。policy の識別子には
ccbench の stock pin と generator / review 登録簿が入っているので、pin を進めるか生成器を 1 つ
登録するだけで版が上がり、その前に記録された v2 campaign は purpose を問わず読めなくなる。

**完了判定。** 旧 policy を記録した v2 campaign が `HISTORICAL_RAW` で読め、
`CERTIFIED_ACCEPTANCE` では従来どおり拒否されることを、挙動テストが両向きで固定する。

## scope

`orchestrator/campaign/artifact_admission.py` の post-policy 経路で、`HISTORICAL_RAW` のときだけ
照合先を「現行 policy」から「その lock に記録された policy」へ替える。attempt topology 検証にも
記録 policy を渡す。歴史 view の診断へ、`current-closure-unavailable` とは**別の識別子**を出す。

## scope 外 (実装しない)

- certified 経路の受理集合の変更。
- どの消費者がどの purpose を宣言するかの再分類 (**D1366 がユーザー裁定を経た別 wave と定めている**)。
- [T-2483] の exact-62 歴史 grammar (別 module `campaign_lock.py`)。
- 仮想リスク向けの gate・検査・台帳・一般化の追加。

## 不変条件 (これを崩す案は書かない)

1. `CampaignReadPurpose.CERTIFIED_ACCEPTANCE` の受理集合を 1 件も広げない。certified 側は
   現行 policy との一致要求をそのまま維持する。
2. **「読めるようにすること」を certified への昇格に使わない (絶対規律 2)。** 歴史 view は
   `require_certified_campaign_view` の exact 型 gate で certified consumer 境界を通れないままとする。
   `_require_verifier_epoch_for_purpose` の「historical epoch cannot enter certified acceptance」も
   そのまま残す。
3. 構造検査を 1 つも落とさない。`wal._validate_attempt_topology`、`wal.validate_trigger_bindings`、
   `_validate_trigger_provenance`、build_start source evidence 照合、lock/WAL bytes の再読照合は
   歴史閲覧でも全部通す。**替えるのは比較先だけである。**
4. 記録された policy をそのまま信じない。記録側にも exact な形 (現行 policy と同じ key 集合、
   同じ `schema` literal) を要求する。任意の dict を素通しにしない。
5. flag / boolean 引数による緩和にしない。purpose は decode より前に exact enum で確定済みであり、
   その enum だけが分岐の根拠になる (D1653 の必須条件と同型)。
6. v1 lock の downgrade 拒否 (`campaign-lock/v1 with build_admission is a post-policy downgrade`) と
   overlay 拒否は 1 byte も変えない。

## (P1) 親の provisional 裁定 — 段 3 の攻撃対象

**「記録された policy preimage は現行 policy と等しくなくてよいが、現行 policy と同じ key 集合と
同じ `schema` literal を持つ exact な形であることを要求する」。**

緩めすぎ (任意 dict を通し、偽造 lock が弱い policy を名乗れる) と、締めすぎ (実質的に現行一致を
要求し直して何も解けていない) の両側から攻めること。

## 成果物影響 (DW-G05)

放置すると、次に stock pin が前進するか generator / review 登録簿へ 1 件足した時点で、その前に
記録された v2 campaign を読む図・材料レポートの生成器が一斉に停止し、過去の測定を材料レポートへ
再投入できなくなる。

## 分割方針

段 2 plan 1 本、段 3 敵対 2 レンズ、段 5 実装子 1 本 (編集面が 1 module に収まる)、
段 6 レビュー 2 本 + fix。
