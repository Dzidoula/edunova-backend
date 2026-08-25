def compute_mastery(success: int, failure: int) -> str:
    total = success + failure
    if total < 2:
        return "unknown"
    if failure >= 3 or (success / total) < 0.4:
        return "difficulty"
    if (success / total) < 0.7:
        return "to_strengthen"
    return "mastered"
