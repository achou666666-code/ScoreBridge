from fixture_score import fixture_score
from scorebridge.score_ir import save_score
save_score(fixture_score(), "examples/vertical-slice.score.json")
