import difflib

def cerca(to_search, card_db):
    l = [card_db["data"][i]["name"] for i in range(len(card_db["data"]))]
    val = difflib.get_close_matches(word=to_search, possibilities=l, cutoff=0)
    return {"nome": val[0], "di_quanto": difflib.SequenceMatcher(None, to_search, val[0]).ratio()}
