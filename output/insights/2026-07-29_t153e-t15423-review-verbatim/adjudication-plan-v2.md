# 段 4 裁定・plan v2 — [T-153(e)] + [T-154(2)(3)]

## 裁定

- A-1 (`---` divider): real / 採用 / scope 内。commit message parser は
  `interpret-trailers --parse --no-divider` を使う。
- A-2 = B-1 (ambient Git config): real / 採用 / scope 内。parser は repo 外 cwd、system/global
  config 無効化、`GIT_CONFIG_*` 注入除去、separator `:` 固定で canonical 化する。
- A-3 (単一 epoch): real / 部分採用 / scope 内。単一 HEAD epoch は採らず、各監査 commit の
  ancestry に policy needle の `-S` change が存在するかを検査する。policy 削除後も適用を維持し、
  別 branch の独立導入にも追随する。pre-policy range は非遡及契約どおり受理するため、
  「epoch 不在を常に rc=2」は refuted。
- A-4 = B-4 (raw grammar): real / 採用 / scope 内。候補は物理行の先頭で SP/HTAB を除いた後に
  case-insensitive `Co-Authored-By` + SP/HTAB + `:` が続く行。bullet/quote は本文として非候補、
  indent/fence 内の候補形は attribution と紛らわしいため拒否する。
- A-5 = B-3/B-4 (境界 matrix): real / 採用 / scope 内。CRLF、continuation、exact duplicate、
  divider、config alias、message-file、既定履歴、明示 range、別 lineage、policy 削除後を固定する。
- A-6 = B-2 (`SELF_LIMITS`): real / 採用 / scope 内。brief P2 を覆し、
  `PROVENANCE_LIMITS` を `all_limits` と budget test 集合だけへ合流し、dispatch allowlist 外を pin する。
- A-7 (183 bytes): real / 採用 / scope 内。policy は追記でなく置換・縮約し、安全義務を保った
  9,000 bytes 以下を停止条件とする。上限変更はしない。
- A-8 (既存履歴内訳): real / nit。互換観測であり安全根拠にせず、実装 blocker にはしない。
- B-5 (parse 一回): real / nit。各 validator 間の二重 subprocess は受理集合へ影響せず scope 外。
  canonical parser の共用だけ行い、最適化を完了条件にしない。
- B-6/B-7: refuted。living docs、budget consumer、T-153(e) の新 D closure は plan v2 で充足可能。

## 実装 plan v2

1. `tools/check_ai_provenance.py`: canonical trailer parser、raw CAB candidate count、CAB finding を
   既存 AI-Agent finding と直積し、`none` の早期 return でも失わない。
2. 履歴経路は commit ごとに policy needle の ancestry 実在を検査し、該当 commit だけ CAB gate を
   適用する。`--message-file` は working policy の現行規約として常時適用する。
3. `orchestrator/tests/test_check_ai_provenance.py`: canonical parser の正負外延と、
   message-file / default history / range / lineage / deletion の境界を固定する。
4. `tools/check_docs.py`: 独立 `PROVENANCE_LIMITS = {"docs/ai-provenance.md": TextLimit(9_000)}`。
5. `orchestrator/tests/test_check_docs.py`: 9,000 exact、9,001 reject、registry literal、
   dispatch allowlist 非拡張、budget-governed 集合を固定する。
6. 親が `docs/ai-provenance.md`、新 D98、worklog、逐語・変異台帳を記録する。実装子は docs を触らない。

## 変異事前登録

- M1: `--no-divider` を外す。divider 後の真の trailer 正例または trailer 後の本文負例だけが赤。
- M2: canonical config 隔離を外す。ambient alias が分断 raw CAB と別 alias trailer を相殺する負例が赤。
- M3: 件数を boolean/set に縮退。同一値 duplicate の正例または body+final 同値 CAB 負例が赤。
- M4: `AI-Agent: none` 早期 return から CAB finding を落とす。分断 CAB + final none 負例が赤。
- M5: ancestry gate を常時適用へ変える。pre-policy 分断 CAB commit の非遡及正例が赤。
- M6: default history / `--range` / message-file のいずれかから CAB finding を外す。
  各経路の独立 positive-control が赤。
- M7: `PROVENANCE_LIMITS` を `all_limits` から外す。9,001-byte 負例が受理される。
- 過剰拒否 control: CAB 無し、contiguous mixed-case/colon-space、exact duplicate、CAB + none、
  bullet/quote 本文、Markdown divider を含む本文 + 最終 contiguous trailer、9,000-byte exact を緑固定する。

## 所有

- Codex author 1 unit: checker 2 本 + 境界テスト 2 本。相互依存する単一受理集合変更のため一枚岩。
- 親: brief・裁定・docs・統合・全走・mutation・commit・local main。
