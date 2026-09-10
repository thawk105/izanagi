# T-182 段1 probe 生実測 (親が実行)

## 可用性 (trivial prompt, reasoning 既定 xhigh)
- gpt-5.4-mini: rc=0
- gpt-5.4-nano: rc=1
- gpt-5.1-codex-mini: rc=1
- gpt-5.6-luna: rc=0
- gpt-5.6-terra: rc=0

## reasoning=max + ファイル読取 (prompt2.txt, prompt_hash 45a76772...)
- gpt-5.6-sol: rc=0 wall=49s
- gpt-5.6-luna: rc=0 wall=70s
- gpt-5.6-terra: rc=0 wall=99s
- gpt-5.4-mini: rc=1 wall=4s

## reasoning='ultra' (不正値) probe
- gpt-5.6-sol: rc=0
- gpt-5.6-luna: rc=0
- gpt-5.6-terra: rc=0
- gpt-5.4-mini: rc=1

## 同時実行 (交絡)
- pgrep -c -f codex = 28 (T-126 / T-180 / T-181 / ai-provenance-forward-fix / dev-wave-skill が並行)
