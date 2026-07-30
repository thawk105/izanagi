# 6b64d21 forward-only 是正 — 段 4 裁定・plan v2・変異事前登録

## 裁定

- plan v1 の旧 tuple は失効。元 event の観測値へ固定し、後日命名になる `scope` は採用しない。
- exact payload は `target=6b64d21753d2cfc790f80caba29df7a40fef3072; product=claude; model=claude-opus-5; reasoning=xhigh; role=integrator`。
- 一回限りの対象専用 singleton とし、dict / registry / CLI / env で対象を追加できる一般制度にしない。
- correction の一意性 domain は selected revision set。別 branch の候補は同じ監査集合へ合流した時だけ重複になる。
- `rev-list --reverse` の順序は根拠にせず、membership は set、lineage は strict `merge-base --is-ancestor` で判定する。
- correction trailer は物理 1 行の raw value と隔離 canonical parser value の双方を exact 比較する。
- target の missing finding 1 件だけを抑止し、CAB、別 commit、correction commit 自身の全 finding は残す。
- rc=0 でも `forward-corrected=1 target=<sha> correction=<sha>` を出し、native-valid と区別する。
- `--message-file` は current HEAD の通常子を仮定した preflight と表示し、commit 後 history 監査を権威とする。
- target の combined resolution は docs 3 pathだけ。実装 bytes は parent commit で Codex author 監査済みで、
  correction は target message を合成せず D95 gate の既存 path/message 意味論を変えない。
- `MERGE_RC=0` は tail の rc なので根拠から除外。merge 成立は 2-parent object、tuple は raw event fieldで固定する。
- 原 session ID は tracked evidence へ残さず、timestamp・sanitized field・event line SHA-256を記録する。
- correction の根拠 artifact、新 D、policy、failure 再発、phase/worklog を同 wave の監査対象に含める。
- T 番号は land 時に D70 で再走査し、停止中 consumer は branch / handoff path で名指しする。
- ambient Git view / replace refs の一般 hardening は既存 checker 全体の別問題として scope 外。

## 実装 plan v2

1. `tools/check_ai_provenance.py`
   - incident 固有の key / target / exact payload を immutable literal singleton として追加する。
   - raw key 候補を物理行で抽出し、候補時だけ隔離 canonical parser を呼ぶ。
   - commit ごとの通常 finding と correction finding を先に構造化し、selected set 全体で
     exact 1 candidate、target membership、strict descendant、target 実欠落、correction commit
     通常 green を連言にする。
   - 連言成立時だけ target の exact missing finding を除き、forward-corrected record を保持する。
   - correction candidate を含む message-file は exact raw/canonical、target object、HEAD ancestry、
     target 実欠落、既存 candidate 不在を preflight し、限定 status を出す。
2. `orchestrator/tests/test_check_ai_provenance.py`
   - production literal pinを置き、合成 SHA monkeypatchだけの自己整合を避ける。
   - 2-parent target fixtureで `T^!`、`C^!`、`T^1..C`、sibling merge、duplicate、merge-side findingを固定する。
   - continuation、body+valid trailer、field drift、scope追加、unknown payload、raw/canonical failureを分離する。
   - target missing+CAB、別 commitの各既存 finding、correction commit自身の既存 findingを件数・SHAで固定する。
   - unrelated rangeは従来green、通常 message-file は対象欠落の影響を受けない正例を置く。
3. 親 docs
   - `docs/ai-provenance.md` は非規範的な重複例を縮約し、9,000 bytes内で一回限り形式・status・range意味論を記す。
   - new D に対象限定、evidence、D95、history非改変、却下案を記録する。
   - failures は F25 / F37 と post-merge stale audit の再発を erratum として記録し、旧 worklog値は書き換えない。
4. correction commit
   - 通常 `AI-Agent` trailer と exact `AI-Agent-Correction` を同じ最終 trailer blockへ置く。
   - commit前 message-file、commit後 default history、`T^!`赤、`C^!`赤、`T^1..C`緑を実走する。

## 変異事前登録

| ID | operator | 第一失敗 assert |
|---|---|---|
| M1 | target membership 条件を除去 | `C^!` が orphan finding を失う |
| M2 | strict descendant 条件を除去 | sibling merge selected set が lineage finding を失う |
| M3 | production target / payload exact 比較を緩和 | literal pin または field-drift node が赤 |
| M4 | candidate cardinality `==1` を `>=1` 化 | 2 descendant correction の duplicate finding が消える |
| M5 | raw physical value 比較を除去 | continuation 形式が誤受理される |
| M6 | target 実欠落確認を除去 | valid target + correction が unneeded finding を失う |
| M7 | target 単位でなく missing 文言を全体削除 | 同 range の別 missing SHA が消える |
| M8 | correction commit 通常 green 条件を除去 | candidate は有効でも target missing finding が不正に消える |
| M9 | message-file の既存 candidate 探索を除去 | 2件目 pending correction preflight が誤受理される |
| M10 | forward-corrected status 出力を除去 | rc=0 実履歴 stdout の target/correction pin が消える |
| M11 | raw/canonical multiplicity 照合を除去 | body候補 + valid trailer の配置違反が消える |

- 各 mutant は上表 node の単一 finding / status 差を直接 assert し、単なる rc 赤を kill と数えない。
- correctionなしの unrelated range、通常 message-file、native-valid history を過剰拒否検出の正例とする。
- ancestry-path 中間 candidate 探索は selected-set cardinalityと独立に kill不能なので変異対象にしない。
