from app.services.mastery import compute_mastery


def test_fewer_than_two_attempts_is_unknown():
    assert compute_mastery(success=1, failure=0) == "unknown"


def test_three_or_more_failures_is_difficulty():
    assert compute_mastery(success=1, failure=3) == "difficulty"


def test_low_success_ratio_is_difficulty():
    assert compute_mastery(success=1, failure=2) == "difficulty"  # 1/3 < 0.4


def test_middling_ratio_is_to_strengthen():
    assert compute_mastery(success=3, failure=2) == "to_strengthen"  # 3/5 = 0.6


def test_high_ratio_is_mastered():
    assert compute_mastery(success=8, failure=1) == "mastered"  # 8/9 ≈ 0.89
