def compute_mastery(success: int, failure: int) -> str:
    total = success + failure
    if total < 2:
        return "unknown"
    ratio = success / total
    # Trois échecs ou plus ne condamnent pas la notion à vie : de bonnes réussites récentes la sortent de "difficulty".
    if ratio < 0.4 or (failure >= 3 and ratio < 0.7):
        return "difficulty"
    if ratio < 0.7:
        return "to_strengthen"
    return "mastered"
