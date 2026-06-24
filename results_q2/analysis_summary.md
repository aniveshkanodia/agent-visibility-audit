# Experiment Analysis Summary

## Pick rates by model and arm

| model | arm | picks | reps | pick_rate | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- | --- |
| claude-haiku-4-5 | cite_source | 14 | 30 | 0.467 | 0.302 | 0.639 |
| claude-haiku-4-5 | control | 4 | 30 | 0.133 | 0.053 | 0.297 |
| claude-haiku-4-5 | keyword_stuff | 11 | 30 | 0.367 | 0.219 | 0.545 |
| claude-haiku-4-5 | problem_match | 18 | 30 | 0.6 | 0.423 | 0.754 |
| claude-haiku-4-5 | quotation | 22 | 30 | 0.733 | 0.556 | 0.858 |
| claude-haiku-4-5 | statistic | 13 | 30 | 0.433 | 0.274 | 0.608 |
| gemini-3.5-flash | cite_source | 0 | 30 | 0.0 | 0.0 | 0.114 |
| gemini-3.5-flash | control | 0 | 30 | 0.0 | 0.0 | 0.114 |
| gemini-3.5-flash | keyword_stuff | 3 | 30 | 0.1 | 0.035 | 0.256 |
| gemini-3.5-flash | problem_match | 1 | 30 | 0.033 | 0.006 | 0.167 |
| gemini-3.5-flash | quotation | 0 | 30 | 0.0 | 0.0 | 0.114 |
| gemini-3.5-flash | statistic | 3 | 30 | 0.1 | 0.035 | 0.256 |

## Lift vs control

| model | arm | pick_rate | control_rate | lift | lift_ci_low | lift_ci_high | picks | reps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| claude-haiku-4-5 | cite_source | 0.467 | 0.133 | 0.333 | 0.006 | 0.585 | 14 | 30 |
| claude-haiku-4-5 | keyword_stuff | 0.367 | 0.133 | 0.233 | -0.078 | 0.492 | 11 | 30 |
| claude-haiku-4-5 | problem_match | 0.6 | 0.133 | 0.467 | 0.126 | 0.701 | 18 | 30 |
| claude-haiku-4-5 | quotation | 0.733 | 0.133 | 0.6 | 0.259 | 0.805 | 22 | 30 |
| claude-haiku-4-5 | statistic | 0.433 | 0.133 | 0.3 | -0.023 | 0.555 | 13 | 30 |
| gemini-3.5-flash | cite_source | 0.0 | 0.0 | 0.0 | -0.114 | 0.114 | 0 | 30 |
| gemini-3.5-flash | keyword_stuff | 0.1 | 0.0 | 0.1 | -0.079 | 0.256 | 3 | 30 |
| gemini-3.5-flash | problem_match | 0.033 | 0.0 | 0.033 | -0.108 | 0.167 | 1 | 30 |
| gemini-3.5-flash | quotation | 0.0 | 0.0 | 0.0 | -0.114 | 0.114 | 0 | 30 |
| gemini-3.5-flash | statistic | 0.1 | 0.0 | 0.1 | -0.079 | 0.256 | 3 | 30 |