# Experiment Analysis Summary

## Pick rates by model and arm

| model | arm | picks | reps | pick_rate | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- | --- |
| claude-haiku-4-5 | cite_source | 8 | 10 | 0.8 | 0.49 | 0.943 |
| claude-haiku-4-5 | control | 1 | 10 | 0.1 | 0.018 | 0.404 |
| claude-haiku-4-5 | keyword_stuff | 9 | 10 | 0.9 | 0.596 | 0.982 |
| claude-haiku-4-5 | problem_match | 9 | 10 | 0.9 | 0.596 | 0.982 |
| claude-haiku-4-5 | quotation | 9 | 10 | 0.9 | 0.596 | 0.982 |
| claude-haiku-4-5 | statistic | 4 | 10 | 0.4 | 0.168 | 0.687 |
| gemini-3.5-flash | cite_source | 10 | 10 | 1.0 | 0.722 | 1.0 |
| gemini-3.5-flash | control | 5 | 10 | 0.5 | 0.237 | 0.763 |
| gemini-3.5-flash | keyword_stuff | 10 | 10 | 1.0 | 0.722 | 1.0 |
| gemini-3.5-flash | problem_match | 10 | 10 | 1.0 | 0.722 | 1.0 |
| gemini-3.5-flash | quotation | 10 | 10 | 1.0 | 0.722 | 1.0 |
| gemini-3.5-flash | statistic | 10 | 10 | 1.0 | 0.722 | 1.0 |

## Lift vs control

| model | arm | pick_rate | control_rate | lift | lift_ci_low | lift_ci_high | picks | reps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| claude-haiku-4-5 | cite_source | 0.8 | 0.1 | 0.7 | 0.086 | 0.925 | 8 | 10 |
| claude-haiku-4-5 | keyword_stuff | 0.9 | 0.1 | 0.8 | 0.192 | 0.964 | 9 | 10 |
| claude-haiku-4-5 | problem_match | 0.9 | 0.1 | 0.8 | 0.192 | 0.964 | 9 | 10 |
| claude-haiku-4-5 | quotation | 0.9 | 0.1 | 0.8 | 0.192 | 0.964 | 9 | 10 |
| claude-haiku-4-5 | statistic | 0.4 | 0.1 | 0.3 | -0.236 | 0.669 | 4 | 10 |
| gemini-3.5-flash | cite_source | 1.0 | 0.5 | 0.5 | -0.041 | 0.763 | 10 | 10 |
| gemini-3.5-flash | keyword_stuff | 1.0 | 0.5 | 0.5 | -0.041 | 0.763 | 10 | 10 |
| gemini-3.5-flash | problem_match | 1.0 | 0.5 | 0.5 | -0.041 | 0.763 | 10 | 10 |
| gemini-3.5-flash | quotation | 1.0 | 0.5 | 0.5 | -0.041 | 0.763 | 10 | 10 |
| gemini-3.5-flash | statistic | 1.0 | 0.5 | 0.5 | -0.041 | 0.763 | 10 | 10 |