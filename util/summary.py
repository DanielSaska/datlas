


def addUniqueEntry(entry,summary):
    if "entries" not in summary:
        summary["entries"] = [entry]
        return summary
    for e in summary["entries"]:
        if e["name"] == entry["name"]:
            return summary
    summary["entries"].append(entry)
    return summary
